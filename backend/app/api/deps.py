"""Dependencias de FastAPI: sesión de DB, usuario actual y control de roles (§14)."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.seguridad import decodificar_token
from app.models.base import RolUsuario
from app.models.usuarios import RolUsuarioAsignado, Usuario

bearer = HTTPBearer(auto_error=True)


class UsuarioActual:
    """Usuario autenticado con sus roles/alcances resueltos."""

    def __init__(self, usuario: Usuario, roles: list[RolUsuarioAsignado]):
        self.usuario = usuario
        self.id = usuario.id
        self.nivel_jerarquico = usuario.nivel_jerarquico
        self.roles = roles

    def tiene_rol(self, *roles: RolUsuario) -> bool:
        return any(r.rol in roles for r in self.roles)

    def tiene_rol_en_propiedad(self, rol: RolUsuario, propiedad_id: uuid.UUID | None) -> bool:
        """True si tiene el rol con alcance corporativo (propiedad NULL) o sobre esa propiedad."""
        for r in self.roles:
            if r.rol == rol and (r.propiedad_id is None or r.propiedad_id == propiedad_id):
                return True
        return False

    def es_corporativo(self) -> bool:
        """Roles con visibilidad de TODAS las propiedades + catálogo maestro."""
        return self.tiene_rol(RolUsuario.super_admin, RolUsuario.editor_corporativo)

    def propiedades_accesibles(self) -> set[uuid.UUID] | None:
        """Propiedades que el usuario puede VER. `None` = todas (corporativo); un `set` = solo
        esas (las de sus roles con `propiedad_id`); set vacío = ninguna (§14, aislamiento)."""
        if self.es_corporativo():
            return None
        return {r.propiedad_id for r in self.roles if r.propiedad_id is not None}

    def puede_ver_propiedad(self, propiedad_id: uuid.UUID) -> bool:
        acc = self.propiedades_accesibles()
        return acc is None or propiedad_id in acc


async def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> UsuarioActual:
    payload = decodificar_token(cred.credentials, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        uid = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    usuario = (await db.execute(select(Usuario).where(Usuario.id == uid))).scalar_one_or_none()
    if not usuario or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo o inexistente"
        )

    roles_q = select(RolUsuarioAsignado).where(RolUsuarioAsignado.usuario_id == uid)
    roles = list((await db.execute(roles_q)).scalars())
    return UsuarioActual(usuario, roles)


def require_rol(*roles: RolUsuario):
    """Dependency factory: exige que el usuario tenga al menos uno de los roles indicados."""

    async def _dep(actual: UsuarioActual = Depends(get_current_user)) -> UsuarioActual:
        if not actual.tiene_rol(*roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenés permisos para esta acción",
            )
        return actual

    return _dep
