"""CRUD del master de SOPs: formato único, numeración atómica, versionado y búsqueda
(§7.1, §7.2, §7.18, §8.5). Las transiciones de estado y la firma van en E4.3."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, get_current_user, require_rol
from app.core.config import get_settings
from app.core.db import get_db
from app.models.base import EstadoDocumento, RolUsuario, TipoDocumento
from app.models.catalogos import Area, Departamento, Sistema
from app.models.puesto import DescriptorPuestoMaster
from app.models.sop import (
    ColaboradorSop,
    FirmaElectronica,
    FirmanteSop,
    SopMaster,
    SopMasterDepartamentoAfectado,
    SopMasterPuestoResponsable,
    SopMasterSistema,
    SopMasterVersion,
)
from app.models.usuarios import Usuario
from app.schemas.sop import (
    DepartamentoMini,
    PuestoMini,
    SopActualizar,
    SopCrear,
    SopDetalle,
    SopItem,
    SopLista,
    SopSmartActualizar,
    SopVersionDetalle,
    SopVersionItem,
)

router = APIRouter(prefix="/api/sops", tags=["sops"])

# Solo el editor del ámbito corporativo (o super_admin) gestiona el master.
editor = require_rol(RolUsuario.editor_corporativo, RolUsuario.super_admin)

# Estados en los que se puede editar el contenido (§7.6: 'firmado' es inmutable).
EDITABLES = {EstadoDocumento.borrador, EstadoDocumento.en_revision, EstadoDocumento.rechazado}

# Campos de relación (no son columnas de SopMaster; se manejan aparte en crear/actualizar).
CAMPOS_RELACION = {"departamentos_afectados_ids", "puestos_responsables_ids"}


async def _area_por_codigo(db: AsyncSession, codigo: str) -> Area:
    area = (await db.execute(select(Area).where(Area.codigo == codigo))).scalar_one_or_none()
    if not area:
        raise HTTPException(status_code=404, detail=f"Área '{codigo}' no existe")
    return area


async def _sistemas_codigos(db: AsyncSession, sop_id: uuid.UUID) -> list[str]:
    q = (
        select(Sistema.codigo)
        .join(SopMasterSistema, SopMasterSistema.sistema_id == Sistema.id)
        .where(SopMasterSistema.sop_master_id == sop_id)
    )
    return list((await db.execute(q)).scalars())


async def _departamentos_afectados(db: AsyncSession, sop_id: uuid.UUID) -> list[DepartamentoMini]:
    q = (
        select(Departamento)
        .join(
            SopMasterDepartamentoAfectado,
            SopMasterDepartamentoAfectado.departamento_id == Departamento.id,
        )
        .where(SopMasterDepartamentoAfectado.sop_master_id == sop_id)
        .order_by(Departamento.codigo)
    )
    return [
        DepartamentoMini(id=d.id, codigo=d.codigo, nombre=d.nombre)
        for d in (await db.execute(q)).scalars()
    ]


async def _puestos_responsables(db: AsyncSession, sop_id: uuid.UUID) -> list[PuestoMini]:
    q = (
        select(DescriptorPuestoMaster)
        .join(
            SopMasterPuestoResponsable,
            SopMasterPuestoResponsable.descriptor_puesto_master_id == DescriptorPuestoMaster.id,
        )
        .where(SopMasterPuestoResponsable.sop_master_id == sop_id)
        .order_by(DescriptorPuestoMaster.codigo)
    )
    return [
        PuestoMini(id=p.id, codigo=p.codigo, titulo=p.titulo)
        for p in (await db.execute(q)).scalars()
    ]


async def _set_departamentos_afectados(
    db: AsyncSession, sop_id: uuid.UUID, ids: list[uuid.UUID]
) -> None:
    """Reemplaza la lista completa de departamentos afectados (no incremental)."""
    from sqlalchemy import delete

    await db.execute(
        delete(SopMasterDepartamentoAfectado).where(
            SopMasterDepartamentoAfectado.sop_master_id == sop_id
        )
    )
    if not ids:
        return
    validos = set(
        (
            await db.execute(select(Departamento.id).where(Departamento.id.in_(set(ids))))
        ).scalars()
    )
    for did in validos:
        db.add(SopMasterDepartamentoAfectado(sop_master_id=sop_id, departamento_id=did))


async def _set_puestos_responsables(
    db: AsyncSession, sop_id: uuid.UUID, ids: list[uuid.UUID]
) -> None:
    """Reemplaza la lista completa de puestos responsables (no incremental)."""
    from sqlalchemy import delete

    await db.execute(
        delete(SopMasterPuestoResponsable).where(SopMasterPuestoResponsable.sop_master_id == sop_id)
    )
    if not ids:
        return
    validos = set(
        (
            await db.execute(
                select(DescriptorPuestoMaster.id).where(
                    DescriptorPuestoMaster.id.in_(set(ids)),
                    DescriptorPuestoMaster.eliminado_en.is_(None),
                )
            )
        ).scalars()
    )
    for pid in validos:
        db.add(SopMasterPuestoResponsable(sop_master_id=sop_id, descriptor_puesto_master_id=pid))


async def _exigir_puede_editar_smart(
    db: AsyncSession, sop_id: uuid.UUID, actual: UsuarioActual
) -> None:
    """Quién puede escribir la capa SMART: el corporativo, o un colaborador **redactor**
    invitado a ESE SOP.

    La colaboración es el mecanismo para que cada área complete sus propios pendientes sin
    darle el master entero. Crear/borrar SOPs y editar los 9 campos base siguen siendo
    exclusivos del corporativo."""
    if actual.es_corporativo():
        return
    redactor = (
        await db.execute(
            select(ColaboradorSop).where(
                ColaboradorSop.sop_master_id == sop_id,
                ColaboradorSop.usuario_id == actual.id,
                ColaboradorSop.rol_colaboracion == "redactor",
            )
        )
    ).scalars().first()
    if redactor is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "No sos colaborador redactor de este SOP. Pedile al editor corporativo "
                "que te invite a colaborar."
            ),
        )


def _exigir_sello(sop: SopMaster, base: datetime | None) -> None:
    """Concurrencia optimista sobre `actualizado_en`.

    Sin sello NO hay control: los scripts de migración escriben sin abrir un editor.
    Con sello, si el SOP cambió desde que se cargó el editor, se rechaza en vez de pisar
    el trabajo del otro usuario."""
    if base is None:
        return
    actual = sop.actualizado_en
    if actual.tzinfo is None:
        actual = actual.replace(tzinfo=timezone.utc)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    if actual != base:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Otro usuario guardó cambios en este SOP mientras lo editabas. "
                "Recargá la ficha para no pisar su trabajo; tus cambios no se guardaron."
            ),
        )


def _snapshot(sop: SopMaster) -> dict:
    return {
        "codigo": sop.codigo, "nombre": sop.nombre, "tipo": sop.tipo.value,
        "proposito": sop.proposito, "evaluacion_riesgos": sop.evaluacion_riesgos,
        "controles_existentes": sop.controles_existentes, "procedimiento": sop.procedimiento,
        "responsables": sop.responsables, "evidencia": sop.evidencia,
        "frecuencia_revision": sop.frecuencia_revision.value if sop.frecuencia_revision else None,
        "smart": sop.smart,
    }


async def _detalle(db: AsyncSession, sop: SopMaster, area_codigo: str) -> SopDetalle:
    return SopDetalle(
        id=sop.id, codigo=sop.codigo, numero=sop.numero, area_codigo=area_codigo,
        tipo=sop.tipo, nombre=sop.nombre, estado=sop.estado, version_actual=sop.version_actual,
        departamento_id=sop.departamento_id, proposito=sop.proposito,
        evaluacion_riesgos=sop.evaluacion_riesgos, controles_existentes=sop.controles_existentes,
        procedimiento=sop.procedimiento, responsables=sop.responsables, evidencia=sop.evidencia,
        frecuencia_revision=sop.frecuencia_revision, smart=sop.smart,
        sistemas_codigos=await _sistemas_codigos(db, sop.id),
        departamentos_afectados=await _departamentos_afectados(db, sop.id),
        puestos_responsables=await _puestos_responsables(db, sop.id),
        creado_en=sop.creado_en, actualizado_en=sop.actualizado_en,
    )


async def _get_activo(db: AsyncSession, sop_id: uuid.UUID) -> SopMaster:
    sop = (await db.execute(select(SopMaster).where(SopMaster.id == sop_id))).scalar_one_or_none()
    if not sop or sop.eliminado_en is not None:
        raise HTTPException(status_code=404, detail="SOP no encontrado")
    return sop


@router.post("", response_model=SopDetalle, status_code=status.HTTP_201_CREATED)
async def crear_sop(
    datos: SopCrear,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> SopDetalle:
    from app.services.numeracion import siguiente_codigo_area

    area = await _area_por_codigo(db, datos.area_codigo)
    numero, codigo = await siguiente_codigo_area(db, area)
    sop = SopMaster(
        numero=numero, area_id=area.id, codigo=codigo, tipo=datos.tipo, nombre=datos.nombre,
        departamento_id=datos.departamento_id, proposito=datos.proposito,
        evaluacion_riesgos=datos.evaluacion_riesgos,
        controles_existentes=datos.controles_existentes,
        procedimiento=datos.procedimiento, responsables=datos.responsables,
        evidencia=datos.evidencia, frecuencia_revision=datos.frecuencia_revision,
        smart=datos.smart.model_dump() if datos.smart else None,
        estado=EstadoDocumento.borrador, version_actual=1, creado_por=actual.id,
    )
    db.add(sop)
    await db.flush()
    # sistemas asumidos (§7.13)
    for cod in dict.fromkeys(datos.sistemas_codigos):
        sis = (await db.execute(select(Sistema).where(Sistema.codigo == cod))).scalar_one_or_none()
        if sis:
            db.add(SopMasterSistema(sop_master_id=sop.id, sistema_id=sis.id))
    await _set_departamentos_afectados(db, sop.id, datos.departamentos_afectados_ids)
    await _set_puestos_responsables(db, sop.id, datos.puestos_responsables_ids)
    db.add(SopMasterVersion(
        sop_master_id=sop.id, version=1, snapshot=_snapshot(sop),
        nota_cambio="Creación", estado_en_version=sop.estado.value, creado_por=actual.id,
    ))
    await db.commit()
    await db.refresh(sop)
    return await _detalle(db, sop, area.codigo)


@router.get("", response_model=SopLista)
async def listar_sops(
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
    area: str | None = None,
    departamento_id: uuid.UUID | None = None,
    departamento_relacionado_id: uuid.UUID | None = Query(
        None,
        description="Vista 'por Departamento': incluye SOPs propios de este departamento Y "
                    "los que lo afectan; cada item vuelve etiquetado en relacion_departamento.",
    ),
    estado: EstadoDocumento | None = None,
    tipo: TipoDocumento | None = None,
    sistema: str | None = None,
    origen_propiedad: str | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> SopLista:
    filtros = [SopMaster.eliminado_en.is_(None)]
    if origen_propiedad:
        filtros.append(SopMaster.origen_propiedad == origen_propiedad)
    if area:
        a = await _area_por_codigo(db, area)
        filtros.append(SopMaster.area_id == a.id)
    if departamento_id:
        filtros.append(SopMaster.departamento_id == departamento_id)
    afectados_ids: set[uuid.UUID] = set()
    if departamento_relacionado_id:
        afectados_ids = set(
            (await db.execute(
                select(SopMasterDepartamentoAfectado.sop_master_id).where(
                    SopMasterDepartamentoAfectado.departamento_id == departamento_relacionado_id
                )
            )).scalars()
        )
        filtros.append(
            or_(
                SopMaster.departamento_id == departamento_relacionado_id,
                SopMaster.id.in_(afectados_ids),
            )
        )
    if estado:
        filtros.append(SopMaster.estado == estado)
    if tipo:
        filtros.append(SopMaster.tipo == tipo)
    if q:
        filtros.append(SopMaster.nombre.ilike(f"%{q}%"))
    if sistema:
        sub = (
            select(SopMasterSistema.sop_master_id)
            .join(Sistema, Sistema.id == SopMasterSistema.sistema_id)
            .where(Sistema.codigo == sistema)
        )
        filtros.append(SopMaster.id.in_(sub))

    total_q = select(func.count()).select_from(SopMaster).where(*filtros)
    total = (await db.execute(total_q)).scalar_one()
    areas = {a.id: a.codigo for a in (await db.execute(select(Area))).scalars()}
    q_sops = (
        select(SopMaster).where(*filtros).order_by(SopMaster.codigo).limit(limit).offset(offset)
    )
    items = []
    for s in (await db.execute(q_sops)).scalars():
        relacion = None
        if departamento_relacionado_id:
            es_propio = s.departamento_id == departamento_relacionado_id
            es_afecta = s.id in afectados_ids
            relacion = "ambos" if es_propio and es_afecta else "propio" if es_propio else "afecta"
        items.append(SopItem(
            id=s.id, codigo=s.codigo, numero=s.numero, area_codigo=areas.get(s.area_id, "?"),
            tipo=s.tipo, nombre=s.nombre, estado=s.estado, version_actual=s.version_actual,
            departamento_id=s.departamento_id, relacion_departamento=relacion,
        ))
    return SopLista(total=total, items=items)


@router.get("/pendientes-firma", response_model=list[SopItem])
async def pendientes_firma(
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
) -> list[SopItem]:
    """Cola del firmante: SOPs en_firma donde el usuario actual es firmante designado y
    aún NO firmó la versión vigente. Declarado antes de `/{sop_id}` para no colisionar."""
    mis = {
        r for r in (await db.execute(
            select(FirmanteSop.sop_master_id).where(FirmanteSop.usuario_id == actual.id)
        )).scalars()
    }
    if not mis:
        return []
    sops = list(
        (await db.execute(
            select(SopMaster).where(
                SopMaster.id.in_(mis),
                SopMaster.estado == EstadoDocumento.en_firma,
                SopMaster.eliminado_en.is_(None),
            ).order_by(SopMaster.codigo)
        )).scalars()
    )
    areas = {a.id: a.codigo for a in (await db.execute(select(Area))).scalars()}
    out: list[SopItem] = []
    for s in sops:
        ya = (
            await db.execute(
                select(FirmaElectronica).where(
                    FirmaElectronica.sop_master_id == s.id,
                    FirmaElectronica.version == s.version_actual,
                    FirmaElectronica.usuario_id == actual.id,
                )
            )
        ).scalar_one_or_none()
        if ya:
            continue
        out.append(SopItem(
            id=s.id, codigo=s.codigo, numero=s.numero, area_codigo=areas.get(s.area_id, "?"),
            tipo=s.tipo, nombre=s.nombre, estado=s.estado, version_actual=s.version_actual,
            departamento_id=s.departamento_id, relacion_departamento=None,
        ))
    return out


@router.get("/{sop_id}", response_model=SopDetalle)
async def obtener_sop(
    sop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
) -> SopDetalle:
    sop = await _get_activo(db, sop_id)
    area = (await db.execute(select(Area).where(Area.id == sop.area_id))).scalar_one()
    return await _detalle(db, sop, area.codigo)


@router.get("/{sop_id}/export.pdf")
async def exportar_sop_pdf(
    sop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(get_current_user),
) -> Response:
    """PDF de la versión vigente del SOP (incluye la capa SMART si existe), para compartir
    por fuera —p. ej. WhatsApp— y pedir validación en la plataforma. NO es el documento
    controlado: si el SOP no está firmado, el PDF lleva un sello de BORRADOR y un enlace a
    la ficha. Cualquier usuario autenticado puede descargarlo."""
    from app.firma.pdf import generar_pdf_sop

    sop = await _get_activo(db, sop_id)
    area = (await db.execute(select(Area).where(Area.id == sop.area_id))).scalar_one()
    dueno = (
        await db.execute(select(Departamento).where(Departamento.id == sop.departamento_id))
    ).scalar_one_or_none() if sop.departamento_id else None
    afectados = await _departamentos_afectados(db, sop.id)
    settings = get_settings()

    meta = {
        "codigo": sop.codigo, "nombre": sop.nombre,
        "estado": sop.estado.value, "version": sop.version_actual,
        "area": area.codigo,
        "departamento": f"{dueno.codigo} — {dueno.nombre}" if dueno else "—",
        "afectados": [f"{d.codigo}" for d in afectados],
        "generado_por": actual.usuario.nombre,
        "url": f"{settings.frontend_url.rstrip('/')}/biblioteca/{sop.id}",
    }
    datos = {
        "proposito": sop.proposito, "evaluacion_riesgos": sop.evaluacion_riesgos,
        "controles_existentes": sop.controles_existentes, "procedimiento": sop.procedimiento,
        "responsables": sop.responsables, "evidencia": sop.evidencia,
        "frecuencia_revision": sop.frecuencia_revision.value if sop.frecuencia_revision else None,
        "smart": sop.smart,
    }
    pdf = generar_pdf_sop(datos, meta)
    return Response(
        content=pdf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{sop.codigo}.pdf"'},
    )


@router.put("/{sop_id}", response_model=SopDetalle)
async def actualizar_sop(
    sop_id: uuid.UUID,
    datos: SopActualizar,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> SopDetalle:
    sop = await _get_activo(db, sop_id)
    if sop.estado not in EDITABLES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede editar un SOP en estado '{sop.estado.value}'. "
                   "Un documento firmado exige una nueva versión.",
        )
    cambios = datos.model_dump(exclude_unset=True)
    if "departamentos_afectados_ids" in cambios:
        await _set_departamentos_afectados(db, sop.id, cambios.pop("departamentos_afectados_ids"))
    if "puestos_responsables_ids" in cambios:
        await _set_puestos_responsables(db, sop.id, cambios.pop("puestos_responsables_ids"))
    for campo, valor in cambios.items():
        setattr(sop, campo, valor)
    await db.commit()
    await db.refresh(sop)
    area = (await db.execute(select(Area).where(Area.id == sop.area_id))).scalar_one()
    return await _detalle(db, sop, area.codigo)


@router.put("/{sop_id}/smart", response_model=SopDetalle)
async def actualizar_smart(
    sop_id: uuid.UUID,
    datos: SopSmartActualizar,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(get_current_user),
) -> SopDetalle:
    """Persiste la capa SMART reformateada (adopción del estándar SOP SMART).

    Escriben el corporativo y los colaboradores **redactores** de este SOP (§colaboración).
    Aditivo: NO toca los 9 campos, ni el estado, ni la numeración. Escribe un snapshot
    de versión con el contenido resultante para auditoría y rollback. Un SOP 'firmado' es
    inmutable (§7.6): reformatearlo exige abrir una versión nueva primero."""
    await _exigir_puede_editar_smart(db, sop_id, actual)
    sop = await _get_activo(db, sop_id)
    if sop.estado == EstadoDocumento.firmado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un SOP firmado es inmutable; abra una nueva versión antes de reformatear.",
        )
    _exigir_sello(sop, datos.base_actualizado_en)
    sop.smart = datos.smart.model_dump()
    db.add(SopMasterVersion(
        sop_master_id=sop.id, version=sop.version_actual, snapshot=_snapshot(sop),
        nota_cambio=datos.nota_cambio, estado_en_version=sop.estado.value, creado_por=actual.id,
    ))
    await db.commit()
    await db.refresh(sop)
    area = (await db.execute(select(Area).where(Area.id == sop.area_id))).scalar_one()
    return await _detalle(db, sop, area.codigo)


# --- Historial de versiones (snapshots) + rollback de la capa SMART -------------------


async def _version_o_404(db: AsyncSession, sop_id: uuid.UUID, ver_id: uuid.UUID) -> SopMasterVersion:
    v = (
        await db.execute(
            select(SopMasterVersion).where(
                SopMasterVersion.id == ver_id, SopMasterVersion.sop_master_id == sop_id
            )
        )
    ).scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Versión no encontrada para este SOP")
    return v


@router.get("/{sop_id}/versiones", response_model=list[SopVersionItem])
async def listar_versiones(
    sop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
) -> list[SopVersionItem]:
    """Historial de snapshots del SOP, del más reciente al más viejo.

    Cada guardado (9 campos o capa SMART) deja una fila. Es la base del rollback."""
    await _get_activo(db, sop_id)
    filas = (
        await db.execute(
            select(SopMasterVersion)
            .where(SopMasterVersion.sop_master_id == sop_id)
            .order_by(SopMasterVersion.creado_en.desc())
        )
    ).scalars().all()
    autores = {
        u.id: u.nombre
        for u in (await db.execute(select(Usuario))).scalars()
    }
    return [
        SopVersionItem(
            id=v.id, version=v.version, nota_cambio=v.nota_cambio,
            estado_en_version=v.estado_en_version, creado_en=v.creado_en,
            creado_por=v.creado_por, creado_por_nombre=autores.get(v.creado_por),
            tiene_smart=bool((v.snapshot or {}).get("smart")),
        )
        for v in filas
    ]


@router.get("/{sop_id}/versiones/{version_id}", response_model=SopVersionDetalle)
async def detalle_version(
    sop_id: uuid.UUID,
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
) -> SopVersionDetalle:
    """Snapshot completo (9 campos + capa SMART) tal como quedó en ese guardado."""
    await _get_activo(db, sop_id)
    v = await _version_o_404(db, sop_id, version_id)
    autor = (
        await db.execute(select(Usuario).where(Usuario.id == v.creado_por))
    ).scalar_one_or_none() if v.creado_por else None
    return SopVersionDetalle(
        id=v.id, version=v.version, nota_cambio=v.nota_cambio,
        estado_en_version=v.estado_en_version, creado_en=v.creado_en,
        creado_por=v.creado_por, creado_por_nombre=autor.nombre if autor else None,
        tiene_smart=bool((v.snapshot or {}).get("smart")), snapshot=v.snapshot or {},
    )


@router.post("/{sop_id}/versiones/{version_id}/restaurar-smart", response_model=SopDetalle)
async def restaurar_smart(
    sop_id: uuid.UUID,
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> SopDetalle:
    """Devuelve la capa SMART a como estaba en ese snapshot.

    Restaura SOLO `smart`: los 9 campos base no se tocan, para que un rollback de la
    capa SMART no revierta sin querer ediciones del formato base. La restauración deja
    su propio snapshot, así que también se puede deshacer."""
    sop = await _get_activo(db, sop_id)
    if sop.estado == EstadoDocumento.firmado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un SOP firmado es inmutable; abra una nueva versión antes de restaurar.",
        )
    v = await _version_o_404(db, sop_id, version_id)
    smart = (v.snapshot or {}).get("smart")
    if not smart:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Esa versión no tiene capa SMART: no hay nada que restaurar.",
        )
    sop.smart = smart
    db.add(SopMasterVersion(
        sop_master_id=sop.id, version=sop.version_actual, snapshot=_snapshot(sop),
        nota_cambio=f"Capa SMART restaurada del snapshot del {v.creado_en:%Y-%m-%d %H:%M} UTC",
        estado_en_version=sop.estado.value, creado_por=actual.id,
    ))
    await db.commit()
    await db.refresh(sop)
    area = (await db.execute(select(Area).where(Area.id == sop.area_id))).scalar_one()
    return await _detalle(db, sop, area.codigo)


@router.post("/{sop_id}/nueva-version", response_model=SopDetalle)
async def nueva_version(
    sop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> SopDetalle:
    """Editar un documento firmado exige versión nueva (§7.6): arranca en borrador,
    la versión firmada anterior permanece íntegra."""
    sop = await _get_activo(db, sop_id)
    if sop.estado != EstadoDocumento.firmado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se crea una nueva versión a partir de un documento firmado.",
        )
    sop.version_actual += 1
    sop.estado = EstadoDocumento.borrador
    db.add(SopMasterVersion(
        sop_master_id=sop.id, version=sop.version_actual, snapshot=_snapshot(sop),
        nota_cambio="Apertura de nueva versión para edición", estado_en_version="borrador",
        creado_por=actual.id,
    ))
    await db.commit()
    await db.refresh(sop)
    area = (await db.execute(select(Area).where(Area.id == sop.area_id))).scalar_one()
    return await _detalle(db, sop, area.codigo)


@router.delete("/{sop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_sop(
    sop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(editor),
) -> None:
    """Soft delete. El número del área NO se reutiliza (§7.2)."""
    from datetime import UTC, datetime

    sop = await _get_activo(db, sop_id)
    sop.eliminado_en = datetime.now(UTC)
    await db.commit()
