"""Schemas Pydantic del master de SOPs (formato único de 9 campos, §7.1).

La capa SMART (`SopSmart`) es la adopción del estándar "SOP SMART" (18 secciones +
apéndices A–F). Se guarda como JSONB aditivo en `sop_master.smart`; no reemplaza los 9
campos. Todos los campos son opcionales: lo que no exista en el SOP original va a
`pendiente_confirmar` — NUNCA se inventan políticas, montos, aprobadores ni sistemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.base import EstadoDocumento, FrecuenciaRevision, TipoDocumento


# ---------------------------------------------------------------------------
# Capa SMART — estructura canónica "SMART-1.0"
# ---------------------------------------------------------------------------
class SmartDefinicion(BaseModel):
    termino: str
    definicion: str


class SmartRaci(BaseModel):
    """§6 + apéndice D. Matriz RACI por actividad."""

    actividad: str
    responsible: str = ""
    accountable: str = ""
    consulted: str = ""
    informed: str = ""


class SmartPaso(BaseModel):
    """§10. Paso auditable del procedimiento."""

    paso: int
    nombre: str = ""
    responsable: str = ""
    accion: str = ""
    sistema_documento: str = ""
    evidencia: str = ""
    control: str = ""


class SmartEvidencia(BaseModel):
    """§11 + apéndice E (documentos)."""

    evidencia: str
    responsable: str = ""
    revisor: str = ""
    archivo: str = ""
    retencion: str = ""


class SmartControl(BaseModel):
    """§12 + apéndice C. Control clave."""

    control: str
    riesgo: str = ""
    responsable: str = ""
    frecuencia: str = ""
    evidencia: str = ""
    accion_correctiva: str = ""


class SmartKpi(BaseModel):
    """§13. Indicador; `recomendado=True` cuando no existía en el SOP original."""

    indicador: str
    meta: str = ""
    recomendado: bool = False


class SmartExcepcion(BaseModel):
    """§15. Excepción y escalamiento."""

    excepcion: str
    responsable_escalar: str = ""
    aprobador: str = ""
    evidencia: str = ""
    tiempo_maximo: str = ""


class SmartVersion(BaseModel):
    """§18. Fila de control de versiones."""

    version: str
    fecha: str = ""
    preparado_por: str = ""
    revisado_por: str = ""
    aprobado_por: str = ""
    cambios: str = ""
    proxima_revision: str = ""


class SmartDocumento(BaseModel):
    """§9 + apéndice E. Documento/reporte/formato relacionado."""

    documento: str
    responsable: str = ""
    frecuencia: str = ""
    ubicacion: str = ""
    retencion: str = ""


class SmartChecklist(BaseModel):
    """Apéndice B. Punto de control de cumplimiento."""

    n: int
    punto: str
    cumplido: str = ""
    comentarios: str = ""


class SopSmart(BaseModel):
    """Documento SMART completo. §1 (código) y §2 (nombre) viven en las columnas del SOP."""

    formato: str = "SMART-1.0"
    objetivo: str = ""  # §3
    alcance: str = ""  # §4
    definiciones: list[SmartDefinicion] = []  # §5
    raci: list[SmartRaci] = []  # §6 (+ apéndice D)
    frecuencia_deadlines: str = ""  # §7
    sistemas: list[str] = []  # §8 (narrativo; los enlaces estructurados van en sistemas_codigos)
    documentos_relacionados: list[SmartDocumento] = []  # §9 (+ apéndice E)
    procedimiento: list[SmartPaso] = []  # §10
    evidencia_requerida: list[SmartEvidencia] = []  # §11
    controles_clave: list[SmartControl] = []  # §12 (+ apéndice C)
    kpis: list[SmartKpi] = []  # §13
    riesgos_mitigados: list[str] = []  # §14
    excepciones: list[SmartExcepcion] = []  # §15
    archivo_retencion: str = ""  # §16
    entrenamiento: str = ""  # §17
    control_versiones: list[SmartVersion] = []  # §18
    resumen_ejecutivo: str = ""  # apéndice A
    checklist: list[SmartChecklist] = []  # apéndice B
    pendiente_confirmar: list[str] = []  # apéndice F


class DepartamentoMini(BaseModel):
    id: uuid.UUID
    codigo: str
    nombre: str


class PuestoMini(BaseModel):
    id: uuid.UUID
    codigo: str
    titulo: str


class SopCrear(BaseModel):
    area_codigo: str = Field(..., description="Prefijo del área, ej. FIN")
    tipo: TipoDocumento = TipoDocumento.sop
    nombre: str
    departamento_id: uuid.UUID | None = None
    # 9 campos (opcionales al crear; se completan en la colaboración)
    proposito: str | None = None
    evaluacion_riesgos: str | None = None
    controles_existentes: str | None = None
    procedimiento: dict | None = None
    responsables: str | None = None
    evidencia: str | None = None
    frecuencia_revision: FrecuenciaRevision | None = None
    smart: SopSmart | None = None
    sistemas_codigos: list[str] = []
    # Departamentos que impacta además del dueño, y puestos responsables directos.
    departamentos_afectados_ids: list[uuid.UUID] = []
    puestos_responsables_ids: list[uuid.UUID] = []


class SopActualizar(BaseModel):
    """Actualización de contenido (no cambia área/numero/codigo/estado).

    `departamentos_afectados_ids`/`puestos_responsables_ids`: si se envían, reemplazan
    la lista completa (no es incremental); omitirlos deja la lista actual intacta."""

    nombre: str | None = None
    departamento_id: uuid.UUID | None = None
    proposito: str | None = None
    evaluacion_riesgos: str | None = None
    controles_existentes: str | None = None
    procedimiento: dict | None = None
    responsables: str | None = None
    evidencia: str | None = None
    frecuencia_revision: FrecuenciaRevision | None = None
    smart: SopSmart | None = None
    departamentos_afectados_ids: list[uuid.UUID] | None = None
    puestos_responsables_ids: list[uuid.UUID] | None = None


class SopSmartActualizar(BaseModel):
    """Body de `PUT /api/sops/{id}/smart`: persiste la capa SMART reformateada.

    `nota_cambio` alimenta el snapshot de versión (auditoría / rollback).

    `base_actualizado_en` es el sello de concurrencia optimista: el `actualizado_en`
    que traía el SOP cuando se abrió el editor. Si en el medio otro usuario guardó,
    el sello ya no coincide y la escritura se rechaza con 409 en vez de pisarlo.
    Omitirlo salta el control (lo usan los scripts de migración)."""

    smart: SopSmart
    nota_cambio: str = "Reformateo al estándar SOP SMART (SMART-1.0)"
    base_actualizado_en: datetime | None = None


class SopVersionItem(BaseModel):
    """Fila del historial: una por guardado. El snapshot completo va en el detalle."""

    id: uuid.UUID
    version: int
    nota_cambio: str | None = None
    estado_en_version: str | None = None
    creado_en: datetime
    creado_por: uuid.UUID | None = None
    creado_por_nombre: str | None = None
    tiene_smart: bool = False


class SopVersionDetalle(SopVersionItem):
    snapshot: dict


class SopItem(BaseModel):
    id: uuid.UUID
    codigo: str
    numero: int
    area_codigo: str
    tipo: TipoDocumento
    nombre: str
    estado: EstadoDocumento
    version_actual: int
    departamento_id: uuid.UUID | None = None
    # NOTA: la marca interna `origen_propiedad` NO se expone aquí a propósito (es una
    # huella invisible para el despliegue; solo se consulta vía el filtro del listado).
    # Presente solo cuando se filtra/agrupa por departamento (vista "por Departamento");
    # None en la vista "por Área".
    relacion_departamento: str | None = None  # 'propio' | 'afecta' | 'ambos'


class SopDetalle(SopItem):
    proposito: str | None = None
    evaluacion_riesgos: str | None = None
    controles_existentes: str | None = None
    procedimiento: dict | None = None
    responsables: str | None = None
    evidencia: str | None = None
    frecuencia_revision: FrecuenciaRevision | None = None
    smart: SopSmart | None = None
    sistemas_codigos: list[str] = []
    departamentos_afectados: list[DepartamentoMini] = []
    puestos_responsables: list[PuestoMini] = []
    creado_en: datetime
    actualizado_en: datetime


class SopLista(BaseModel):
    total: int
    items: list[SopItem]
