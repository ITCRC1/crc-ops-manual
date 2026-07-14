"""Capacitación / Training por departamento (§8).

Manuales de capacitación organizados por departamento (según el organigrama), con
secciones editables, reordenables y borrables. Contenido propio de CRC.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import PKMixin, SoftDeleteMixin, TimestampMixin


class TrainingManual(Base, PKMixin, TimestampMixin, SoftDeleteMixin):
    """Un manual de capacitación por departamento (puede haber varios por depto)."""

    __tablename__ = "training_manual"

    departamento_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departamentos.id"), nullable=True, index=True
    )
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    # Capa Training SMART (#3 de la trilogía): ficha estructurada de cómo se lleva a
    # cabo el training. JSONB aditivo y nullable; NULL = aún sin ficha (cae al contenido
    # base de secciones). Paralelo a sop_master.smart y descriptor_puesto_master.smart.
    smart: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class TrainingSeccion(Base, PKMixin, TimestampMixin, SoftDeleteMixin):
    """Sección de contenido de un manual. `orden` controla la secuencia."""

    __tablename__ = "training_seccion"

    training_manual_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_manual.id"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    contenido: Mapped[str | None] = mapped_column(Text, nullable=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
