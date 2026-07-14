"""Adopción/adaptación de manuales de capacitación por propiedad (Etapa C).

Espejo del motor de SOPs (`propiedad_sops.py`) sobre `propiedad_training_manual`: cada hotel
adopta un manual maestro tal cual, lo adapta (override de la ficha TRAIN-SMART por sección,
hereda el resto) o crea uno local. La capa SMART efectiva se resuelve en `services/merge.py`."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, get_current_user
from app.core.db import get_db
from app.models.base import EstadoAsignacion, ModoAsignacion, RolUsuario
from app.models.catalogos import Propiedad
from app.models.propiedad import PropiedadTrainingManual
from app.models.training import TrainingManual
from app.schemas.propiedad_training import (
    AsignarTrainingRequest,
    PropiedadTrainingDetalle,
    PropiedadTrainingOut,
    SmartOverridesTrainingRequest,
)
from app.services.auditoria import auditar
from app.services.merge import smart_efectivo_training, smart_master_training

router = APIRouter(tags=["asignacion"])

EDITABLES = {EstadoAsignacion.borrador, EstadoAsignacion.en_revision, EstadoAsignacion.rechazado}


def _puede_gestionar(actual: UsuarioActual, propiedad_id: uuid.UUID) -> bool:
    return (
        actual.tiene_rol(RolUsuario.super_admin, RolUsuario.editor_corporativo)
        or actual.tiene_rol_en_propiedad(RolUsuario.editor_propiedad, propiedad_id)
    )


def _exigir_ver(actual: UsuarioActual, propiedad_id: uuid.UUID) -> None:
    if not actual.puede_ver_propiedad(propiedad_id):
        raise HTTPException(status_code=403, detail="Sin acceso a esta propiedad")


async def _propiedad(db: AsyncSession, prop_id: uuid.UUID) -> Propiedad:
    p = (await db.execute(select(Propiedad).where(Propiedad.id == prop_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    return p


async def _get_pt(db: AsyncSession, prop_id: uuid.UUID, pt_id: uuid.UUID) -> PropiedadTrainingManual:
    pt = (
        await db.execute(
            select(PropiedadTrainingManual).where(PropiedadTrainingManual.id == pt_id)
        )
    ).scalar_one_or_none()
    if not pt or pt.eliminado_en is not None or pt.propiedad_id != prop_id:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return pt


async def _titulo(db: AsyncSession, pt: PropiedadTrainingManual) -> str:
    if pt.titulo_local:
        return pt.titulo_local
    if pt.training_manual_id:
        m = await db.get(TrainingManual, pt.training_manual_id)
        if m:
            return m.titulo
    return "(capacitación local)"


async def _out(db: AsyncSession, pt: PropiedadTrainingManual) -> PropiedadTrainingOut:
    return PropiedadTrainingOut(
        id=pt.id, propiedad_id=pt.propiedad_id, training_manual_id=pt.training_manual_id,
        modo=pt.modo, titulo=await _titulo(db, pt), titulo_local=pt.titulo_local,
        estado=pt.estado, creado_en=pt.creado_en,
    )


async def _detalle(db: AsyncSession, pt: PropiedadTrainingManual) -> PropiedadTrainingDetalle:
    base = await _out(db, pt)
    return PropiedadTrainingDetalle(
        **base.model_dump(),
        smart_efectivo=await smart_efectivo_training(db, pt),
        smart_master=await smart_master_training(db, pt),
        smart_overrides=pt.smart_overrides,
    )


@router.get(
    "/api/propiedades/{prop_id}/capacitaciones", response_model=list[PropiedadTrainingOut]
)
async def listar(
    prop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    _exigir_ver(actual, prop_id)
    filas = list(
        (await db.execute(
            select(PropiedadTrainingManual).where(
                PropiedadTrainingManual.propiedad_id == prop_id,
                PropiedadTrainingManual.eliminado_en.is_(None),
            )
        )).scalars()
    )
    return [await _out(db, pt) for pt in filas]


@router.post(
    "/api/propiedades/{prop_id}/capacitaciones",
    response_model=PropiedadTrainingDetalle, status_code=201,
)
async def asignar(
    prop_id: uuid.UUID, datos: AsignarTrainingRequest, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    if not _puede_gestionar(actual, prop_id):
        raise HTTPException(status_code=403, detail="Sin permisos sobre esta propiedad")

    if datos.modo in (ModoAsignacion.adoptado, ModoAsignacion.adaptado):
        if not datos.training_manual_id:
            raise HTTPException(
                status_code=422, detail="training_manual_id es requerido para adoptar/adaptar"
            )
        m = await db.get(TrainingManual, datos.training_manual_id)
        if not m or m.eliminado_en is not None:
            raise HTTPException(status_code=404, detail="Manual de capacitación no encontrado")
        existe = (
            await db.execute(
                select(PropiedadTrainingManual).where(
                    PropiedadTrainingManual.propiedad_id == prop_id,
                    PropiedadTrainingManual.training_manual_id == datos.training_manual_id,
                    PropiedadTrainingManual.eliminado_en.is_(None),
                )
            )
        ).scalar_one_or_none()
        if existe:
            raise HTTPException(status_code=409, detail="La propiedad ya tiene este manual.")
        estado = (
            EstadoAsignacion.vigente
            if datos.modo == ModoAsignacion.adoptado
            else EstadoAsignacion.borrador
        )
    elif datos.modo == ModoAsignacion.local:
        if not datos.titulo_local:
            raise HTTPException(status_code=422, detail="Un manual local requiere 'titulo_local'.")
        estado = EstadoAsignacion.borrador
    else:
        raise HTTPException(status_code=422, detail="Modo no soportado.")

    pt = PropiedadTrainingManual(
        propiedad_id=prop_id, training_manual_id=datos.training_manual_id, modo=datos.modo,
        titulo_local=datos.titulo_local, smart_overrides=datos.smart_overrides, estado=estado,
    )
    db.add(pt)
    await db.flush()
    auditar(db, actual.id, "propiedad_training_manual", pt.id, f"crear:{datos.modo.value}", ip=request.client.host)
    await db.commit()
    await db.refresh(pt)
    return await _detalle(db, pt)


@router.get(
    "/api/propiedades/{prop_id}/capacitaciones/{pt_id}", response_model=PropiedadTrainingDetalle
)
async def obtener(
    prop_id: uuid.UUID, pt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    _exigir_ver(actual, prop_id)
    pt = await _get_pt(db, prop_id, pt_id)
    return await _detalle(db, pt)


@router.put(
    "/api/propiedades/{prop_id}/capacitaciones/{pt_id}/smart-overrides",
    response_model=PropiedadTrainingDetalle,
)
async def actualizar_smart_overrides(
    prop_id: uuid.UUID, pt_id: uuid.UUID, datos: SmartOverridesTrainingRequest, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    """Personaliza la ficha TRAIN-SMART por propiedad. En `adaptado` guarda deltas por sección
    (las ausentes heredan del master); en `local` guarda la ficha completa."""
    await _propiedad(db, prop_id)
    if not _puede_gestionar(actual, prop_id):
        raise HTTPException(status_code=403, detail="Sin permisos sobre esta propiedad")
    pt = await _get_pt(db, prop_id, pt_id)
    if pt.estado not in EDITABLES:
        raise HTTPException(status_code=409, detail=f"No editable en estado '{pt.estado.value}'.")
    if pt.modo not in (ModoAsignacion.adaptado, ModoAsignacion.local):
        raise HTTPException(
            status_code=409,
            detail="Solo un manual adaptado o local puede personalizar la ficha SMART.",
        )
    pt.smart_overrides = datos.smart_overrides
    auditar(db, actual.id, "propiedad_training_manual", pt.id, "smart-overrides", ip=request.client.host)
    await db.commit()
    await db.refresh(pt)
    return await _detalle(db, pt)


@router.post(
    "/api/propiedades/{prop_id}/capacitaciones/{pt_id}/adaptar",
    response_model=PropiedadTrainingDetalle,
)
async def adaptar(
    prop_id: uuid.UUID, pt_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    """Convierte una asignación ADOPTADA en ADAPTADA para poder personalizar la ficha SMART
    (arranca sin overrides = hereda todo) y vuelve a `borrador`."""
    await _propiedad(db, prop_id)
    if not _puede_gestionar(actual, prop_id):
        raise HTTPException(status_code=403, detail="Sin permisos sobre esta propiedad")
    pt = await _get_pt(db, prop_id, pt_id)
    if pt.modo != ModoAsignacion.adoptado:
        raise HTTPException(status_code=409, detail="Solo una asignación adoptada puede adaptarse.")
    pt.modo = ModoAsignacion.adaptado
    pt.estado = EstadoAsignacion.borrador
    auditar(db, actual.id, "propiedad_training_manual", pt.id, "adaptar", ip=request.client.host)
    await db.commit()
    await db.refresh(pt)
    return await _detalle(db, pt)


@router.delete("/api/propiedades/{prop_id}/capacitaciones/{pt_id}", status_code=204)
async def eliminar(
    prop_id: uuid.UUID, pt_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    if not _puede_gestionar(actual, prop_id):
        raise HTTPException(status_code=403, detail="Sin permisos sobre esta propiedad")
    pt = await _get_pt(db, prop_id, pt_id)
    pt.eliminado_en = datetime.now(UTC)
    auditar(db, actual.id, "propiedad_training_manual", pt.id, "eliminar", ip=request.client.host)
    await db.commit()
