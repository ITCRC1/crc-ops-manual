"""Sistemas por propiedad (§8.9, `propiedad_sistemas`), aportado por el owner
(2026-07-04). Alimenta el asistente de asignación (§7.13): compara los sistemas que
asume cada SOP master vs. los que tiene la propiedad.

- CWL: el stack completo del catálogo, EXCEPTO Skills4IT — asunción: Skills4IT es el
  POS de las otras 3 propiedades y Simphony ya cubre ese rol en CWL (tener dos POS a
  la vez sería redundante). Corregir en PROPIEDAD_SISTEMAS si CWL también lo usa.
- Amarena / Oxígen / Ojochal: Skills4IT (POS), SiteMinder (channel manager) y
  QuickBooks (contable). HubSpot está "próximo" — NO se siembra todavía como sistema
  activo; agregarlo cuando el owner confirme que ya está en producción ahí.

Idempotente (UniqueConstraint propiedad_id+sistema_id evita duplicados).

Uso:
    python -m app.seed_propiedad_sistemas
"""

import asyncio

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models.catalogos import Propiedad, PropiedadSistema, Sistema

SISTEMAS_CWL_TODOS = [
    "OPERA", "SIMPHONY", "INTEGRITY", "INVENTORY", "SITEMINDER", "SYNXIS",
    "HUBSPOT", "QUICKBOOKS", "STARLINK", "SOLAR", "GENERADOR", "MARITIMO",
]
SISTEMAS_OTRAS = ["SKILLS4IT", "SITEMINDER", "QUICKBOOKS"]

PROPIEDAD_SISTEMAS: dict[str, list[str]] = {
    "CWL": SISTEMAS_CWL_TODOS,
    "AMA": SISTEMAS_OTRAS,
    "OXI": SISTEMAS_OTRAS,
    "OJO": SISTEMAS_OTRAS,
}


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        propiedades = {p.codigo: p for p in (await db.execute(select(Propiedad))).scalars()}
        sistemas = {s.codigo: s for s in (await db.execute(select(Sistema))).scalars()}
        existentes = {
            (r.propiedad_id, r.sistema_id)
            for r in (await db.execute(select(PropiedadSistema))).scalars()
        }

        creados = 0
        for cod_prop, sistemas_cod in PROPIEDAD_SISTEMAS.items():
            prop = propiedades.get(cod_prop)
            if not prop:
                print(f"  (propiedad '{cod_prop}' no existe, se omite)")
                continue
            for cod_sis in sistemas_cod:
                sis = sistemas.get(cod_sis)
                if not sis:
                    print(f"  (sistema '{cod_sis}' no existe, se omite)")
                    continue
                clave = (prop.id, sis.id)
                if clave in existentes:
                    continue
                db.add(PropiedadSistema(propiedad_id=prop.id, sistema_id=sis.id))
                existentes.add(clave)
                creados += 1
        await db.commit()
    print(f"Sistemas por propiedad creados: {creados}")


if __name__ == "__main__":
    asyncio.run(seed())
