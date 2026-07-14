"""Render del contenido efectivo de una asignación de propiedad (A2, §7.9).

- adoptado: usa el snapshot del master en la versión fijada, tal cual.
- adaptado: merge(snapshot_master[version_fijada], overrides) — solo se guardan deltas.
- local:    usa campos_locales (sin master).
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import ModoAsignacion
from app.models.propiedad import PropiedadPuesto, PropiedadSop, PropiedadTrainingManual
from app.models.puesto import DescriptorPuestoMaster
from app.models.sop import SopMaster, SopMasterVersion
from app.models.training import TrainingManual

CAMPOS = [
    "nombre", "proposito", "evaluacion_riesgos", "controles_existentes",
    "procedimiento", "responsables", "evidencia", "frecuencia_revision",
]

# Campos de contenido de un descriptor de puesto (el detalle del puesto por propiedad).
PUESTO_CAMPOS = [
    "titulo", "nivel_jerarquico", "categoria", "proposito",
    "responsabilidades", "nivel_autoridad", "kpis", "requisitos",
]


async def _snapshot_master(db: AsyncSession, sop_master_id: uuid.UUID, version: int) -> dict:
    v = (
        await db.execute(
            select(SopMasterVersion).where(
                SopMasterVersion.sop_master_id == sop_master_id,
                SopMasterVersion.version == version,
            )
        )
    ).scalar_one_or_none()
    return dict(v.snapshot) if v and v.snapshot else {}


async def contenido_efectivo(db: AsyncSession, ps: PropiedadSop) -> dict:
    if ps.modo == ModoAsignacion.local:
        base = dict(ps.campos_locales or {})
    else:
        base = await _snapshot_master(db, ps.sop_master_id, ps.version_fijada or 1)
        if ps.modo == ModoAsignacion.adaptado and ps.overrides:
            base.update(ps.overrides)  # override por campos (deltas)
    return {k: base.get(k) for k in CAMPOS}


async def contenido_master_sop(db: AsyncSession, ps: PropiedadSop) -> dict:
    """Contenido del master en la versión fijada (para el editor de adaptación: mostrar la
    sección heredada y poder restaurarla). Vacío para asignaciones locales."""
    if ps.modo == ModoAsignacion.local or not ps.sop_master_id:
        return {}
    base = await _snapshot_master(db, ps.sop_master_id, ps.version_fijada or 1)
    return {k: base.get(k) for k in CAMPOS}


async def smart_master_sop(db: AsyncSession, ps: PropiedadSop) -> dict:
    """Capa SMART del master (para el editor de adaptación: mostrar la sección heredada
    y poder restaurarla). Vacío para asignaciones locales o SOPs sin capa SMART."""
    if ps.modo == ModoAsignacion.local or not ps.sop_master_id:
        return {}
    m = await db.get(SopMaster, ps.sop_master_id)
    return dict(m.smart) if m and m.smart else {}


async def smart_efectivo_sop(db: AsyncSession, ps: PropiedadSop) -> dict:
    """Capa SMART efectiva de la asignación (lo que ve/usa la propiedad):
    - adoptado: la SMART del master, tal cual.
    - adaptado: merge por SECCIÓN (master ∪ overrides); solo se guardan las secciones cambiadas.
    - local:    la SMART local completa (sin master), guardada en smart_overrides."""
    if ps.modo == ModoAsignacion.local:
        return dict(ps.smart_overrides or {})
    base = await smart_master_sop(db, ps)
    if ps.modo == ModoAsignacion.adaptado and ps.smart_overrides:
        base = {**base, **ps.smart_overrides}  # override por sección (top-level key)
    return base


def resolver_puesto(pp: PropiedadPuesto, master: DescriptorPuestoMaster | None) -> dict[str, Any]:
    """Campos de cabecera resueltos de un puesto por propiedad (para lista/árbol):
    precedencia overrides locales > master > fallback. Puro (sin DB) para evitar N+1
    cuando el llamador ya precargó los masters."""
    ov = pp.overrides or {}
    return {
        "titulo": ov.get("titulo") or (master.titulo if master else "(puesto local)"),
        "codigo": ov.get("codigo") or (master.codigo if master else None),
        "nivel_jerarquico": ov.get("nivel_jerarquico") or (master.nivel_jerarquico if master else 4),
        "categoria": ov.get("categoria") or (master.categoria if master else None),
        "departamento_id": master.departamento_id if master else None,
    }


async def contenido_efectivo_puesto(db: AsyncSession, pp: PropiedadPuesto) -> dict:
    """Contenido descriptivo efectivo de un puesto (adoptado/adaptado/local, §7.9)."""
    if pp.modo == ModoAsignacion.local:
        base = dict(pp.overrides or {})
    else:
        master = (
            await db.get(DescriptorPuestoMaster, pp.descriptor_puesto_master_id)
            if pp.descriptor_puesto_master_id
            else None
        )
        base = {c: getattr(master, c, None) for c in PUESTO_CAMPOS} if master else {}
        if pp.modo == ModoAsignacion.adaptado and pp.overrides:
            base.update(pp.overrides)
    return {k: base.get(k) for k in PUESTO_CAMPOS}


async def smart_master_puesto(db: AsyncSession, pp: PropiedadPuesto) -> dict:
    """Capa JD SMART del descriptor master (para el editor de adaptación: heredar/restaurar).
    Vacío para puestos locales o descriptores sin capa SMART."""
    if pp.modo == ModoAsignacion.local or not pp.descriptor_puesto_master_id:
        return {}
    m = await db.get(DescriptorPuestoMaster, pp.descriptor_puesto_master_id)
    return dict(m.smart) if m and m.smart else {}


async def smart_efectivo_puesto(db: AsyncSession, pp: PropiedadPuesto) -> dict:
    """Capa JD SMART efectiva de la asignación (lo que ve/usa la propiedad):
    - adoptado: la SMART del descriptor master, tal cual.
    - adaptado: merge por SECCIÓN (master ∪ overrides); solo se guardan las secciones cambiadas.
    - local:    la SMART local completa (sin master), guardada en smart_overrides."""
    if pp.modo == ModoAsignacion.local:
        return dict(pp.smart_overrides or {})
    base = await smart_master_puesto(db, pp)
    if pp.modo == ModoAsignacion.adaptado and pp.smart_overrides:
        base = {**base, **pp.smart_overrides}
    return base


async def smart_master_training(db: AsyncSession, pt: PropiedadTrainingManual) -> dict:
    """Ficha TRAIN-SMART del manual master (para el editor: heredar/restaurar).
    Vacío para manuales locales o sin ficha SMART."""
    if pt.modo == ModoAsignacion.local or not pt.training_manual_id:
        return {}
    m = await db.get(TrainingManual, pt.training_manual_id)
    return dict(m.smart) if m and m.smart else {}


async def smart_efectivo_training(db: AsyncSession, pt: PropiedadTrainingManual) -> dict:
    """Ficha TRAIN-SMART efectiva de la asignación (lo que ve/usa la propiedad):
    - adoptado: la ficha del manual master, tal cual.
    - adaptado: merge por SECCIÓN (master ∪ overrides); solo se guardan las secciones cambiadas.
    - local:    la ficha local completa (sin master), guardada en smart_overrides."""
    if pt.modo == ModoAsignacion.local:
        return dict(pt.smart_overrides or {})
    base = await smart_master_training(db, pt)
    if pt.modo == ModoAsignacion.adaptado and pt.smart_overrides:
        base = {**base, **pt.smart_overrides}
    return base
