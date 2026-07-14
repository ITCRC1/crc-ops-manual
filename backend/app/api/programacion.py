"""Programación de SOPs (§ apartado opcional al final de cada SOP) y calendario
consolidado con export iCalendar (.ics).

Lectura: cualquier usuario autenticado. Escritura (crear/editar/borrar la
programación de un SOP): editor corporativo o super_admin. La programación es
metadata operativa de agenda — se puede editar independientemente del estado del
documento (incluso si el SOP ya está firmado), sin re-versionar el controlado."""

import uuid
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, get_current_user, require_rol
from app.core.db import get_db
from app.models.base import RolUsuario
from app.models.catalogos import Area
from app.models.puesto import DescriptorPuestoMaster
from app.models.sop import ProgramacionSop, SopMaster, SopMasterDepartamentoAfectado
from app.schemas.programacion import (
    CalendarioOut,
    EventoCalendario,
    ProgramacionActualizar,
    ProgramacionCrear,
    ProgramacionOut,
)
from app.services.programacion import MAX_DIAS_RANGO, expandir_ocurrencias, generar_ics

router = APIRouter(tags=["programacion"])

editor = require_rol(RolUsuario.editor_corporativo, RolUsuario.super_admin)


async def _get_sop(db: AsyncSession, sop_id: uuid.UUID) -> SopMaster:
    sop = (await db.execute(select(SopMaster).where(SopMaster.id == sop_id))).scalar_one_or_none()
    if not sop or sop.eliminado_en is not None:
        raise HTTPException(status_code=404, detail="SOP no encontrado")
    return sop


async def _get_prog(db: AsyncSession, sop_id: uuid.UUID, prog_id: uuid.UUID) -> ProgramacionSop:
    p = (
        await db.execute(select(ProgramacionSop).where(ProgramacionSop.id == prog_id))
    ).scalar_one_or_none()
    if not p or p.eliminado_en is not None or p.sop_master_id != sop_id:
        raise HTTPException(status_code=404, detail="Programación no encontrada")
    return p


async def _titulos_puestos(db: AsyncSession, ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    filas = (
        await db.execute(
            select(DescriptorPuestoMaster.id, DescriptorPuestoMaster.titulo).where(
                DescriptorPuestoMaster.id.in_(ids)
            )
        )
    ).all()
    return {i: t for i, t in filas}


def _out(p: ProgramacionSop, titulo_puesto: str | None) -> ProgramacionOut:
    return ProgramacionOut(
        id=p.id, sop_master_id=p.sop_master_id, titulo=p.titulo, descripcion=p.descripcion,
        tipo_recurrencia=p.tipo_recurrencia, fecha=p.fecha, hora=p.hora, fecha_fin=p.fecha_fin,
        responsable_puesto_id=p.responsable_puesto_id, responsable_texto=p.responsable_texto,
        responsable_puesto_titulo=titulo_puesto, activo=p.activo, orden=p.orden,
    )


async def _validar_puesto(db: AsyncSession, puesto_id: uuid.UUID | None) -> None:
    if puesto_id is None:
        return
    existe = (
        await db.execute(
            select(DescriptorPuestoMaster.id).where(
                DescriptorPuestoMaster.id == puesto_id,
                DescriptorPuestoMaster.eliminado_en.is_(None),
            )
        )
    ).scalar_one_or_none()
    if not existe:
        raise HTTPException(status_code=404, detail="Puesto responsable no encontrado")


# --- CRUD anidado bajo el SOP ---


@router.get("/api/sops/{sop_id}/programacion", response_model=list[ProgramacionOut])
async def listar_programacion(
    sop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
) -> list[ProgramacionOut]:
    await _get_sop(db, sop_id)
    q = (
        select(ProgramacionSop)
        .where(ProgramacionSop.sop_master_id == sop_id, ProgramacionSop.eliminado_en.is_(None))
        .order_by(ProgramacionSop.orden, ProgramacionSop.creado_en)
    )
    progs = list((await db.execute(q)).scalars())
    titulos = await _titulos_puestos(db, {p.responsable_puesto_id for p in progs})
    return [_out(p, titulos.get(p.responsable_puesto_id)) for p in progs]


@router.post(
    "/api/sops/{sop_id}/programacion",
    response_model=ProgramacionOut,
    status_code=status.HTTP_201_CREATED,
)
async def crear_programacion(
    sop_id: uuid.UUID,
    datos: ProgramacionCrear,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> ProgramacionOut:
    await _get_sop(db, sop_id)
    await _validar_puesto(db, datos.responsable_puesto_id)
    if datos.orden is None:
        maximo = (
            await db.execute(
                select(func.coalesce(func.max(ProgramacionSop.orden), -1)).where(
                    ProgramacionSop.sop_master_id == sop_id,
                    ProgramacionSop.eliminado_en.is_(None),
                )
            )
        ).scalar_one()
        orden = int(maximo) + 1
    else:
        orden = datos.orden
    p = ProgramacionSop(
        sop_master_id=sop_id, titulo=datos.titulo, descripcion=datos.descripcion,
        tipo_recurrencia=datos.tipo_recurrencia, fecha=datos.fecha, hora=datos.hora,
        fecha_fin=datos.fecha_fin, responsable_puesto_id=datos.responsable_puesto_id,
        responsable_texto=datos.responsable_texto, activo=datos.activo, orden=orden,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    titulos = await _titulos_puestos(db, {p.responsable_puesto_id})
    return _out(p, titulos.get(p.responsable_puesto_id))


@router.put("/api/sops/{sop_id}/programacion/{prog_id}", response_model=ProgramacionOut)
async def actualizar_programacion(
    sop_id: uuid.UUID,
    prog_id: uuid.UUID,
    datos: ProgramacionActualizar,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> ProgramacionOut:
    p = await _get_prog(db, sop_id, prog_id)
    cambios = datos.model_dump(exclude_unset=True)
    if "responsable_puesto_id" in cambios:
        await _validar_puesto(db, cambios["responsable_puesto_id"])
    for campo, valor in cambios.items():
        setattr(p, campo, valor)
    await db.commit()
    await db.refresh(p)
    titulos = await _titulos_puestos(db, {p.responsable_puesto_id})
    return _out(p, titulos.get(p.responsable_puesto_id))


@router.delete("/api/sops/{sop_id}/programacion/{prog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_programacion(
    sop_id: uuid.UUID,
    prog_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> None:
    p = await _get_prog(db, sop_id, prog_id)
    p.eliminado_en = datetime.now(UTC)
    await db.commit()


# --- Calendario consolidado ---


async def _programaciones_filtradas(
    db: AsyncSession,
    sop_id: uuid.UUID | None,
    area: str | None,
    departamento_id: uuid.UUID | None,
) -> list[tuple[ProgramacionSop, SopMaster]]:
    """Programaciones activas de SOPs vivos, con filtros combinables. Devuelve pares
    (programacion, sop)."""
    filtros = [
        ProgramacionSop.eliminado_en.is_(None),
        ProgramacionSop.activo.is_(True),
        SopMaster.eliminado_en.is_(None),
    ]
    if sop_id:
        filtros.append(SopMaster.id == sop_id)
    if area:
        a = (await db.execute(select(Area).where(Area.codigo == area))).scalar_one_or_none()
        if not a:
            raise HTTPException(status_code=404, detail=f"Área '{area}' no existe")
        filtros.append(SopMaster.area_id == a.id)
    if departamento_id:
        afectados = select(SopMasterDepartamentoAfectado.sop_master_id).where(
            SopMasterDepartamentoAfectado.departamento_id == departamento_id
        )
        filtros.append(
            or_(SopMaster.departamento_id == departamento_id, SopMaster.id.in_(afectados))
        )
    q = (
        select(ProgramacionSop, SopMaster)
        .join(SopMaster, SopMaster.id == ProgramacionSop.sop_master_id)
        .where(*filtros)
    )
    return list((await db.execute(q)).all())


@router.get("/api/calendario", response_model=CalendarioOut)
async def calendario(
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
    desde: date = Query(..., description="Inicio del rango (YYYY-MM-DD)"),
    hasta: date = Query(..., description="Fin del rango (YYYY-MM-DD)"),
    sop_id: uuid.UUID | None = None,
    area: str | None = None,
    departamento_id: uuid.UUID | None = None,
) -> CalendarioOut:
    if hasta < desde:
        raise HTTPException(status_code=400, detail="'hasta' no puede ser anterior a 'desde'.")
    if (hasta - desde).days > MAX_DIAS_RANGO:
        raise HTTPException(
            status_code=400, detail=f"El rango no puede exceder {MAX_DIAS_RANGO} días."
        )
    pares = await _programaciones_filtradas(db, sop_id, area, departamento_id)
    titulos = await _titulos_puestos(db, {p.responsable_puesto_id for p, _s in pares})

    eventos: list[EventoCalendario] = []
    for prog, sop in pares:
        resp = prog.responsable_texto or titulos.get(prog.responsable_puesto_id)
        for f in expandir_ocurrencias(prog, desde, hasta):
            eventos.append(EventoCalendario(
                programacion_id=prog.id, sop_id=sop.id, sop_codigo=sop.codigo,
                sop_nombre=sop.nombre, titulo=prog.titulo, descripcion=prog.descripcion,
                fecha=f, hora=prog.hora, dia_completo=prog.hora is None, responsable=resp,
            ))
    eventos.sort(key=lambda e: (e.fecha, e.hora or datetime.min.time(), e.sop_codigo))
    return CalendarioOut(desde=desde, hasta=hasta, total=len(eventos), eventos=eventos)


@router.get("/api/calendario/export.ics")
async def exportar_ics(
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
    sop_id: uuid.UUID | None = None,
    area: str | None = None,
    departamento_id: uuid.UUID | None = None,
) -> Response:
    """iCalendar suscribible/importable en Google Calendar. Emite un evento recurrente
    (RRULE) por programación, no la expansión — así el calendario se mantiene al día."""
    pares = await _programaciones_filtradas(db, sop_id, area, departamento_id)
    items = [(prog, sop.codigo, sop.nombre) for prog, sop in pares]
    ics = generar_ics(items, dtstamp=datetime.now(UTC))
    return Response(
        content=ics,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="crc-ops-calendario.ics"'},
    )
