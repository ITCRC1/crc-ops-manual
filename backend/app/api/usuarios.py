"""Gestión mínima de usuarios (§8.2): listado (para designar firmantes/colaboradores)
y alta. El alta la realiza sólo el super_admin. La edición completa de roles/estado
queda para una iteración posterior."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, get_current_user, require_rol
from app.core.config import get_settings
from app.core.db import get_db
from app.core.seguridad import hash_password
from app.models.base import RolUsuario
from app.models.config import Configuracion
from app.models.usuarios import RolUsuarioAsignado, Usuario
from app.schemas.usuarios import RolAsignarIn, UsuarioActualizar, UsuarioCrear, UsuarioListItem
from app.services.auditoria import auditar

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])
settings = get_settings()


async def _nivel_minimo_firmante(db: AsyncSession) -> int:
    cfg = (
        await db.execute(
            select(Configuracion).where(Configuracion.clave == "nivel_minimo_firmante")
        )
    ).scalar_one_or_none()
    try:
        return int(cfg.valor) if cfg else settings.nivel_minimo_firmante
    except (TypeError, ValueError):
        return settings.nivel_minimo_firmante


async def _roles_por_usuario(db: AsyncSession, ids: list[uuid.UUID]) -> dict[uuid.UUID, list]:
    if not ids:
        return {}
    filas = (
        await db.execute(select(RolUsuarioAsignado).where(RolUsuarioAsignado.usuario_id.in_(ids)))
    ).scalars()
    out: dict[uuid.UUID, list] = {}
    for r in filas:
        out.setdefault(r.usuario_id, []).append(
            RolAsignarIn(rol=r.rol, propiedad_id=r.propiedad_id)
        )
    return out


@router.get("", response_model=list[UsuarioListItem])
async def listar_usuarios(
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
    elegibles_firmante: bool = False,
    activos: bool = True,
    q: str | None = None,
) -> list[UsuarioListItem]:
    filtros = []
    if activos:
        filtros.append(Usuario.activo.is_(True))
    if elegibles_firmante:
        nivel = await _nivel_minimo_firmante(db)
        filtros.append(Usuario.nivel_jerarquico <= nivel)
    if q:
        patron = f"%{q}%"
        filtros.append(Usuario.nombre.ilike(patron) | Usuario.email.ilike(patron))

    usuarios = list(
        (await db.execute(select(Usuario).where(*filtros).order_by(Usuario.nombre))).scalars()
    )
    roles = await _roles_por_usuario(db, [u.id for u in usuarios])
    return [
        UsuarioListItem(
            id=u.id, nombre=u.nombre, email=u.email, nivel_jerarquico=u.nivel_jerarquico,
            activo=u.activo, roles=roles.get(u.id, []),
        )
        for u in usuarios
    ]


@router.post("", response_model=UsuarioListItem, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    datos: UsuarioCrear,
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(require_rol(RolUsuario.super_admin)),
) -> UsuarioListItem:
    existe = (
        await db.execute(select(func.count()).select_from(Usuario).where(Usuario.email == datos.email))
    ).scalar_one()
    if existe:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese correo.")
    u = Usuario(
        nombre=datos.nombre, email=datos.email, password_hash=hash_password(datos.password),
        nivel_jerarquico=datos.nivel_jerarquico, activo=True,
    )
    db.add(u)
    await db.flush()
    for r in datos.roles:
        db.add(RolUsuarioAsignado(usuario_id=u.id, rol=r.rol, propiedad_id=r.propiedad_id))
    await db.commit()
    await db.refresh(u)
    return UsuarioListItem(
        id=u.id, nombre=u.nombre, email=u.email, nivel_jerarquico=u.nivel_jerarquico,
        activo=u.activo, roles=datos.roles,
    )


async def _es_super_admin(db: AsyncSession, usuario_id: uuid.UUID) -> bool:
    fila = (
        await db.execute(
            select(RolUsuarioAsignado.id).where(
                RolUsuarioAsignado.usuario_id == usuario_id,
                RolUsuarioAsignado.rol == RolUsuario.super_admin,
            )
        )
    ).first()
    return fila is not None


async def _otros_superadmins_activos(db: AsyncSession, excluir_id: uuid.UUID) -> int:
    return (
        await db.execute(
            select(func.count(func.distinct(RolUsuarioAsignado.usuario_id)))
            .select_from(RolUsuarioAsignado)
            .join(Usuario, Usuario.id == RolUsuarioAsignado.usuario_id)
            .where(
                RolUsuarioAsignado.rol == RolUsuario.super_admin,
                Usuario.activo.is_(True),
                RolUsuarioAsignado.usuario_id != excluir_id,
            )
        )
    ).scalar_one()


@router.patch("/{usuario_id}", response_model=UsuarioListItem)
async def actualizar_usuario(
    usuario_id: uuid.UUID,
    datos: UsuarioActualizar,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(require_rol(RolUsuario.super_admin)),
) -> UsuarioListItem:
    """Edita nivel jerárquico (⇒ elegibilidad de firmante), estado y roles. El correo y la
    contraseña no se tocan acá. Invariante: el sistema conserva ≥1 super_admin activo."""
    u = (await db.execute(select(Usuario).where(Usuario.id == usuario_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    campos = datos.model_dump(exclude_unset=True)

    # No dejar al sistema sin ningún super administrador activo (lockout).
    es_super = await _es_super_admin(db, u.id)
    activo_despues = datos.activo if datos.activo is not None else u.activo
    super_despues = (
        any(r.rol == RolUsuario.super_admin for r in datos.roles)
        if datos.roles is not None
        else es_super
    )
    if es_super and not (super_despues and activo_despues):
        if await _otros_superadmins_activos(db, u.id) == 0:
            raise HTTPException(
                status_code=409,
                detail="El sistema quedaría sin ningún super administrador activo.",
            )

    if datos.nombre is not None:
        nombre = datos.nombre.strip()
        if not nombre:
            raise HTTPException(status_code=422, detail="El nombre no puede quedar vacío.")
        u.nombre = nombre
    if datos.nivel_jerarquico is not None:
        u.nivel_jerarquico = datos.nivel_jerarquico
    if datos.activo is not None:
        u.activo = datos.activo
    if datos.roles is not None:
        await db.execute(delete(RolUsuarioAsignado).where(RolUsuarioAsignado.usuario_id == u.id))
        for r in datos.roles:
            db.add(RolUsuarioAsignado(usuario_id=u.id, rol=r.rol, propiedad_id=r.propiedad_id))
    auditar(db, actual.id, "usuario", u.id, "actualizar", {"campos": list(campos)}, request.client.host)
    await db.commit()
    await db.refresh(u)
    roles = await _roles_por_usuario(db, [u.id])
    return UsuarioListItem(
        id=u.id, nombre=u.nombre, email=u.email, nivel_jerarquico=u.nivel_jerarquico,
        activo=u.activo, roles=roles.get(u.id, []),
    )
