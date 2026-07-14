"""Etapa 3 — Carga de los 24 Descriptores de Puesto (§10.6).

Crea descriptor_puesto_master (estado borrador) con jerarquía reporta_a (FK self),
niveles 1-4 derivados del título (validados contra la narrativa del organigrama) y
snapshot v1. Idempotente.

Uso:
    python -m app.ingestion.cargar_descriptores
"""

import asyncio
import json
import re
import unicodedata
from pathlib import Path

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models import Departamento, DescriptorPuestoMaster, DescriptorPuestoVersion, Usuario
from app.models.base import EstadoDocumento

RAIZ = Path(__file__).resolve().parents[3]
ING = RAIZ / "seed" / "ingesta"
ADMIN_EMAIL = "Finance@thecostaricacollection.com"

# Reutiliza utilidades de la carga de SOPs
from app.ingestion.cargar_sops import DEPTO_KEYWORDS, _uno  # noqa: E402

SEC = {
    "proposito": "Propósito del Puesto",
    "responsabilidades": "Responsabilidades Clave",
    "nivel_autoridad": "Nivel de Autoridad",
    "kpis": "Indicadores Clave de Desempeño (KPIs)",
    "competencias": "Competencias Requeridas",
    "requisitos_fisicos": "Requisitos Físicos y del Entorno",
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def nivel_jerarquico(titulo: str) -> int:
    t = titulo.upper()
    if "GENERAL MANAGER" in t:
        return 1
    if any(k in t for k in ("CHIEF", "DIRECTOR", "CONTROLLER")):
        return 2
    if "ASISTENTE" in t or "ASSISTANT" in t:
        return 4
    jefaturas = ("GERENTE", "MANAGER", "SUPERVISOR", "COORDINADOR", "CHEF", "AUDITOR", "JEFE")
    if any(k in t for k in jefaturas):
        return 3
    return 4


def _seccion(jd: dict, nombre: str) -> list[str]:
    return jd["secciones"].get(nombre, [])


async def cargar() -> None:
    jds = json.loads((ING / "jds.json").read_text(encoding="utf-8"))

    def por_codigo(cod):
        return select(DescriptorPuestoMaster).where(DescriptorPuestoMaster.codigo == cod)

    async with AsyncSessionLocal() as db:
        admin = await _uno(db, select(Usuario).where(Usuario.email == ADMIN_EMAIL))
        dept_stmt = select(Departamento).where(Departamento.propiedad_propietaria_id.is_(None))
        deptos = {d.codigo: d for d in (await db.execute(dept_stmt)).scalars()}

        # Paso 1: crear todos (sin reporta_a) y recordar título->id
        titulo_a_id: dict[str, str] = {}
        creados = 0
        for jd in jds:
            if await _uno(db, por_codigo(jd["codigo"])):
                continue
            depto_txt = jd["departamento"].lower()
            depto_id = None
            for kw, dcod in DEPTO_KEYWORDS:
                if kw in depto_txt and dcod in deptos:
                    depto_id = deptos[dcod].id
                    break
            titulo = jd["titulo"] + (f" ({jd['subtitulo']})" if jd["subtitulo"] else "")
            requisitos = "\n".join(
                _seccion(jd, SEC["competencias"]) + _seccion(jd, SEC["requisitos_fisicos"])
            )
            d = DescriptorPuestoMaster(
                codigo=jd["codigo"],
                titulo=titulo,
                departamento_id=depto_id,
                nivel_jerarquico=nivel_jerarquico(jd["titulo"]),
                proposito="\n".join(_seccion(jd, SEC["proposito"])).strip() or None,
                responsabilidades=_seccion(jd, SEC["responsabilidades"]),
                nivel_autoridad="\n".join(_seccion(jd, SEC["nivel_autoridad"])).strip() or None,
                kpis=_seccion(jd, SEC["kpis"]),
                requisitos=requisitos.strip() or None,
                estado=EstadoDocumento.borrador,
                version_actual=1,
            )
            db.add(d)
            await db.flush()
            titulo_a_id[_norm(jd["titulo"])] = d.id
            creados += 1

        # Paso 2: resolver reporta_a por título (el más largo contenido en el texto)
        todos = {_norm(x["titulo"]): x for x in jds}
        resueltos = 0
        for jd in jds:
            d = await _uno(db, por_codigo(jd["codigo"]))
            if not d:
                continue
            ra = _norm(jd["reporta_a"])
            candidatos = [t for t in todos if t and t in ra and t != _norm(jd["titulo"])]
            if candidatos:
                mejor = max(candidatos, key=len)
                dest = await _uno(db, por_codigo(todos[mejor]["codigo"]))
                if dest and d.reporta_a_id != dest.id:
                    d.reporta_a_id = dest.id
                    resueltos += 1
            # snapshot v1 (solo la primera vez)
            ver_stmt = select(DescriptorPuestoVersion).where(
                DescriptorPuestoVersion.descriptor_puesto_master_id == d.id
            )
            if not await _uno(db, ver_stmt):
                db.add(DescriptorPuestoVersion(
                    descriptor_puesto_master_id=d.id, version=1,
                    snapshot={"codigo": d.codigo, "titulo": d.titulo,
                              "nivel_jerarquico": d.nivel_jerarquico,
                              "reporta_a": jd["reporta_a"], "proposito": d.proposito,
                              "responsabilidades": d.responsabilidades, "kpis": d.kpis},
                    nota_cambio="Carga inicial desde Job_Descriptions.docx (Etapa 3).",
                    estado_en_version="borrador",
                    creado_por=admin.id if admin else None,
                ))
        await db.commit()
    print(f"Descriptores creados: {creados}  | reporta_a resueltos: {resueltos}")


if __name__ == "__main__":
    asyncio.run(cargar())
