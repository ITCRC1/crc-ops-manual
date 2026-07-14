"""Schemas de asignación de SOPs por propiedad."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.base import EstadoAsignacion, ModoAsignacion


class AsignarRequest(BaseModel):
    modo: ModoAsignacion
    sop_master_id: uuid.UUID | None = None  # requerido para adoptado/adaptado; None para local
    overrides: dict | None = None  # deltas para adaptado
    campos_locales: dict | None = None  # contenido para local


class OverridesRequest(BaseModel):
    overrides: dict | None = None
    campos_locales: dict | None = None


class SmartOverridesRequest(BaseModel):
    """Deltas de la capa SMART por sección (adaptado) o SMART local completa (local)."""

    smart_overrides: dict | None = None


class PropiedadSopOut(BaseModel):
    id: uuid.UUID
    propiedad_id: uuid.UUID
    sop_master_id: uuid.UUID | None
    modo: ModoAsignacion
    version_fijada: int | None
    codigo_local: str | None
    estado: EstadoAsignacion
    requiere_actualizacion: bool
    master_retirado: bool
    creado_en: datetime


class PropiedadSopDetalle(PropiedadSopOut):
    contenido_efectivo: dict          # merge master + overrides (lo que se lee/usa)
    contenido_master: dict = {}       # snapshot del master en la versión fijada (para restaurar)
    overrides: dict | None = None     # deltas locales (adaptado): qué secciones base son locales
    campos_locales: dict | None = None  # contenido de un SOP local
    # --- Capa SMART por propiedad (Etapa A) ---
    smart_efectivo: dict = {}         # SMART efectiva (master ∪ smart_overrides) — lo que se usa
    smart_master: dict = {}           # SMART del master (para mostrar la sección heredada/restaurar)
    smart_overrides: dict | None = None  # deltas SMART locales: qué secciones SMART son locales


class Sugerencia(BaseModel):
    sop_master_id: uuid.UUID
    codigo: str
    nombre: str
    sugerencia: ModoAsignacion
    sistemas_faltantes: list[str]
    motivo: str
