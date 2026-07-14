"""Catálogos de solo-lectura (§8.4): áreas, propiedades, departamentos y sistemas.

Cualquier usuario autenticado puede leerlos; alimentan los filtros y selectores del
frontend. La edición del catálogo es una operación de datos (A7) y no se expone aquí.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, get_current_user
from app.core.db import get_db
from app.models.catalogos import Area, Departamento, Division, Propiedad, Sistema
from app.schemas.catalogos import (
    AreaOut,
    DepartamentoOut,
    DivisionOut,
    PropiedadOut,
    SistemaOut,
)

router = APIRouter(prefix="/api/catalogos", tags=["catalogos"])


@router.get("/areas", response_model=list[AreaOut])
async def listar_areas(
    db: AsyncSession = Depends(get_db), _: UsuarioActual = Depends(get_current_user)
):
    filas = (await db.execute(select(Area).order_by(Area.codigo))).scalars()
    return [AreaOut(id=a.id, codigo=a.codigo, nombre=a.nombre) for a in filas]


@router.get("/propiedades", response_model=list[PropiedadOut])
async def listar_propiedades(
    db: AsyncSession = Depends(get_db), _: UsuarioActual = Depends(get_current_user)
):
    filas = (await db.execute(select(Propiedad).order_by(Propiedad.codigo))).scalars()
    return [PropiedadOut(id=p.id, codigo=p.codigo, nombre=p.nombre) for p in filas]


@router.get("/departamentos", response_model=list[DepartamentoOut])
async def listar_departamentos(
    db: AsyncSession = Depends(get_db), _: UsuarioActual = Depends(get_current_user)
):
    filas = (await db.execute(select(Departamento).order_by(Departamento.codigo))).scalars()
    return [
        DepartamentoOut(
            id=d.id, codigo=d.codigo, nombre=d.nombre,
            propiedad_propietaria_id=d.propiedad_propietaria_id,
            division_id=d.division_id,
        )
        for d in filas
    ]


@router.get("/divisiones", response_model=list[DivisionOut])
async def listar_divisiones(
    db: AsyncSession = Depends(get_db), _: UsuarioActual = Depends(get_current_user)
):
    filas = (
        await db.execute(select(Division).order_by(Division.orden, Division.codigo))
    ).scalars()
    return [
        DivisionOut(id=d.id, codigo=d.codigo, nombre=d.nombre, parent_id=d.parent_id, orden=d.orden)
        for d in filas
    ]


@router.get("/sistemas", response_model=list[SistemaOut])
async def listar_sistemas(
    db: AsyncSession = Depends(get_db), _: UsuarioActual = Depends(get_current_user)
):
    filas = (await db.execute(select(Sistema).order_by(Sistema.codigo))).scalars()
    return [
        SistemaOut(id=s.id, codigo=s.codigo, nombre=s.nombre, categoria=s.categoria)
        for s in filas
    ]
