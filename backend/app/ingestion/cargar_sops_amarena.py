"""Entrega ordenada del Procedimiento de Contabilidad General de Amarena como SOPs.

Para cada política del manual (5.1–7): si ya existe un SOP maestro que la cubre, lo marca
como política de Amarena (origen_propiedad='AMA', prioridad de transferencia); si no
existe, crea el SOP nuevo (formato de 9 campos, wording del documento con neutralidad de
sistema). Mapeo curado en seed/ingesta/sops_amarena_contab.json (producido por el
workflow de cobertura+redacción+verificación). Idempotente.

Neutralidad: los procedimientos NO nombran el PMS/sistema (Amarena usa Skills4IT; se
adapta en el despliegue). La marca origen_propiedad='AMA' permite filtrarlos para el
despliegue final a Amarena.

Uso:  python -m app.ingestion.cargar_sops_amarena
"""

import asyncio
import json
import re
import unicodedata
from pathlib import Path

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models import Departamento, Usuario
from app.models.base import EstadoDocumento, FrecuenciaRevision, TipoDocumento
from app.models.catalogos import Area
from app.models.sop import SopMaster, SopMasterDepartamentoAfectado, SopMasterVersion
from app.services.numeracion import siguiente_codigo_area

RAIZ = Path(__file__).resolve().parents[3]
DATOS = RAIZ / "seed" / "ingesta" / "sops_amarena_contab.json"
ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ORIGEN = "AMA"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def _txt(v):
    if isinstance(v, list):
        return "; ".join(str(x) for x in v) or None
    return v or None


async def _uno(db, stmt):
    return (await db.execute(stmt)).scalars().first()


async def cargar() -> None:
    if not DATOS.exists():
        print("SOPs Amarena: (sin mapeo sops_amarena_contab.json; se omite)")
        return
    datos = json.loads(DATOS.read_text(encoding="utf-8"))
    marcar = datos.get("marcar", [])
    crear = datos.get("crear", [])

    async with AsyncSessionLocal() as db:
        admin = await _uno(db, select(Usuario).where(Usuario.email == ADMIN_EMAIL))
        areas = {a.codigo: a for a in (await db.execute(select(Area))).scalars()}
        deptos = {
            d.codigo: d
            for d in (
                await db.execute(
                    select(Departamento).where(Departamento.propiedad_propietaria_id.is_(None))
                )
            ).scalars()
        }
        existentes = list((await db.execute(select(SopMaster))).scalars())
        por_codigo = {s.codigo: s for s in existentes}
        vistos = {(s.departamento_id, _norm(s.nombre)) for s in existentes}

        # 1) Marcar SOPs existentes que ya cubren políticas de Amarena.
        marcados = 0
        for cod in marcar:
            s = por_codigo.get(cod)
            if s and s.eliminado_en is None and s.origen_propiedad != ORIGEN:
                s.origen_propiedad = ORIGEN
                marcados += 1

        # 2) Crear los SOPs nuevos (huecos del manual no cubiertos).
        creados = 0
        for e in crear:
            area = areas.get(e.get("area", "FIN")) or areas.get("FIN")
            depto = deptos.get(e.get("dept", "FIN"))
            if not area or not depto:
                continue
            clave = (depto.id, _norm(e["titulo"]))
            if clave in vistos:
                # Ya existe: marcarlo y, si sigue en borrador, refrescar su contenido
                # desde el seed (permite mejorar el wording sin duplicar).
                existente = next(
                    (s for s in existentes if s.departamento_id == depto.id and _norm(s.nombre) == _norm(e["titulo"])),
                    None,
                )
                if existente:
                    if existente.origen_propiedad != ORIGEN:
                        existente.origen_propiedad = ORIGEN
                        marcados += 1
                    if existente.estado == EstadoDocumento.borrador:
                        existente.proposito = _txt(e.get("proposito"))
                        existente.evaluacion_riesgos = _txt(e.get("evaluacion_riesgos"))
                        existente.controles_existentes = _txt(e.get("controles_existentes"))
                        existente.procedimiento = {"secciones": e.get("procedimiento", [])}
                        existente.responsables = _txt(e.get("responsables"))
                        existente.evidencia = _txt(e.get("evidencia"))
                        frec2 = None
                        if e.get("frecuencia_revision"):
                            try:
                                frec2 = FrecuenciaRevision(e["frecuencia_revision"])
                            except ValueError:
                                frec2 = None
                        existente.frecuencia_revision = frec2
                continue
            frec = None
            if e.get("frecuencia_revision"):
                try:
                    frec = FrecuenciaRevision(e["frecuencia_revision"])
                except ValueError:
                    frec = None
            _num, codigo = await siguiente_codigo_area(db, area)
            sop = SopMaster(
                numero=_num, area_id=area.id, codigo=codigo, tipo=TipoDocumento.sop,
                nombre=e["titulo"], departamento_id=depto.id,
                proposito=_txt(e.get("proposito")),
                evaluacion_riesgos=_txt(e.get("evaluacion_riesgos")),
                controles_existentes=_txt(e.get("controles_existentes")),
                procedimiento={"secciones": e.get("procedimiento", [])},
                responsables=_txt(e.get("responsables")),
                evidencia=_txt(e.get("evidencia")),
                frecuencia_revision=frec,
                estado=EstadoDocumento.borrador, version_actual=1,
                creado_por=admin.id if admin else None,
                origen_propiedad=ORIGEN,
            )
            db.add(sop)
            await db.flush()
            vistos.add(clave)
            # departamentos afectados
            for acod in e.get("afectados", []) or []:
                dep = deptos.get(acod)
                if dep and dep.id != depto.id:
                    db.add(SopMasterDepartamentoAfectado(sop_master_id=sop.id, departamento_id=dep.id))
            db.add(SopMasterVersion(
                sop_master_id=sop.id, version=1,
                snapshot={"codigo": sop.codigo, "nombre": sop.nombre,
                          "origen": "SOP de política de Amarena (contabilidad), neutralizado"},
                nota_cambio="Creación (política de contabilidad de Amarena).",
                estado_en_version="borrador", creado_por=admin.id if admin else None,
            ))
            creados += 1
        await db.commit()
    print(f"SOPs Amarena: marcados existentes {marcados} | creados nuevos {creados}")


if __name__ == "__main__":
    asyncio.run(cargar())
