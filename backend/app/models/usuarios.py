"""Master data de usuarios y roles con alcance por propiedad (§5)."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import PKMixin, RolUsuario, TimestampMixin, rol_usuario_enum


class Usuario(Base, PKMixin, TimestampMixin):
    __tablename__ = "usuarios"

    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    departamento_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departamentos.id"), nullable=True, index=True
    )
    puesto_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("descriptor_puesto_master.id"), nullable=True, index=True
    )
    # 1 alta dirección · 2 dirección funcional · 3 jefatura/gerencia · 4 operativo
    nivel_jerarquico: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class RolUsuarioAsignado(Base, PKMixin, TimestampMixin):
    """Varios roles/propiedades por usuario. propiedad_id NULL = alcance corporativo."""

    __tablename__ = "roles_usuario"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    rol: Mapped[RolUsuario] = mapped_column(rol_usuario_enum, nullable=False)
    propiedad_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propiedades.id"), nullable=True, index=True
    )
