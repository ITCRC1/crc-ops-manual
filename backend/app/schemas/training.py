"""Schemas de Capacitación / Training.

La capa Training SMART (`TrainingSmart`) es el #3 de la trilogía SMART (paralelo a
`SopSmart` y `DescriptorSmart`): la ficha estructurada de CÓMO se lleva a cabo cada
training. Se guarda como JSONB aditivo en `training_manual.smart`; no reemplaza las
secciones de contenido. Todos los campos son opcionales: lo que no exista todavía va a
`pendiente_confirmar` — NUNCA se inventan obligatoriedad legal, certificaciones,
aprobadores ni vigencias sin base.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Capa Training SMART — estructura canónica "TRAIN-SMART-1.0"
# ---------------------------------------------------------------------------
class SmartContenido(BaseModel):
    """Un módulo/tema del temario del training."""

    n: int
    tema: str
    descripcion: str = ""
    material_ref: str = ""  # referencia a un training_manual/sección/SOP que lo cubre


class SmartMaterial(BaseModel):
    """Material de apoyo (manual, SOP, video, presentación, enlace externo)."""

    material: str
    tipo: str = ""  # manual | sop | video | presentacion | enlace | otro
    referencia: str = ""  # código de SOP/manual o URL


class SmartEvaluacion(BaseModel):
    """Método de evaluación del aprendizaje."""

    metodo: str  # examen | práctica | observación | firma de asistencia | otro
    criterio_aprobacion: str = ""
    nota_minima: str = ""


class SmartEvidenciaTrain(BaseModel):
    """Evidencia que queda del training completado (para el registro futuro)."""

    evidencia: str
    responsable: str = ""
    archivo: str = ""
    retencion: str = ""


class SmartVigencia(BaseModel):
    """Vigencia y recertificación del training."""

    vigencia_meses: str = ""  # cuánto vale el training antes de re-tomarlo
    requiere_recertificacion: bool = False
    condiciones_recert: str = ""


class SmartKpiTrain(BaseModel):
    """Indicador; `recomendado=True` cuando no existía definido para el training."""

    indicador: str
    meta: str = ""
    recomendado: bool = False


class SmartVersionTrain(BaseModel):
    """Fila de control de versiones de la ficha."""

    version: str
    fecha: str = ""
    preparado_por: str = ""
    revisado_por: str = ""
    aprobado_por: str = ""
    cambios: str = ""
    proxima_revision: str = ""


class TrainingSmart(BaseModel):
    """Ficha SMART completa de un training. El título vive en la columna del manual."""

    formato: str = "TRAIN-SMART-1.0"
    objetivo: str = ""  # objetivos de aprendizaje
    modalidad: str = ""  # presencial | virtual | OJT | mixta
    duracion: str = ""  # horas / sesiones
    dirigido_a: list[str] = []  # puestos/roles objetivo
    imparte: str = ""  # quién lo imparte / instructor / responsable
    prerequisitos: list[str] = []
    contenidos: list[SmartContenido] = []  # temario
    materiales: list[SmartMaterial] = []
    evaluacion: list[SmartEvaluacion] = []
    evidencia: list[SmartEvidenciaTrain] = []
    vigencia: SmartVigencia = SmartVigencia()
    obligatoria: bool = False
    base_obligatoriedad: str = ""  # base legal/normativa; vacío = pendiente de validar
    kpis: list[SmartKpiTrain] = []
    control_versiones: list[SmartVersionTrain] = []
    resumen_ejecutivo: str = ""
    pendiente_confirmar: list[str] = []


class SeccionCrear(BaseModel):
    titulo: str = Field(min_length=1)
    contenido: str | None = None
    orden: int | None = None  # si se omite, va al final


class SeccionActualizar(BaseModel):
    titulo: str | None = None
    contenido: str | None = None
    orden: int | None = None


class SeccionOut(BaseModel):
    id: uuid.UUID
    training_manual_id: uuid.UUID
    titulo: str
    contenido: str | None = None
    orden: int
    creado_en: datetime
    actualizado_en: datetime


class ManualCrear(BaseModel):
    titulo: str = Field(min_length=1)
    departamento_id: uuid.UUID | None = None
    descripcion: str | None = None


class ManualActualizar(BaseModel):
    titulo: str | None = None
    departamento_id: uuid.UUID | None = None
    descripcion: str | None = None


class ManualItem(BaseModel):
    id: uuid.UUID
    titulo: str
    departamento_id: uuid.UUID | None = None
    departamento_codigo: str | None = None
    descripcion: str | None = None
    total_secciones: int
    tiene_smart: bool = False
    creado_en: datetime
    actualizado_en: datetime


class ManualDetalle(ManualItem):
    secciones: list[SeccionOut] = []
    smart: TrainingSmart | None = None


class ManualSmartActualizar(BaseModel):
    """Body de `PUT /api/capacitacion/manuales/{id}/smart`: persiste la ficha Training SMART."""

    smart: TrainingSmart


class ReordenarRequest(BaseModel):
    """Lista de ids de sección en el nuevo orden deseado."""

    orden_ids: list[uuid.UUID]
