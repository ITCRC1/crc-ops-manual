// Hooks de datos (React Query) sobre el cliente `api`.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, apiUpload, qs } from "./api";
import type {
  Area,
  AuditoriaLista,
  BitacoraControlOut,
  BusquedaLista,
  CalendarioOut,
  ColaboradorOut,
  Departamento,
  DepartamentoAsignado,
  DescriptorDetalle,
  JdSmart,
  DescriptorLista,
  Division,
  DocumentoControladoLista,
  DocumentoControladoOut,
  ExtraerIntake,
  FirmanteOut,
  NodoOrganigrama,
  OcupanteArmador,
  ProgramacionSop,
  Propiedad,
  PropiedadResumen,
  PropiedadSopDetalle,
  PropiedadSopOut,
  PuestoArmador,
  PuestoArmadorDetalle,
  SembrarResultado,
  Sistema,
  SistemaAsignado,
  SopDetalle,
  PropiedadTrainingDetalle,
  PropiedadTrainingItem,
  SopItem,
  SopLista,
  SopSmart,
  SopVersionItem,
  SugerenciaSop,
  TriageIntake,
  TrainingManualDetalle,
  TrainingManualItem,
  TrainingSmart,
  UsuarioListItem,
  VerificacionIntegridad,
} from "./types";

export interface SopFiltros {
  area?: string;
  departamento_id?: string;
  departamento_relacionado_id?: string;
  estado?: string;
  tipo?: string;
  sistema?: string;
  origen_propiedad?: string; // curaduría: SOPs marcados con origen de una propiedad (ej. AMA)
  q?: string;
  limit?: number;
  offset?: number;
}

export function useSops(filtros: SopFiltros, enabled = true) {
  return useQuery({
    queryKey: ["sops", filtros],
    queryFn: () => api<SopLista>(`/api/sops${qs({ ...filtros })}`),
    enabled,
  });
}

export function useSop(id: string | undefined) {
  return useQuery({
    queryKey: ["sop", id],
    queryFn: () => api<SopDetalle>(`/api/sops/${id}`),
    enabled: !!id,
  });
}

export interface DescriptorFiltros {
  departamento_id?: string;
  nivel_jerarquico?: number;
  categoria?: string;
  estado?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export function useDescriptores(filtros: DescriptorFiltros) {
  return useQuery({
    queryKey: ["descriptores", filtros],
    queryFn: () => api<DescriptorLista>(`/api/descriptores${qs({ ...filtros })}`),
  });
}

export function useDescriptor(id: string | undefined) {
  return useQuery({
    queryKey: ["descriptor", id],
    queryFn: () => api<DescriptorDetalle>(`/api/descriptores/${id}`),
    enabled: !!id,
  });
}

// Persiste la capa JD SMART (aditiva). No toca los campos base ni el estado.
export function useActualizarDescriptorSmart(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { smart: JdSmart }) =>
      api<DescriptorDetalle>(`/api/descriptores/${id}/smart`, { method: "PUT", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["descriptor", id] });
      qc.invalidateQueries({ queryKey: ["descriptores"] });
    },
  });
}

export function useCrearDescriptor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) =>
      api<DescriptorDetalle>("/api/descriptores", { method: "POST", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["descriptores"] });
      qc.invalidateQueries({ queryKey: ["organigrama"] });
    },
  });
}

export function useActualizarDescriptor(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) =>
      api<DescriptorDetalle>(`/api/descriptores/${id}`, { method: "PUT", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["descriptor", id] });
      qc.invalidateQueries({ queryKey: ["descriptores"] });
      qc.invalidateQueries({ queryKey: ["organigrama"] });
    },
  });
}

export function useEliminarDescriptor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api(`/api/descriptores/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["descriptores"] });
      qc.invalidateQueries({ queryKey: ["organigrama"] });
    },
  });
}

export function useOrganigrama(departamentoId?: string) {
  return useQuery({
    queryKey: ["organigrama", departamentoId ?? null],
    queryFn: () =>
      api<NodoOrganigrama[]>(`/api/organigrama${qs({ departamento_id: departamentoId })}`),
  });
}

export function useBusqueda(params: {
  q: string;
  entidad?: string;
  area?: string;
  departamento_id?: string;
  estado?: string;
}) {
  return useQuery({
    queryKey: ["busqueda", params],
    queryFn: () => api<BusquedaLista>(`/api/busqueda${qs({ ...params, limit: 200 })}`),
    enabled: params.q.trim().length > 0,
  });
}

export function useAreas() {
  return useQuery({
    queryKey: ["catalogo", "areas"],
    queryFn: () => api<Area[]>("/api/catalogos/areas"),
    staleTime: 5 * 60 * 1000,
  });
}

export function usePropiedades() {
  return useQuery({
    queryKey: ["catalogo", "propiedades"],
    queryFn: () => api<Propiedad[]>("/api/catalogos/propiedades"),
    staleTime: 5 * 60 * 1000,
  });
}

export function useDepartamentos() {
  return useQuery({
    queryKey: ["catalogo", "departamentos"],
    queryFn: () => api<Departamento[]>("/api/catalogos/departamentos"),
    staleTime: 5 * 60 * 1000,
  });
}

export function useDivisiones() {
  return useQuery({
    queryKey: ["catalogo", "divisiones"],
    queryFn: () => api<Division[]>("/api/catalogos/divisiones"),
    staleTime: 5 * 60 * 1000,
  });
}

export function useSistemas() {
  return useQuery({
    queryKey: ["catalogo", "sistemas"],
    queryFn: () => api<Sistema[]>("/api/catalogos/sistemas"),
    staleTime: 5 * 60 * 1000,
  });
}

// --- Usuarios (§8.2) ---

export function useUsuarios(params: { elegibles_firmante?: boolean; q?: string } = {}) {
  return useQuery({
    queryKey: ["usuarios", params],
    queryFn: () => api<UsuarioListItem[]>(`/api/usuarios${qs({ ...params })}`),
  });
}

export function useCrearUsuario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) => api<UsuarioListItem>("/api/usuarios", { method: "POST", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["usuarios"] }),
  });
}

export function useActualizarUsuario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { id: string; body: unknown }) =>
      api<UsuarioListItem>(`/api/usuarios/${vars.id}`, { method: "PATCH", body: vars.body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["usuarios"] }),
  });
}

// Centro de firmas: cola de firma del usuario actual
export function usePendientesFirma() {
  return useQuery({
    queryKey: ["pendientes-firma"],
    queryFn: () => api<SopItem[]>("/api/sops/pendientes-firma"),
  });
}

// --- Escritura de SOPs (E5) ---

export function useCrearSop() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) => api<SopDetalle>("/api/sops", { method: "POST", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sops"] }),
  });
}

export function useActualizarSop(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) => api<SopDetalle>(`/api/sops/${id}`, { method: "PUT", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sop", id] });
      qc.invalidateQueries({ queryKey: ["sops"] });
    },
  });
}

// Capa SMART. El endpoint escribe además un snapshot de versión (auditoría/rollback)
// y responde 409 si el SOP está firmado, o si otro usuario guardó después de que se
// abriera el editor (`base_actualizado_en` = sello de concurrencia optimista).
export function useActualizarSmart(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      smart: SopSmart;
      nota_cambio?: string;
      base_actualizado_en?: string;
    }) => api<SopDetalle>(`/api/sops/${id}/smart`, { method: "PUT", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sop", id] });
      qc.invalidateQueries({ queryKey: ["sops"] });
    },
  });
}

// Historial de snapshots: uno por guardado. Es la base del rollback.
export function useVersiones(id: string, enabled = true) {
  return useQuery({
    queryKey: ["versiones", id],
    queryFn: () => api<SopVersionItem[]>(`/api/sops/${id}/versiones`),
    enabled,
  });
}

export function useRestaurarSmart(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (versionId: string) =>
      api<SopDetalle>(`/api/sops/${id}/versiones/${versionId}/restaurar-smart`, {
        method: "POST",
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sop", id] });
      qc.invalidateQueries({ queryKey: ["versiones", id] });
      qc.invalidateQueries({ queryKey: ["sops"] });
    },
  });
}

// Transiciones de estado y nueva versión: POST /api/sops/{id}/{accion}
export function useAccionSop(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (accion: string) => api(`/api/sops/${id}/${accion}`, { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sop", id] });
      qc.invalidateQueries({ queryKey: ["sops"] });
      qc.invalidateQueries({ queryKey: ["firmantes", id] });
    },
  });
}

export function useFirmantes(id: string, enabled = true) {
  return useQuery({
    queryKey: ["firmantes", id],
    queryFn: () => api<FirmanteOut[]>(`/api/sops/${id}/firmantes`),
    enabled,
  });
}

export function useDesignarFirmante(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { usuario_id: string; orden: number; obligatorio: boolean }) =>
      api(`/api/sops/${id}/firmantes`, { method: "POST", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["firmantes", id] }),
  });
}

export function useReasignarFirmante(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { firmante_id: string; nuevo_usuario_id: string }) =>
      api(`/api/sops/${id}/firmantes/${vars.firmante_id}/reasignar`, {
        method: "POST",
        body: { nuevo_usuario_id: vars.nuevo_usuario_id },
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["firmantes", id] }),
  });
}

export function useInvitarColaborador(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { usuario_id: string; rol_colaboracion: string; seccion_asignada?: string }) =>
      api(`/api/sops/${id}/colaboradores`, { method: "POST", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["colaboradores", id] }),
  });
}

// Un colaborador `redactor` puede editar la capa SMART de ese SOP. La ficha lo consulta
// para decidir si muestra el botón; el backend lo vuelve a verificar al guardar.
export function useColaboradores(id: string) {
  return useQuery({
    queryKey: ["colaboradores", id],
    queryFn: () => api<ColaboradorOut[]>(`/api/sops/${id}/colaboradores`),
  });
}

export function useRevocarColaborador(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (colaboradorId: string) =>
      api(`/api/sops/${id}/colaboradores/${colaboradorId}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["colaboradores", id] }),
  });
}

export function useInvitarColaboradoresLote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { sop_ids: string[]; usuario_ids: string[]; rol_colaboracion?: string }) =>
      api<{ creados: number; ya_existian: number }>("/api/sops/colaboradores/lote", {
        method: "POST",
        body,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["colaboradores"] }),
  });
}

export function useFirmar(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { metodo: string }) => api(`/api/sops/${id}/firmar`, { method: "POST", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sop", id] });
      qc.invalidateQueries({ queryKey: ["firmantes", id] });
      qc.invalidateQueries({ queryKey: ["documento-controlado", id] });
    },
  });
}

export function useRechazar(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { comentario: string }) =>
      api(`/api/sops/${id}/rechazar`, { method: "POST", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sop", id] });
      qc.invalidateQueries({ queryKey: ["firmantes", id] });
    },
  });
}

export function useDocumentoControlado(id: string, enabled: boolean) {
  return useQuery({
    queryKey: ["documento-controlado", id],
    queryFn: () => api<DocumentoControladoOut>(`/api/sops/${id}/documento-controlado`),
    enabled,
    retry: false,
  });
}

// --- Auditoría y custodia (§8.8, §8.18) ---

export interface AuditoriaFiltros {
  entidad?: string;
  accion?: string;
  usuario_id?: string;
  limit?: number;
  offset?: number;
}

export function useAuditoria(filtros: AuditoriaFiltros) {
  return useQuery({
    queryKey: ["auditoria", filtros],
    queryFn: () => api<AuditoriaLista>(`/api/auditoria${qs({ ...filtros })}`),
  });
}

export function useDocumentosControlados(soloVigentes = false) {
  return useQuery({
    queryKey: ["documentos-controlados", soloVigentes],
    queryFn: () =>
      api<DocumentoControladoLista>(
        `/api/documentos-controlados${qs({ solo_vigentes: soloVigentes, limit: 200 })}`,
      ),
  });
}

export function useBitacora(docId: string | null) {
  return useQuery({
    queryKey: ["bitacora", docId],
    queryFn: () => api<BitacoraControlOut[]>(`/api/documentos-controlados/${docId}/bitacora`),
    enabled: !!docId,
  });
}

export function useVerificarIntegridad() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (docId: string) =>
      api<VerificacionIntegridad>(`/api/documentos-controlados/${docId}/verificar-integridad`, {
        method: "POST",
      }),
    onSuccess: (_d, docId) => qc.invalidateQueries({ queryKey: ["bitacora", docId] }),
  });
}

// --- Capacitación / Training (§8) ---

export function useManuales(departamentoId?: string) {
  return useQuery({
    queryKey: ["manuales", departamentoId ?? null],
    queryFn: () =>
      api<TrainingManualItem[]>(`/api/capacitacion/manuales${qs({ departamento_id: departamentoId })}`),
  });
}

export function useManual(id: string | undefined) {
  return useQuery({
    queryKey: ["manual", id],
    queryFn: () => api<TrainingManualDetalle>(`/api/capacitacion/manuales/${id}`),
    enabled: !!id,
  });
}

export function useCrearManual() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) =>
      api<TrainingManualDetalle>("/api/capacitacion/manuales", { method: "POST", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["manuales"] }),
  });
}

export function useActualizarManual(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) =>
      api<TrainingManualDetalle>(`/api/capacitacion/manuales/${id}`, { method: "PUT", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["manual", id] });
      qc.invalidateQueries({ queryKey: ["manuales"] });
    },
  });
}

export function useEliminarManual() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api(`/api/capacitacion/manuales/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["manuales"] }),
  });
}

// Persiste la capa Training SMART (aditiva). No toca las secciones base.
export function useActualizarManualSmart(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { smart: TrainingSmart }) =>
      api<TrainingManualDetalle>(`/api/capacitacion/manuales/${id}/smart`, { method: "PUT", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["manual", id] });
      qc.invalidateQueries({ queryKey: ["manuales"] });
    },
  });
}

export function useCrearSeccion(manualId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { titulo: string; contenido?: string | null }) =>
      api(`/api/capacitacion/manuales/${manualId}/secciones`, { method: "POST", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["manual", manualId] }),
  });
}

export function useActualizarSeccion(manualId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { seccionId: string; titulo?: string; contenido?: string | null }) =>
      api(`/api/capacitacion/manuales/${manualId}/secciones/${vars.seccionId}`, {
        method: "PUT",
        body: { titulo: vars.titulo, contenido: vars.contenido },
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["manual", manualId] }),
  });
}

export function useEliminarSeccion(manualId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (seccionId: string) =>
      api(`/api/capacitacion/manuales/${manualId}/secciones/${seccionId}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["manual", manualId] }),
  });
}

export function useReordenarSecciones(manualId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ordenIds: string[]) =>
      api(`/api/capacitacion/manuales/${manualId}/reordenar`, {
        method: "POST",
        body: { orden_ids: ordenIds },
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["manual", manualId] }),
  });
}

// --- Programación de SOPs + calendario consolidado ---

export function useProgramacion(sopId: string | undefined) {
  return useQuery({
    queryKey: ["programacion", sopId],
    queryFn: () => api<ProgramacionSop[]>(`/api/sops/${sopId}/programacion`),
    enabled: !!sopId,
  });
}

export function useCrearProgramacion(sopId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) =>
      api<ProgramacionSop>(`/api/sops/${sopId}/programacion`, { method: "POST", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["programacion", sopId] });
      qc.invalidateQueries({ queryKey: ["calendario"] });
    },
  });
}

export function useActualizarProgramacion(sopId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { progId: string; body: unknown }) =>
      api<ProgramacionSop>(`/api/sops/${sopId}/programacion/${vars.progId}`, {
        method: "PUT",
        body: vars.body,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["programacion", sopId] });
      qc.invalidateQueries({ queryKey: ["calendario"] });
    },
  });
}

export function useEliminarProgramacion(sopId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (progId: string) =>
      api(`/api/sops/${sopId}/programacion/${progId}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["programacion", sopId] });
      qc.invalidateQueries({ queryKey: ["calendario"] });
    },
  });
}

export interface CalendarioFiltros {
  desde: string;
  hasta: string;
  sop_id?: string;
  area?: string;
  departamento_id?: string;
}

export function useCalendario(filtros: CalendarioFiltros) {
  return useQuery({
    queryKey: ["calendario", filtros],
    queryFn: () => api<CalendarioOut>(`/api/calendario${qs({ ...filtros })}`),
    enabled: !!filtros.desde && !!filtros.hasta,
  });
}

// --- Armador por propiedad ---

export function useResumenPropiedades() {
  return useQuery({
    queryKey: ["armador", "resumen"],
    queryFn: () => api<PropiedadResumen[]>("/api/propiedades/resumen"),
  });
}

// Departamentos por propiedad
export function usePropiedadDepartamentos(propId: string | undefined) {
  return useQuery({
    queryKey: ["armador", "departamentos", propId],
    queryFn: () => api<DepartamentoAsignado[]>(`/api/propiedades/${propId}/departamentos`),
    enabled: !!propId,
  });
}

export function useFijarDepartamentos(propId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (departamento_ids: string[]) =>
      api<DepartamentoAsignado[]>(`/api/propiedades/${propId}/departamentos`, {
        method: "PUT",
        body: { departamento_ids },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["armador", "departamentos", propId] });
      qc.invalidateQueries({ queryKey: ["armador", "resumen"] });
    },
  });
}

// Puestos por propiedad (organigrama local)
export function usePropiedadPuestos(propId: string | undefined) {
  return useQuery({
    queryKey: ["armador", "puestos", propId],
    queryFn: () => api<PuestoArmador[]>(`/api/propiedades/${propId}/puestos`),
    enabled: !!propId,
  });
}

export function usePropiedadPuesto(propId: string, ppId: string | undefined) {
  return useQuery({
    queryKey: ["armador", "puesto", propId, ppId],
    queryFn: () => api<PuestoArmadorDetalle>(`/api/propiedades/${propId}/puestos/${ppId}`),
    enabled: !!ppId,
  });
}

function invalidarPuestos(qc: ReturnType<typeof useQueryClient>, propId: string) {
  qc.invalidateQueries({ queryKey: ["armador", "puestos", propId] });
  qc.invalidateQueries({ queryKey: ["armador", "resumen"] });
}

export function useCrearPuesto(propId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) =>
      api<PuestoArmador>(`/api/propiedades/${propId}/puestos`, { method: "POST", body }),
    onSuccess: () => invalidarPuestos(qc, propId),
  });
}

export function useActualizarPuesto(propId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { ppId: string; body: unknown }) =>
      api<PuestoArmadorDetalle>(`/api/propiedades/${propId}/puestos/${vars.ppId}`, {
        method: "PUT",
        body: vars.body,
      }),
    onSuccess: (_d, vars) => {
      invalidarPuestos(qc, propId);
      qc.invalidateQueries({ queryKey: ["armador", "puesto", propId, vars.ppId] });
    },
  });
}

export function useActualizarSmartOverridesPuesto(propId: string, ppId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { smart_overrides: Record<string, unknown> | null }) =>
      api<PuestoArmadorDetalle>(
        `/api/propiedades/${propId}/puestos/${ppId}/smart-overrides`,
        { method: "PUT", body },
      ),
    onSuccess: () => {
      invalidarPuestos(qc, propId);
      qc.invalidateQueries({ queryKey: ["armador", "puesto", propId, ppId] });
    },
  });
}

export function useEliminarPuesto(propId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ppId: string) =>
      api(`/api/propiedades/${propId}/puestos/${ppId}`, { method: "DELETE" }),
    onSuccess: () => invalidarPuestos(qc, propId),
  });
}

export function useSembrarDesdeMaestro(propId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { departamento_ids?: string[] | null; incluir_sin_departamento?: boolean }) =>
      api<SembrarResultado>(`/api/propiedades/${propId}/puestos/sembrar-desde-maestro`, {
        method: "POST",
        body,
      }),
    onSuccess: () => invalidarPuestos(qc, propId),
  });
}

// Titulares (ocupantes) de un puesto
export function useOcupantes(propId: string, ppId: string | undefined) {
  return useQuery({
    queryKey: ["armador", "ocupantes", propId, ppId],
    queryFn: () =>
      api<OcupanteArmador[]>(`/api/propiedades/${propId}/puestos/${ppId}/ocupantes`),
    enabled: !!ppId,
  });
}

export function useAgregarOcupante(propId: string, ppId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { usuario_id: string; es_principal?: boolean; nota?: string | null }) =>
      api<OcupanteArmador>(`/api/propiedades/${propId}/puestos/${ppId}/ocupantes`, {
        method: "POST",
        body,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["armador", "ocupantes", propId, ppId] });
      qc.invalidateQueries({ queryKey: ["armador", "puesto", propId, ppId] });
      invalidarPuestos(qc, propId);
    },
  });
}

export function useQuitarOcupante(propId: string, ppId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ocupanteId: string) =>
      api(`/api/propiedades/${propId}/puestos/${ppId}/ocupantes/${ocupanteId}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["armador", "ocupantes", propId, ppId] });
      qc.invalidateQueries({ queryKey: ["armador", "puesto", propId, ppId] });
      invalidarPuestos(qc, propId);
    },
  });
}

// Sistemas por propiedad
export function usePropiedadSistemas(propId: string | undefined) {
  return useQuery({
    queryKey: ["armador", "sistemas", propId],
    queryFn: () => api<SistemaAsignado[]>(`/api/propiedades/${propId}/sistemas`),
    enabled: !!propId,
  });
}

export function useFijarSistemas(propId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sistema_ids: string[]) =>
      api<SistemaAsignado[]>(`/api/propiedades/${propId}/sistemas`, {
        method: "PUT",
        body: { sistema_ids },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["armador", "sistemas", propId] });
      qc.invalidateQueries({ queryKey: ["armador", "resumen"] });
    },
  });
}

// SOPs por propiedad (motor adoptar/adaptar/local + sugerencias)
export function useAsignacionesSop(propId: string | undefined) {
  return useQuery({
    queryKey: ["armador", "asignaciones", propId],
    queryFn: () => api<PropiedadSopOut[]>(`/api/propiedades/${propId}/asignaciones`),
    enabled: !!propId,
  });
}

export function useSugerenciasSop(propId: string | undefined) {
  return useQuery({
    queryKey: ["armador", "sugerencias", propId],
    queryFn: () => api<SugerenciaSop[]>(`/api/propiedades/${propId}/sugerencias`),
    enabled: !!propId,
  });
}

export function useAsignarSop(propId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      modo: string;
      sop_master_id?: string | null;
      overrides?: Record<string, unknown> | null;
      campos_locales?: Record<string, unknown> | null;
    }) =>
      api<PropiedadSopOut>(`/api/propiedades/${propId}/asignaciones`, { method: "POST", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["armador", "asignaciones", propId] });
      qc.invalidateQueries({ queryKey: ["armador", "sugerencias", propId] });
      qc.invalidateQueries({ queryKey: ["armador", "resumen"] });
    },
  });
}

// Detalle + adaptación por secciones de una asignación de SOP
export function usePropiedadSop(psId: string | undefined) {
  return useQuery({
    queryKey: ["armador", "propiedad-sop", psId],
    queryFn: () => api<PropiedadSopDetalle>(`/api/propiedad-sops/${psId}`),
    enabled: !!psId,
  });
}

// --- Capacitaciones por propiedad (Etapa C) ---
function invalidarCapacitaciones(qc: ReturnType<typeof useQueryClient>, propId: string) {
  qc.invalidateQueries({ queryKey: ["armador", "capacitaciones", propId] });
  qc.invalidateQueries({ queryKey: ["armador", "resumen"] });
}

export function usePropiedadCapacitaciones(propId: string) {
  return useQuery({
    queryKey: ["armador", "capacitaciones", propId],
    queryFn: () =>
      api<PropiedadTrainingItem[]>(`/api/propiedades/${propId}/capacitaciones`),
  });
}

export function usePropiedadCapacitacion(propId: string, ptId: string | undefined) {
  return useQuery({
    queryKey: ["armador", "capacitacion", propId, ptId],
    queryFn: () =>
      api<PropiedadTrainingDetalle>(`/api/propiedades/${propId}/capacitaciones/${ptId}`),
    enabled: !!ptId,
  });
}

export function useAsignarCapacitacion(propId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) =>
      api<PropiedadTrainingDetalle>(`/api/propiedades/${propId}/capacitaciones`, {
        method: "POST",
        body,
      }),
    onSuccess: () => invalidarCapacitaciones(qc, propId),
  });
}

export function useAdaptarCapacitacion(propId: string, ptId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api<PropiedadTrainingDetalle>(
        `/api/propiedades/${propId}/capacitaciones/${ptId}/adaptar`,
        { method: "POST" },
      ),
    onSuccess: () => {
      invalidarCapacitaciones(qc, propId);
      qc.invalidateQueries({ queryKey: ["armador", "capacitacion", propId, ptId] });
    },
  });
}

export function useActualizarSmartOverridesTraining(propId: string, ptId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { smart_overrides: Record<string, unknown> | null }) =>
      api<PropiedadTrainingDetalle>(
        `/api/propiedades/${propId}/capacitaciones/${ptId}/smart-overrides`,
        { method: "PUT", body },
      ),
    onSuccess: () => {
      invalidarCapacitaciones(qc, propId);
      qc.invalidateQueries({ queryKey: ["armador", "capacitacion", propId, ptId] });
    },
  });
}

export function useEliminarCapacitacion(propId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ptId: string) =>
      api(`/api/propiedades/${propId}/capacitaciones/${ptId}`, { method: "DELETE" }),
    onSuccess: () => invalidarCapacitaciones(qc, propId),
  });
}

export function useActualizarOverridesSop(propId: string, psId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      overrides?: Record<string, unknown> | null;
      campos_locales?: Record<string, unknown> | null;
    }) =>
      api<PropiedadSopDetalle>(`/api/propiedad-sops/${psId}/overrides`, { method: "PUT", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["armador", "propiedad-sop", psId] });
      qc.invalidateQueries({ queryKey: ["armador", "asignaciones", propId] });
    },
  });
}

export function useActualizarSmartOverridesSop(propId: string, psId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { smart_overrides: Record<string, unknown> | null }) =>
      api<PropiedadSopDetalle>(`/api/propiedad-sops/${psId}/smart-overrides`, {
        method: "PUT",
        body,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["armador", "propiedad-sop", psId] });
      qc.invalidateQueries({ queryKey: ["armador", "asignaciones", propId] });
    },
  });
}

export function useAdaptarSop(propId: string, psId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api<PropiedadSopDetalle>(`/api/propiedad-sops/${psId}/adaptar`, { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["armador", "propiedad-sop", psId] });
      qc.invalidateQueries({ queryKey: ["armador", "asignaciones", propId] });
    },
  });
}

// --- Laboratorio de intake ---

export function useAnalizarIntake() {
  return useMutation({
    mutationFn: (body: { nombre: string; texto: string }) =>
      api<TriageIntake>("/api/intake/analizar", { method: "POST", body }),
  });
}

export function useExtraerIntake() {
  return useMutation({
    mutationFn: (archivo: File) => {
      const form = new FormData();
      form.append("archivo", archivo);
      return apiUpload<ExtraerIntake>("/api/intake/extraer", form);
    },
  });
}
