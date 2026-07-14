"""Schemas del Armador por propiedad: departamentos, puestos (organigrama local con
adoptar/adaptar/local), titulares (ocupantes), sistemas y resumen por hotel."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.base import EstadoAsignacion, ModoAsignacion

# --- Departamentos por propiedad ---


class DepartamentosSet(BaseModel):
    """Reemplazo del conjunto completo de departamentos que aplican a la propiedad."""

    departamento_ids: list[uuid.UUID]


class DepartamentoAsignadoOut(BaseModel):
    id: uuid.UUID          # id del departamento (master)
    codigo: str
    nombre: str
    division_id: uuid.UUID | None = None


# --- Puestos por propiedad (organigrama local) ---


class PuestoCrear(BaseModel):
    modo: ModoAsignacion
    descriptor_puesto_master_id: uuid.UUID | None = None  # req. para adoptado/adaptado
    overrides: dict | None = None  # deltas (adaptado) o contenido (local: requiere 'titulo')
    reporta_a_id: uuid.UUID | None = None  # otro propiedad_puesto de la MISMA propiedad
    dotacion: int | None = None


class PuestoActualizar(BaseModel):
    overrides: dict | None = None
    reporta_a_id: uuid.UUID | None = None
    dotacion: int | None = None


class SmartOverridesPuestoRequest(BaseModel):
    """Deltas de la capa JD SMART por sección (adaptado) o SMART local completa (local)."""

    smart_overrides: dict | None = None


class PuestoOut(BaseModel):
    id: uuid.UUID
    propiedad_id: uuid.UUID
    descriptor_puesto_master_id: uuid.UUID | None
    modo: ModoAsignacion
    titulo: str
    codigo: str | None = None
    nivel_jerarquico: int
    categoria: str | None = None
    departamento_id: uuid.UUID | None = None
    departamento_codigo: str | None = None
    reporta_a_id: uuid.UUID | None = None
    dotacion: int | None = None
    estado: EstadoAsignacion
    requiere_actualizacion: bool
    ocupantes_count: int = 0


class OcupanteOut(BaseModel):
    id: uuid.UUID
    usuario_id: uuid.UUID
    usuario_nombre: str
    usuario_email: str
    es_principal: bool
    nota: str | None = None


class PuestoDetalle(PuestoOut):
    contenido_efectivo: dict
    ocupantes: list[OcupanteOut] = []
    creado_en: datetime
    # Capa JD SMART por propiedad (Etapa B)
    smart_efectivo: dict = {}
    smart_master: dict = {}
    smart_overrides: dict | None = None


class SembrarRequest(BaseModel):
    """Siembra en bloque el organigrama maestro de los departamentos indicados como
    puestos adoptados de la propiedad, remapeando la jerarquía `reporta_a`."""

    departamento_ids: list[uuid.UUID] | None = None  # None = todos los asignados
    incluir_sin_departamento: bool = False  # también la cúpula (puestos maestros sin depto)


class SembrarResultado(BaseModel):
    creados: int
    omitidos: int  # ya existían (idempotente)


# --- Titulares (ocupantes) ---


class OcupanteCrear(BaseModel):
    usuario_id: uuid.UUID
    es_principal: bool = True
    nota: str | None = None


# --- Sistemas por propiedad ---


class SistemasSet(BaseModel):
    sistema_ids: list[uuid.UUID]


class SistemaAsignadoOut(BaseModel):
    id: uuid.UUID          # id del sistema (master)
    codigo: str
    nombre: str
    categoria: str | None = None


# --- Resumen por propiedad (hub del armador) ---


class PropiedadResumen(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    activo: bool
    departamentos: int
    puestos: int
    ocupantes: int
    sops: int
    sistemas: int
