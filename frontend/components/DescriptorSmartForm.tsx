"use client";

import { useMemo, useState } from "react";

import { Button, Input, Textarea } from "./ui";
import { useToast } from "./toast";
import { ApiError } from "@/lib/api";
import { useCambiosSinGuardar } from "@/lib/cambios-sin-guardar";
import { useActualizarDescriptorSmart } from "@/lib/hooks";
import type { DescriptorDetalle, JdSmart } from "@/lib/types";

const JD_VACIO: Required<JdSmart> = {
  formato: "JD-SMART-1.0",
  departamento: "",
  reporta_a: "",
  supervisa: [],
  resumen_puesto: "",
  objetivo: "",
  resumen_ejecutivo: "",
  responsabilidades_smart: [],
  funciones: { diarias: [], semanales: [], mensuales: [], por_evento: [] },
  sops_relacionados: [],
  sops_recomendados: [],
  kpis: [],
  autoridad: [],
  relaciones_internas: [],
  relaciones_externas: [],
  sistemas: [],
  documentos: [],
  competencias_tecnicas: [],
  competencias_conductuales: [],
  experiencia_formacion: "",
  cumplimiento_confidencialidad: [],
  estandares_servicio: [],
  horario_condiciones: "",
  perfil_exito: "",
  ciclo_revision: "",
  control_versiones: [],
  checklist: [],
  pendiente_confirmar: [],
};

type Fila = Record<string, unknown>;
interface Col {
  key: string;
  label: string;
  tipo?: "texto" | "area" | "check";
  ancho?: string;
}

function Seccion({
  n,
  titulo,
  ayuda,
  children,
}: {
  n: string;
  titulo: string;
  ayuda?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="border-t border-linea pt-5">
      <h3 className="text-sm font-semibold text-petrol-oscuro">
        <span className="mr-2 font-mono text-xs text-carbon-suave">{n}</span>
        {titulo}
      </h3>
      {ayuda && <p className="mt-0.5 text-xs text-carbon-suave">{ayuda}</p>}
      <div className="mt-3">{children}</div>
    </section>
  );
}

function TablaEditable({
  cols,
  filas,
  onChange,
  filaVacia,
  auto,
  etiquetaAgregar,
}: {
  cols: Col[];
  filas: Fila[];
  onChange: (filas: Fila[]) => void;
  filaVacia: () => Fila;
  auto?: string;
  etiquetaAgregar: string;
}) {
  function renumerar(fs: Fila[]): Fila[] {
    return auto ? fs.map((f, i) => ({ ...f, [auto]: i + 1 })) : fs;
  }
  function set(i: number, key: string, valor: unknown) {
    onChange(filas.map((f, j) => (i === j ? { ...f, [key]: valor } : f)));
  }
  return (
    <div>
      {filas.length > 0 && (
        <div className="overflow-x-auto rounded-md border border-linea">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-linea bg-petrol-tint/40 text-left text-xs uppercase tracking-wide text-carbon-suave">
                {auto && <th className="w-10 px-2 py-2 font-semibold">#</th>}
                {cols.map((c) => (
                  <th key={c.key} className={`px-2 py-2 font-semibold ${c.ancho ?? ""}`}>
                    {c.label}
                  </th>
                ))}
                <th className="w-10 px-2 py-2" />
              </tr>
            </thead>
            <tbody>
              {filas.map((f, i) => (
                <tr key={i} className="border-b border-linea align-top last:border-0">
                  {auto && (
                    <td className="px-2 py-2 text-center font-mono text-xs text-carbon-suave">
                      {i + 1}
                    </td>
                  )}
                  {cols.map((c) => (
                    <td key={c.key} className="px-2 py-2">
                      {c.tipo === "check" ? (
                        <input
                          type="checkbox"
                          checked={Boolean(f[c.key])}
                          onChange={(e) => set(i, c.key, e.target.checked)}
                          className="mt-2 h-4 w-4"
                          aria-label={c.label}
                        />
                      ) : c.tipo === "area" ? (
                        <Textarea
                          rows={2}
                          value={String(f[c.key] ?? "")}
                          onChange={(e) => set(i, c.key, e.target.value)}
                          aria-label={c.label}
                        />
                      ) : (
                        <Input
                          value={String(f[c.key] ?? "")}
                          onChange={(e) => set(i, c.key, e.target.value)}
                          aria-label={c.label}
                        />
                      )}
                    </td>
                  ))}
                  <td className="px-2 py-2">
                    <button
                      type="button"
                      onClick={() => onChange(renumerar(filas.filter((_, j) => j !== i)))}
                      className="rounded px-2 py-1 text-xs text-rechazado hover:bg-rechazado/10"
                      aria-label="Eliminar fila"
                      title="Eliminar fila"
                    >
                      Quitar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Button
        type="button"
        variant="secondary"
        className="mt-2"
        onClick={() => onChange(renumerar([...filas, filaVacia()]))}
      >
        + {etiquetaAgregar}
      </Button>
    </div>
  );
}

function ListaTexto({
  items,
  onChange,
  etiquetaAgregar,
  placeholder,
}: {
  items: string[];
  onChange: (v: string[]) => void;
  etiquetaAgregar: string;
  placeholder?: string;
}) {
  return (
    <div className="space-y-2">
      {items.map((valor, i) => (
        <div key={i} className="flex gap-2">
          <Input
            value={valor}
            placeholder={placeholder}
            onChange={(e) => onChange(items.map((v, j) => (i === j ? e.target.value : v)))}
            aria-label={etiquetaAgregar}
          />
          <button
            type="button"
            onClick={() => onChange(items.filter((_, j) => j !== i))}
            className="shrink-0 rounded px-2 text-xs text-rechazado hover:bg-rechazado/10"
          >
            Quitar
          </button>
        </div>
      ))}
      <Button type="button" variant="secondary" onClick={() => onChange([...items, ""])}>
        + {etiquetaAgregar}
      </Button>
    </div>
  );
}

// Modo `override`: reusar este formulario para adaptar la capa JD SMART por PROPIEDAD
// (guarda deltas por sección contra el master). Aditivo: sin `override` = edición del master.
export type JdSmartOverride = {
  inicial: JdSmart;
  guardar: (limpio: JdSmart) => Promise<void>;
  guardando: boolean;
  sucioKey: string;
  encabezado?: React.ReactNode;
};

export function DescriptorSmartForm({
  descriptor,
  onDone,
  override,
}: {
  descriptor?: DescriptorDetalle;
  onDone: () => void;
  override?: JdSmartOverride;
}) {
  const { notify } = useToast();
  const guardar = useActualizarDescriptorSmart(descriptor?.id ?? "");
  const fuente = override ? override.inicial : descriptor?.smart;
  const inicial = useMemo<Required<JdSmart>>(
    () => ({
      ...JD_VACIO,
      ...(fuente ?? {}),
      funciones: { ...JD_VACIO.funciones, ...(fuente?.funciones ?? {}) },
    }),
    [fuente],
  );
  const [smart, setSmart] = useState<Required<JdSmart>>(inicial);

  const sucio = useMemo(() => JSON.stringify(smart) !== JSON.stringify(inicial), [smart, inicial]);
  useCambiosSinGuardar(override?.sucioKey ?? `descriptor-smart:${descriptor?.id}`, sucio);
  const guardando = override ? override.guardando : guardar.isPending;

  function campo<K extends keyof JdSmart>(k: K, v: Required<JdSmart>[K]) {
    setSmart((s) => ({ ...s, [k]: v }));
  }
  function funcion(k: keyof Required<JdSmart>["funciones"], v: string[]) {
    setSmart((s) => ({ ...s, funciones: { ...s.funciones, [k]: v } }));
  }

  function cancelar() {
    if (sucio && !window.confirm("Se van a descartar los cambios sin guardar. ¿Seguro?")) return;
    onDone();
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const arr = (a?: string[]) => (a ?? []).filter((s) => s.trim());
    const limpio: JdSmart = {
      ...smart,
      formato: "JD-SMART-1.0",
      supervisa: arr(smart.supervisa),
      relaciones_externas: arr(smart.relaciones_externas),
      competencias_tecnicas: arr(smart.competencias_tecnicas),
      competencias_conductuales: arr(smart.competencias_conductuales),
      cumplimiento_confidencialidad: arr(smart.cumplimiento_confidencialidad),
      estandares_servicio: arr(smart.estandares_servicio),
      pendiente_confirmar: arr(smart.pendiente_confirmar),
      funciones: {
        diarias: arr(smart.funciones.diarias),
        semanales: arr(smart.funciones.semanales),
        mensuales: arr(smart.funciones.mensuales),
        por_evento: arr(smart.funciones.por_evento),
      },
      responsabilidades_smart: smart.responsabilidades_smart
        .filter((r) => (r.responsabilidad ?? "").trim())
        .map((r, i) => ({ ...r, n: i + 1 })),
      sops_relacionados: smart.sops_relacionados.filter((s) => (s.codigo_sop ?? "").trim()),
      sops_recomendados: smart.sops_recomendados.filter((s) =>
        (s.responsabilidad_sin_sop ?? "").trim(),
      ),
      kpis: smart.kpis.filter((k) => (k.kpi ?? "").trim()),
      autoridad: smart.autoridad.filter((a) => (a.tipo_decision ?? "").trim()),
      relaciones_internas: smart.relaciones_internas.filter((r) => (r.area_puesto ?? "").trim()),
      sistemas: smart.sistemas.filter((s) => (s.sistema ?? "").trim()),
      documentos: smart.documentos.filter((d) => (d.documento ?? "").trim()),
      control_versiones: smart.control_versiones.filter((v) => (v.version ?? "").trim()),
      checklist: smart.checklist
        .filter((c) => (c.punto ?? "").trim())
        .map((c, i) => ({ ...c, n: i + 1 })),
    };
    try {
      if (override) {
        await override.guardar(limpio);
      } else {
        await guardar.mutateAsync({ smart: limpio });
      }
      notify("JD SMART guardado.");
      onDone();
    } catch (err) {
      notify(err instanceof ApiError ? err.detail : "No se pudo guardar.", "error");
    }
  }

  const pendientes = smart.pendiente_confirmar.length;

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {override?.encabezado ?? (
          <div>
            <h2 className="text-sm font-semibold text-petrol-oscuro">Editar JD SMART</h2>
            <p className="text-xs text-carbon-suave">
              Los campos base del descriptor no se tocan desde acá.
            </p>
          </div>
        )}
        {pendientes > 0 && (
          <span className="rounded-full bg-en-firma/15 px-3 py-1 text-xs font-medium text-en-firma">
            {pendientes} pendiente{pendientes === 1 ? "" : "s"} de confirmar
          </span>
        )}
      </div>

      <Seccion
        n="30."
        titulo="Información pendiente de confirmar / validar"
        ayuda="Vacíos que el reformateo NO inventó (autoridad, línea de reporte, etc.). Al resolver uno: escribí el dato en su sección y quitá la línea de acá."
      >
        <ListaTexto
          items={smart.pendiente_confirmar}
          onChange={(v) => campo("pendiente_confirmar", v)}
          etiquetaAgregar="pendiente"
          placeholder="Ej: Límites de autoridad pendientes de confirmar"
        />
      </Seccion>

      <Seccion n="A." titulo="Resumen ejecutivo">
        <Textarea
          rows={5}
          value={smart.resumen_ejecutivo}
          onChange={(e) => campo("resumen_ejecutivo", e.target.value)}
          aria-label="Resumen ejecutivo"
        />
      </Seccion>

      <Seccion n="3-5." titulo="Departamento / Reporta a / Supervisa">
        <div className="grid gap-3 sm:grid-cols-2">
          <Input
            placeholder="Departamento"
            value={smart.departamento}
            onChange={(e) => campo("departamento", e.target.value)}
            aria-label="Departamento"
          />
          <Input
            placeholder="Reporta a"
            value={smart.reporta_a}
            onChange={(e) => campo("reporta_a", e.target.value)}
            aria-label="Reporta a"
          />
        </div>
        <p className="mb-1 mt-3 text-xs font-semibold text-carbon-suave">Puestos que supervisa</p>
        <ListaTexto
          items={smart.supervisa}
          onChange={(v) => campo("supervisa", v)}
          etiquetaAgregar="puesto supervisado"
        />
      </Seccion>

      <Seccion n="6." titulo="Resumen del puesto">
        <Textarea
          rows={3}
          value={smart.resumen_puesto}
          onChange={(e) => campo("resumen_puesto", e.target.value)}
          aria-label="Resumen del puesto"
        />
      </Seccion>

      <Seccion n="7." titulo="Objetivo del puesto">
        <Textarea
          rows={3}
          value={smart.objetivo}
          onChange={(e) => campo("objetivo", e.target.value)}
          aria-label="Objetivo"
        />
      </Seccion>

      <Seccion
        n="8."
        titulo="Responsabilidades SMART"
        ayuda="Cada una con su SOP relacionado, rol, frecuencia, evidencia y KPI. El número se renumera solo."
      >
        <TablaEditable
          auto="n"
          cols={[
            { key: "responsabilidad", label: "Responsabilidad", tipo: "area", ancho: "w-1/3" },
            { key: "sop_relacionado", label: "SOP" },
            { key: "rol_sop", label: "Rol" },
            { key: "frecuencia", label: "Frec." },
            { key: "evidencia", label: "Evidencia" },
            { key: "kpi", label: "KPI" },
          ]}
          filas={smart.responsabilidades_smart as unknown as Fila[]}
          onChange={(f) => campo("responsabilidades_smart", f as unknown as Required<JdSmart>["responsabilidades_smart"])}
          filaVacia={() => ({
            n: 0,
            responsabilidad: "",
            sop_relacionado: "",
            rol_sop: "",
            frecuencia: "",
            evidencia: "",
            kpi: "",
          })}
          etiquetaAgregar="responsabilidad"
        />
      </Seccion>

      <Seccion n="9." titulo="Funciones por frecuencia">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="mb-1 text-xs font-semibold text-carbon-suave">Diarias</p>
            <ListaTexto items={smart.funciones.diarias ?? []} onChange={(v) => funcion("diarias", v)} etiquetaAgregar="diaria" />
          </div>
          <div>
            <p className="mb-1 text-xs font-semibold text-carbon-suave">Semanales</p>
            <ListaTexto items={smart.funciones.semanales ?? []} onChange={(v) => funcion("semanales", v)} etiquetaAgregar="semanal" />
          </div>
          <div>
            <p className="mb-1 text-xs font-semibold text-carbon-suave">Mensuales</p>
            <ListaTexto items={smart.funciones.mensuales ?? []} onChange={(v) => funcion("mensuales", v)} etiquetaAgregar="mensual" />
          </div>
          <div>
            <p className="mb-1 text-xs font-semibold text-carbon-suave">Por evento</p>
            <ListaTexto items={smart.funciones.por_evento ?? []} onChange={(v) => funcion("por_evento", v)} etiquetaAgregar="por evento" />
          </div>
        </div>
      </Seccion>

      <Seccion n="10." titulo="SOPs SMART relacionados">
        <TablaEditable
          cols={[
            { key: "codigo_sop", label: "Cód. SOP", ancho: "w-24" },
            { key: "nombre_sop", label: "Nombre SOP" },
            { key: "depto_sop", label: "Depto SOP" },
            { key: "relacion", label: "Relación", tipo: "area" },
            { key: "rol", label: "Rol" },
            { key: "frecuencia", label: "Frec." },
            { key: "evidencia", label: "Evidencia" },
            { key: "estado", label: "Estado" },
          ]}
          filas={smart.sops_relacionados as unknown as Fila[]}
          onChange={(f) => campo("sops_relacionados", f as unknown as Required<JdSmart>["sops_relacionados"])}
          filaVacia={() => ({
            codigo_sop: "",
            nombre_sop: "",
            depto_sop: "",
            relacion: "",
            rol: "",
            frecuencia: "",
            evidencia: "",
            estado: "Requiere validación",
          })}
          etiquetaAgregar="SOP"
        />
      </Seccion>

      <Seccion n="12." titulo="SOPs recomendados para creación">
        <TablaEditable
          cols={[
            { key: "responsabilidad_sin_sop", label: "Responsabilidad sin SOP", tipo: "area", ancho: "w-1/4" },
            { key: "sop_recomendado", label: "SOP recomendado" },
            { key: "justificacion", label: "Justificación", tipo: "area" },
            { key: "prioridad", label: "Prioridad" },
            { key: "depto", label: "Depto." },
          ]}
          filas={smart.sops_recomendados as unknown as Fila[]}
          onChange={(f) => campo("sops_recomendados", f as unknown as Required<JdSmart>["sops_recomendados"])}
          filaVacia={() => ({
            responsabilidad_sin_sop: "",
            sop_recomendado: "",
            justificacion: "",
            prioridad: "Media",
            depto: "",
          })}
          etiquetaAgregar="recomendación"
        />
      </Seccion>

      <Seccion
        n="13."
        titulo="KPIs / indicadores"
        ayuda='Marcá "Recomendado" cuando el KPI no venía en el JD original.'
      >
        <TablaEditable
          cols={[
            { key: "kpi", label: "KPI", ancho: "w-1/5" },
            { key: "definicion", label: "Definición", tipo: "area" },
            { key: "meta", label: "Meta" },
            { key: "frecuencia", label: "Frec." },
            { key: "fuente", label: "Fuente" },
            { key: "responsable", label: "Responsable" },
            { key: "recomendado", label: "Recom.", tipo: "check" },
          ]}
          filas={smart.kpis as unknown as Fila[]}
          onChange={(f) => campo("kpis", f as unknown as Required<JdSmart>["kpis"])}
          filaVacia={() => ({
            kpi: "",
            definicion: "",
            meta: "",
            frecuencia: "",
            fuente: "",
            responsable: "",
            recomendado: true,
          })}
          etiquetaAgregar="KPI"
        />
      </Seccion>

      <Seccion
        n="14."
        titulo="Autoridad y nivel de decisión"
        ayuda="No inventar montos ni aprobaciones que no estén documentados."
      >
        <TablaEditable
          cols={[
            { key: "tipo_decision", label: "Tipo de decisión", ancho: "w-1/4" },
            { key: "puede_aprobar", label: "Puede aprobar" },
            { key: "debe_consultar", label: "Debe consultar" },
            { key: "debe_escalar", label: "Debe escalar" },
          ]}
          filas={smart.autoridad as unknown as Fila[]}
          onChange={(f) => campo("autoridad", f as unknown as Required<JdSmart>["autoridad"])}
          filaVacia={() => ({
            tipo_decision: "",
            puede_aprobar: "",
            debe_consultar: "",
            debe_escalar: "",
          })}
          etiquetaAgregar="decisión"
        />
      </Seccion>

      <Seccion n="15." titulo="Relaciones internas clave">
        <TablaEditable
          cols={[
            { key: "area_puesto", label: "Área / Puesto", ancho: "w-1/3" },
            { key: "motivo", label: "Motivo" },
            { key: "frecuencia", label: "Frecuencia" },
          ]}
          filas={smart.relaciones_internas as unknown as Fila[]}
          onChange={(f) => campo("relaciones_internas", f as unknown as Required<JdSmart>["relaciones_internas"])}
          filaVacia={() => ({ area_puesto: "", motivo: "", frecuencia: "" })}
          etiquetaAgregar="relación interna"
        />
      </Seccion>

      <Seccion n="16." titulo="Relaciones externas clave">
        <ListaTexto
          items={smart.relaciones_externas}
          onChange={(v) => campo("relaciones_externas", v)}
          etiquetaAgregar="relación externa"
        />
      </Seccion>

      <Seccion n="17." titulo="Sistemas, herramientas y reportes">
        <TablaEditable
          cols={[
            { key: "sistema", label: "Sistema / Reporte", ancho: "w-1/4" },
            { key: "uso", label: "Uso" },
            { key: "frecuencia", label: "Frec." },
            { key: "sop_relacionado", label: "SOP" },
          ]}
          filas={smart.sistemas as unknown as Fila[]}
          onChange={(f) => campo("sistemas", f as unknown as Required<JdSmart>["sistemas"])}
          filaVacia={() => ({ sistema: "", uso: "", frecuencia: "", sop_relacionado: "" })}
          etiquetaAgregar="sistema"
        />
      </Seccion>

      <Seccion n="18." titulo="Documentos y entregables">
        <TablaEditable
          cols={[
            { key: "documento", label: "Documento", ancho: "w-1/4" },
            { key: "responsable", label: "Responsable" },
            { key: "frecuencia", label: "Frec." },
            { key: "revisor", label: "Revisor" },
            { key: "ubicacion", label: "Ubicación" },
            { key: "sop_relacionado", label: "SOP" },
          ]}
          filas={smart.documentos as unknown as Fila[]}
          onChange={(f) => campo("documentos", f as unknown as Required<JdSmart>["documentos"])}
          filaVacia={() => ({
            documento: "",
            responsable: "",
            frecuencia: "",
            revisor: "",
            ubicacion: "",
            sop_relacionado: "",
          })}
          etiquetaAgregar="documento"
        />
      </Seccion>

      <Seccion n="19." titulo="Competencias técnicas">
        <ListaTexto
          items={smart.competencias_tecnicas}
          onChange={(v) => campo("competencias_tecnicas", v)}
          etiquetaAgregar="competencia técnica"
        />
      </Seccion>

      <Seccion n="20." titulo="Competencias conductuales">
        <ListaTexto
          items={smart.competencias_conductuales}
          onChange={(v) => campo("competencias_conductuales", v)}
          etiquetaAgregar="competencia conductual"
        />
      </Seccion>

      <Seccion n="21." titulo="Experiencia y formación">
        <Textarea
          rows={3}
          value={smart.experiencia_formacion}
          onChange={(e) => campo("experiencia_formacion", e.target.value)}
          aria-label="Experiencia y formación"
        />
      </Seccion>

      <Seccion n="22." titulo="Cumplimiento, control interno y confidencialidad">
        <ListaTexto
          items={smart.cumplimiento_confidencialidad}
          onChange={(v) => campo("cumplimiento_confidencialidad", v)}
          etiquetaAgregar="ítem de cumplimiento"
        />
      </Seccion>

      <Seccion n="23." titulo="Estándares de servicio y cultura">
        <ListaTexto
          items={smart.estandares_servicio}
          onChange={(v) => campo("estandares_servicio", v)}
          etiquetaAgregar="estándar"
        />
      </Seccion>

      <Seccion n="24." titulo="Horario y condiciones operativas">
        <Textarea
          rows={2}
          value={smart.horario_condiciones}
          onChange={(e) => campo("horario_condiciones", e.target.value)}
          aria-label="Horario y condiciones"
        />
      </Seccion>

      <Seccion n="25." titulo="Perfil de éxito">
        <Textarea
          rows={3}
          value={smart.perfil_exito}
          onChange={(e) => campo("perfil_exito", e.target.value)}
          aria-label="Perfil de éxito"
        />
      </Seccion>

      <Seccion n="26." titulo="Ciclo de revisión del desempeño">
        <Textarea
          rows={2}
          value={smart.ciclo_revision}
          onChange={(e) => campo("ciclo_revision", e.target.value)}
          aria-label="Ciclo de revisión"
        />
      </Seccion>

      <Seccion n="27." titulo="Revisión, aprobación y control de versiones">
        <TablaEditable
          cols={[
            { key: "version", label: "Versión", ancho: "w-20" },
            { key: "fecha", label: "Fecha" },
            { key: "preparado_por", label: "Preparado por" },
            { key: "revisado_por", label: "Revisado por" },
            { key: "aprobado_por", label: "Aprobado por" },
            { key: "cambios", label: "Cambios", tipo: "area" },
            { key: "proxima_revision", label: "Próxima rev." },
          ]}
          filas={smart.control_versiones as unknown as Fila[]}
          onChange={(f) => campo("control_versiones", f as unknown as Required<JdSmart>["control_versiones"])}
          filaVacia={() => ({
            version: "",
            fecha: "",
            preparado_por: "",
            revisado_por: "",
            aprobado_por: "",
            cambios: "",
            proxima_revision: "",
          })}
          etiquetaAgregar="versión"
        />
      </Seccion>

      <Seccion n="29." titulo="Checklist de validación">
        <TablaEditable
          auto="n"
          cols={[
            { key: "punto", label: "Punto de validación", ancho: "w-1/2" },
            { key: "cumplido", label: "Cumplido" },
            { key: "comentarios", label: "Comentarios" },
          ]}
          filas={smart.checklist as unknown as Fila[]}
          onChange={(f) => campo("checklist", f as unknown as Required<JdSmart>["checklist"])}
          filaVacia={() => ({ n: 0, punto: "", cumplido: "", comentarios: "" })}
          etiquetaAgregar="punto"
        />
      </Seccion>

      <div className="flex gap-2 border-t border-linea pt-4">
        <Button type="submit" disabled={guardando}>
          {guardando ? "Guardando…" : "Guardar JD SMART"}
        </Button>
        <Button type="button" variant="secondary" onClick={cancelar}>
          Cancelar
        </Button>
        {sucio && (
          <span className="self-center text-xs text-carbon-suave">Hay cambios sin guardar.</span>
        )}
      </div>
    </form>
  );
}
