"""Reorganiza los SOPs por la nueva estructura de departamentos.

Asigna a cada SOP su departamento dueño y sus departamentos afectados (N:M) según el
mapeo curado en seed/ingesta/sop_departamentos.json (clasificación por contenido, hecha
con subagentes). Idempotente: reafirma el dueño y reemplaza la lista de afectados.

Uso:  python -m app.ingestion.cargar_sop_departamentos
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import delete, select

from app.core.db import AsyncSessionLocal
from app.models import Departamento, SopMaster
from app.models.sop import SopMasterDepartamentoAfectado

RAIZ = Path(__file__).resolve().parents[3]
MAPEO = RAIZ / "seed" / "ingesta" / "sop_departamentos.json"


async def cargar() -> None:
    mapeo = json.loads(MAPEO.read_text(encoding="utf-8"))

    async with AsyncSessionLocal() as db:
        deptos = {
            d.codigo: d
            for d in (
                await db.execute(
                    select(Departamento).where(Departamento.propiedad_propietaria_id.is_(None))
                )
            ).scalars()
        }
        due, afe = 0, 0
        for entry in mapeo:
            sop = (
                await db.execute(
                    select(SopMaster).where(SopMaster.codigo == entry["codigo"])
                )
            ).scalar_one_or_none()
            if not sop or sop.eliminado_en is not None:
                continue
            dueno = deptos.get(entry.get("departamento"))
            if dueno and sop.departamento_id != dueno.id:
                sop.departamento_id = dueno.id
                due += 1
            # Afectados: reemplazo completo (excluye al dueño y duplicados).
            await db.execute(
                delete(SopMasterDepartamentoAfectado).where(
                    SopMasterDepartamentoAfectado.sop_master_id == sop.id
                )
            )
            vistos: set = set()
            for acod in entry.get("afectados", []) or []:
                dep = deptos.get(acod)
                if dep and dep.id != (dueno.id if dueno else None) and dep.id not in vistos:
                    db.add(
                        SopMasterDepartamentoAfectado(
                            sop_master_id=sop.id, departamento_id=dep.id
                        )
                    )
                    vistos.add(dep.id)
                    afe += 1
        await db.commit()
    print(f"SOPs reorganizados: dueño asignado {due} | vínculos afectados {afe}")


if __name__ == "__main__":
    asyncio.run(cargar())
