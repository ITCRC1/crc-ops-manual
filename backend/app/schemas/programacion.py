"""Schemas de programación de SOPs y del calendario consolidado."""

import uuid
from datetime import date, time

from pydantic import BaseModel, Field, model_validator

from app.models.base import TipoRecurrencia


class ProgramacionCrear(BaseModel):
    titulo: str = Field(min_length=1, max_length=300)
    descripcion: str | None = None
    tipo_recurrencia: TipoRecurrencia = TipoRecurrencia.unica
    fecha: date  # fecha de ejecución (ancla): obligatoria
    hora: time | None = None
    fecha_fin: date | None = None
    responsable_puesto_id: uuid.UUID | None = None
    responsable_texto: str | None = Field(default=None, max_length=300)
    activo: bool = True
    orden: int | None = None  # si se omite, va al final

    @model_validator(mode="after")
    def _coherencia(self):
        if self.fecha_fin and self.fecha_fin < self.fecha:
            raise ValueError("'fecha_fin' no puede ser anterior a la fecha de ejecución.")
        return self


class ProgramacionActualizar(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=300)
    descripcion: str | None = None
    tipo_recurrencia: TipoRecurrencia | None = None
    fecha: date | None = None
    hora: time | None = None
    fecha_fin: date | None = None
    responsable_puesto_id: uuid.UUID | None = None
    responsable_texto: str | None = Field(default=None, max_length=300)
    activo: bool | None = None
    orden: int | None = None


class ProgramacionOut(BaseModel):
    id: uuid.UUID
    sop_master_id: uuid.UUID
    titulo: str
    descripcion: str | None = None
    tipo_recurrencia: TipoRecurrencia
    fecha: date
    hora: time | None = None
    fecha_fin: date | None = None
    responsable_puesto_id: uuid.UUID | None = None
    responsable_texto: str | None = None
    responsable_puesto_titulo: str | None = None  # resuelto para mostrar
    activo: bool
    orden: int


class EventoCalendario(BaseModel):
    programacion_id: uuid.UUID
    sop_id: uuid.UUID
    sop_codigo: str
    sop_nombre: str
    titulo: str
    descripcion: str | None = None
    fecha: date
    hora: time | None = None
    dia_completo: bool
    responsable: str | None = None


class CalendarioOut(BaseModel):
    desde: date
    hasta: date
    total: int
    eventos: list[EventoCalendario]
