"""Armador por propiedad: cada hotel arma su operación eligiendo del catálogo maestro
—departamentos, puestos (organigrama local adoptar/adaptar/local con jerarquía propia),
titulares de cada puesto y sistemas— más un resumen por propiedad para el hub (§5, §7.8-7.13).

Complementa a `propiedad_sops.py` (motor de SOPs por propiedad, ya existente) cubriendo la
escritura de `propiedad_departamentos`, `propiedad_puesto` (+ ocupantes) y `propiedad_sistemas`.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, get_current_user
from app.core.db import get_db
from app.models.base import EstadoAsignacion, ModoAsignacion, RolUsuario
from app.models.catalogos import (
    Departamento,
    Propiedad,
    PropiedadDepartamento,
    PropiedadSistema,
    Sistema,
)
from app.models.propiedad import PropiedadPuesto, PropiedadPuestoOcupante, PropiedadSop
from app.models.puesto import DescriptorPuestoMaster
from app.models.usuarios import Usuario
from app.schemas.propiedad_armador import (
    DepartamentoAsignadoOut,
    DepartamentosSet,
    OcupanteCrear,
    OcupanteOut,
    PropiedadResumen,
    PuestoActualizar,
    PuestoCrear,
    PuestoDetalle,
    PuestoOut,
    SembrarRequest,
    SembrarResultado,
    SistemaAsignadoOut,
    SistemasSet,
    SmartOverridesPuestoRequest,
)
from app.services.auditoria import auditar
from app.services.merge import (
    contenido_efectivo_puesto,
    resolver_puesto,
    smart_efectivo_puesto,
    smart_master_puesto,
)

router = APIRouter(tags=["armador"])

EDITABLES = {EstadoAsignacion.borrador, EstadoAsignacion.en_revision, EstadoAsignacion.rechazado}


def _puede_gestionar(actual: UsuarioActual, propiedad_id: uuid.UUID) -> bool:
    return actual.tiene_rol(
        RolUsuario.super_admin, RolUsuario.editor_corporativo
    ) or actual.tiene_rol_en_propiedad(RolUsuario.editor_propiedad, propiedad_id)


async def _propiedad(db: AsyncSession, prop_id: uuid.UUID) -> Propiedad:
    p = (await db.execute(select(Propiedad).where(Propiedad.id == prop_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    return p


def _exigir_permiso(actual: UsuarioActual, prop_id: uuid.UUID) -> None:
    if not _puede_gestionar(actual, prop_id):
        raise HTTPException(status_code=403, detail="Sin permisos sobre esta propiedad")


def _exigir_ver(actual: UsuarioActual, prop_id: uuid.UUID) -> None:
    """Visibilidad por propiedad (§14): cada usuario ve solo su(s) propiedad(es); el
    corporativo ve todas."""
    if not actual.puede_ver_propiedad(prop_id):
        raise HTTPException(status_code=403, detail="Sin acceso a esta propiedad")


async def _deptos_map(db: AsyncSession) -> dict[uuid.UUID, str]:
    return {d.id: d.codigo for d in (await db.execute(select(Departamento))).scalars()}


# =========================================================================================
# RESUMEN (hub del armador)
# =========================================================================================


@router.get("/api/propiedades/resumen", response_model=list[PropiedadResumen])
async def resumen_propiedades(
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user)
):
    acc = actual.propiedades_accesibles()  # None = todas (corporativo)
    props = list(
        (await db.execute(select(Propiedad).order_by(Propiedad.codigo))).scalars()
    )
    if acc is not None:
        props = [p for p in props if p.id in acc]

    async def _conteo(stmt) -> dict[uuid.UUID, int]:
        return {pid: n for pid, n in (await db.execute(stmt)).all()}

    deptos = await _conteo(
        select(PropiedadDepartamento.propiedad_id, func.count()).group_by(
            PropiedadDepartamento.propiedad_id
        )
    )
    puestos = await _conteo(
        select(PropiedadPuesto.propiedad_id, func.count())
        .where(PropiedadPuesto.eliminado_en.is_(None))
        .group_by(PropiedadPuesto.propiedad_id)
    )
    ocupantes = await _conteo(
        select(PropiedadPuesto.propiedad_id, func.count(PropiedadPuestoOcupante.id))
        .join(PropiedadPuestoOcupante, PropiedadPuestoOcupante.propiedad_puesto_id == PropiedadPuesto.id)
        .where(PropiedadPuesto.eliminado_en.is_(None))
        .group_by(PropiedadPuesto.propiedad_id)
    )
    sops = await _conteo(
        select(PropiedadSop.propiedad_id, func.count())
        .where(PropiedadSop.eliminado_en.is_(None))
        .group_by(PropiedadSop.propiedad_id)
    )
    sistemas = await _conteo(
        select(PropiedadSistema.propiedad_id, func.count()).group_by(
            PropiedadSistema.propiedad_id
        )
    )
    return [
        PropiedadResumen(
            id=p.id, codigo=p.codigo, nombre=p.nombre, activo=p.activo,
            departamentos=deptos.get(p.id, 0), puestos=puestos.get(p.id, 0),
            ocupantes=ocupantes.get(p.id, 0), sops=sops.get(p.id, 0),
            sistemas=sistemas.get(p.id, 0),
        )
        for p in props
    ]


# =========================================================================================
# DEPARTAMENTOS por propiedad
# =========================================================================================


async def _listar_departamentos(db: AsyncSession, prop_id: uuid.UUID) -> list[DepartamentoAsignadoOut]:
    rows = (
        await db.execute(
            select(Departamento)
            .join(PropiedadDepartamento, PropiedadDepartamento.departamento_id == Departamento.id)
            .where(PropiedadDepartamento.propiedad_id == prop_id)
            .order_by(Departamento.codigo)
        )
    ).scalars()
    return [
        DepartamentoAsignadoOut(id=d.id, codigo=d.codigo, nombre=d.nombre, division_id=d.division_id)
        for d in rows
    ]


@router.get("/api/propiedades/{prop_id}/departamentos", response_model=list[DepartamentoAsignadoOut])
async def listar_departamentos(
    prop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    _exigir_ver(actual, prop_id)
    return await _listar_departamentos(db, prop_id)


@router.put("/api/propiedades/{prop_id}/departamentos", response_model=list[DepartamentoAsignadoOut])
async def fijar_departamentos(
    prop_id: uuid.UUID, datos: DepartamentosSet, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    _exigir_permiso(actual, prop_id)
    nuevos = set(datos.departamento_ids)
    if nuevos:
        validos = {
            r for r in (await db.execute(
                select(Departamento.id).where(Departamento.id.in_(nuevos))
            )).scalars()
        }
        faltan = nuevos - validos
        if faltan:
            raise HTTPException(status_code=422, detail=f"Departamentos inexistentes: {faltan}")

    actuales = {
        pd.departamento_id: pd
        for pd in (await db.execute(
            select(PropiedadDepartamento).where(PropiedadDepartamento.propiedad_id == prop_id)
        )).scalars()
    }
    for dep_id, pd in actuales.items():
        if dep_id not in nuevos:
            await db.delete(pd)
    for dep_id in nuevos:
        if dep_id not in actuales:
            db.add(PropiedadDepartamento(propiedad_id=prop_id, departamento_id=dep_id))
    auditar(db, actual.id, "propiedad_departamento", prop_id, "fijar",
            {"total": len(nuevos)}, request.client.host)
    await db.commit()
    return await _listar_departamentos(db, prop_id)


# =========================================================================================
# PUESTOS por propiedad (organigrama local)
# =========================================================================================


def _out_puesto(
    pp: PropiedadPuesto, master: DescriptorPuestoMaster | None,
    deptos: dict[uuid.UUID, str], ocupantes_count: int = 0,
) -> PuestoOut:
    r = resolver_puesto(pp, master)
    dep_id = r["departamento_id"]
    return PuestoOut(
        id=pp.id, propiedad_id=pp.propiedad_id,
        descriptor_puesto_master_id=pp.descriptor_puesto_master_id, modo=pp.modo,
        titulo=r["titulo"], codigo=r["codigo"], nivel_jerarquico=r["nivel_jerarquico"],
        categoria=r["categoria"], departamento_id=dep_id,
        departamento_codigo=deptos.get(dep_id) if dep_id else None,
        reporta_a_id=pp.reporta_a_id, dotacion=pp.dotacion, estado=pp.estado,
        requiere_actualizacion=pp.requiere_actualizacion, ocupantes_count=ocupantes_count,
    )


async def _get_puesto(db: AsyncSession, prop_id: uuid.UUID, pp_id: uuid.UUID) -> PropiedadPuesto:
    pp = (
        await db.execute(select(PropiedadPuesto).where(PropiedadPuesto.id == pp_id))
    ).scalar_one_or_none()
    if not pp or pp.eliminado_en is not None or pp.propiedad_id != prop_id:
        raise HTTPException(status_code=404, detail="Puesto no encontrado en esta propiedad")
    return pp


async def _verificar_sin_ciclo(
    db: AsyncSession, prop_id: uuid.UUID, pp_id: uuid.UUID, nuevo_jefe_id: uuid.UUID
) -> None:
    """Sube por la cadena de reporte desde el nuevo jefe; si alcanza al propio puesto, el
    cambio cerraría un ciclo en el organigrama (§8.14, mismo criterio que el master)."""
    visto: set[uuid.UUID] = set()
    actual: uuid.UUID | None = nuevo_jefe_id
    while actual is not None:
        if actual == pp_id:
            raise HTTPException(status_code=409, detail="El cambio crearía un ciclo en el organigrama.")
        if actual in visto:
            break
        visto.add(actual)
        actual = (
            await db.execute(
                select(PropiedadPuesto.reporta_a_id).where(
                    PropiedadPuesto.id == actual,
                    PropiedadPuesto.propiedad_id == prop_id,
                    PropiedadPuesto.eliminado_en.is_(None),
                )
            )
        ).scalar_one_or_none()


async def _ocupantes(db: AsyncSession, pp_id: uuid.UUID) -> list[OcupanteOut]:
    rows = (
        await db.execute(
            select(PropiedadPuestoOcupante, Usuario)
            .join(Usuario, Usuario.id == PropiedadPuestoOcupante.usuario_id)
            .where(PropiedadPuestoOcupante.propiedad_puesto_id == pp_id)
            .order_by(PropiedadPuestoOcupante.es_principal.desc(), Usuario.nombre)
        )
    ).all()
    return [
        OcupanteOut(
            id=o.id, usuario_id=o.usuario_id, usuario_nombre=u.nombre, usuario_email=u.email,
            es_principal=o.es_principal, nota=o.nota,
        )
        for o, u in rows
    ]


async def _detalle_puesto(
    db: AsyncSession, pp: PropiedadPuesto, master: DescriptorPuestoMaster | None,
    deptos: dict[uuid.UUID, str],
) -> PuestoDetalle:
    ocupantes = await _ocupantes(db, pp.id)
    base = _out_puesto(pp, master, deptos, ocupantes_count=len(ocupantes))
    return PuestoDetalle(
        **base.model_dump(),
        contenido_efectivo=await contenido_efectivo_puesto(db, pp),
        ocupantes=ocupantes,
        creado_en=pp.creado_en,
        smart_efectivo=await smart_efectivo_puesto(db, pp),
        smart_master=await smart_master_puesto(db, pp),
        smart_overrides=pp.smart_overrides,
    )


@router.get("/api/propiedades/{prop_id}/puestos", response_model=list[PuestoOut])
async def listar_puestos(
    prop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    _exigir_ver(actual, prop_id)
    puestos = list(
        (await db.execute(
            select(PropiedadPuesto).where(
                PropiedadPuesto.propiedad_id == prop_id, PropiedadPuesto.eliminado_en.is_(None)
            )
        )).scalars()
    )
    masters = {m.id: m for m in (await db.execute(select(DescriptorPuestoMaster))).scalars()}
    deptos = await _deptos_map(db)
    conteos: dict[uuid.UUID, int] = {}
    if puestos:
        conteos = {
            pid: n
            for pid, n in (await db.execute(
                select(PropiedadPuestoOcupante.propiedad_puesto_id, func.count())
                .where(PropiedadPuestoOcupante.propiedad_puesto_id.in_([p.id for p in puestos]))
                .group_by(PropiedadPuestoOcupante.propiedad_puesto_id)
            )).all()
        }
    return [
        _out_puesto(p, masters.get(p.descriptor_puesto_master_id), deptos, conteos.get(p.id, 0))
        for p in puestos
    ]


@router.post("/api/propiedades/{prop_id}/puestos", response_model=PuestoOut, status_code=201)
async def crear_puesto(
    prop_id: uuid.UUID, datos: PuestoCrear, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    _exigir_permiso(actual, prop_id)

    master: DescriptorPuestoMaster | None = None
    if datos.modo in (ModoAsignacion.adoptado, ModoAsignacion.adaptado):
        if not datos.descriptor_puesto_master_id:
            raise HTTPException(
                status_code=422,
                detail="descriptor_puesto_master_id es requerido para adoptar/adaptar",
            )
        master = (
            await db.execute(
                select(DescriptorPuestoMaster).where(
                    DescriptorPuestoMaster.id == datos.descriptor_puesto_master_id
                )
            )
        ).scalar_one_or_none()
        if not master or master.eliminado_en is not None:
            raise HTTPException(status_code=404, detail="Descriptor de puesto master no encontrado")
        existe = (
            await db.execute(
                select(PropiedadPuesto).where(
                    PropiedadPuesto.propiedad_id == prop_id,
                    PropiedadPuesto.descriptor_puesto_master_id == master.id,
                    PropiedadPuesto.eliminado_en.is_(None),
                )
            )
        ).scalar_one_or_none()
        if existe:
            raise HTTPException(status_code=409, detail="La propiedad ya tiene este puesto del maestro.")
    elif datos.modo == ModoAsignacion.local:
        if not (datos.overrides or {}).get("titulo"):
            raise HTTPException(status_code=422, detail="Un puesto local requiere 'titulo' en overrides.")
    else:
        raise HTTPException(status_code=422, detail="Modo no soportado para puestos.")

    if datos.reporta_a_id is not None:
        await _get_puesto(db, prop_id, datos.reporta_a_id)  # 404 si no pertenece a la propiedad

    if datos.modo == ModoAsignacion.adoptado:
        estado, overrides, version = EstadoAsignacion.vigente, None, master.version_actual
    elif datos.modo == ModoAsignacion.adaptado:
        estado, overrides, version = EstadoAsignacion.borrador, (datos.overrides or {}), master.version_actual
    else:  # local
        estado, overrides, version = EstadoAsignacion.borrador, (datos.overrides or {}), None

    pp = PropiedadPuesto(
        propiedad_id=prop_id, descriptor_puesto_master_id=datos.descriptor_puesto_master_id,
        modo=datos.modo, version_fijada=version, overrides=overrides,
        reporta_a_id=datos.reporta_a_id, dotacion=datos.dotacion, estado=estado,
    )
    db.add(pp)
    await db.flush()
    auditar(db, actual.id, "propiedad_puesto", pp.id, f"crear:{datos.modo.value}", ip=request.client.host)
    await db.commit()
    await db.refresh(pp)
    return _out_puesto(pp, master, await _deptos_map(db))


@router.get("/api/propiedades/{prop_id}/puestos/{pp_id}", response_model=PuestoDetalle)
async def obtener_puesto(
    prop_id: uuid.UUID, pp_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    _exigir_ver(actual, prop_id)
    pp = await _get_puesto(db, prop_id, pp_id)
    master = (
        await db.get(DescriptorPuestoMaster, pp.descriptor_puesto_master_id)
        if pp.descriptor_puesto_master_id else None
    )
    return await _detalle_puesto(db, pp, master, await _deptos_map(db))


@router.put("/api/propiedades/{prop_id}/puestos/{pp_id}", response_model=PuestoDetalle)
async def actualizar_puesto(
    prop_id: uuid.UUID, pp_id: uuid.UUID, datos: PuestoActualizar, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    _exigir_permiso(actual, prop_id)
    pp = await _get_puesto(db, prop_id, pp_id)
    campos = datos.model_dump(exclude_unset=True)

    if "reporta_a_id" in campos:
        nuevo = campos["reporta_a_id"]
        if nuevo is not None:
            if nuevo == pp.id:
                raise HTTPException(status_code=422, detail="Un puesto no puede reportarse a sí mismo.")
            await _get_puesto(db, prop_id, nuevo)
            await _verificar_sin_ciclo(db, prop_id, pp.id, nuevo)
        pp.reporta_a_id = nuevo
    if "dotacion" in campos:
        pp.dotacion = campos["dotacion"]
    if "overrides" in campos and campos["overrides"] is not None:
        if pp.modo == ModoAsignacion.adoptado:
            raise HTTPException(
                status_code=409, detail="Un puesto adoptado no admite overrides; adaptalo primero."
            )
        pp.overrides = campos["overrides"]

    auditar(db, actual.id, "propiedad_puesto", pp.id, "actualizar", ip=request.client.host)
    await db.commit()
    await db.refresh(pp)
    master = (
        await db.get(DescriptorPuestoMaster, pp.descriptor_puesto_master_id)
        if pp.descriptor_puesto_master_id else None
    )
    return await _detalle_puesto(db, pp, master, await _deptos_map(db))


@router.put(
    "/api/propiedades/{prop_id}/puestos/{pp_id}/smart-overrides", response_model=PuestoDetalle
)
async def actualizar_smart_overrides_puesto(
    prop_id: uuid.UUID, pp_id: uuid.UUID, datos: SmartOverridesPuestoRequest, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    """Personaliza la capa JD SMART por propiedad. En `adaptado` guarda deltas por sección
    (las ausentes heredan del master); en `local` guarda la SMART completa."""
    await _propiedad(db, prop_id)
    _exigir_permiso(actual, prop_id)
    pp = await _get_puesto(db, prop_id, pp_id)
    if pp.modo not in (ModoAsignacion.adaptado, ModoAsignacion.local):
        raise HTTPException(
            status_code=409,
            detail="Solo un puesto adaptado o local puede personalizar la capa SMART.",
        )
    pp.smart_overrides = datos.smart_overrides
    auditar(db, actual.id, "propiedad_puesto", pp.id, "smart-overrides", ip=request.client.host)
    await db.commit()
    await db.refresh(pp)
    master = (
        await db.get(DescriptorPuestoMaster, pp.descriptor_puesto_master_id)
        if pp.descriptor_puesto_master_id else None
    )
    return await _detalle_puesto(db, pp, master, await _deptos_map(db))


@router.delete("/api/propiedades/{prop_id}/puestos/{pp_id}", status_code=204)
async def eliminar_puesto(
    prop_id: uuid.UUID, pp_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    from datetime import UTC, datetime

    await _propiedad(db, prop_id)
    _exigir_permiso(actual, prop_id)
    pp = await _get_puesto(db, prop_id, pp_id)
    # Promover a los subordinados al superior del puesto eliminado (evita huérfanos colgando).
    hijos = list(
        (await db.execute(
            select(PropiedadPuesto).where(
                PropiedadPuesto.reporta_a_id == pp.id, PropiedadPuesto.eliminado_en.is_(None)
            )
        )).scalars()
    )
    for h in hijos:
        h.reporta_a_id = pp.reporta_a_id
    # Quitar titulares del puesto eliminado.
    for oc in (await db.execute(
        select(PropiedadPuestoOcupante).where(PropiedadPuestoOcupante.propiedad_puesto_id == pp.id)
    )).scalars():
        await db.delete(oc)
    pp.eliminado_en = datetime.now(UTC)
    auditar(db, actual.id, "propiedad_puesto", pp.id, "eliminar", ip=request.client.host)
    await db.commit()


@router.post(
    "/api/propiedades/{prop_id}/puestos/sembrar-desde-maestro", response_model=SembrarResultado
)
async def sembrar_desde_maestro(
    prop_id: uuid.UUID, datos: SembrarRequest, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    """Adopta en bloque el organigrama maestro de los departamentos indicados (o de todos
    los asignados a la propiedad) como puestos adoptados, remapeando la jerarquía `reporta_a`
    a los puestos de la propiedad. Idempotente: omite los puestos ya presentes."""
    await _propiedad(db, prop_id)
    _exigir_permiso(actual, prop_id)

    if datos.departamento_ids is not None:
        target = set(datos.departamento_ids)
    else:
        target = {
            r for r in (await db.execute(
                select(PropiedadDepartamento.departamento_id).where(
                    PropiedadDepartamento.propiedad_id == prop_id
                )
            )).scalars()
        }

    cond = []
    if target:
        cond.append(DescriptorPuestoMaster.departamento_id.in_(target))
    if datos.incluir_sin_departamento:
        cond.append(DescriptorPuestoMaster.departamento_id.is_(None))
    if not cond:
        return SembrarResultado(creados=0, omitidos=0)

    masters = list(
        (await db.execute(
            select(DescriptorPuestoMaster).where(
                DescriptorPuestoMaster.eliminado_en.is_(None), or_(*cond)
            )
        )).scalars()
    )
    existentes = list(
        (await db.execute(
            select(PropiedadPuesto).where(
                PropiedadPuesto.propiedad_id == prop_id, PropiedadPuesto.eliminado_en.is_(None)
            )
        )).scalars()
    )
    por_master: dict[uuid.UUID, PropiedadPuesto] = {
        pp.descriptor_puesto_master_id: pp for pp in existentes if pp.descriptor_puesto_master_id
    }

    nuevos: list[tuple[PropiedadPuesto, DescriptorPuestoMaster]] = []
    omitidos = 0
    for m in masters:
        if m.id in por_master:
            omitidos += 1
            continue
        pp = PropiedadPuesto(
            propiedad_id=prop_id, descriptor_puesto_master_id=m.id, modo=ModoAsignacion.adoptado,
            version_fijada=m.version_actual, estado=EstadoAsignacion.vigente, dotacion=1,
        )
        db.add(pp)
        nuevos.append((pp, m))
    await db.flush()

    for pp, m in nuevos:  # completar el mapa con los recién creados
        por_master[m.id] = pp
    for pp, m in nuevos:  # remapear reporta_a al puesto de la propiedad, si el jefe fue sembrado
        if m.reporta_a_id and m.reporta_a_id in por_master:
            pp.reporta_a_id = por_master[m.reporta_a_id].id

    auditar(db, actual.id, "propiedad_puesto", prop_id, "sembrar_desde_maestro",
            {"creados": len(nuevos), "omitidos": omitidos}, request.client.host)
    await db.commit()
    return SembrarResultado(creados=len(nuevos), omitidos=omitidos)


# =========================================================================================
# TITULARES (ocupantes) de un puesto
# =========================================================================================


@router.get(
    "/api/propiedades/{prop_id}/puestos/{pp_id}/ocupantes", response_model=list[OcupanteOut]
)
async def listar_ocupantes(
    prop_id: uuid.UUID, pp_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    _exigir_ver(actual, prop_id)
    await _get_puesto(db, prop_id, pp_id)
    return await _ocupantes(db, pp_id)


@router.post(
    "/api/propiedades/{prop_id}/puestos/{pp_id}/ocupantes", response_model=OcupanteOut, status_code=201
)
async def agregar_ocupante(
    prop_id: uuid.UUID, pp_id: uuid.UUID, datos: OcupanteCrear, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    _exigir_permiso(actual, prop_id)
    await _get_puesto(db, prop_id, pp_id)
    usuario = (
        await db.execute(select(Usuario).where(Usuario.id == datos.usuario_id))
    ).scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    dup = (
        await db.execute(
            select(PropiedadPuestoOcupante).where(
                PropiedadPuestoOcupante.propiedad_puesto_id == pp_id,
                PropiedadPuestoOcupante.usuario_id == datos.usuario_id,
            )
        )
    ).scalar_one_or_none()
    if dup:
        raise HTTPException(status_code=409, detail="Ese usuario ya es titular de este puesto.")
    if datos.es_principal:  # a lo sumo un titular principal por puesto
        for otro in (await db.execute(
            select(PropiedadPuestoOcupante).where(
                PropiedadPuestoOcupante.propiedad_puesto_id == pp_id,
                PropiedadPuestoOcupante.es_principal.is_(True),
            )
        )).scalars():
            otro.es_principal = False
    oc = PropiedadPuestoOcupante(
        propiedad_puesto_id=pp_id, usuario_id=datos.usuario_id,
        es_principal=datos.es_principal, nota=datos.nota,
    )
    db.add(oc)
    await db.flush()
    auditar(db, actual.id, "propiedad_puesto_ocupante", oc.id, "agregar", ip=request.client.host)
    await db.commit()
    return OcupanteOut(
        id=oc.id, usuario_id=usuario.id, usuario_nombre=usuario.nombre, usuario_email=usuario.email,
        es_principal=oc.es_principal, nota=oc.nota,
    )


@router.delete(
    "/api/propiedades/{prop_id}/puestos/{pp_id}/ocupantes/{ocupante_id}", status_code=204
)
async def quitar_ocupante(
    prop_id: uuid.UUID, pp_id: uuid.UUID, ocupante_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    _exigir_permiso(actual, prop_id)
    await _get_puesto(db, prop_id, pp_id)
    oc = (
        await db.execute(
            select(PropiedadPuestoOcupante).where(
                PropiedadPuestoOcupante.id == ocupante_id,
                PropiedadPuestoOcupante.propiedad_puesto_id == pp_id,
            )
        )
    ).scalar_one_or_none()
    if not oc:
        raise HTTPException(status_code=404, detail="Titular no encontrado")
    await db.delete(oc)
    auditar(db, actual.id, "propiedad_puesto_ocupante", ocupante_id, "quitar", ip=request.client.host)
    await db.commit()


# =========================================================================================
# SISTEMAS por propiedad
# =========================================================================================


async def _listar_sistemas(db: AsyncSession, prop_id: uuid.UUID) -> list[SistemaAsignadoOut]:
    rows = (
        await db.execute(
            select(Sistema)
            .join(PropiedadSistema, PropiedadSistema.sistema_id == Sistema.id)
            .where(PropiedadSistema.propiedad_id == prop_id)
            .order_by(Sistema.codigo)
        )
    ).scalars()
    return [
        SistemaAsignadoOut(id=s.id, codigo=s.codigo, nombre=s.nombre, categoria=s.categoria)
        for s in rows
    ]


@router.get("/api/propiedades/{prop_id}/sistemas", response_model=list[SistemaAsignadoOut])
async def listar_sistemas(
    prop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    _exigir_ver(actual, prop_id)
    return await _listar_sistemas(db, prop_id)


@router.put("/api/propiedades/{prop_id}/sistemas", response_model=list[SistemaAsignadoOut])
async def fijar_sistemas(
    prop_id: uuid.UUID, datos: SistemasSet, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    await _propiedad(db, prop_id)
    _exigir_permiso(actual, prop_id)
    nuevos = set(datos.sistema_ids)
    if nuevos:
        validos = {
            r for r in (await db.execute(
                select(Sistema.id).where(Sistema.id.in_(nuevos))
            )).scalars()
        }
        faltan = nuevos - validos
        if faltan:
            raise HTTPException(status_code=422, detail=f"Sistemas inexistentes: {faltan}")

    actuales = {
        ps.sistema_id: ps
        for ps in (await db.execute(
            select(PropiedadSistema).where(PropiedadSistema.propiedad_id == prop_id)
        )).scalars()
    }
    for sis_id, ps in actuales.items():
        if sis_id not in nuevos:
            await db.delete(ps)
    for sis_id in nuevos:
        if sis_id not in actuales:
            db.add(PropiedadSistema(propiedad_id=prop_id, sistema_id=sis_id))
    auditar(db, actual.id, "propiedad_sistema", prop_id, "fijar",
            {"total": len(nuevos)}, request.client.host)
    await db.commit()
    return await _listar_sistemas(db, prop_id)
