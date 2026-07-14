"""Descriptores de Puesto (Job Descriptions) — tablas propias por la jerarquía (A4, §5)."""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import (
    EstadoDocumento,
    PKMixin,
    SoftDeleteMixin,
    TimestampMixin,
    estado_documento_enum,
)


class DescriptorPuestoMaster(Base, PKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "descriptor_puesto_master"

    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    reporta_a_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("descriptor_puesto_master.id"), nullable=True, index=True
    )
    departamento_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departamentos.id"), nullable=True, index=True
    )
    nivel_jerarquico: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    # Categoría del puesto (organigrama): director | gerente_departamental | supervisor | linea.
    categoria: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    proposito: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsabilidades: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    nivel_autoridad: Mapped[str | None] = mapped_column(Text, nullable=True)
    kpis: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    requisitos: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Capa JD SMART (estándar JD SMART, ~30 secciones + crosswalk a SOPs). JSONB aditivo y
    # nullable: NULL = JD aún sin reformatear (el frontend cae al formato base). No migra los
    # campos existentes. Paralelo a `sop_master.smart`.
    smart: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    estado: Mapped[EstadoDocumento] = mapped_column(
        estado_documento_enum,
        nullable=False,
        default=EstadoDocumento.borrador,
        index=True,
    )
    version_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class DescriptorPuestoVersion(Base, PKMixin, TimestampMixin):
    __tablename__ = "descriptor_puesto_versiones"

    descriptor_puesto_master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("descriptor_puesto_master.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    nota_cambio: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado_en_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
