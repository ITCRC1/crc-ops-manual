"use client";

import { useMemo, useState } from "react";

import { Button, Input, Textarea } from "./ui";
import { useToast } from "./toast";
import { ApiError } from "@/lib/api";
import { useCambiosSinGuardar } from "@/lib/cambios-sin-guardar";
import { useActualizarManualSmart } from "@/lib/hooks";
import type { TrainingManualDetalle, TrainingSmart } from "@/lib/types";

const TRAIN_VACIO: Required<TrainingSmart> = {
  formato: "TRAIN-SMART-1.0",
  objetivo: "",
  modalidad: "",
  duracion: "",
  dirigido_a: [],
  imparte: "",
  prerequisitos: [],
  contenidos: [],
  materiales: [],
  evaluacion: [],
  evidencia: [],
  vigencia: { vigencia_meses: "", requiere_recertificacion: false, condiciones_recert: "" },
  obligatoria: false,
  base_obligatoriedad: "",
  kpis: [],
  control_versiones: [],
  resumen_ejecutivo: "",
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

// Modo `override`: reusar este formulario para adaptar la ficha TRAIN-SMART por PROPIEDAD
// (guarda deltas por sección contra el master). Aditivo: sin `override` = edición del master.
export type TrainingSmartOverride = {
  inicial: TrainingSmart;
  guardar: (limpio: TrainingSmart) => Promise<void>;
  guardando: boolean;
  sucioKey: string;
  encabezado?: React.ReactNode;
};

export function TrainingSmartForm({
  manual,
  onDone,
  override,
}: {
  manual?: TrainingManualDetalle;
  onDone: () => void;
  override?: TrainingSmartOverride;
}) {
  const { notify } = useToast();
  const guardar = useActualizarManualSmart(manual?.id ?? "");
  const fuente = override ? override.inicial : manual?.smart;
  const inicial = useMemo<Required<TrainingSmart>>(
    () => ({
      ...TRAIN_VACIO,
      ...(fuente ?? {}),
      vigencia: { ...TRAIN_VACIO.vigencia, ...(fuente?.vigencia ?? {}) },
    }),
    [fuente],
  );
  const [smart, setSmart] = useState<Required<TrainingSmart>>(inicial);

  const sucio = useMemo(() => JSON.stringify(smart) !== JSON.stringify(inicial), [smart, inicial]);
  useCambiosSinGuardar(override?.sucioKey ?? `manual-smart:${manual?.id}`, sucio);
  const guardando = override ? override.guardando : guardar.isPending;

  function campo<K extends keyof TrainingSmart>(k: K, v: Required<TrainingSmart>[K]) {
    setSmart((s) => ({ ...s, [k]: v }));
  }
  function vigencia(k: keyof Required<TrainingSmart>["vigencia"], v: unknown) {
    setSmart((s) => ({ ...s, vigencia: { ...s.vigencia, [k]: v } }));
  }

  function cancelar() {
    if (sucio && !window.confirm("Se van a descartar los cambios sin guardar. ¿Seguro?")) return;
    onDone();
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const arr = (a?: string[]) => (a ?? []).filter((s) => s.trim());
    const limpio: TrainingSmart = {
      ...smart,
      formato: "TRAIN-SMART-1.0",
      dirigido_a: arr(smart.dirigido_a),
      prerequisitos: arr(smart.prerequisitos),
      pendiente_confirmar: arr(smart.pendiente_confirmar),
      contenidos: smart.contenidos
        .filter((c) => (c.tema ?? "").trim())
        .map((c, i) => ({ ...c, n: i + 1 })),
      materiales: smart.materiales.filter((m) => (m.material ?? "").trim()),
      evaluacion: smart.evaluacion.filter((e2) => (e2.metodo ?? "").trim()),
      evidencia: smart.evidencia.filter((e2) => (e2.evidencia ?? "").trim()),
      kpis: smart.kpis.filter((k) => (k.indicador ?? "").trim()),
      control_versiones: smart.control_versiones.filter((v) => (v.version ?? "").trim()),
    };
    try {
      if (override) {
        await override.guardar(limpio);
      } else {
        await guardar.mutateAsync({ smart: limpio });
      }
      notify("Training SMART guardado.");
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
            <h2 className="text-sm font-semibold text-petrol-oscuro">Editar Training SMART</h2>
            <p className="text-xs text-carbon-suave">
              Las secciones base del manual no se tocan desde acá.
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
        n="P."
        titulo="Información pendiente de confirmar / validar"
        ayuda="Vacíos que no se deben inventar (obligatoriedad, nota mínima, etc.). Al resolver uno: escribí el dato en su sección y quitá la línea de acá."
      >
        <ListaTexto
          items={smart.pendiente_confirmar}
          onChange={(v) => campo("pendiente_confirmar", v)}
          etiquetaAgregar="pendiente"
          placeholder="Ej: Base de obligatoriedad pendiente de confirmar"
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

      <Seccion n="1." titulo="Objetivo de la capacitación">
        <Textarea
          rows={3}
          value={smart.objetivo}
          onChange={(e) => campo("objetivo", e.target.value)}
          aria-label="Objetivo"
        />
      </Seccion>

      <Seccion n="2." titulo="Modalidad, duración e instructor">
        <div className="grid gap-3 sm:grid-cols-3">
          <Input
            placeholder="Modalidad (presencial / virtual / OJT / mixta)"
            value={smart.modalidad}
            onChange={(e) => campo("modalidad", e.target.value)}
            aria-label="Modalidad"
          />
          <Input
            placeholder="Duración (horas / sesiones)"
            value={smart.duracion}
            onChange={(e) => campo("duracion", e.target.value)}
            aria-label="Duración"
          />
          <Input
            placeholder="Imparte / instructor"
            value={smart.imparte}
            onChange={(e) => campo("imparte", e.target.value)}
            aria-label="Imparte"
          />
        </div>
      </Seccion>

      <Seccion n="3." titulo="Dirigido a" ayuda="Puestos o roles objetivo de la capacitación.">
        <ListaTexto
          items={smart.dirigido_a}
          onChange={(v) => campo("dirigido_a", v)}
          etiquetaAgregar="puesto / rol"
        />
      </Seccion>

      <Seccion n="4." titulo="Prerequisitos">
        <ListaTexto
          items={smart.prerequisitos}
          onChange={(v) => campo("prerequisitos", v)}
          etiquetaAgregar="prerequisito"
        />
      </Seccion>

      <Seccion
        n="5."
        titulo="Contenidos / temario"
        ayuda="Cada tema con su descripción y material de referencia. El número se renumera solo."
      >
        <TablaEditable
          auto="n"
          cols={[
            { key: "tema", label: "Tema", ancho: "w-1/4" },
            { key: "descripcion", label: "Descripción", tipo: "area", ancho: "w-1/3" },
            { key: "material_ref", label: "Material ref." },
          ]}
          filas={smart.contenidos as unknown as Fila[]}
          onChange={(f) => campo("contenidos", f as unknown as Required<TrainingSmart>["contenidos"])}
          filaVacia={() => ({ n: 0, tema: "", descripcion: "", material_ref: "" })}
          etiquetaAgregar="contenido"
        />
      </Seccion>

      <Seccion n="6." titulo="Materiales y recursos">
        <TablaEditable
          cols={[
            { key: "material", label: "Material", ancho: "w-1/3" },
            { key: "tipo", label: "Tipo" },
            { key: "referencia", label: "Referencia" },
          ]}
          filas={smart.materiales as unknown as Fila[]}
          onChange={(f) => campo("materiales", f as unknown as Required<TrainingSmart>["materiales"])}
          filaVacia={() => ({ material: "", tipo: "", referencia: "" })}
          etiquetaAgregar="material"
        />
      </Seccion>

      <Seccion n="7." titulo="Evaluación">
        <TablaEditable
          cols={[
            { key: "metodo", label: "Método", ancho: "w-1/3" },
            { key: "criterio_aprobacion", label: "Criterio de aprobación" },
            { key: "nota_minima", label: "Nota mínima" },
          ]}
          filas={smart.evaluacion as unknown as Fila[]}
          onChange={(f) => campo("evaluacion", f as unknown as Required<TrainingSmart>["evaluacion"])}
          filaVacia={() => ({ metodo: "", criterio_aprobacion: "", nota_minima: "" })}
          etiquetaAgregar="evaluación"
        />
      </Seccion>

      <Seccion n="8." titulo="Evidencia y registros">
        <TablaEditable
          cols={[
            { key: "evidencia", label: "Evidencia", ancho: "w-1/4" },
            { key: "responsable", label: "Responsable" },
            { key: "archivo", label: "Archivo" },
            { key: "retencion", label: "Retención" },
          ]}
          filas={smart.evidencia as unknown as Fila[]}
          onChange={(f) => campo("evidencia", f as unknown as Required<TrainingSmart>["evidencia"])}
          filaVacia={() => ({ evidencia: "", responsable: "", archivo: "", retencion: "" })}
          etiquetaAgregar="evidencia"
        />
      </Seccion>

      <Seccion n="9." titulo="Vigencia y recertificación">
        <div className="grid gap-3 sm:grid-cols-3">
          <Input
            placeholder="Vigencia (meses)"
            value={smart.vigencia.vigencia_meses ?? ""}
            onChange={(e) => vigencia("vigencia_meses", e.target.value)}
            aria-label="Vigencia en meses"
          />
          <label className="flex items-center gap-2 text-sm text-carbon">
            <input
              type="checkbox"
              checked={Boolean(smart.vigencia.requiere_recertificacion)}
              onChange={(e) => vigencia("requiere_recertificacion", e.target.checked)}
              className="h-4 w-4"
            />
            Requiere recertificación
          </label>
          <Input
            placeholder="Condiciones de recert."
            value={smart.vigencia.condiciones_recert ?? ""}
            onChange={(e) => vigencia("condiciones_recert", e.target.value)}
            aria-label="Condiciones de recertificación"
          />
        </div>
      </Seccion>

      <Seccion
        n="10."
        titulo="Obligatoriedad"
        ayuda="No marcar obligatoria sin base documentada. Si falta la base, dejala en pendientes."
      >
        <label className="mb-3 flex items-center gap-2 text-sm text-carbon">
          <input
            type="checkbox"
            checked={smart.obligatoria}
            onChange={(e) => campo("obligatoria", e.target.checked)}
            className="h-4 w-4"
          />
          Capacitación obligatoria
        </label>
        <Textarea
          rows={2}
          placeholder="Base de obligatoriedad (norma, política, riesgo…)"
          value={smart.base_obligatoriedad}
          onChange={(e) => campo("base_obligatoriedad", e.target.value)}
          aria-label="Base de obligatoriedad"
        />
      </Seccion>

      <Seccion
        n="11."
        titulo="KPIs / indicadores"
        ayuda='Marcá "Recomendado" cuando el indicador no venía definido.'
      >
        <TablaEditable
          cols={[
            { key: "indicador", label: "Indicador", ancho: "w-1/3" },
            { key: "meta", label: "Meta" },
            { key: "recomendado", label: "Recom.", tipo: "check" },
          ]}
          filas={smart.kpis as unknown as Fila[]}
          onChange={(f) => campo("kpis", f as unknown as Required<TrainingSmart>["kpis"])}
          filaVacia={() => ({ indicador: "", meta: "", recomendado: true })}
          etiquetaAgregar="KPI"
        />
      </Seccion>

      <Seccion n="12." titulo="Revisión, aprobación y control de versiones">
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
          onChange={(f) =>
            campo("control_versiones", f as unknown as Required<TrainingSmart>["control_versiones"])
          }
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

      <div className="flex gap-2 border-t border-linea pt-4">
        <Button type="submit" disabled={guardando}>
          {guardando ? "Guardando…" : "Guardar Training SMART"}
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
