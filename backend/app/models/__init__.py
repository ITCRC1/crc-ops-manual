"""Registro central de modelos. Importar todo aquí para que Base.metadata los conozca."""

from app.models.auditoria import Adjunto, BitacoraControl, RegistroAuditoria
from app.models.catalogos import (
    Area,
    ContadorArea,
    ContadorDescriptor,
    ContadorLocal,
    Departamento,
    Division,
    Propiedad,
    PropiedadDepartamento,
    PropiedadSistema,
    Sistema,
)
from app.models.config import Configuracion, MarcoInstitucional
from app.models.propiedad import (
    PropiedadPuesto,
    PropiedadPuestoOcupante,
    PropiedadSop,
    PropiedadSopBitacora,
    PropiedadTrainingManual,
)
from app.models.puesto import DescriptorPuestoMaster, DescriptorPuestoVersion
from app.models.sop import (
    ColaboradorSop,
    DocumentoControlado,
    FirmaElectronica,
    FirmanteSop,
    ProgramacionSop,
    SopMaster,
    SopMasterDepartamentoAfectado,
    SopMasterPuestoResponsable,
    SopMasterSistema,
    SopMasterVersion,
)
from app.models.training import TrainingManual, TrainingSeccion
from app.models.usuarios import RolUsuarioAsignado, Usuario

__all__ = [
    "Adjunto",
    "Area",
    "BitacoraControl",
    "ColaboradorSop",
    "Configuracion",
    "ContadorArea",
    "ContadorDescriptor",
    "ContadorLocal",
    "Departamento",
    "DescriptorPuestoMaster",
    "DescriptorPuestoVersion",
    "Division",
    "DocumentoControlado",
    "FirmaElectronica",
    "FirmanteSop",
    "MarcoInstitucional",
    "Propiedad",
    "PropiedadDepartamento",
    "PropiedadPuesto",
    "PropiedadPuestoOcupante",
    "PropiedadSistema",
    "PropiedadSop",
    "PropiedadSopBitacora",
    "PropiedadTrainingManual",
    "ProgramacionSop",
    "RegistroAuditoria",
    "RolUsuarioAsignado",
    "Sistema",
    "SopMaster",
    "SopMasterDepartamentoAfectado",
    "SopMasterPuestoResponsable",
    "SopMasterSistema",
    "SopMasterVersion",
    "TrainingManual",
    "TrainingSeccion",
    "Usuario",
]
