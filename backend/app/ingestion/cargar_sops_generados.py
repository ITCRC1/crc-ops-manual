"""Carga genérica de SOPs generados (contenido original CRC) en sop_master (borrador).

Lee un JSON con {items:[{clave, area, tipo, draft:{9 campos}}]} y crea cada SOP con
numeración atómica por área + snapshot v1. Idempotente (por nombre). Uso:

    python -m app.ingestion.cargar_sops_generados <ruta_json> [<origen>]
"""

import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.ingestion.cargar_sops import _uno
from app.models import Area, SopMaster, SopMasterVersion, Usuario
from app.models.base import EstadoDocumento, FrecuenciaRevision, TipoDocumento
from app.services.numeracion import siguiente_codigo_area

ADMIN_EMAIL = "Finance@thecostaricacollection.com"


async def cargar(ruta: str, origen: str = "SOP generado (contenido original CRC)") -> None:
    items = json.loads(Path(ruta).read_text(encoding="utf-8"))["items"]
    async with AsyncSessionLocal() as db:
        admin = await _uno(db, select(Usuario).where(Usuario.email == ADMIN_EMAIL))
        areas = {a.codigo: a for a in (await db.execute(select(Area))).scalars()}
        creados = 0
        for it in items:
            b = it["draft"]
            nombre = b["titulo"]
            if await _uno(db, select(SopMaster).where(SopMaster.nombre == nombre)):
                continue
            area = areas[it["area"]]
            numero, codigo = await siguiente_codigo_area(db, area)
            sop = SopMaster(
                numero=numero, area_id=area.id, codigo=codigo, tipo=TipoDocumento(it["tipo"]),
                nombre=nombre, proposito=b.get("proposito"),
                evaluacion_riesgos=b.get("evaluacion_riesgos"),
                controles_existentes=b.get("controles_existentes"),
                procedimiento={"secciones": b.get("procedimiento", [])},
                responsables=b.get("responsables"), evidencia=b.get("evidencia"),
                frecuencia_revision=FrecuenciaRevision(b["frecuencia_revision"]),
                estado=EstadoDocumento.borrador, version_actual=1,
                creado_por=admin.id if admin else None,
            )
            db.add(sop)
            await db.flush()
            db.add(SopMasterVersion(
                sop_master_id=sop.id, version=1,
                snapshot={"codigo": codigo, "nombre": nombre, "area": it["area"],
                          "origen": origen, "proposito": sop.proposito,
                          "procedimiento": sop.procedimiento},
                nota_cambio=f"Carga inicial — {origen}.", estado_en_version="borrador",
                creado_por=admin.id if admin else None,
            ))
            creados += 1
            print(f"  {codigo}  [{it['area']}/{it['tipo']}]  {nombre[:55]}")
        await db.commit()
    print(f"SOPs creados: {creados}")


if __name__ == "__main__":
    ruta = sys.argv[1]
    origen = sys.argv[2] if len(sys.argv) > 2 else "SOP generado (contenido original CRC)"
    asyncio.run(cargar(ruta, origen))
