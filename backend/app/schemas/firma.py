"""Schemas de colaboración, firmantes y firma electrónica."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class FirmanteCrear(BaseModel):
    usuario_id: uuid.UUID
    orden: int = 1
    obligatorio: bool = True


class FirmanteOut(BaseModel):
    id: uuid.UUID
    usuario_id: uuid.UUID
    orden: int
    obligatorio: bool
    firmado: bool


class ColaboradorCrear(BaseModel):
    usuario_id: uuid.UUID
    rol_colaboracion: str = "redactor"  # redactor | revisor
    seccion_asignada: str | None = None


class ColaboradorOut(BaseModel):
    id: uuid.UUID
    usuario_id: uuid.UUID
    usuario_nombre: str | None = None
    rol_colaboracion: str
    seccion_asignada: str | None = None
    estado: str


class ColaboradoresLote(BaseModel):
    """Invita a varias personas a varios SOPs de una vez.

    Invitar uno por uno no escala: son 151 SOPs y el equipo entero debe completar sus
    pendientes. Es idempotente: repetir la invitación no duplica filas."""

    sop_ids: list[uuid.UUID]
    usuario_ids: list[uuid.UUID]
    rol_colaboracion: str = "redactor"  # redactor = puede editar la capa SMART


class ColaboradoresLoteResultado(BaseModel):
    creados: int
    ya_existian: int


class FirmarRequest(BaseModel):
    metodo: str = "clave"


class RechazarRequest(BaseModel):
    comentario: str  # obligatorio (B5)


class ReasignarRequest(BaseModel):
    nuevo_usuario_id: uuid.UUID


class FirmaOut(BaseModel):
    usuario_id: uuid.UUID
    version: int
    fecha_hora: datetime
    metodo: str | None = None


class DocumentoControladoOut(BaseModel):
    id: uuid.UUID
    sop_master_id: uuid.UUID
    version: int
    hash_pdf: str | None
    fecha_firma: datetime | None
    es_vigente: bool
