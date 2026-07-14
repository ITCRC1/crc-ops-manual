"""Schemas de solo-lectura de los catálogos (§8.4). Alimentan filtros y selectores
del frontend (áreas, propiedades, departamentos, sistemas)."""

import uuid

from pydantic import BaseModel


class AreaOut(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str


class PropiedadOut(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str


class DepartamentoOut(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    propiedad_propietaria_id: uuid.UUID | None = None
    division_id: uuid.UUID | None = None


class DivisionOut(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    parent_id: uuid.UUID | None = None  # None = división raíz; con valor = subdivisión
    orden: int


class SistemaOut(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    categoria: str | None = None
