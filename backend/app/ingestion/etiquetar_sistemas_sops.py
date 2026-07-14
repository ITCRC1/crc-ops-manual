"""Etiquetado de sistemas asumidos por cada SOP master, por reconocimiento de texto
sobre el cuerpo ya cargado (§7.13). Alimenta el asistente de asignación por propiedad:
compara `sop_master_sistemas` vs `propiedad_sistemas` para sugerir adoptar/adaptar.

Patrones validados contra falsos positivos reales del corpus (219 coincidencias
revisadas a mano antes de fijar esto):
- 'OPERA': el software SIEMPRE se escribe en mayúsculas en el corpus; el verbo
  español 'opera' (3ra persona de 'operar', ej. "CRC opera el servicio...") SIEMPRE
  en minúsculas. Por eso el patrón es sensible a mayúsculas (sin IGNORECASE) — más
  preciso que cualquier lista de exclusiones por palabra siguiente (una exclusión de
  "no seguido de 'c'" bloqueaba por error "OPERA Cloud", el caso más común).
- 'generador': excluye la frase contable 'hecho generador' (no es infraestructura).
- El resto son nombres propios de sistema (Simphony, Integrity, QuickBooks, ...) sin
  colisión conocida con vocabulario común del corpus.

Idempotente (UniqueConstraint sop_master_id+sistema_id evita duplicados).

Uso:
    python -m app.ingestion.etiquetar_sistemas_sops
"""

import asyncio
import re

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models.catalogos import Sistema
from app.models.sop import SopMaster, SopMasterSistema

# codigo_sistema -> (patrón, sensible_a_mayusculas)
PATRONES: dict[str, tuple[str, bool]] = {
    "OPERA": (r"\bOPERA\b", True),  # case-sensitive: distingue software de verbo
    "SIMPHONY": (r"Simphony", False),
    "SKILLS4IT": (r"Skills4", False),
    "SITEMINDER": (r"SiteMinder", False),
    "SYNXIS": (r"SynXis", False),
    "HUBSPOT": (r"HubSpot", False),
    "INTEGRITY": (r"\bIntegrity\b", False),
    "QUICKBOOKS": (r"QuickBooks", False),
    "INVENTORY": (r"Inventory\s+Management", False),
    "STARLINK": (r"Starlink", False),
    "SOLAR": (r"panel(?:es)?\s+solar|fotovoltaic", False),
    "GENERADOR": (r"(?<!hecho\s)generador(?:es)?", False),
    "MARITIMO": (r"embarcaci|lancha|\bbote(?:s)?\b|mar[ií]tim", False),
}


def _texto_de(s: SopMaster) -> str:
    partes = [
        s.nombre or "", s.proposito or "", s.evaluacion_riesgos or "",
        s.controles_existentes or "", s.responsables or "", s.evidencia or "",
    ]
    proc = s.procedimiento or {}
    if isinstance(proc, dict):
        lista = proc.get("secciones") or proc.get("pasos") or proc.get("contenido") or []
        partes.extend(str(x) for x in lista)
    return " ".join(partes)


async def etiquetar() -> None:
    async with AsyncSessionLocal() as db:
        sistemas = {s.codigo: s for s in (await db.execute(select(Sistema))).scalars()}
        sops = list((await db.execute(select(SopMaster))).scalars())
        existentes = {
            (r.sop_master_id, r.sistema_id)
            for r in (await db.execute(select(SopMasterSistema))).scalars()
        }

        creados = 0
        por_sistema: dict[str, int] = {cod: 0 for cod in PATRONES}
        for s in sops:
            txt = _texto_de(s)
            for cod, (patron, sensible_mayus) in PATRONES.items():
                sistema = sistemas.get(cod)
                if not sistema:
                    continue
                flags = 0 if sensible_mayus else re.IGNORECASE
                if not re.search(patron, txt, flags):
                    continue
                clave = (s.id, sistema.id)
                if clave in existentes:
                    continue
                db.add(SopMasterSistema(sop_master_id=s.id, sistema_id=sistema.id))
                existentes.add(clave)
                creados += 1
                por_sistema[cod] += 1
        await db.commit()
    print(f"Etiquetas sop_master_sistemas creadas: {creados}")
    for cod, n in sorted(por_sistema.items(), key=lambda kv: -kv[1]):
        if n:
            print(f"  {cod}: {n}")


if __name__ == "__main__":
    asyncio.run(etiquetar())
