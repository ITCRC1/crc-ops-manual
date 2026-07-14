"""Pre-asignación a Amarena (AMA) de los SOPs marcados `origen_propiedad='AMA'`.

Son los SOPs del Procedimiento de Contabilidad de Amarena (contenido propio: Skill4,
cuentas y montos de Amarena). Se adoptan en la propiedad AMA en modo `adoptado`. Como los
masters están en `borrador` (aún sin firmar), la asignación se crea en `estado=borrador`:
pasará a `vigente` cuando el master se firme (§11), igual que la pre-asignación de CWL.
Idempotente.

Uso:
    python -m app.ingestion.cargar_asignaciones_amarena
"""

import asyncio

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.ingestion.cargar_sops import _uno
from app.models import Propiedad, PropiedadSop, SopMaster
from app.models.base import EstadoAsignacion, ModoAsignacion

ORIGEN = "AMA"


async def cargar() -> None:
    async with AsyncSessionLocal() as db:
        ama = await _uno(db, select(Propiedad).where(Propiedad.codigo == ORIGEN))
        if not ama:
            print(f"No existe la propiedad {ORIGEN}; corré el seed primero.")
            return

        sops = list(
            (await db.execute(
                select(SopMaster).where(
                    SopMaster.origen_propiedad == ORIGEN,
                    SopMaster.eliminado_en.is_(None),
                )
            )).scalars()
        )
        creados = 0
        for sop in sops:
            existe = await _uno(
                db,
                select(PropiedadSop).where(
                    PropiedadSop.propiedad_id == ama.id,
                    PropiedadSop.sop_master_id == sop.id,
                    PropiedadSop.eliminado_en.is_(None),
                ),
            )
            if existe:
                continue
            db.add(PropiedadSop(
                propiedad_id=ama.id,
                sop_master_id=sop.id,
                modo=ModoAsignacion.adoptado,
                version_fijada=sop.version_actual,
                estado=EstadoAsignacion.borrador,
                requiere_actualizacion=False,
                master_retirado=False,
            ))
            creados += 1
        await db.commit()
    print(f"Asignaciones AMA (adoptado) creadas: {creados}  | SOPs origen=AMA: {len(sops)}")


if __name__ == "__main__":
    asyncio.run(cargar())
