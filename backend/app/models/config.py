"""Configuración de negocio y marco institucional (§5)."""

import uuid

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import PKMixin, TimestampMixin


class Configuracion(Base, PKMixin, TimestampMixin):
    """Parámetros editables. Semilla obligatoria: nivel_minimo_firmante = 3 (A7)."""

    __tablename__ = "configuracion"

    clave: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    valor: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False, default="text")  # int/text/bool
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    editable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class MarcoInstitucional(Base, PKMixin, TimestampMixin):
    """Contenido corporativo editable y versionado. Un registro activo + historial."""

    __tablename__ = "marco_institucional"

    vision: Mapped[str | None] = mapped_column(Text, nullable=True)
    mision: Mapped[str | None] = mapped_column(Text, nullable=True)
    objetivos_estrategicos: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    valores: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    declaracion_valor: Mapped[str | None] = mapped_column(Text, nullable=True)
    manifiesto: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    editado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
