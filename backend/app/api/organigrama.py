"""Organigrama derivado de `reporta_a` (§8.14): árbol por niveles 1–4.

- `/api/organigrama` — jerarquía del master de descriptores (fuente única de puestos).
- `/api/propiedades/{prop_id}/organigrama` — jerarquía de la dotación de una propiedad
  (`propiedad_puesto`), resolviendo el título desde el master u overrides locales.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, get_current_user
from app.core.db import get_db
from app.models.catalogos import Departamento, Propiedad
from app.models.propiedad import PropiedadPuesto
from app.models.puesto import DescriptorPuestoMaster
from app.schemas.descriptor import NodoOrganigrama
from app.services.organigrama import construir_arbol

router = APIRouter(tags=["organigrama"])


@router.get("/api/organigrama", response_model=list[NodoOrganigrama])
async def organigrama_master(
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
    departamento_id: uuid.UUID | None = None,
):
    filtros = [DescriptorPuestoMaster.eliminado_en.is_(None)]
    if departamento_id:
        filtros.append(DescriptorPuestoMaster.departamento_id == departamento_id)
    descriptores = list(
        (await db.execute(select(DescriptorPuestoMaster).where(*filtros))).scalars()
    )
    deptos = {
        d.id: d.codigo for d in (await db.execute(select(Departamento))).scalars()
    }
    nodos = [
        {
            "id": d.id, "codigo": d.codigo, "titulo": d.titulo,
            "nivel_jerarquico": d.nivel_jerarquico, "categoria": d.categoria,
            "estado": d.estado.value,
            "departamento_id": d.departamento_id,
            "departamento_codigo": deptos.get(d.departamento_id),
            "reporta_a_id": d.reporta_a_id,
        }
        for d in descriptores
    ]
    return construir_arbol(nodos)


@router.get("/api/propiedades/{prop_id}/organigrama", response_model=list[NodoOrganigrama])
async def organigrama_propiedad(
    prop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(get_current_user),
):
    prop = (
        await db.execute(select(Propiedad).where(Propiedad.id == prop_id))
    ).scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    if not actual.puede_ver_propiedad(prop_id):
        raise HTTPException(status_code=403, detail="Sin acceso a esta propiedad")

    puestos = list(
        (await db.execute(
            select(PropiedadPuesto).where(
                PropiedadPuesto.propiedad_id == prop_id,
                PropiedadPuesto.eliminado_en.is_(None),
            )
        )).scalars()
    )
    masters = {
        m.id: m
        for m in (await db.execute(select(DescriptorPuestoMaster))).scalars()
    }
    deptos = {d.id: d.codigo for d in (await db.execute(select(Departamento))).scalars()}

    nodos = []
    for p in puestos:
        master = masters.get(p.descriptor_puesto_master_id)
        overrides = p.overrides or {}
        titulo = overrides.get("titulo") or (master.titulo if master else "(puesto local)")
        codigo = overrides.get("codigo") or (master.codigo if master else str(p.id))
        nivel = overrides.get("nivel_jerarquico") or (master.nivel_jerarquico if master else 4)
        depto_id = master.departamento_id if master else None
        nodos.append({
            "id": p.id, "codigo": codigo, "titulo": titulo, "nivel_jerarquico": nivel,
            "categoria": master.categoria if master else None,
            "estado": p.estado.value, "departamento_id": depto_id,
            "departamento_codigo": deptos.get(depto_id),
            "reporta_a_id": p.reporta_a_id,
        })
    return construir_arbol(nodos)
