"""Reclasifica los SOPs de bodegas/recepción/inventario de F&B (FBS) a Finanzas (FIN):
en CRC, bodegas y compras son de Finanzas. Reasigna código atómico FIN; los números FBS
quedan retirados (§7.2). Idempotente: si el SOP ya no está en FBS, se omite.

Uso:
    python -m app.ingestion.reclasificar_bodegas
"""

import asyncio

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.ingestion.cargar_sops import _uno
from app.models.catalogos import Area
from app.models.sop import SopMaster
from app.services.auditoria import auditar
from app.services.numeracion import siguiente_codigo_area

# SOPs curados de bodega/recepción/inventario que originalmente entraron bajo FBS.
CODIGOS_FBS = ["FBS-0011", "FBS-0012", "FBS-0013", "FBS-0014",
               "FBS-0015", "FBS-0016", "FBS-0017", "FBS-0018"]


async def cargar() -> None:
    async with AsyncSessionLocal() as db:
        fin = (await db.execute(select(Area).where(Area.codigo == "FIN"))).scalar_one()
        movidos = 0
        for cod in CODIGOS_FBS:
            sop = await _uno(db, select(SopMaster).where(SopMaster.codigo == cod))
            if not sop or sop.eliminado_en is not None:
                continue  # ya reclasificado (idempotente) o inexistente
            viejo = sop.codigo
            numero, nuevo = await siguiente_codigo_area(db, fin)
            sop.area_id, sop.numero, sop.codigo = fin.id, numero, nuevo
            auditar(db, None, "sop_master", sop.id, "reclasificacion_area",
                    {"de": viejo, "a": nuevo, "motivo": "bodegas/compras son de Finanzas"})
            movidos += 1
        await db.commit()
    print(f"Bodegas reclasificadas FBS->FIN: {movidos}")


if __name__ == "__main__":
    asyncio.run(cargar())
