"""Etapa 3+ — Carga de los borradores de SOP que cierran las brechas del gap analysis.

Contenido ORIGINAL de CRC (generado y revisado adversarialmente; ver
seed/ingesta/gap_drafts.json). Se insertan en sop_master (estado borrador) en el área
asignada (CT/FIN/HR), con número atómico del contador por área. Idempotente (por nombre).

Uso:
    python -m app.ingestion.cargar_brechas
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.ingestion.cargar_sops import _uno
from app.ingestion.cargar_usali import _siguiente_numero
from app.models import Area, SopMaster, SopMasterVersion, Usuario
from app.models.base import EstadoDocumento, FrecuenciaRevision, TipoDocumento

RAIZ = Path(__file__).resolve().parents[3]
ING = RAIZ / "seed" / "ingesta"
ADMIN_EMAIL = "Finance@thecostaricacollection.com"


async def cargar() -> None:
    data = json.loads((ING / "gap_drafts.json").read_text(encoding="utf-8"))
    drafts = data["drafts"]
    # metadatos (area/tipo) por clave desde gap_topics
    _tops = json.loads((ING / "gap_topics.json").read_text(encoding="utf-8"))
    topics = {t["clave"]: t for t in _tops}

    async with AsyncSessionLocal() as db:
        admin = await _uno(db, select(Usuario).where(Usuario.email == ADMIN_EMAIL))
        areas = {a.codigo: a for a in (await db.execute(select(Area))).scalars()}

        creados = 0
        for dr in drafts:
            b = dr["draft"]
            meta = topics.get(dr["clave"])
            if not meta:
                continue
            nombre = b["titulo"]
            if await _uno(db, select(SopMaster).where(SopMaster.nombre == nombre)):
                continue
            area = areas[meta["area"]]
            numero = await _siguiente_numero(db, area)
            codigo = f"{area.codigo}-{numero:04d}"
            sop = SopMaster(
                numero=numero,
                area_id=area.id,
                codigo=codigo,
                tipo=TipoDocumento(meta["tipo"]),
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
                snapshot={"codigo": codigo, "nombre": nombre, "area": meta["area"],
                          "origen": "borrador para brecha de control (gap analysis)",
                          "categoria_brecha": meta["categoria"],
                          "proposito": sop.proposito,
                          "procedimiento": sop.procedimiento},
                nota_cambio="Borrador para cerrar brecha de control (contenido original CRC).",
                estado_en_version="borrador",
                creado_por=admin.id if admin else None,
            ))
            creados += 1
            print(f"  {codigo}  [{meta['area']}/{meta['tipo']}]  {nombre[:55]}")
        await db.commit()
    print(f"Borradores de brechas creados: {creados}")


if __name__ == "__main__":
    asyncio.run(cargar())
