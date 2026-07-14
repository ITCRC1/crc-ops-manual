"""Schemas de gestión de usuarios (§8.2). Alta y listado; alimenta la designación de
firmantes/colaboradores del frontend."""

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.models.base import RolUsuario


class RolAsignarIn(BaseModel):
    rol: RolUsuario
    propiedad_id: uuid.UUID | None = None  # None = alcance corporativo


class UsuarioCrear(BaseModel):
    nombre: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)
    nivel_jerarquico: int = Field(4, ge=1, le=4)
    roles: list[RolAsignarIn] = []


class UsuarioActualizar(BaseModel):
    """Edición de usuario (super_admin). Campos omitidos quedan intactos; `roles`, si se
    envía, reemplaza el conjunto completo."""

    nombre: str | None = Field(None, min_length=1)
    nivel_jerarquico: int | None = Field(None, ge=1, le=4)
    activo: bool | None = None
    roles: list[RolAsignarIn] | None = None


class UsuarioListItem(BaseModel):
    id: uuid.UUID
    nombre: str
    email: EmailStr
    nivel_jerarquico: int
    activo: bool
    roles: list[RolAsignarIn] = []
