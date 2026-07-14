"""Endpoints de autenticación: login, refresh y perfil (§4, §14)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, get_current_user
from app.core.db import get_db
from app.core.rate_limit import limite_login
from app.core.seguridad import (
    crear_access_token,
    crear_refresh_token,
    decodificar_token,
    verificar_password,
)
from app.models.usuarios import Usuario
from app.schemas.auth import LoginRequest, RefreshRequest, RolOut, TokenResponse, UsuarioOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(limite_login)])
async def login(datos: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    usuario = (
        await db.execute(select(Usuario).where(Usuario.email == datos.email))
    ).scalar_one_or_none()
    # Mensaje genérico para no filtrar si el email existe.
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas"
    )
    if not usuario or not usuario.activo:
        raise credenciales_invalidas
    if not verificar_password(datos.password, usuario.password_hash):
        raise credenciales_invalidas
    return TokenResponse(
        access_token=crear_access_token(str(usuario.id)),
        refresh_token=crear_refresh_token(str(usuario.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(datos: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    invalido = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido"
    )
    payload = decodificar_token(datos.refresh_token, "refresh")
    if not payload:
        raise invalido
    try:
        uid = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise invalido
    usuario = (await db.execute(select(Usuario).where(Usuario.id == uid))).scalar_one_or_none()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo")
    return TokenResponse(
        access_token=crear_access_token(str(usuario.id)),
        refresh_token=crear_refresh_token(str(usuario.id)),
    )


@router.get("/me", response_model=UsuarioOut)
async def me(actual: UsuarioActual = Depends(get_current_user)) -> UsuarioOut:
    return UsuarioOut(
        id=actual.usuario.id,
        nombre=actual.usuario.nombre,
        email=actual.usuario.email,
        nivel_jerarquico=actual.usuario.nivel_jerarquico,
        activo=actual.usuario.activo,
        roles=[RolOut(rol=r.rol.value, propiedad_id=r.propiedad_id) for r in actual.roles],
    )
