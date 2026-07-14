"""Motor de asignación de SOPs por propiedad: adoptar / adaptar / local, overrides,
sincronización y sugerencias por sistemas (§7.8-7.13, §11, A1/A2/B3)."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, get_current_user
from app.core.db import get_db
from app.models.base import EstadoAsignacion, EstadoDocumento, ModoAsignacion, RolUsuario
from app.models.catalogos import Propiedad, PropiedadSistema
from app.models.propiedad import PropiedadSop
from app.models.sop import SopMaster, SopMasterSistema
from app.schemas.propiedad_sop import (
    AsignarRequest,
    OverridesRequest,
    PropiedadSopDetalle,
    PropiedadSopOut,
    SmartOverridesRequest,
    Sugerencia,
)
from app.services.auditoria import auditar
from app.services.merge import (
    contenido_efectivo,
    contenido_master_sop,
    smart_efectivo_sop,
    smart_master_sop,
)
from app.services.numeracion import siguiente_codigo_local

router = APIRouter(tags=["asignacion"])

EDITABLES = {EstadoAsignacion.borrador, EstadoAsignacion.en_revision, EstadoAsignacion.rechazado}


def _puede_gestionar(actual: UsuarioActual, propiedad_id: uuid.UUID) -> bool:
    return (
        actual.tiene_rol(RolUsuario.super_admin, RolUsuario.editor_corporativo)
        or actual.tiene_rol_en_propiedad(RolUsuario.editor_propiedad, propiedad_id)
    )


def _exigir_ver(actual: UsuarioActual, propiedad_id: uuid.UUID) -> None:
    """Visibilidad por propiedad (§14): cada usuario ve solo su(s) propiedad(es)."""
    if not actual.puede_ver_propiedad(propiedad_id):
        raise HTTPException(status_code=403, detail="Sin acceso a esta propiedad")


async def _propiedad(db: AsyncSession, prop_id: uuid.UUID) -> Propiedad:
    p = (await db.execute(select(Propiedad).where(Propiedad.id == prop_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    return p


def _out(ps: PropiedadSop) -> PropiedadSopOut:
    return PropiedadSopOut(
        id=ps.id, propiedad_id=ps.propiedad_id, sop_master_id=ps.sop_master_id, modo=ps.modo,
        version_fijada=ps.version_fijada, codigo_local=ps.codigo_local, estado=ps.estado,
        requiere_actualizacion=ps.requiere_actualizacion, master_retirado=ps.master_retirado,
        creado_en=ps.creado_en,
    )


@router.post("/api/propiedades/{prop_id}/asignaciones", response_model=PropiedadSopOut, status_code=201)
async def asignar(
    prop_id: uuid.UUID, datos: AsignarRequest, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    prop = await _propiedad(db, prop_id)
    if not _puede_gestionar(actual, prop_id):
        raise HTTPException(status_code=403, detail="Sin permisos sobre esta propiedad")

    if datos.modo == ModoAsignacion.local:
        _, codigo_local = await siguiente_codigo_local(db, prop)
        ps = PropiedadSop(
            propiedad_id=prop_id, sop_master_id=None, modo=ModoAsignacion.local,
            codigo_local=codigo_local, campos_locales=datos.campos_locales or {},
            estado=EstadoAsignacion.borrador,
        )
    else:
        if not datos.sop_master_id:
            raise HTTPException(status_code=422, detail="sop_master_id es requerido para adoptar/adaptar")
        master = (
            await db.execute(select(SopMaster).where(SopMaster.id == datos.sop_master_id))
        ).scalar_one_or_none()
        if not master or master.eliminado_en is not None:
            raise HTTPException(status_code=404, detail="SOP master no encontrado")
        # Solo el set aprobado (firmado) es asignable (§7.4)
        if master.estado != EstadoDocumento.firmado:
            raise HTTPException(
                status_code=409,
                detail="Solo un SOP master firmado puede asignarse a una propiedad.",
            )
        if master.estado == EstadoDocumento.archivado:  # (defensivo) retiro bloquea nuevas (§7.12)
            raise HTTPException(status_code=409, detail="El master está retirado; no es asignable.")
        # Unicidad (propiedad, master) para no-local (§5)
        existe = (
            await db.execute(
                select(PropiedadSop).where(
                    PropiedadSop.propiedad_id == prop_id,
                    PropiedadSop.sop_master_id == datos.sop_master_id,
                    PropiedadSop.eliminado_en.is_(None),
                )
            )
        ).scalar_one_or_none()
        if existe:
            raise HTTPException(status_code=409, detail="La propiedad ya tiene asignado este SOP.")

        if datos.modo == ModoAsignacion.adoptado:
            # Hereda la firma del master → directo a vigente (§11)
            ps = PropiedadSop(
                propiedad_id=prop_id, sop_master_id=master.id, modo=ModoAsignacion.adoptado,
                version_fijada=master.version_actual, estado=EstadoAsignacion.vigente,
                fecha_vigencia=datetime.now(UTC),
            )
        else:  # adaptado → requiere firma local, arranca en borrador (§7.9)
            ps = PropiedadSop(
                propiedad_id=prop_id, sop_master_id=master.id, modo=ModoAsignacion.adaptado,
                version_fijada=master.version_actual, overrides=datos.overrides or {},
                estado=EstadoAsignacion.borrador,
            )
    db.add(ps)
    await db.flush()
    auditar(db, actual.id, "propiedad_sop", ps.id, f"asignar:{datos.modo.value}", ip=request.client.host)
    await db.commit()
    await db.refresh(ps)
    return _out(ps)


@router.get("/api/propiedades/{prop_id}/asignaciones", response_model=list[PropiedadSopOut])
async def listar_asignaciones(
    prop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    _exigir_ver(actual, prop_id)
    q = select(PropiedadSop).where(
        PropiedadSop.propiedad_id == prop_id, PropiedadSop.eliminado_en.is_(None)
    )
    return [_out(ps) for ps in (await db.execute(q)).scalars()]


async def _get_ps(db: AsyncSession, ps_id: uuid.UUID) -> PropiedadSop:
    ps = (await db.execute(select(PropiedadSop).where(PropiedadSop.id == ps_id))).scalar_one_or_none()
    if not ps or ps.eliminado_en is not None:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return ps


async def _detalle(db: AsyncSession, ps: PropiedadSop) -> PropiedadSopDetalle:
    base = _out(ps)
    return PropiedadSopDetalle(
        **base.model_dump(),
        contenido_efectivo=await contenido_efectivo(db, ps),
        contenido_master=await contenido_master_sop(db, ps),
        overrides=ps.overrides,
        campos_locales=ps.campos_locales,
        smart_efectivo=await smart_efectivo_sop(db, ps),
        smart_master=await smart_master_sop(db, ps),
        smart_overrides=ps.smart_overrides,
    )


@router.get("/api/propiedad-sops/{ps_id}", response_model=PropiedadSopDetalle)
async def obtener_asignacion(
    ps_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    ps = await _get_ps(db, ps_id)
    _exigir_ver(actual, ps.propiedad_id)
    return await _detalle(db, ps)


@router.put("/api/propiedad-sops/{ps_id}/overrides", response_model=PropiedadSopDetalle)
async def actualizar_overrides(
    ps_id: uuid.UUID, datos: OverridesRequest,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    ps = await _get_ps(db, ps_id)
    if not _puede_gestionar(actual, ps.propiedad_id):
        raise HTTPException(status_code=403, detail="Sin permisos sobre esta propiedad")
    if ps.estado not in EDITABLES:
        raise HTTPException(status_code=409, detail=f"No editable en estado '{ps.estado.value}'.")
    if ps.modo == ModoAsignacion.adaptado and datos.overrides is not None:
        ps.overrides = datos.overrides
    elif ps.modo == ModoAsignacion.local and datos.campos_locales is not None:
        ps.campos_locales = datos.campos_locales
    else:
        raise HTTPException(status_code=409, detail="El modo de la asignación no admite ese cambio.")
    await db.commit()
    await db.refresh(ps)
    return await _detalle(db, ps)


@router.put("/api/propiedad-sops/{ps_id}/smart-overrides", response_model=PropiedadSopDetalle)
async def actualizar_smart_overrides(
    ps_id: uuid.UUID, datos: SmartOverridesRequest,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    """Personaliza la capa SMART por propiedad. En `adaptado` guarda deltas por sección
    (las secciones ausentes heredan del master); en `local` guarda la SMART completa."""
    ps = await _get_ps(db, ps_id)
    if not _puede_gestionar(actual, ps.propiedad_id):
        raise HTTPException(status_code=403, detail="Sin permisos sobre esta propiedad")
    if ps.estado not in EDITABLES:
        raise HTTPException(status_code=409, detail=f"No editable en estado '{ps.estado.value}'.")
    if ps.modo not in (ModoAsignacion.adaptado, ModoAsignacion.local):
        raise HTTPException(
            status_code=409,
            detail="Solo una asignación adaptada o local puede personalizar la capa SMART.",
        )
    ps.smart_overrides = datos.smart_overrides
    await db.commit()
    await db.refresh(ps)
    return await _detalle(db, ps)


@router.post("/api/propiedad-sops/{ps_id}/adaptar", response_model=PropiedadSopDetalle)
async def adaptar(
    ps_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    """Convierte una asignación ADOPTADA en ADAPTADA para poder personalizar secciones
    (overrides). Arranca sin overrides (hereda todo) y vuelve a `borrador`: la versión
    local requiere su propia firma antes de quedar vigente (§7.9)."""
    ps = await _get_ps(db, ps_id)
    if not _puede_gestionar(actual, ps.propiedad_id):
        raise HTTPException(status_code=403, detail="Sin permisos sobre esta propiedad")
    if ps.modo != ModoAsignacion.adoptado:
        raise HTTPException(status_code=409, detail="Solo una asignación adoptada puede adaptarse.")
    ps.modo = ModoAsignacion.adaptado
    ps.overrides = ps.overrides or {}
    ps.estado = EstadoAsignacion.borrador
    ps.fecha_vigencia = None
    auditar(db, actual.id, "propiedad_sop", ps.id, "adaptar", ip=request.client.host)
    await db.commit()
    await db.refresh(ps)
    return await _detalle(db, ps)


@router.post("/api/propiedad-sops/{ps_id}/actualizar", response_model=PropiedadSopOut)
async def sincronizar(
    ps_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    """Actualiza version_fijada a la versión firmada vigente del master y limpia la
    bandera requiere_actualizacion (§7.11). Nunca es automático."""
    ps = await _get_ps(db, ps_id)
    if not _puede_gestionar(actual, ps.propiedad_id):
        raise HTTPException(status_code=403, detail="Sin permisos sobre esta propiedad")
    if not ps.sop_master_id:
        raise HTTPException(status_code=409, detail="Una asignación local no se sincroniza con un master.")
    master = (await db.execute(select(SopMaster).where(SopMaster.id == ps.sop_master_id))).scalar_one()
    ps.version_fijada = master.version_actual
    ps.requiere_actualizacion = False
    auditar(db, actual.id, "propiedad_sop", ps.id, "sincronizar",
            {"version_fijada": master.version_actual}, request.client.host)
    await db.commit()
    await db.refresh(ps)
    return _out(ps)


@router.get("/api/propiedades/{prop_id}/sugerencias", response_model=list[Sugerencia])
async def sugerencias_por_sistemas(
    prop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    """Compara los sistemas que asume cada master firmado vs. los sistemas de la propiedad
    y sugiere adoptar / adaptar / no_aplica (§7.13). Nunca automático — siempre editable."""
    await _propiedad(db, prop_id)
    _exigir_ver(actual, prop_id)
    sistemas_prop = {
        r for r in (await db.execute(
            select(PropiedadSistema.sistema_id).where(PropiedadSistema.propiedad_id == prop_id)
        )).scalars()
    }
    ya_asignados = {
        r for r in (await db.execute(
            select(PropiedadSop.sop_master_id).where(
                PropiedadSop.propiedad_id == prop_id, PropiedadSop.eliminado_en.is_(None)
            )
        )).scalars() if r
    }
    masters = list(
        (await db.execute(
            select(SopMaster).where(
                SopMaster.estado == EstadoDocumento.firmado, SopMaster.eliminado_en.is_(None)
            )
        )).scalars()
    )
    salida: list[Sugerencia] = []
    for m in masters:
        if m.id in ya_asignados:
            continue
        req = list(
            (await db.execute(
                select(SopMasterSistema.sistema_id).where(SopMasterSistema.sop_master_id == m.id)
            )).scalars()
        )
        faltantes_ids = [s for s in req if s not in sistemas_prop]
        if not req or not faltantes_ids:
            sug, motivo = ModoAsignacion.adoptado, "La propiedad tiene todos los sistemas que asume el SOP."
        else:
            sug, motivo = ModoAsignacion.adaptado, "Faltan sistemas; requiere adaptación o no_aplica."
        salida.append(Sugerencia(
            sop_master_id=m.id, codigo=m.codigo, nombre=m.nombre, sugerencia=sug,
            sistemas_faltantes=[str(s) for s in faltantes_ids], motivo=motivo,
        ))
    return salida
