"""Capacitación / Training: manuales por departamento y secciones editables (§8).

Lectura: cualquier usuario autenticado. Escritura (crear/editar/borrar/reordenar):
editor corporativo o super_admin.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, get_current_user, require_rol
from app.core.db import get_db
from app.models.base import RolUsuario
from app.models.catalogos import Departamento
from app.models.training import TrainingManual, TrainingSeccion
from app.schemas.training import (
    ManualActualizar,
    ManualCrear,
    ManualDetalle,
    ManualItem,
    ManualSmartActualizar,
    ReordenarRequest,
    SeccionActualizar,
    SeccionCrear,
    SeccionOut,
)

router = APIRouter(prefix="/api/capacitacion", tags=["capacitacion"])

editor = require_rol(RolUsuario.editor_corporativo, RolUsuario.super_admin)


def _seccion_out(s: TrainingSeccion) -> SeccionOut:
    return SeccionOut(
        id=s.id, training_manual_id=s.training_manual_id, titulo=s.titulo,
        contenido=s.contenido, orden=s.orden, creado_en=s.creado_en,
        actualizado_en=s.actualizado_en,
    )


async def _get_manual(db: AsyncSession, manual_id: uuid.UUID) -> TrainingManual:
    m = (
        await db.execute(select(TrainingManual).where(TrainingManual.id == manual_id))
    ).scalar_one_or_none()
    if not m or m.eliminado_en is not None:
        raise HTTPException(status_code=404, detail="Manual no encontrado")
    return m


async def _get_seccion(
    db: AsyncSession, manual_id: uuid.UUID, seccion_id: uuid.UUID
) -> TrainingSeccion:
    s = (
        await db.execute(select(TrainingSeccion).where(TrainingSeccion.id == seccion_id))
    ).scalar_one_or_none()
    if not s or s.eliminado_en is not None or s.training_manual_id != manual_id:
        raise HTTPException(status_code=404, detail="Sección no encontrada")
    return s


async def _secciones(db: AsyncSession, manual_id: uuid.UUID) -> list[TrainingSeccion]:
    q = (
        select(TrainingSeccion)
        .where(TrainingSeccion.training_manual_id == manual_id, TrainingSeccion.eliminado_en.is_(None))
        .order_by(TrainingSeccion.orden, TrainingSeccion.creado_en)
    )
    return list((await db.execute(q)).scalars())


async def _depto_codigo(db: AsyncSession, depto_id: uuid.UUID | None) -> str | None:
    if not depto_id:
        return None
    return (
        await db.execute(select(Departamento.codigo).where(Departamento.id == depto_id))
    ).scalar_one_or_none()


# --- Manuales ---


@router.get("/manuales", response_model=list[ManualItem])
async def listar_manuales(
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
    departamento_id: uuid.UUID | None = None,
) -> list[ManualItem]:
    filtros = [TrainingManual.eliminado_en.is_(None)]
    if departamento_id:
        filtros.append(TrainingManual.departamento_id == departamento_id)
    manuales = list(
        (await db.execute(select(TrainingManual).where(*filtros).order_by(TrainingManual.titulo))).scalars()
    )
    deptos = {d.id: d.codigo for d in (await db.execute(select(Departamento))).scalars()}
    salida = []
    for m in manuales:
        total = (
            await db.execute(
                select(func.count())
                .select_from(TrainingSeccion)
                .where(
                    TrainingSeccion.training_manual_id == m.id,
                    TrainingSeccion.eliminado_en.is_(None),
                )
            )
        ).scalar_one()
        salida.append(ManualItem(
            id=m.id, titulo=m.titulo, departamento_id=m.departamento_id,
            departamento_codigo=deptos.get(m.departamento_id), descripcion=m.descripcion,
            total_secciones=total, tiene_smart=m.smart is not None,
            creado_en=m.creado_en, actualizado_en=m.actualizado_en,
        ))
    return salida


@router.post("/manuales", response_model=ManualDetalle, status_code=status.HTTP_201_CREATED)
async def crear_manual(
    datos: ManualCrear,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> ManualDetalle:
    if datos.departamento_id and not await _depto_codigo(db, datos.departamento_id):
        raise HTTPException(status_code=404, detail="Departamento no encontrado")
    m = TrainingManual(
        titulo=datos.titulo, departamento_id=datos.departamento_id,
        descripcion=datos.descripcion, creado_por=actual.id,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return await _detalle(db, m)


async def _detalle(db: AsyncSession, m: TrainingManual) -> ManualDetalle:
    secciones = await _secciones(db, m.id)
    return ManualDetalle(
        id=m.id, titulo=m.titulo, departamento_id=m.departamento_id,
        departamento_codigo=await _depto_codigo(db, m.departamento_id), descripcion=m.descripcion,
        total_secciones=len(secciones), tiene_smart=m.smart is not None,
        creado_en=m.creado_en, actualizado_en=m.actualizado_en,
        secciones=[_seccion_out(s) for s in secciones],
        smart=m.smart,
    )


@router.get("/manuales/{manual_id}", response_model=ManualDetalle)
async def obtener_manual(
    manual_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
) -> ManualDetalle:
    m = await _get_manual(db, manual_id)
    return await _detalle(db, m)


@router.put("/manuales/{manual_id}", response_model=ManualDetalle)
async def actualizar_manual(
    manual_id: uuid.UUID,
    datos: ManualActualizar,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> ManualDetalle:
    m = await _get_manual(db, manual_id)
    cambios = datos.model_dump(exclude_unset=True)
    if "departamento_id" in cambios and cambios["departamento_id"]:
        if not await _depto_codigo(db, cambios["departamento_id"]):
            raise HTTPException(status_code=404, detail="Departamento no encontrado")
    for campo, valor in cambios.items():
        setattr(m, campo, valor)
    await db.commit()
    await db.refresh(m)
    return await _detalle(db, m)


@router.put("/manuales/{manual_id}/smart", response_model=ManualDetalle)
async def actualizar_smart(
    manual_id: uuid.UUID,
    datos: ManualSmartActualizar,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> ManualDetalle:
    """Persiste la ficha Training SMART (#3 de la trilogía) del manual."""
    m = await _get_manual(db, manual_id)
    m.smart = datos.smart.model_dump()
    await db.commit()
    await db.refresh(m)
    return await _detalle(db, m)


@router.delete("/manuales/{manual_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_manual(
    manual_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> None:
    m = await _get_manual(db, manual_id)
    m.eliminado_en = datetime.now(UTC)
    await db.commit()


# --- Secciones ---


@router.post("/manuales/{manual_id}/secciones", response_model=SeccionOut, status_code=201)
async def crear_seccion(
    manual_id: uuid.UUID,
    datos: SeccionCrear,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> SeccionOut:
    await _get_manual(db, manual_id)
    if datos.orden is None:
        maximo = (
            await db.execute(
                select(func.coalesce(func.max(TrainingSeccion.orden), -1)).where(
                    TrainingSeccion.training_manual_id == manual_id,
                    TrainingSeccion.eliminado_en.is_(None),
                )
            )
        ).scalar_one()
        orden = int(maximo) + 1
    else:
        orden = datos.orden
    s = TrainingSeccion(
        training_manual_id=manual_id, titulo=datos.titulo, contenido=datos.contenido, orden=orden,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return _seccion_out(s)


@router.put("/manuales/{manual_id}/secciones/{seccion_id}", response_model=SeccionOut)
async def actualizar_seccion(
    manual_id: uuid.UUID,
    seccion_id: uuid.UUID,
    datos: SeccionActualizar,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> SeccionOut:
    s = await _get_seccion(db, manual_id, seccion_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(s, campo, valor)
    await db.commit()
    await db.refresh(s)
    return _seccion_out(s)


@router.delete("/manuales/{manual_id}/secciones/{seccion_id}", status_code=204)
async def eliminar_seccion(
    manual_id: uuid.UUID,
    seccion_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> None:
    s = await _get_seccion(db, manual_id, seccion_id)
    s.eliminado_en = datetime.now(UTC)
    await db.commit()


@router.post("/manuales/{manual_id}/reordenar", response_model=ManualDetalle)
async def reordenar_secciones(
    manual_id: uuid.UUID,
    datos: ReordenarRequest,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> ManualDetalle:
    """Aplica el nuevo orden según la lista de ids recibida (las no incluidas quedan al final)."""
    m = await _get_manual(db, manual_id)
    secciones = {s.id: s for s in await _secciones(db, manual_id)}
    pos = 0
    for sid in datos.orden_ids:
        s = secciones.get(sid)
        if s:
            s.orden = pos
            pos += 1
    # las secciones no mencionadas se mantienen después, preservando su orden relativo
    for s in sorted(secciones.values(), key=lambda x: x.orden):
        if s.id not in set(datos.orden_ids):
            s.orden = pos
            pos += 1
    await db.commit()
    return await _detalle(db, m)
