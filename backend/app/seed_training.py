"""Seed de Capacitación: un manual por departamento (según el organigrama) + el
contenido propio de CRC del manual de Recepción.

- Crea (idempotente, por título + departamento) un manual de capacitación para cada
  departamento del organigrama; los demás quedan vacíos, listos para completar.
- El manual de Recepción se puebla con las secciones de `seed/training/recepcion.json`
  (contenido original de CRC). Las secciones sólo se cargan si el manual aún no tiene
  ninguna, para no duplicar en corridas repetidas.

Uso:
    python -m app.seed_training
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import func, select

from app.core.db import AsyncSessionLocal
from app.models.catalogos import Departamento
from app.models.training import TrainingManual, TrainingSeccion

RAIZ = Path(__file__).resolve().parents[1].parent
TRAINING_DIR = RAIZ / "seed" / "training"  # un JSON por departamento: <CODIGO>.json

# codigo_departamento -> título del manual (según el organigrama de CWL)
MANUALES = {
    "REC": "Manual de Capacitación — Recepción",
    "HK": "Manual de Capacitación — Ama de Llaves",
    "FB": "Manual de Capacitación — Alimentos y Bebidas",
    "KIT": "Manual de Capacitación — Cocina",
    "MANT": "Manual de Capacitación — Mantenimiento",
    "SEG": "Manual de Capacitación — Seguridad",
    "RES": "Manual de Capacitación — Reservas",
    "SM": "Manual de Capacitación — Ventas y Mercadeo",
    "FIN": "Manual de Capacitación — Finanzas y Contabilidad",
    "HR": "Manual de Capacitación — Recursos Humanos",
    "IT": "Manual de Capacitación — Tecnología de Información",
    "TOURS": "Manual de Capacitación — Experiencias y Tours",
}


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        deptos = {
            d.codigo: d
            for d in (
                await db.execute(
                    select(Departamento).where(Departamento.propiedad_propietaria_id.is_(None))
                )
            ).scalars()
        }

        manuales_por_codigo: dict[str, TrainingManual] = {}
        creados = 0
        for codigo, titulo in MANUALES.items():
            depto = deptos.get(codigo)
            if not depto:
                continue
            existente = (
                await db.execute(
                    select(TrainingManual).where(
                        TrainingManual.titulo == titulo,
                        TrainingManual.departamento_id == depto.id,
                        TrainingManual.eliminado_en.is_(None),
                    )
                )
            ).scalar_one_or_none()
            if existente:
                manuales_por_codigo[codigo] = existente
                continue
            m = TrainingManual(titulo=titulo, departamento_id=depto.id)
            db.add(m)
            await db.flush()
            manuales_por_codigo[codigo] = m
            creados += 1

        # Poblar cada manual con su contenido propio de CRC (seed/training/<CODIGO>.json).
        # Solo si el manual todavía no tiene secciones (idempotente).
        poblados: dict[str, int] = {}
        for codigo, manual in manuales_por_codigo.items():
            archivo = TRAINING_DIR / f"{codigo}.json"
            if not archivo.exists():
                continue
            ya_tiene = (
                await db.execute(
                    select(func.count())
                    .select_from(TrainingSeccion)
                    .where(
                        TrainingSeccion.training_manual_id == manual.id,
                        TrainingSeccion.eliminado_en.is_(None),
                    )
                )
            ).scalar_one()
            if ya_tiene:
                continue
            data = json.loads(archivo.read_text(encoding="utf-8"))
            for i, s in enumerate(data["secciones"]):
                db.add(TrainingSeccion(
                    training_manual_id=manual.id,
                    titulo=s["titulo"],
                    contenido=s.get("contenido") or None,
                    orden=s.get("orden", i),
                ))
            poblados[codigo] = len(data["secciones"])

        await db.commit()
    resumen = ", ".join(f"{c}:{n}" for c, n in sorted(poblados.items())) or "ninguno"
    print(f"Manuales creados: {creados}  | poblados (secciones): {resumen}")


if __name__ == "__main__":
    asyncio.run(seed())
