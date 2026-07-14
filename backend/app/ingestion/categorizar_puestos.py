"""Clasifica cada descriptor en una categoría de puesto según el organigrama.

Categorías: director | gerente_departamental | supervisor | linea. La regla parte del
nivel jerárquico y afina el nivel 3 (que mezcla gerencias y supervisiones) por título.
Es el punto de partida editable: solo rellena los que están sin categoría, para no
pisar ajustes manuales hechos desde la app.

Uso:  python -m app.ingestion.categorizar_puestos
"""

import asyncio
import re
import unicodedata

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models import DescriptorPuestoMaster

# Palabras (normalizadas, sin acentos) que marcan gerencia departamental en nivel 3.
_GERENCIA = ("gerente", "chef", "director", "supervisor general", "jefe", "capitan de barco")


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def categoria_de(nivel: int, titulo: str) -> str:
    if nivel <= 2:
        return "director"
    if nivel == 3:
        t = _norm(titulo)
        return "gerente_departamental" if any(k in t for k in _GERENCIA) else "supervisor"
    return "linea"


async def categorizar(recompute: bool = False) -> None:
    async with AsyncSessionLocal() as db:
        descs = list((await db.execute(select(DescriptorPuestoMaster))).scalars())
        n = 0
        for d in descs:
            if d.eliminado_en is not None:
                continue
            if d.categoria and not recompute:
                continue
            nueva = categoria_de(d.nivel_jerarquico, d.titulo)
            if d.categoria != nueva:
                d.categoria = nueva
                n += 1
        await db.commit()
    print(f"Puestos categorizados: {n} (recompute={recompute})")


if __name__ == "__main__":
    import sys
    asyncio.run(categorizar(recompute="--recompute" in sys.argv))
