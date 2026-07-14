"""Búsqueda global con filtros combinables (§8.16).

Busca en el master de SOPs/políticas y en el master de descriptores, con filtros por
entidad, área (solo SOPs), departamento y estado. Devuelve una lista unificada.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, get_current_user
from app.core.db import get_db
from app.models.base import EstadoDocumento, TipoDocumento
from app.models.catalogos import Area
from app.models.puesto import DescriptorPuestoMaster
from app.models.sop import SopMaster
from app.schemas.busqueda import BusquedaLista, ResultadoBusqueda

router = APIRouter(prefix="/api/busqueda", tags=["busqueda"])


@router.get("", response_model=BusquedaLista)
async def buscar(
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
    q: str = Query(..., min_length=1, description="Texto a buscar en código/título/propósito"),
    entidad: str = Query("todos", pattern="^(todos|sop|politica|descriptor)$"),
    area: str | None = None,
    departamento_id: uuid.UUID | None = None,
    estado: EstadoDocumento | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> BusquedaLista:
    patron = f"%{q}%"
    resultados: list[ResultadoBusqueda] = []

    area_obj = None
    if area:
        area_obj = (
            await db.execute(select(Area).where(Area.codigo == area))
        ).scalar_one_or_none()
        if not area_obj:
            raise HTTPException(status_code=404, detail=f"Área '{area}' no existe")

    # --- SOPs / políticas ---
    incluir_sop = entidad in ("todos", "sop", "politica")
    if incluir_sop:
        areas_cod = {a.id: a.codigo for a in (await db.execute(select(Area))).scalars()}
        filtros = [
            SopMaster.eliminado_en.is_(None),
            SopMaster.nombre.ilike(patron)
            | SopMaster.codigo.ilike(patron)
            | SopMaster.proposito.ilike(patron),
        ]
        if entidad == "sop":
            filtros.append(SopMaster.tipo == TipoDocumento.sop)
        elif entidad == "politica":
            filtros.append(SopMaster.tipo == TipoDocumento.politica)
        if area_obj:
            filtros.append(SopMaster.area_id == area_obj.id)
        if departamento_id:
            filtros.append(SopMaster.departamento_id == departamento_id)
        if estado:
            filtros.append(SopMaster.estado == estado)
        sops = (
            await db.execute(
                select(SopMaster).where(*filtros).order_by(SopMaster.codigo)
            )
        ).scalars()
        for s in sops:
            resultados.append(ResultadoBusqueda(
                entidad=s.tipo.value, id=s.id, codigo=s.codigo, titulo=s.nombre,
                estado=s.estado, area_codigo=areas_cod.get(s.area_id),
                departamento_id=s.departamento_id,
            ))

    # --- Descriptores de puesto (sin área; se excluyen si se filtró por área) ---
    incluir_desc = entidad in ("todos", "descriptor") and area_obj is None
    if incluir_desc:
        filtros = [
            DescriptorPuestoMaster.eliminado_en.is_(None),
            DescriptorPuestoMaster.titulo.ilike(patron)
            | DescriptorPuestoMaster.codigo.ilike(patron)
            | DescriptorPuestoMaster.proposito.ilike(patron),
        ]
        if departamento_id:
            filtros.append(DescriptorPuestoMaster.departamento_id == departamento_id)
        if estado:
            filtros.append(DescriptorPuestoMaster.estado == estado)
        descs = (
            await db.execute(
                select(DescriptorPuestoMaster)
                .where(*filtros)
                .order_by(DescriptorPuestoMaster.codigo)
            )
        ).scalars()
        for d in descs:
            resultados.append(ResultadoBusqueda(
                entidad="descriptor", id=d.id, codigo=d.codigo, titulo=d.titulo,
                estado=d.estado, area_codigo=None, departamento_id=d.departamento_id,
            ))

    resultados.sort(key=lambda r: (r.entidad, r.codigo))
    total = len(resultados)
    return BusquedaLista(total=total, items=resultados[offset : offset + limit])
