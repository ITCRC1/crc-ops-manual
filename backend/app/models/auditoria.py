"""Control, auditoría y adjuntos (§5)."""

import uuid

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import PKMixin, TimestampMixin


class BitacoraControl(Base, PKMixin, TimestampMixin):
    """Log de accesos/cambios a documentos controlados (custodio, §7.7)."""

    __tablename__ = "bitacora_control"

    documento_controlado_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documento_controlado.id"), nullable=False, index=True
    )
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    detalle: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)


class RegistroAuditoria(Base, PKMixin, TimestampMixin):
    """Trazabilidad transversal de acciones sensibles (§7.18)."""

    __tablename__ = "registro_auditoria"

    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    entidad: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entidad_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    detalle: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Adjunto(Base, PKMixin, TimestampMixin):
    """No almacenar el PDF de USALI (regla legal)."""

    __tablename__ = "adjuntos"

    entidad: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entidad_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(300), nullable=False)
    mime: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tamano: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    subido_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
