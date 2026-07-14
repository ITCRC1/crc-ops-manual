"""Etapa 3 — Carga de los 4 borradores del pack financiero USALI (§10.7).

Contenido ORIGINAL de CRC alineado al estándar (generado y revisado adversarialmente;
ver seed/ingesta/usali_drafts.json). Se insertan en sop_master (estado borrador) en las
áreas FIN/GOV, tomando el siguiente número atómico del contador por área. Idempotente
(por nombre). Snapshot v1 incluido.

Uso:
    python -m app.ingestion.cargar_usali
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.ingestion.cargar_sops import _uno
from app.models import Area, ContadorArea, SopMaster, SopMasterVersion, Usuario
from app.models.base import EstadoDocumento, FrecuenciaRevision, TipoDocumento

RAIZ = Path(__file__).resolve().parents[3]
ING = RAIZ / "seed" / "ingesta"
ADMIN_EMAIL = "Finance@thecostaricacollection.com"


async def _siguiente_numero(db, area) -> int:
    cont = await _uno(db, select(ContadorArea).where(ContadorArea.area_id == area.id))
    if not cont:
        cont = ContadorArea(area_id=area.id, ultimo_numero=0)
        db.add(cont)
        await db.flush()
    cont.ultimo_numero += 1
    return cont.ultimo_numero


async def cargar() -> None:
    drafts = json.loads((ING / "usali_drafts.json").read_text(encoding="utf-8"))["drafts"]
    async with AsyncSessionLocal() as db:
        admin = await _uno(db, select(Usuario).where(Usuario.email == ADMIN_EMAIL))
        areas = {a.codigo: a for a in (await db.execute(select(Area))).scalars()}

        creados = 0
        for dr in drafts:
            b = dr["draft"]
            nombre = b["titulo"]
            if await _uno(db, select(SopMaster).where(SopMaster.nombre == nombre)):
                continue
            area = areas[dr["area"]]
            numero = await _siguiente_numero(db, area)
            codigo = f"{area.codigo}-{numero:04d}"
            sop = SopMaster(
                numero=numero,
                area_id=area.id,
                codigo=codigo,
                tipo=TipoDocumento(dr["tipo"]),
                nombre=nombre,
                proposito=b.get("proposito"),
                evaluacion_riesgos=b.get("evaluacion_riesgos"),
                controles_existentes=b.get("controles_existentes"),
                procedimiento={"secciones": b.get("procedimiento", [])},
                responsables=b.get("responsables"),
                evidencia=b.get("evidencia"),
                frecuencia_revision=FrecuenciaRevision(b["frecuencia_revision"]),
                estado=EstadoDocumento.borrador,
                version_actual=1,
                creado_por=admin.id if admin else None,
            )
            db.add(sop)
            await db.flush()
            db.add(SopMasterVersion(
                sop_master_id=sop.id, version=1,
                snapshot={"codigo": codigo, "nombre": nombre, "area": dr["area"],
                          "origen": "pack financiero USALI (borrador original CRC)",
                          "proposito": sop.proposito, "procedimiento": sop.procedimiento},
                nota_cambio="Borrador del pack financiero USALI (Etapa 3, contenido original CRC).",
                estado_en_version="borrador",
                creado_por=admin.id if admin else None,
            ))
            creados += 1
            print(f"  {codigo}  {nombre[:60]}")
        await db.commit()
    print(f"Borradores USALI creados: {creados}")


if __name__ == "__main__":
    asyncio.run(cargar())
