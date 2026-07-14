// Tipos del dominio, espejo de los schemas del backend (§5, §8).

export type EstadoDocumento =
  | "borrador"
  | "en_revision"
  | "en_firma"
  | "firmado"
  | "rechazado"
  | "archivado";

export type TipoDocumento = "sop" | "politica";

export interface RolOut {
  rol: string;
  propiedad_id: string | null;
}

export interface Me {
  id: string;
  nombre: string;
  email: string;
  nivel_jerarquico: number;
  activo: boolean;
  roles: RolOut[];
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type RelacionDepartamento = "propio" | "afecta" | "ambos";

export interface DepartamentoMini {
  id: string;
  codigo: string;
  nombre: string;
}

export interface PuestoMini {
  id: string;
  codigo: string;
  titulo: string;
}

export interface SopItem {
  id: string;
  codigo: string;
  numero: number;
  area_codigo: string;
  tipo: TipoDocumento;
  nombre: string;
  estado: EstadoDocumento;
  version_actual: number;
  departamento_id: string | null;
  // Solo presente en la vista "por Departamento" (departamento_relacionado_id).
  relacion_departamento: RelacionDepartamento | null;
}

// --- Capa SMART (estándar "SOP SMART": 18 secciones + apéndices A–F) ---
export interface SmartDefinicion {
  termino: string;
  definicion: string;
}
export interface SmartRaci {
  actividad: string;
  responsible: string;
  accountable: string;
  consulted: string;
  informed: string;
}
export interface SmartPaso {
  paso: number;
  nombre: string;
  responsable: string;
  accion: string;
  sistema_documento: string;
  evidencia: string;
  control: string;
}
export interface SmartEvidencia {
  evidencia: string;
  responsable: string;
  revisor: string;
  archivo: string;
  retencion: string;
}
export interface SmartControl {
  control: string;
  riesgo: string;
  responsable: string;
  frecuencia: string;
  evidencia: string;
  accion_correctiva: string;
}
export interface SmartKpi {
  indicador: string;
  meta: string;
  recomendado: boolean;
}
export interface SmartExcepcion {
  excepcion: string;
  responsable_escalar: string;
  aprobador: string;
  evidencia: string;
  tiempo_maximo: string;
}
export interface SmartVersion {
  version: string;
  fecha: string;
  preparado_por: string;
  revisado_por: string;
  aprobado_por: string;
  cambios: string;
  proxima_revision: string;
}
export interface SmartDocumento {
  documento: string;
  responsable: string;
  frecuencia: string;
  ubicacion: string;
  retencion: string;
}
export interface SmartChecklist {
  n: number;
  punto: string;
  cumplido: string;
  comentarios: string;
}
export interface SopSmart {
  formato: string;
  objetivo: string;
  alcance: string;
  definiciones: SmartDefinicion[];
  raci: SmartRaci[];
  frecuencia_deadlines: string;
  sistemas: string[];
  documentos_relacionados: SmartDocumento[];
  procedimiento: SmartPaso[];
  evidencia_requerida: SmartEvidencia[];
  controles_clave: SmartControl[];
  kpis: SmartKpi[];
  riesgos_mitigados: string[];
  excepciones: SmartExcepcion[];
  archivo_retencion: string;
  entrenamiento: string;
  control_versiones: SmartVersion[];
  resumen_ejecutivo: string;
  checklist: SmartChecklist[];
  pendiente_confirmar: string[];
}

export interface ColaboradorOut {
  id: string;
  usuario_id: string;
  usuario_nombre: string | null;
  rol_colaboracion: string;
  seccion_asignada: string | null;
  estado: string;
}

export interface SopVersionItem {
  id: string;
  version: number;
  nota_cambio: string | null;
  estado_en_version: string | null;
  creado_en: string;
  creado_por: string | null;
  creado_por_nombre: string | null;
  tiene_smart: boolean;
}

export interface SopDetalle extends SopItem {
  proposito: string | null;
  evaluacion_riesgos: string | null;
  controles_existentes: string | null;
  procedimiento: unknown;
  responsables: string | null;
  evidencia: string | null;
  frecuencia_revision: string | null;
  smart: SopSmart | null;
  sistemas_codigos: string[];
  departamentos_afectados: DepartamentoMini[];
  puestos_responsables: PuestoMini[];
  creado_en: string;
  actualizado_en: string;
}

export interface SopLista {
  total: number;
  items: SopItem[];
}

export interface DescriptorItem {
  id: string;
  codigo: string;
  titulo: string;
  nivel_jerarquico: number;
  categoria: string | null;
  estado: EstadoDocumento;
  version_actual: number;
  departamento_id: string | null;
  reporta_a_id: string | null;
}

export interface JdSmart {
  formato?: string;
  departamento?: string;
  reporta_a?: string;
  supervisa?: string[];
  resumen_puesto?: string;
  objetivo?: string;
  resumen_ejecutivo?: string;
  responsabilidades_smart?: {
    n?: number; responsabilidad?: string; sop_relacionado?: string; rol_sop?: string;
    frecuencia?: string; evidencia?: string; kpi?: string;
  }[];
  funciones?: { diarias?: string[]; semanales?: string[]; mensuales?: string[]; por_evento?: string[] };
  sops_relacionados?: {
    codigo_sop?: string; nombre_sop?: string; depto_sop?: string; relacion?: string;
    rol?: string; frecuencia?: string; evidencia?: string; estado?: string;
  }[];
  sops_recomendados?: {
    responsabilidad_sin_sop?: string; sop_recomendado?: string; justificacion?: string;
    prioridad?: string; depto?: string;
  }[];
  kpis?: {
    kpi?: string; definicion?: string; frecuencia?: string; fuente?: string;
    meta?: string; responsable?: string; recomendado?: boolean;
  }[];
  autoridad?: { tipo_decision?: string; puede_aprobar?: string; debe_consultar?: string; debe_escalar?: string }[];
  relaciones_internas?: { area_puesto?: string; motivo?: string; frecuencia?: string }[];
  relaciones_externas?: string[];
  sistemas?: { sistema?: string; uso?: string; frecuencia?: string; sop_relacionado?: string }[];
  documentos?: {
    documento?: string; responsable?: string; frecuencia?: string; revisor?: string;
    ubicacion?: string; sop_relacionado?: string;
  }[];
  competencias_tecnicas?: string[];
  competencias_conductuales?: string[];
  experiencia_formacion?: string;
  cumplimiento_confidencialidad?: string[];
  estandares_servicio?: string[];
  horario_condiciones?: string;
  perfil_exito?: string;
  ciclo_revision?: string;
  control_versiones?: {
    version?: string; fecha?: string; preparado_por?: string; revisado_por?: string;
    aprobado_por?: string; cambios?: string; proxima_revision?: string;
  }[];
  checklist?: { n?: number; punto?: string; cumplido?: string; comentarios?: string }[];
  pendiente_confirmar?: string[];
}

export interface DescriptorDetalle extends DescriptorItem {
  departamento_codigo: string | null;
  reporta_a_codigo: string | null;
  proposito: string | null;
  responsabilidades: string[] | null;
  nivel_autoridad: string | null;
  kpis: string[] | null;
  requisitos: string | null;
  smart: JdSmart | null;
  creado_en: string;
  actualizado_en: string;
}

export interface DescriptorLista {
  total: number;
  items: DescriptorItem[];
}

export interface NodoOrganigrama {
  id: string;
  codigo: string;
  titulo: string;
  nivel_jerarquico: number;
  categoria: string | null;
  estado: string;
  departamento_id: string | null;
  departamento_codigo: string | null;
  hijos: NodoOrganigrama[];
}

export interface ResultadoBusqueda {
  entidad: string; // 'sop' | 'politica' | 'descriptor'
  id: string;
  codigo: string;
  titulo: string;
  estado: EstadoDocumento;
  area_codigo: string | null;
  departamento_id: string | null;
}

export interface BusquedaLista {
  total: number;
  items: ResultadoBusqueda[];
}

export interface FirmanteOut {
  id: string;
  usuario_id: string;
  orden: number;
  obligatorio: boolean;
  firmado: boolean;
}

export interface RolAsignar {
  rol: string;
  propiedad_id: string | null;
}

export interface UsuarioListItem {
  id: string;
  nombre: string;
  email: string;
  nivel_jerarquico: number;
  activo: boolean;
  roles: RolAsignar[];
}

export interface DocumentoControladoOut {
  id: string;
  sop_master_id: string;
  version: number;
  hash_pdf: string | null;
  fecha_firma: string | null;
  es_vigente: boolean;
}

export interface TrainingSeccion {
  id: string;
  training_manual_id: string;
  titulo: string;
  contenido: string | null;
  orden: number;
  creado_en: string;
  actualizado_en: string;
}

export interface TrainingManualItem {
  id: string;
  titulo: string;
  departamento_id: string | null;
  departamento_codigo: string | null;
  descripcion: string | null;
  total_secciones: number;
  creado_en: string;
  actualizado_en: string;
}

// Adopción/adaptación de un manual por propiedad (Etapa C)
export interface PropiedadTrainingItem {
  id: string;
  propiedad_id: string;
  training_manual_id: string | null;
  modo: ModoAsignacion;
  titulo: string;
  titulo_local: string | null;
  estado: EstadoAsignacion;
  creado_en: string;
}

export interface PropiedadTrainingDetalle extends PropiedadTrainingItem {
  smart_efectivo: Record<string, unknown>;
  smart_master: Record<string, unknown>;
  smart_overrides: Record<string, unknown> | null;
}

export interface TrainingSmart {
  formato?: string;
  objetivo?: string;
  modalidad?: string;
  duracion?: string;
  dirigido_a?: string[];
  imparte?: string;
  prerequisitos?: string[];
  contenidos?: { n?: number; tema?: string; descripcion?: string; material_ref?: string }[];
  materiales?: { material?: string; tipo?: string; referencia?: string }[];
  evaluacion?: { metodo?: string; criterio_aprobacion?: string; nota_minima?: string }[];
  evidencia?: { evidencia?: string; responsable?: string; archivo?: string; retencion?: string }[];
  vigencia?: {
    vigencia_meses?: string;
    requiere_recertificacion?: boolean;
    condiciones_recert?: string;
  };
  obligatoria?: boolean;
  base_obligatoriedad?: string;
  kpis?: { indicador?: string; meta?: string; recomendado?: boolean }[];
  control_versiones?: {
    version?: string; fecha?: string; preparado_por?: string; revisado_por?: string;
    aprobado_por?: string; cambios?: string; proxima_revision?: string;
  }[];
  resumen_ejecutivo?: string;
  pendiente_confirmar?: string[];
}

export interface TrainingManualDetalle extends TrainingManualItem {
  secciones: TrainingSeccion[];
  smart?: TrainingSmart | null;
  tiene_smart?: boolean;
}

export interface Area {
  id: string;
  codigo: string;
  nombre: string;
}

export interface Propiedad {
  id: string;
  codigo: string;
  nombre: string;
}

export interface Departamento {
  id: string;
  codigo: string;
  nombre: string;
  propiedad_propietaria_id: string | null;
  division_id: string | null;
}

export interface Division {
  id: string;
  codigo: string;
  nombre: string;
  parent_id: string | null; // null = división raíz; con valor = subdivisión
  orden: number;
}

export interface RegistroAuditoria {
  id: string;
  usuario_id: string | null;
  entidad: string;
  entidad_id: string | null;
  accion: string;
  detalle: Record<string, unknown> | null;
  ip: string | null;
  creado_en: string;
}

export interface AuditoriaLista {
  total: number;
  items: RegistroAuditoria[];
}

export interface DocumentoControladoItem {
  id: string;
  sop_master_id: string;
  sop_codigo: string | null;
  sop_nombre: string | null;
  version: number;
  hash_pdf: string | null;
  fecha_firma: string | null;
  es_vigente: boolean;
  custodio_id: string | null;
  creado_en: string;
}

export interface DocumentoControladoLista {
  total: number;
  items: DocumentoControladoItem[];
}

export interface BitacoraControlOut {
  id: string;
  documento_controlado_id: string;
  accion: string;
  detalle: Record<string, unknown> | null;
  usuario_id: string | null;
  creado_en: string;
}

export interface VerificacionIntegridad {
  documento_controlado_id: string;
  integro: boolean;
  hash_esperado: string | null;
  hash_actual: string | null;
  mensaje: string;
}

export interface Sistema {
  id: string;
  codigo: string;
  nombre: string;
  categoria: string | null;
}

// --- Programación / Calendario ---

export type TipoRecurrencia =
  | "unica"
  | "diaria"
  | "semanal"
  | "quincenal"
  | "mensual"
  | "trimestral"
  | "anual";

export interface ProgramacionSop {
  id: string;
  sop_master_id: string;
  titulo: string;
  descripcion: string | null;
  tipo_recurrencia: TipoRecurrencia;
  fecha: string; // fecha de ejecución (ancla)
  hora: string | null;
  fecha_fin: string | null;
  responsable_puesto_id: string | null;
  responsable_texto: string | null;
  responsable_puesto_titulo: string | null;
  activo: boolean;
  orden: number;
}

export interface EventoCalendario {
  programacion_id: string;
  sop_id: string;
  sop_codigo: string;
  sop_nombre: string;
  titulo: string;
  descripcion: string | null;
  fecha: string;
  hora: string | null;
  dia_completo: boolean;
  responsable: string | null;
}

export interface CalendarioOut {
  desde: string;
  hasta: string;
  total: number;
  eventos: EventoCalendario[];
}

// --- Armador por propiedad ---

export type ModoAsignacion = "adoptado" | "adaptado" | "local" | "no_aplica";

export type EstadoAsignacion =
  | "borrador"
  | "en_revision"
  | "en_firma"
  | "vigente"
  | "rechazado"
  | "archivado";

export interface PropiedadResumen {
  id: string;
  codigo: string;
  nombre: string;
  activo: boolean;
  departamentos: number;
  puestos: number;
  ocupantes: number;
  sops: number;
  sistemas: number;
}

export interface DepartamentoAsignado {
  id: string;
  codigo: string;
  nombre: string;
  division_id: string | null;
}

export interface SistemaAsignado {
  id: string;
  codigo: string;
  nombre: string;
  categoria: string | null;
}

export interface OcupanteArmador {
  id: string;
  usuario_id: string;
  usuario_nombre: string;
  usuario_email: string;
  es_principal: boolean;
  nota: string | null;
}

export interface PuestoArmador {
  id: string;
  propiedad_id: string;
  descriptor_puesto_master_id: string | null;
  modo: ModoAsignacion;
  titulo: string;
  codigo: string | null;
  nivel_jerarquico: number;
  categoria: string | null;
  departamento_id: string | null;
  departamento_codigo: string | null;
  reporta_a_id: string | null;
  dotacion: number | null;
  estado: EstadoAsignacion;
  requiere_actualizacion: boolean;
  ocupantes_count: number;
}

export interface PuestoArmadorDetalle extends PuestoArmador {
  contenido_efectivo: Record<string, unknown>;
  ocupantes: OcupanteArmador[];
  creado_en: string;
  // Capa JD SMART por propiedad (Etapa B)
  smart_efectivo: Record<string, unknown>;
  smart_master: Record<string, unknown>;
  smart_overrides: Record<string, unknown> | null;
}

export interface SembrarResultado {
  creados: number;
  omitidos: number;
}

// SOPs por propiedad (motor adoptar/adaptar/local existente)

export interface PropiedadSopOut {
  id: string;
  propiedad_id: string;
  sop_master_id: string | null;
  modo: ModoAsignacion;
  version_fijada: number | null;
  codigo_local: string | null;
  estado: EstadoAsignacion;
  requiere_actualizacion: boolean;
  master_retirado: boolean;
  creado_en: string;
}

export interface SugerenciaSop {
  sop_master_id: string;
  codigo: string;
  nombre: string;
  sugerencia: ModoAsignacion;
  sistemas_faltantes: string[];
  motivo: string;
}

// --- Laboratorio de intake ---

export interface SimilarIntake {
  id: string;
  codigo: string;
  nombre: string;
  area_codigo: string;
  estado: string;
  score: number;
}

export interface TriageIntake {
  verdict: "posible_duplicado" | "nuevo";
  umbral: number;
  similares: SimilarIntake[];
}

export interface ExtraerIntake {
  nombre: string;
  texto: string;
}

export interface PropiedadSopDetalle extends PropiedadSopOut {
  contenido_efectivo: Record<string, unknown>; // lo que se lee (master + overrides)
  contenido_master: Record<string, unknown>; // snapshot del master (para restaurar)
  overrides: Record<string, unknown> | null; // qué secciones base son locales (adaptado)
  campos_locales: Record<string, unknown> | null; // contenido de un SOP local
  // Capa SMART por propiedad (Etapa A)
  smart_efectivo: Record<string, unknown>; // SMART efectiva (master ∪ smart_overrides)
  smart_master: Record<string, unknown>; // SMART del master (para heredar/restaurar)
  smart_overrides: Record<string, unknown> | null; // qué secciones SMART son locales
}
