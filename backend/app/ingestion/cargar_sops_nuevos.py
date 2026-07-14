"""Crea SOPs nuevos (formato estándar de 9 campos) para los departamentos nuevos que
quedaron con poca cobertura (Spa, Lavandería, Mercadeo Digital, Transporte, Comedor de
Empleados, Concierge). Contenido propio de CRC redactado con subagentes; congelado en
seed/ingesta/sops_nuevos_departamentos.json.

Cada SOP toma su código de un ÁREA existente (prefijo) y su departamento dueño del nuevo
mapa. Idempotente: no duplica por (departamento + nombre normalizado).

Uso:  python -m app.ingestion.cargar_sops_nuevos
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
from app.models.sop import SopMaster, SopMasterVersion
from app.services.numeracion import siguiente_codigo_area

RAIZ = Path(__file__).resolve().parents[3]
DATOS = RAIZ / "seed" / "ingesta" / "sops_nuevos_departamentos.json"
ADMIN_EMAIL = "Finance@thecostaricacollection.com"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


async def _uno(db, stmt):
    return (await db.execute(stmt)).scalars().first()


def _txt(v):
    """Los campos de texto pueden venir como lista desde el generador; se unen."""
    if isinstance(v, list):
        return "; ".join(str(x) for x in v) or None
    return v or None


async def cargar() -> None:
    datos = json.loads(DATOS.read_text(encoding="utf-8"))

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
        # Índice de SOPs existentes por (depto, nombre normalizado) para no duplicar.
        existentes = list((await db.execute(select(SopMaster))).scalars())
        vistos = {(s.departamento_id, _norm(s.nombre)) for s in existentes}

        creados = 0
        for e in datos:
            area = areas.get(e["area"])
            depto = deptos.get(e["departamento"])
            if not area or not depto:
                continue
            clave = (depto.id, _norm(e["nombre"]))
            if clave in vistos:
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
                nombre=e["nombre"], departamento_id=depto.id,
                proposito=_txt(e.get("proposito")),
                evaluacion_riesgos=_txt(e.get("evaluacion_riesgos")),
                controles_existentes=_txt(e.get("controles_existentes")),
                procedimiento={"secciones": e.get("procedimiento", [])},
                responsables=_txt(e.get("responsables")),
                evidencia=_txt(e.get("evidencia")),
                frecuencia_revision=frec,
                estado=EstadoDocumento.borrador, version_actual=1,
                creado_por=admin.id if admin else None,
            )
            db.add(sop)
            await db.flush()
            vistos.add(clave)
            db.add(SopMasterVersion(
                sop_master_id=sop.id, version=1,
                snapshot={"codigo": sop.codigo, "nombre": sop.nombre,
                          "origen": "SOP nuevo de departamento (contenido propio CRC)"},
                nota_cambio="Creación (SOP de departamento nuevo).",
                estado_en_version="borrador", creado_por=admin.id if admin else None,
            ))
            creados += 1
        await db.commit()
    print(f"SOPs nuevos de departamento creados: {creados}")


if __name__ == "__main__":
    asyncio.run(cargar())
