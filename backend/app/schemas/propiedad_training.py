"""Schemas de adopción/adaptación de manuales de capacitación por propiedad (Etapa C)."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.base import EstadoAsignacion, ModoAsignacion


class AsignarTrainingRequest(BaseModel):
    modo: ModoAsignacion
    training_manual_id: uuid.UUID | None = None  # requerido para adoptado/adaptado
    titulo_local: str | None = None  # requerido para local
    smart_overrides: dict | None = None


class SmartOverridesTrainingRequest(BaseModel):
    """Deltas de la ficha TRAIN-SMART por sección (adaptado) o ficha local completa (local)."""

    smart_overrides: dict | None = None


class PropiedadTrainingOut(BaseModel):
    id: uuid.UUID
    propiedad_id: uuid.UUID
    training_manual_id: uuid.UUID | None
    modo: ModoAsignacion
    titulo: str  # resuelto: título del manual master o titulo_local
    titulo_local: str | None = None
    estado: EstadoAsignacion
    creado_en: datetime


class PropiedadTrainingDetalle(PropiedadTrainingOut):
    smart_efectivo: dict = {}
    smart_master: dict = {}
    smart_overrides: dict | None = None
