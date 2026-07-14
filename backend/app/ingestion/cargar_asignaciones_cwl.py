"""Etapa 3 — Pre-asignación del master a CWL en modo `adoptado` (§10.8).

El contenido semilla proviene de Corcovado Wilderness Lodge, por lo que CWL adopta todos
los SOPs del master. Como los masters están en `borrador` (aún sin firmar), la asignación
se crea en `estado=borrador`: pasará a `vigente` cuando el master se firme (Etapa 4, §11).
Las otras tres propiedades arrancan sin asignaciones. Idempotente.

Uso:
    python -m app.ingestion.cargar_asignaciones_cwl
"""

import asyncio

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.ingestion.cargar_sops import _uno
from app.models import Propiedad, PropiedadSop, SopMaster
from app.models.base import EstadoAsignacion, ModoAsignacion


async def cargar() -> None:
    async with AsyncSessionLocal() as db:
        cwl = await _uno(db, select(Propiedad).where(Propiedad.codigo == "CWL"))
        if not cwl:
            print("No existe la propiedad CWL; corré el seed primero.")
            return

        sops = list((await db.execute(select(SopMaster))).scalars())
        creados = 0
        for sop in sops:
            existe = await _uno(
                db,
                select(PropiedadSop).where(
                    PropiedadSop.propiedad_id == cwl.id,
                    PropiedadSop.sop_master_id == sop.id,
                ),
            )
            if existe:
                continue
            db.add(PropiedadSop(
                propiedad_id=cwl.id,
                sop_master_id=sop.id,
                modo=ModoAsignacion.adoptado,
                version_fijada=sop.version_actual,
                estado=EstadoAsignacion.borrador,
                requiere_actualizacion=False,
                master_retirado=False,
            ))
            creados += 1
        await db.commit()
    print(f"Asignaciones CWL (adoptado) creadas: {creados}  | total master: {len(sops)}")


if __name__ == "__main__":
    asyncio.run(cargar())
