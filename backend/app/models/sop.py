"""Master: SOPs y políticas (formato único de 9 campos), colaboración, firma y control (§5)."""

import uuid
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import (
    EstadoDocumento,
    FrecuenciaRevision,
    PKMixin,
    SoftDeleteMixin,
    TimestampMixin,
    TipoDocumento,
    TipoRecurrencia,
    estado_documento_enum,
    frecuencia_revision_enum,
    tipo_documento_enum,
    tipo_recurrencia_enum,
)


class SopMaster(Base, PKMixin, TimestampMixin, SoftDeleteMixin):
    """Formato único de 9 campos (A3). codigo = area.codigo + '-' + numero a 4 dígitos."""

    __tablename__ = "sop_master"
    __table_args__ = (UniqueConstraint("area_id", "numero", name="uq_area_numero"),)

    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("areas.id"), nullable=False, index=True
    )
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    tipo: Mapped[TipoDocumento] = mapped_column(
        tipo_documento_enum,
        nullable=False,
        default=TipoDocumento.sop,
    )
    nombre: Mapped[str] = mapped_column(String(300), nullable=False)
    departamento_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departamentos.id"), nullable=True, index=True
    )
    # 9 campos del formato único
    proposito: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluacion_riesgos: Mapped[str | None] = mapped_column(Text, nullable=True)
    controles_existentes: Mapped[str | None] = mapped_column(Text, nullable=True)
    procedimiento: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # texto estructurado
    responsables: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia: Mapped[str | None] = mapped_column(Text, nullable=True)
    frecuencia_revision: Mapped[FrecuenciaRevision | None] = mapped_column(
        frecuencia_revision_enum, nullable=True
    )
    # Capa SMART (adopción del estándar "SOP SMART" — 18 secciones + apéndices A–F).
    # Estructura JSONB canónica `formato="SMART-1.0"` (ver app/schemas/sop.py::SopSmart).
    # Es ADITIVA: no reemplaza los 9 campos (firma/versiones/adopción siguen operando sobre
    # ellos). NULL = SOP aún sin reformatear al estándar SMART; el frontend cae al formato de
    # 9 campos. No inventa políticas: los vacíos van en `pendiente_confirmar`.
    smart: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    estado: Mapped[EstadoDocumento] = mapped_column(
        estado_documento_enum,
        nullable=False,
        default=EstadoDocumento.borrador,
        index=True,
    )
    version_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    firmado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Marca interna de despliegue (NO restrictiva): código de propiedad cuya política originó
    # este SOP y que tiene PRIORIDAD para ser transferido a esa propiedad (ej. 'AMA').
    # NO implica exclusividad ni propiedad: el SOP sigue siendo parte del catálogo maestro y
    # cualquier propiedad (CWL, Oxígen, Ojochal, etc.) puede adoptarlo/usarlo. Es solo un
    # rastro de curaduría para preseleccionarlos en el despliegue. NULL = sin origen marcado.
    origen_propiedad: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)


class SopMasterVersion(Base, PKMixin, TimestampMixin):
    __tablename__ = "sop_master_versiones"

    sop_master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sop_master.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    nota_cambio: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado_en_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)


class SopMasterSistema(Base, PKMixin, TimestampMixin):
    """Sistemas que el SOP asume (sugerencias, §7.13)."""

    __tablename__ = "sop_master_sistemas"
    __table_args__ = (UniqueConstraint("sop_master_id", "sistema_id", name="uq_sop_sistema"),)

    sop_master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sop_master.id"), nullable=False, index=True
    )
    sistema_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sistemas.id"), nullable=False, index=True
    )


class SopMasterDepartamentoAfectado(Base, PKMixin, TimestampMixin):
    """Departamentos que el SOP afecta además de su dueño (`sop_master.departamento_id`).

    Un SOP puede pertenecer a un departamento (dueño, opcional) y a la vez impactar el
    trabajo de otros — ej. un SOP de Finanzas que exige un paso a Recepción. Esta tabla
    modela esos "afectados"; el dueño no se duplica aquí."""

    __tablename__ = "sop_master_departamentos_afectados"
    __table_args__ = (
        UniqueConstraint("sop_master_id", "departamento_id", name="uq_sop_depto_afectado"),
    )

    sop_master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sop_master.id"), nullable=False, index=True
    )
    departamento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departamentos.id"), nullable=False, index=True
    )


class SopMasterPuestoResponsable(Base, PKMixin, TimestampMixin):
    """Puestos (del master de descriptores) responsables directos del SOP.

    Complementa el campo de texto libre `responsables` (uno de los 9 campos del
    formato único, que no se modifica) con un vínculo estructurado y consultable a
    puestos reales, para poder nombrar y notificar responsables directamente."""

    __tablename__ = "sop_master_puestos_responsables"
    __table_args__ = (
        UniqueConstraint(
            "sop_master_id", "descriptor_puesto_master_id", name="uq_sop_puesto_responsable"
        ),
    )

    sop_master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sop_master.id"), nullable=False, index=True
    )
    descriptor_puesto_master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("descriptor_puesto_master.id"), nullable=False, index=True
    )


class ProgramacionSop(Base, PKMixin, TimestampMixin, SoftDeleteMixin):
    """Actividad programada de un SOP (apartado opcional al final de cada SOP).

    Un SOP declara procesos recurrentes o puntuales ("pagos a proveedores todos los
    lunes 09:00") como parte de su estructura estándar. Cada actividad se expande por
    rango de fechas y alimenta el CALENDARIO GENERAL consolidado (+ export .ics)."""

    __tablename__ = "programacion_sop"

    sop_master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sop_master.id"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    tipo_recurrencia: Mapped[TipoRecurrencia] = mapped_column(
        tipo_recurrencia_enum, nullable=False, default=TipoRecurrencia.unica
    )
    # Fecha de ejecución: ancla de la cadencia (primera ocurrencia). Obligatoria.
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    # Hora del día; si es NULL la actividad es de "día completo".
    hora: Mapped[time | None] = mapped_column(Time, nullable=True)
    # Fin opcional de la repetición (para recurrencias); NULL = sin fin.
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Responsable: vínculo estructurado a un puesto, o texto libre de respaldo.
    responsable_puesto_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("descriptor_puesto_master.id"), nullable=True, index=True
    )
    responsable_texto: Mapped[str | None] = mapped_column(String(300), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ColaboradorSop(Base, PKMixin, TimestampMixin):
    __tablename__ = "colaboradores_sop"

    sop_master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sop_master.id"), nullable=False, index=True
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    rol_colaboracion: Mapped[str] = mapped_column(String(20), nullable=False)  # redactor/revisor
    seccion_asignada: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="invitado")


class FirmanteSop(Base, PKMixin, TimestampMixin):
    """Designados al crear. Restricción de nivel se valida en servicio (§7.3)."""

    __tablename__ = "firmantes_sop"

    sop_master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sop_master.id"), nullable=False, index=True
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    obligatorio: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FirmaElectronica(Base, PKMixin, TimestampMixin):
    """Registro inmutable de la firma (A5)."""

    __tablename__ = "firmas_electronicas"

    sop_master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sop_master.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metodo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hash_pdf: Mapped[str | None] = mapped_column(String(128), nullable=True)


class DocumentoControlado(Base, PKMixin, TimestampMixin):
    """Versión firmada en PDF, inmutable (A5)."""

    __tablename__ = "documento_controlado"

    sop_master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sop_master.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    pdf_storage_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    hash_pdf: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fecha_firma: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    custodio_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True, index=True
    )
    es_vigente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
