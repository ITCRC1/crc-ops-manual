"""Capa de propiedad: asignaciones de SOPs y puestos + bitácora (§5)."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import (
    EstadoAsignacion,
    ModoAsignacion,
    PKMixin,
    SoftDeleteMixin,
    TimestampMixin,
    estado_asignacion_enum,
    modo_asignacion_enum,
)


class PropiedadSop(Base, PKMixin, TimestampMixin, SoftDeleteMixin):
    """sop_master_id NULL = local. Índice único (propiedad_id, sop_master_id) cuando no es local."""

    __tablename__ = "propiedad_sop"

    propiedad_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propiedades.id"), nullable=False, index=True
    )
    sop_master_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sop_master.id"), nullable=True, index=True
    )
    modo: Mapped[ModoAsignacion] = mapped_column(modo_asignacion_enum, nullable=False)
    version_fijada: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overrides: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # solo deltas (A2) — campos base
    # Deltas de la capa SMART por sección (adaptado): solo las secciones SMART que el hotel
    # personalizó. SMART efectivo = {**master.smart, **smart_overrides}. NULL = hereda todo.
    smart_overrides: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    codigo_local: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    campos_locales: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    estado: Mapped[EstadoAsignacion] = mapped_column(
        estado_asignacion_enum,
        nullable=False,
        default=EstadoAsignacion.borrador,
        index=True,
    )
    fecha_vigencia: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requiere_actualizacion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    master_retirado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class PropiedadPuesto(Base, PKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "propiedad_puesto"

    propiedad_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propiedades.id"), nullable=False, index=True
    )
    descriptor_puesto_master_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("descriptor_puesto_master.id"), nullable=True, index=True
    )
    modo: Mapped[ModoAsignacion] = mapped_column(modo_asignacion_enum, nullable=False)
    version_fijada: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overrides: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # campos base del descriptor
    # Deltas de la capa JD SMART por sección (adaptado): solo las secciones SMART que el hotel
    # personalizó. SMART efectivo = {**master.smart, **smart_overrides}. NULL = hereda todo.
    smart_overrides: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reporta_a_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propiedad_puesto.id"), nullable=True, index=True
    )
    dotacion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[EstadoAsignacion] = mapped_column(
        estado_asignacion_enum,
        nullable=False,
        default=EstadoAsignacion.borrador,
        index=True,
    )
    requiere_actualizacion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class PropiedadPuestoOcupante(Base, PKMixin, TimestampMixin):
    """Titular(es) de un puesto de la propiedad: qué usuario(s) ocupan la plaza.

    Permite 0..N ocupantes por puesto (una plaza con dotación >1 puede listar varios).
    `es_principal` marca al titular principal (a lo sumo uno por puesto lo será)."""

    __tablename__ = "propiedad_puesto_ocupante"
    __table_args__ = (
        UniqueConstraint("propiedad_puesto_id", "usuario_id", name="uq_puesto_ocupante"),
    )

    propiedad_puesto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propiedad_puesto.id"), nullable=False, index=True
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    es_principal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    nota: Mapped[str | None] = mapped_column(String(300), nullable=True)


class PropiedadTrainingManual(Base, PKMixin, TimestampMixin, SoftDeleteMixin):
    """Adopción/adaptación de un manual de capacitación por propiedad (Etapa C).

    `training_manual_id` NULL = manual local (sin master). Capa SMART efectiva =
    {**master.smart, **smart_overrides} a nivel de sección; NULL = hereda todo."""

    __tablename__ = "propiedad_training_manual"
    __table_args__ = (
        UniqueConstraint(
            "propiedad_id", "training_manual_id", name="uq_propiedad_training_manual"
        ),
    )

    propiedad_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propiedades.id"), nullable=False, index=True
    )
    training_manual_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_manual.id"), nullable=True, index=True
    )
    modo: Mapped[ModoAsignacion] = mapped_column(modo_asignacion_enum, nullable=False)
    smart_overrides: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    titulo_local: Mapped[str | None] = mapped_column(String(300), nullable=True)
    estado: Mapped[EstadoAsignacion] = mapped_column(
        estado_asignacion_enum,
        nullable=False,
        default=EstadoAsignacion.borrador,
        index=True,
    )


class PropiedadSopBitacora(Base, PKMixin, TimestampMixin):
    __tablename__ = "propiedad_sop_bitacora"

    propiedad_sop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propiedad_sop.id"), nullable=False, index=True
    )
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    campo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    valor_anterior: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_nuevo: Mapped[str | None] = mapped_column(Text, nullable=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
