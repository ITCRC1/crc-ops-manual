"""CRUD del master de Descriptores de Puesto: formato propio, numeración atómica
(JD-###), versionado, jerarquía `reporta_a` y búsqueda (§8.5, §7.2, §7.18)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, get_current_user, require_rol
from app.core.db import get_db
from app.models.base import EstadoDocumento, RolUsuario
from app.models.catalogos import Departamento
from app.models.puesto import DescriptorPuestoMaster, DescriptorPuestoVersion
from app.schemas.descriptor import (
    DescriptorActualizar,
    DescriptorCrear,
    DescriptorDetalle,
    DescriptorItem,
    DescriptorLista,
    DescriptorSmartActualizar,
)
from app.services.auditoria import auditar

router = APIRouter(prefix="/api/descriptores", tags=["descriptores"])

editor = require_rol(RolUsuario.editor_corporativo, RolUsuario.super_admin)

# Igual que en el master de SOPs: 'firmado'/'archivado' son inmutables (§7.6).
EDITABLES = {EstadoDocumento.borrador, EstadoDocumento.en_revision, EstadoDocumento.rechazado}


def _snapshot(d: DescriptorPuestoMaster) -> dict:
    return {
        "codigo": d.codigo, "titulo": d.titulo, "nivel_jerarquico": d.nivel_jerarquico,
        "proposito": d.proposito, "responsabilidades": d.responsabilidades,
        "nivel_autoridad": d.nivel_autoridad, "kpis": d.kpis, "requisitos": d.requisitos,
    }


async def _get_activo(db: AsyncSession, desc_id: uuid.UUID) -> DescriptorPuestoMaster:
    d = (
        await db.execute(select(DescriptorPuestoMaster).where(DescriptorPuestoMaster.id == desc_id))
    ).scalar_one_or_none()
    if not d or d.eliminado_en is not None:
        raise HTTPException(status_code=404, detail="Descriptor no encontrado")
    return d


async def _codigo(db: AsyncSession, desc_id: uuid.UUID | None) -> str | None:
    if not desc_id:
        return None
    return (
        await db.execute(
            select(DescriptorPuestoMaster.codigo).where(DescriptorPuestoMaster.id == desc_id)
        )
    ).scalar_one_or_none()


async def _depto_codigo(db: AsyncSession, depto_id: uuid.UUID | None) -> str | None:
    if not depto_id:
        return None
    return (
        await db.execute(select(Departamento.codigo).where(Departamento.id == depto_id))
    ).scalar_one_or_none()


async def _detalle(db: AsyncSession, d: DescriptorPuestoMaster) -> DescriptorDetalle:
    return DescriptorDetalle(
        id=d.id, codigo=d.codigo, titulo=d.titulo, nivel_jerarquico=d.nivel_jerarquico,
        categoria=d.categoria,
        estado=d.estado, version_actual=d.version_actual, departamento_id=d.departamento_id,
        reporta_a_id=d.reporta_a_id, departamento_codigo=await _depto_codigo(db, d.departamento_id),
        reporta_a_codigo=await _codigo(db, d.reporta_a_id), proposito=d.proposito,
        responsabilidades=d.responsabilidades, nivel_autoridad=d.nivel_autoridad, kpis=d.kpis,
        requisitos=d.requisitos, smart=d.smart, creado_en=d.creado_en, actualizado_en=d.actualizado_en,
    )


async def _validar_jefe(
    db: AsyncSession, reporta_a_id: uuid.UUID | None, propio_id: uuid.UUID | None
) -> None:
    """El jefe debe existir y estar activo; no puede ser uno mismo ni un subordinado
    (evita ciclos en la jerarquía)."""
    if reporta_a_id is None:
        return
    if propio_id is not None and reporta_a_id == propio_id:
        raise HTTPException(status_code=409, detail="Un puesto no puede reportarse a sí mismo.")
    jefe = (
        await db.execute(
            select(DescriptorPuestoMaster).where(DescriptorPuestoMaster.id == reporta_a_id)
        )
    ).scalar_one_or_none()
    if not jefe or jefe.eliminado_en is not None:
        raise HTTPException(status_code=404, detail="El puesto 'reporta_a' no existe.")
    if propio_id is None:
        return
    # Subir por la cadena del jefe: si se llega a 'propio_id', se crearía un ciclo.
    visto: set[uuid.UUID] = set()
    cur: uuid.UUID | None = reporta_a_id
    while cur is not None and cur not in visto:
        if cur == propio_id:
            raise HTTPException(
                status_code=409,
                detail="La asignación crearía un ciclo en la jerarquía (reportar a un subordinado).",
            )
        visto.add(cur)
        cur = (
            await db.execute(
                select(DescriptorPuestoMaster.reporta_a_id).where(
                    DescriptorPuestoMaster.id == cur
                )
            )
        ).scalar_one_or_none()


@router.post("", response_model=DescriptorDetalle, status_code=status.HTTP_201_CREATED)
async def crear_descriptor(
    datos: DescriptorCrear, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
) -> DescriptorDetalle:
    from app.services.numeracion import siguiente_codigo_descriptor

    if datos.departamento_id and not await _depto_codigo(db, datos.departamento_id):
        raise HTTPException(status_code=404, detail="Departamento no encontrado")
    await _validar_jefe(db, datos.reporta_a_id, None)

    from app.ingestion.categorizar_puestos import categoria_de

    _, codigo = await siguiente_codigo_descriptor(db)
    categoria = datos.categoria or categoria_de(datos.nivel_jerarquico, datos.titulo)
    d = DescriptorPuestoMaster(
        codigo=codigo, titulo=datos.titulo, departamento_id=datos.departamento_id,
        reporta_a_id=datos.reporta_a_id, nivel_jerarquico=datos.nivel_jerarquico,
        categoria=categoria,
        proposito=datos.proposito, responsabilidades=datos.responsabilidades,
        nivel_autoridad=datos.nivel_autoridad, kpis=datos.kpis, requisitos=datos.requisitos,
        estado=EstadoDocumento.borrador, version_actual=1,
    )
    db.add(d)
    await db.flush()
    db.add(DescriptorPuestoVersion(
        descriptor_puesto_master_id=d.id, version=1, snapshot=_snapshot(d),
        nota_cambio="Creación", estado_en_version=d.estado.value, creado_por=actual.id,
    ))
    auditar(db, actual.id, "descriptor_puesto_master", d.id, "crear", ip=request.client.host)
    await db.commit()
    await db.refresh(d)
    return await _detalle(db, d)


@router.get("", response_model=DescriptorLista)
async def listar_descriptores(
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
    departamento_id: uuid.UUID | None = None,
    reporta_a_id: uuid.UUID | None = None,
    nivel_jerarquico: int | None = Query(None, ge=1, le=4),
    categoria: str | None = None,
    estado: EstadoDocumento | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> DescriptorLista:
    filtros = [DescriptorPuestoMaster.eliminado_en.is_(None)]
    if departamento_id:
        filtros.append(DescriptorPuestoMaster.departamento_id == departamento_id)
    if reporta_a_id:
        filtros.append(DescriptorPuestoMaster.reporta_a_id == reporta_a_id)
    if nivel_jerarquico:
        filtros.append(DescriptorPuestoMaster.nivel_jerarquico == nivel_jerarquico)
    if categoria:
        filtros.append(DescriptorPuestoMaster.categoria == categoria)
    if estado:
        filtros.append(DescriptorPuestoMaster.estado == estado)
    if q:
        patron = f"%{q}%"
        filtros.append(
            DescriptorPuestoMaster.titulo.ilike(patron)
            | DescriptorPuestoMaster.codigo.ilike(patron)
        )

    total = (
        await db.execute(select(func.count()).select_from(DescriptorPuestoMaster).where(*filtros))
    ).scalar_one()
    q_desc = (
        select(DescriptorPuestoMaster)
        .where(*filtros)
        .order_by(DescriptorPuestoMaster.codigo)
        .limit(limit)
        .offset(offset)
    )
    items = [
        DescriptorItem(
            id=d.id, codigo=d.codigo, titulo=d.titulo, nivel_jerarquico=d.nivel_jerarquico,
            categoria=d.categoria, estado=d.estado, version_actual=d.version_actual,
            departamento_id=d.departamento_id, reporta_a_id=d.reporta_a_id,
        )
        for d in (await db.execute(q_desc)).scalars()
    ]
    return DescriptorLista(total=total, items=items)


@router.get("/{desc_id}", response_model=DescriptorDetalle)
async def obtener_descriptor(
    desc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), _: UsuarioActual = Depends(get_current_user),
) -> DescriptorDetalle:
    d = await _get_activo(db, desc_id)
    return await _detalle(db, d)


@router.put("/{desc_id}", response_model=DescriptorDetalle)
async def actualizar_descriptor(
    desc_id: uuid.UUID, datos: DescriptorActualizar, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
) -> DescriptorDetalle:
    d = await _get_activo(db, desc_id)
    if d.estado not in EDITABLES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede editar un descriptor en estado '{d.estado.value}'. "
                   "Un documento firmado exige una nueva versión.",
        )
    cambios = datos.model_dump(exclude_unset=True)
    if "departamento_id" in cambios and cambios["departamento_id"]:
        if not await _depto_codigo(db, cambios["departamento_id"]):
            raise HTTPException(status_code=404, detail="Departamento no encontrado")
    if "reporta_a_id" in cambios:
        await _validar_jefe(db, cambios["reporta_a_id"], d.id)
    for campo, valor in cambios.items():
        setattr(d, campo, valor)
    auditar(db, actual.id, "descriptor_puesto_master", d.id, "actualizar", ip=request.client.host)
    await db.commit()
    await db.refresh(d)
    return await _detalle(db, d)


@router.put("/{desc_id}/smart", response_model=DescriptorDetalle)
async def actualizar_smart(
    desc_id: uuid.UUID, datos: DescriptorSmartActualizar, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
) -> DescriptorDetalle:
    """Persiste la capa JD SMART (aditiva). No modifica los campos base ni el estado;
    paralelo a `PUT /api/sops/{id}/smart`."""
    d = await _get_activo(db, desc_id)
    d.smart = datos.smart
    auditar(db, actual.id, "descriptor_puesto_master", d.id, "actualizar_smart", ip=request.client.host)
    await db.commit()
    await db.refresh(d)
    return await _detalle(db, d)


@router.post("/{desc_id}/nueva-version", response_model=DescriptorDetalle)
async def nueva_version(
    desc_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
) -> DescriptorDetalle:
    """Editar un descriptor firmado exige versión nueva (§7.6): arranca en borrador y la
    versión firmada anterior permanece íntegra."""
    d = await _get_activo(db, desc_id)
    if d.estado != EstadoDocumento.firmado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se crea una nueva versión a partir de un documento firmado.",
        )
    d.version_actual += 1
    d.estado = EstadoDocumento.borrador
    db.add(DescriptorPuestoVersion(
        descriptor_puesto_master_id=d.id, version=d.version_actual, snapshot=_snapshot(d),
        nota_cambio="Apertura de nueva versión para edición", estado_en_version="borrador",
        creado_por=actual.id,
    ))
    auditar(db, actual.id, "descriptor_puesto_master", d.id, "nueva_version", ip=request.client.host)
    await db.commit()
    await db.refresh(d)
    return await _detalle(db, d)


@router.delete("/{desc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_descriptor(
    desc_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
) -> None:
    """Soft delete. El número global de descriptores NO se reutiliza (§7.2). Los
    subordinados quedan huérfanos y el organigrama los muestra como raíz."""
    from datetime import UTC, datetime

    d = await _get_activo(db, desc_id)
    d.eliminado_en = datetime.now(UTC)
    auditar(db, actual.id, "descriptor_puesto_master", d.id, "eliminar", ip=request.client.host)
    await db.commit()
