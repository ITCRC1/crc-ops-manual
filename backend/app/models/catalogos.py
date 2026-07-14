"""Catálogos editables (extensibilidad sin migración, A7) y contadores de numeración (§7.2)."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import PKMixin, TimestampMixin


class Propiedad(Base, PKMixin, TimestampMixin):
    """Un hotel del grupo. Es el 'inquilino' del modelo."""

    __tablename__ = "propiedades"

    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    razon_social: Mapped[str | None] = mapped_column(String(200), nullable=True)
    zona_horaria: Mapped[str] = mapped_column(
        String(50), nullable=False, default="America/Costa_Rica"
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Area(Base, PKMixin, TimestampMixin):
    """Clasificación funcional con prefijo de código (FIN, GE, ...). Base del código de SOP."""

    __tablename__ = "areas"

    codigo: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Sistema(Base, PKMixin, TimestampMixin):
    """Herramienta operativa/financiera de una propiedad (OPERA, Simphony, ...)."""

    __tablename__ = "sistemas"

    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(50), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)


class PropiedadSistema(Base, PKMixin, TimestampMixin):
    __tablename__ = "propiedad_sistemas"
    __table_args__ = (UniqueConstraint("propiedad_id", "sistema_id", name="uq_propiedad_sistema"),)

    propiedad_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propiedades.id"), nullable=False, index=True
    )
    sistema_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sistemas.id"), nullable=False, index=True
    )
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)


class Division(Base, PKMixin, TimestampMixin):
    """Nivel organizativo por encima del departamento (organigrama).

    Auto-referenciada: una división puede contener subdivisiones (parent_id apunta a la
    división superior). Los departamentos apuntan a la división o subdivisión a la que
    pertenecen directamente vía `Departamento.division_id`.

    Jerarquía CRC: Gerencia General (ápice) → Divisiones funcionales (Operaciones,
    Mercadeo y Ventas, Finanzas, Recursos Humanos) → Subdivisiones (Habitaciones,
    Alimentos y Bebidas, Mantenimiento dentro de Operaciones) → Departamentos → Puestos.
    """

    __tablename__ = "divisiones"

    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("divisiones.id"), nullable=True, index=True
    )
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Departamento(Base, PKMixin, TimestampMixin):
    """propiedad_propietaria_id NULL = estándar; con valor = local."""

    __tablename__ = "departamentos"

    codigo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    propiedad_propietaria_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propiedades.id"), nullable=True, index=True
    )
    division_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("divisiones.id"), nullable=True, index=True
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class PropiedadDepartamento(Base, PKMixin, TimestampMixin):
    __tablename__ = "propiedad_departamentos"
    __table_args__ = (
        UniqueConstraint("propiedad_id", "departamento_id", name="uq_propiedad_departamento"),
    )

    propiedad_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propiedades.id"), nullable=False, index=True
    )
    departamento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departamentos.id"), nullable=False, index=True
    )


class ContadorArea(Base, PKMixin, TimestampMixin):
    """Secuencia por área para numeración atómica (§7.2)."""

    __tablename__ = "contador_area"

    area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("areas.id"), unique=True, nullable=False, index=True
    )
    ultimo_numero: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ContadorLocal(Base, PKMixin, TimestampMixin):
    """Secuencia por propiedad para códigos locales."""

    __tablename__ = "contador_local"

    propiedad_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("propiedades.id"), unique=True, nullable=False, index=True
    )
    ultimo_numero: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ContadorDescriptor(Base, PKMixin, TimestampMixin):
    """Secuencia global (una sola fila) para el código de descriptores (JD-###, §7.2).

    Se bloquea con SELECT ... FOR UPDATE para numeración atómica. La fila se siembra en
    la migración; el servicio la reconcilia con el mayor código existente."""

    __tablename__ = "contador_descriptor"

    ultimo_numero: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
