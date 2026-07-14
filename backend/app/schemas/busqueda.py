"""Schemas de la búsqueda global (§8.16)."""

import uuid

from pydantic import BaseModel

from app.models.base import EstadoDocumento


class ResultadoBusqueda(BaseModel):
    entidad: str  # 'sop' | 'politica' | 'descriptor'
    id: uuid.UUID
    codigo: str
    titulo: str
    estado: EstadoDocumento
    area_codigo: str | None = None
    departamento_id: uuid.UUID | None = None


class BusquedaLista(BaseModel):
    total: int
    items: list[ResultadoBusqueda]
