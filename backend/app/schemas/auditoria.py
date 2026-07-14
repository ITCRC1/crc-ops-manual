"""Schemas de auditoría y custodia documental (§8.8, §8.18, §7.7, §7.18)."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class RegistroAuditoriaOut(BaseModel):
    id: uuid.UUID
    usuario_id: uuid.UUID | None = None
    entidad: str
    entidad_id: uuid.UUID | None = None
    accion: str
    detalle: dict | None = None
    ip: str | None = None
    creado_en: datetime


class AuditoriaLista(BaseModel):
    total: int
    items: list[RegistroAuditoriaOut]


class DocumentoControladoItem(BaseModel):
    id: uuid.UUID
    sop_master_id: uuid.UUID
    sop_codigo: str | None = None
    sop_nombre: str | None = None
    version: int
    hash_pdf: str | None = None
    fecha_firma: datetime | None = None
    es_vigente: bool
    custodio_id: uuid.UUID | None = None
    creado_en: datetime


class DocumentoControladoLista(BaseModel):
    total: int
    items: list[DocumentoControladoItem]


class BitacoraControlOut(BaseModel):
    id: uuid.UUID
    documento_controlado_id: uuid.UUID
    accion: str
    detalle: dict | None = None
    usuario_id: uuid.UUID | None = None
    creado_en: datetime


class VerificacionIntegridad(BaseModel):
    documento_controlado_id: uuid.UUID
    integro: bool
    hash_esperado: str | None = None
    hash_actual: str | None = None
    mensaje: str
