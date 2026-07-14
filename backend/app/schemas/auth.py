"""Schemas Pydantic de autenticación."""

import uuid

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RolOut(BaseModel):
    rol: str
    propiedad_id: uuid.UUID | None = None


class UsuarioOut(BaseModel):
    id: uuid.UUID
    nombre: str
    email: EmailStr
    nivel_jerarquico: int
    activo: bool
    roles: list[RolOut] = []
