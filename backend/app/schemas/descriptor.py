"""Schemas Pydantic de Descriptores de Puesto (§8.5, §8.14).

Mismo formato/versionado que el master de SOPs, pero con los campos propios del
descriptor (propósito, responsabilidades, nivel de autoridad, KPIs, requisitos) y la
jerarquía `reporta_a` que alimenta el organigrama.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.base import EstadoDocumento


CATEGORIAS = ("director", "gerente_departamental", "supervisor", "linea")


class DescriptorCrear(BaseModel):
    titulo: str
    departamento_id: uuid.UUID | None = None
    reporta_a_id: uuid.UUID | None = None
    nivel_jerarquico: int = Field(4, ge=1, le=4)
    categoria: str | None = None
    # Contenido (opcional al crear; se completa en la colaboración)
    proposito: str | None = None
    responsabilidades: list | None = None
    nivel_autoridad: str | None = None
    kpis: list | None = None
    requisitos: str | None = None


class DescriptorActualizar(BaseModel):
    """Actualización de contenido (no cambia código/estado/versión)."""

    titulo: str | None = None
    departamento_id: uuid.UUID | None = None
    reporta_a_id: uuid.UUID | None = None
    nivel_jerarquico: int | None = Field(None, ge=1, le=4)
    categoria: str | None = None
    proposito: str | None = None
    responsabilidades: list | None = None
    nivel_autoridad: str | None = None
    kpis: list | None = None
    requisitos: str | None = None


class DescriptorItem(BaseModel):
    id: uuid.UUID
    codigo: str
    titulo: str
    nivel_jerarquico: int
    categoria: str | None = None
    estado: EstadoDocumento
    version_actual: int
    departamento_id: uuid.UUID | None = None
    reporta_a_id: uuid.UUID | None = None


class DescriptorDetalle(DescriptorItem):
    departamento_codigo: str | None = None
    reporta_a_codigo: str | None = None
    proposito: str | None = None
    responsabilidades: list | None = None
    nivel_autoridad: str | None = None
    kpis: list | None = None
    requisitos: str | None = None
    # Capa JD SMART (~30 secciones + crosswalk a SOPs). NULL = aún sin reformatear.
    smart: dict | None = None
    creado_en: datetime
    actualizado_en: datetime


class DescriptorSmartActualizar(BaseModel):
    """Body de `PUT /api/descriptores/{id}/smart`: persiste la capa JD SMART reformateada."""

    smart: dict


class DescriptorLista(BaseModel):
    total: int
    items: list[DescriptorItem]


class NodoOrganigrama(BaseModel):
    """Nodo del árbol jerárquico derivado de `reporta_a` (§8.14).

    `estado` es texto porque el árbol sirve tanto al master (`estado_documento`) como
    a la dotación por propiedad (`estado_asignacion`)."""

    id: uuid.UUID
    codigo: str
    titulo: str
    nivel_jerarquico: int
    categoria: str | None = None
    estado: str
    departamento_id: uuid.UUID | None = None
    departamento_codigo: str | None = None
    hijos: list["NodoOrganigrama"] = []
