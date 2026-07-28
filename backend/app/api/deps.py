"""Dependencias de FastAPI: sesión de DB, usuario actual y control de roles (§14)."""

import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.seguridad import decodificar_token, hash_password
from app.models.base import RolUsuario
from app.models.usuarios import RolUsuarioAsignado, Usuario

# auto_error=False: sin AUTH_HABILITADA no llega token y el 401 lo decide get_current_user.
bearer = HTTPBearer(auto_error=False)


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


async def _con_roles(db: AsyncSession, usuario: Usuario) -> UsuarioActual:
    roles_q = select(RolUsuarioAsignado).where(RolUsuarioAsignado.usuario_id == usuario.id)
    return UsuarioActual(usuario, list((await db.execute(roles_q)).scalars()))


async def _usuario_sin_auth(db: AsyncSession) -> UsuarioActual:
    """Usuario que asume toda petición cuando AUTH_HABILITADA=false."""
    email = get_settings().auth_usuario_default_email
    usuario = (
        await db.execute(select(Usuario).where(Usuario.email == email))
    ).scalar_one_or_none()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AUTH_HABILITADA=false pero el usuario por defecto '{email}' no existe.",
        )
    return await _con_roles(db, usuario)


async def _usuario_por_email(db: AsyncSession, email: str) -> Usuario | None:
    # Case-insensitive: el email del token del portal puede venir con mayúsculas distintas al
    # guardado en Ops. Se normaliza el claim (strip+lower) y se compara contra lower(email).
    return (
        await db.execute(
            select(Usuario).where(func.lower(Usuario.email) == email.strip().lower())
        )
    ).scalar_one_or_none()


async def _auto_provisionar(db: AsyncSession, email: str, sso: dict) -> Usuario:
    """Auto-provisión (JIT): el portal ya autenticó al usuario, así que en su primer ingreso
    creamos su cuenta LOCAL de Ops con rol `lector` (solo lectura). Un admin puede subirle el
    rol después desde /usuarios. El `role` del token del portal NO se usa para el rol local.
    Password inusable: estos usuarios entran por SSO, nunca por el login interno."""
    usuario = Usuario(
        nombre=sso.get("email") or email,
        email=email,
        password_hash=hash_password("sso-" + uuid.uuid4().hex),
        nivel_jerarquico=4,
        activo=True,
    )
    db.add(usuario)
    try:
        await db.flush()
    except IntegrityError:
        # Carrera: otra petición del mismo usuario lo creó primero. Reusamos ese.
        await db.rollback()
        existente = await _usuario_por_email(db, email)
        if existente:
            return existente
        raise
    db.add(RolUsuarioAsignado(usuario_id=usuario.id, rol=RolUsuario.lector, propiedad_id=None))
    await db.commit()
    return usuario


async def get_current_user(
    request: Request,
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> UsuarioActual:
    # 1. Identidad SSO corporativa (PRIORIDAD). SsoGuardMiddleware, tras validar la cookie
    #    `crc_sso`, deja request.state.user = {"id","email","role"} del PORTAL. Mapeamos por
    #    EMAIL al usuario LOCAL de Ops y usamos SIEMPRE su rol/permiso LOCAL (el `role` del
    #    token es el rol del portal, no el de Ops; no se usa para autorizar acá).
    sso = getattr(request.state, "user", None)
    if sso:
        email = (sso.get("email") or "").strip()
        if not email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El token SSO no incluye un email; no se puede resolver la cuenta.",
            )
        usuario = await _usuario_por_email(db, email)
        if usuario and not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu cuenta en Ops está inactiva; pedile a un administrador que la reactive.",
            )
        if usuario is None:
            # Auto-provisión: el portal ya autenticó → alta local automática con rol lector.
            usuario = await _auto_provisionar(db, email, sso)
        return await _con_roles(db, usuario)

    # 2. Sin SSO: modo sin auth interno (bypass) si AUTH_HABILITADA=false. Se conserva.
    if not get_settings().auth_habilitada:
        return await _usuario_sin_auth(db)

    # 3. Sin SSO pero con Bearer interno válido (pruebas / uso directo). Camino previo intacto.
    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
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

    return await _con_roles(db, usuario)


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
