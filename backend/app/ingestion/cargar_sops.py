"""Etapa 3 — Carga de los cuerpos de SOP en sop_master (tras aprobación, §10.5).

Idempotente. Carga los SOPs del índice curado que tienen cuerpo emparejado en el manual
Word (estado inicial `borrador`). Omite los `solo_excel` (sin cuerpo desarrollado).

Uso:
    python -m app.ingestion.cargar_sops
"""

import asyncio
import json
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models import (
    Area,
    ContadorArea,
    Departamento,
    SopMaster,
    SopMasterVersion,
    Usuario,
)
from app.models.base import EstadoDocumento, FrecuenciaRevision, TipoDocumento

RAIZ = Path(__file__).resolve().parents[3]
ING = RAIZ / "seed" / "ingesta"
ADMIN_EMAIL = "Finance@thecostaricacollection.com"

DEPTO_KEYWORDS = [
    ("finanz", "FIN"), ("contab", "FIN"), ("tesor", "FIN"),
    ("cocina", "KIT"), ("kitchen", "KIT"),
    ("food", "FB"), ("beverage", "FB"), ("aliment", "FB"), ("a&b", "FB"), ("a & b", "FB"),
    ("recursos humanos", "HR"), ("rrhh", "HR"),
    ("sistemas", "IT"), ("tecnolog", "IT"), ("informaci", "IT"),
    ("front", "REC"), ("recep", "REC"), ("guest", "REC"), ("concierge", "REC"),
    ("ventas", "SM"), ("marketing", "SM"), ("comercial", "SM"), ("sales", "SM"),
    ("mantenim", "MANT"), ("segurid", "SEG"), ("reserva", "RES"),
]

FREC = [("mensual", FrecuenciaRevision.mensual), ("trimestral", FrecuenciaRevision.trimestral),
        ("semestral", FrecuenciaRevision.semestral), ("anual", FrecuenciaRevision.anual)]


def _cargar_json(nombre: str):
    return json.loads((ING / nombre).read_text(encoding="utf-8"))


async def _uno(db, stmt):
    return (await db.execute(stmt)).scalar_one_or_none()


def _construir_match(excel, word, wf) -> dict:
    word_norm = defaultdict(list)
    for w in word:
        word_norm[w["norm"]].append(w["codigo"])
    match = {}
    for e in excel:
        if e["norm"] in word_norm:
            match[e["codigo"]] = {"word": [word_norm[e["norm"]][0]], "tipo": "igual"}
    for r in wf["resultados"]:
        v = r["verdicto"]
        match[r["codigo"]] = {"word": v["word_matches_final"], "tipo": v["tipo_relacion_final"]}
    return match


def _frecuencia(texto: str) -> FrecuenciaRevision:
    t = (texto or "").lower()
    # busca la última mención de periodo explícito (p.ej. "Revisión del SOP: Anual")
    encontrada = None
    for palabra, val in FREC:
        if palabra in t:
            encontrada = val
    return encontrada or FrecuenciaRevision.por_cambio


def _procedimiento(parrafos: list[str]) -> dict:
    return {"secciones": parrafos}


async def cargar() -> None:
    excel = _cargar_json("excel_index.json")
    word = _cargar_json("word_index.json")
    wf = _cargar_json("reconciliation_matches.json")
    bodies = _cargar_json("word_bodies.json")
    match = _construir_match(excel, word, wf)

    async with AsyncSessionLocal() as db:
        admin = await _uno(db, select(Usuario).where(Usuario.email == ADMIN_EMAIL))
        areas = {a.codigo: a for a in (await db.execute(select(Area))).scalars()}
        dept_stmt = select(Departamento).where(Departamento.propiedad_propietaria_id.is_(None))
        deptos = {d.codigo: d for d in (await db.execute(dept_stmt)).scalars()}

        creados, omitidos = 0, []
        max_num = defaultdict(int)

        for e in excel:
            ec = e["codigo"]
            m = match.get(ec)
            words = m["word"] if m else []
            cuerpos = [bodies[w] for w in words if w in bodies]
            if not cuerpos:
                omitidos.append(ec)  # solo_excel (sin cuerpo)
                continue

            # idempotencia: por código o por nombre (el código puede haber cambiado por
            # reclasificación de área, p.ej. bodegas FBS→FIN).
            if await _uno(db, select(SopMaster).where(SopMaster.codigo == ec)):
                continue
            if await _uno(db, select(SopMaster).where(SopMaster.nombre == e["nombre"])):
                continue

            prefijo = e["prefijo"]
            area = areas.get(prefijo)
            if not area:
                omitidos.append(ec)
                continue
            numero = int(ec.split("-")[1])
            max_num[prefijo] = max(max_num[prefijo], numero)

            # fusión: concatena varios cuerpos Word; 1:1/división: un solo cuerpo
            def join(campo):
                return "\n\n".join(c[campo] for c in cuerpos if c.get(campo)).strip() or None

            proc_parrafos = []
            for c in cuerpos:
                proc_parrafos += c.get("procedimiento", [])

            depto_txt = " ".join(c.get("departamento", "") for c in cuerpos).lower()
            depto_id = None
            for kw, dcod in DEPTO_KEYWORDS:
                if kw in depto_txt and dcod in deptos:
                    depto_id = deptos[dcod].id
                    break

            sop = SopMaster(
                numero=numero,
                area_id=area.id,
                codigo=ec,
                tipo=TipoDocumento.sop,
                nombre=e["nombre"],
                departamento_id=depto_id,
                proposito=join("proposito"),
                evaluacion_riesgos=join("evaluacion_riesgos"),
                controles_existentes=join("controles_existentes"),
                procedimiento=_procedimiento(proc_parrafos),
                responsables=join("responsables"),
                evidencia=join("evidencia"),
                frecuencia_revision=_frecuencia(
                    " ".join(c.get("frecuencia_revision", "") for c in cuerpos)
                ),
                estado=EstadoDocumento.borrador,
                version_actual=1,
                creado_por=admin.id if admin else None,
            )
            db.add(sop)
            await db.flush()
            db.add(SopMasterVersion(
                sop_master_id=sop.id,
                version=1,
                snapshot={
                    "codigo": ec, "nombre": e["nombre"], "area": e["area"],
                    "word_matches": words, "tipo_relacion": m["tipo"],
                    "proposito": sop.proposito, "evaluacion_riesgos": sop.evaluacion_riesgos,
                    "controles_existentes": sop.controles_existentes,
                    "procedimiento": sop.procedimiento, "responsables": sop.responsables,
                    "evidencia": sop.evidencia,
                },
                nota_cambio="Carga inicial desde el manual (Etapa 3).",
                estado_en_version="borrador",
                creado_por=admin.id if admin else None,
            ))
            creados += 1

        # Contadores por área (para numeración futura)
        for prefijo, mx in max_num.items():
            area = areas.get(prefijo)
            cont = await _uno(db, select(ContadorArea).where(ContadorArea.area_id == area.id))
            if not cont:
                db.add(ContadorArea(area_id=area.id, ultimo_numero=mx))
            elif cont.ultimo_numero < mx:
                cont.ultimo_numero = mx

        await db.commit()
    print(f"SOPs creados: {creados}  | omitidos (sin cuerpo): {omitidos}")


if __name__ == "__main__":
    asyncio.run(cargar())
