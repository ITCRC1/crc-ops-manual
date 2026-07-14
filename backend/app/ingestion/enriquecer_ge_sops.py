"""Etapa 3+ — Enriquecimiento de 5 SOPs de Guest Experience con procedimientos reales.

Actualiza el cuerpo de SOPs existentes (GE-0001/0004/0005/0006/0009) con la versión
detallada y probada (navegación OPERA Cloud), adaptada a CRC y sin datos sensibles ni marca
ajena (ver seed/ingesta/enrich_ge.json). Sube version_actual a 2 y crea snapshot v2,
preservando el v1. Idempotente (no re-aplica si ya existe v2 con este origen).

Uso:
    python -m app.ingestion.enriquecer_ge_sops
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.ingestion.cargar_sops import _uno
from app.models import SopMaster, SopMasterVersion, Usuario
from app.models.base import FrecuenciaRevision

RAIZ = Path(__file__).resolve().parents[3]
ING = RAIZ / "seed" / "ingesta"
ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ORIGEN = "enriquecido con procedimiento real detallado (OPERA Cloud), adaptado a CRC"


async def cargar() -> None:
    drafts = json.loads((ING / "enrich_ge.json").read_text(encoding="utf-8"))["drafts"]
    async with AsyncSessionLocal() as db:
        admin = await _uno(db, select(Usuario).where(Usuario.email == ADMIN_EMAIL))
        actualizados = 0
        for dr in drafts:
            b = dr["draft"]
            sop = await _uno(db, select(SopMaster).where(SopMaster.codigo == dr["codigo"]))
            if not sop:
                print(f"  (no existe {dr['codigo']}, se omite)")
                continue
            # idempotencia: ¿ya existe una versión con este origen?
            ya = await _uno(db, select(SopMasterVersion).where(
                SopMasterVersion.sop_master_id == sop.id, SopMasterVersion.version == 2))
            if ya:
                continue
            # actualizar cuerpo
            sop.proposito = b.get("proposito")
            sop.evaluacion_riesgos = b.get("evaluacion_riesgos")
            sop.controles_existentes = b.get("controles_existentes")
            sop.procedimiento = {"secciones": b.get("procedimiento", [])}
            sop.responsables = b.get("responsables")
            sop.evidencia = b.get("evidencia")
            sop.frecuencia_revision = FrecuenciaRevision(b["frecuencia_revision"])
            sop.version_actual = 2
            db.add(SopMasterVersion(
                sop_master_id=sop.id, version=2,
                snapshot={"codigo": sop.codigo, "nombre": sop.nombre, "origen": ORIGEN,
                          "proposito": sop.proposito, "procedimiento": sop.procedimiento,
                          "controles_existentes": sop.controles_existentes,
                          "responsables": sop.responsables, "evidencia": sop.evidencia},
                nota_cambio="Enriquecido con el procedimiento real detallado (OPERA Cloud), "
                            "adaptado a CRC y sin datos sensibles.",
                estado_en_version="borrador",
                creado_por=admin.id if admin else None,
            ))
            actualizados += 1
            pasos = len(b.get("procedimiento", []))
            print(f"  {sop.codigo} -> v2  {sop.nombre[:45]}  ({pasos} pasos)")
        await db.commit()
    print(f"SOPs GE enriquecidos a v2: {actualizados}")


if __name__ == "__main__":
    asyncio.run(cargar())
