"""Schemas del laboratorio de intake: triage de un procedimiento nuevo vs los SOPs
existentes, y extracción de texto de un archivo subido."""

import uuid

from pydantic import BaseModel


class IntakeAnalizar(BaseModel):
    nombre: str
    texto: str = ""


class SimilarOut(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str
    area_codigo: str
    estado: str
    score: float


class TriageOut(BaseModel):
    verdict: str  # 'posible_duplicado' | 'nuevo'
    umbral: float
    similares: list[SimilarOut]


class ExtraerOut(BaseModel):
    nombre: str
    texto: str
