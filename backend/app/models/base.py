"""Mixins y enumeraciones compartidas (§5 del spec). Nomenclatura en español."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class PKMixin:
    """PK = UUID en todas las tablas (A6)."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    """Todas las tablas con creado_en / actualizado_en."""

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Soft delete en entidades de contenido."""

    eliminado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# --- Enumeraciones (valores en español, §5) ---


class TipoDocumento(str, enum.Enum):
    sop = "sop"
    politica = "politica"


class EstadoDocumento(str, enum.Enum):
    borrador = "borrador"
    en_revision = "en_revision"
    en_firma = "en_firma"
    firmado = "firmado"
    rechazado = "rechazado"
    archivado = "archivado"


class ModoAsignacion(str, enum.Enum):
    adoptado = "adoptado"
    adaptado = "adaptado"
    local = "local"
    no_aplica = "no_aplica"


class EstadoAsignacion(str, enum.Enum):
    borrador = "borrador"
    en_revision = "en_revision"
    en_firma = "en_firma"
    vigente = "vigente"
    rechazado = "rechazado"
    archivado = "archivado"


class FrecuenciaRevision(str, enum.Enum):
    mensual = "mensual"
    trimestral = "trimestral"
    semestral = "semestral"
    anual = "anual"
    por_cambio = "por_cambio"


class TipoRecurrencia(str, enum.Enum):
    """Cadencia de una actividad programada de un SOP (calendario consolidado).

    La `fecha de ejecución` (columna `fecha`) es el ancla: primera ocurrencia y punto
    desde el que se deriva la cadencia (día de la semana, día del mes, etc.)."""

    unica = "unica"          # una sola vez, en la fecha de ejecución
    diaria = "diaria"        # cada día
    semanal = "semanal"      # cada 7 días desde la fecha de ejecución
    quincenal = "quincenal"  # cada 14 días desde la fecha de ejecución
    mensual = "mensual"      # mismo día de mes que la fecha de ejecución
    trimestral = "trimestral"  # cada 3 meses desde la fecha de ejecución
    anual = "anual"          # mismo mes y día que la fecha de ejecución


class RolUsuario(str, enum.Enum):
    super_admin = "super_admin"
    editor_corporativo = "editor_corporativo"
    editor_propiedad = "editor_propiedad"
    custodio_documental = "custodio_documental"
    lector = "lector"


# --- Tipos ENUM de PostgreSQL compartidos ---
# Se define UNA instancia por tipo y se reutiliza en todas las columnas, para que
# SQLAlchemy/Alembic emitan un solo CREATE TYPE (evita "type already exists").

tipo_documento_enum = PgEnum(TipoDocumento, name="tipo_documento", create_type=True)
estado_documento_enum = PgEnum(EstadoDocumento, name="estado_documento", create_type=True)
modo_asignacion_enum = PgEnum(ModoAsignacion, name="modo_asignacion", create_type=True)
estado_asignacion_enum = PgEnum(EstadoAsignacion, name="estado_asignacion", create_type=True)
frecuencia_revision_enum = PgEnum(FrecuenciaRevision, name="frecuencia_revision", create_type=True)
rol_usuario_enum = PgEnum(RolUsuario, name="rol_usuario", create_type=True)
tipo_recurrencia_enum = PgEnum(TipoRecurrencia, name="tipo_recurrencia", create_type=True)
