"use client";

import { useMemo, useState } from "react";

import { Button, Etiqueta, Input, Textarea } from "./ui";
import { useToast } from "./toast";
import { ApiError } from "@/lib/api";
import { useCambiosSinGuardar } from "@/lib/cambios-sin-guardar";
import { useActualizarSmart } from "@/lib/hooks";
import type { SopDetalle, SopSmart } from "@/lib/types";

// Capa SMART vacía: un SOP sin `smart` se puede estrenar desde acá.
const SMART_VACIO: SopSmart = {
  formato: "SMART-1.0",
  objetivo: "",
  alcance: "",
  definiciones: [],
  raci: [],
  frecuencia_deadlines: "",
  sistemas: [],
  documentos_relacionados: [],
  procedimiento: [],
  evidencia_requerida: [],
  controles_clave: [],
  kpis: [],
  riesgos_mitigados: [],
  excepciones: [],
  archivo_retencion: "",
  entrenamiento: "",
  control_versiones: [],
  resumen_ejecutivo: "",
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

/** Tabla de filas agregables/borrables. `auto` es la columna de índice (paso/n): la lleva el form. */
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
                <tr key={i} className="border-b border-linea last:border-0 align-top">
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

/** Lista simple de líneas de texto (sistemas, riesgos, pendientes). */
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

// Modo `override`: reusar este mismo formulario para adaptar la capa SMART por PROPIEDAD
// (guarda deltas por sección contra el master) en vez de editar el master. Aditivo: si no
// se pasa `override`, el comportamiento es idéntico al de antes (edición del master).
export type SopSmartOverride = {
  inicial: SopSmart;
  guardar: (limpio: SopSmart) => Promise<void>;
  guardando: boolean;
  sucioKey: string;
  encabezado?: React.ReactNode;
};

export function SopSmartForm({
  sop,
  onDone,
  override,
}: {
  sop?: SopDetalle;
  onDone: () => void;
  override?: SopSmartOverride;
}) {
  const { notify } = useToast();
  const guardar = useActualizarSmart(sop?.id ?? "");
  const inicial = useMemo<SopSmart>(
    () => ({ ...SMART_VACIO, ...(override ? override.inicial : (sop?.smart ?? {})) }),
    [override, sop?.smart],
  );
  const [smart, setSmart] = useState<SopSmart>(inicial);
  const [nota, setNota] = useState("Edición manual de la capa SMART");

  const sucio = useMemo(() => JSON.stringify(smart) !== JSON.stringify(inicial), [smart, inicial]);
  useCambiosSinGuardar(override?.sucioKey ?? `smart:${sop?.id}`, sucio);
  const guardando = override ? override.guardando : guardar.isPending;

  function campo<K extends keyof SopSmart>(k: K, v: SopSmart[K]) {
    setSmart((s) => ({ ...s, [k]: v }));
  }

  function cancelar() {
    if (sucio && !window.confirm("Se van a descartar los cambios sin guardar. ¿Seguro?")) return;
    onDone();
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    // Se descartan filas y líneas totalmente vacías: agregar una y no llenarla es lo normal.
    const limpio: SopSmart = {
      ...smart,
      formato: "SMART-1.0",
      sistemas: smart.sistemas.filter((s) => s.trim()),
      riesgos_mitigados: smart.riesgos_mitigados.filter((s) => s.trim()),
      pendiente_confirmar: smart.pendiente_confirmar.filter((s) => s.trim()),
      definiciones: smart.definiciones.filter((d) => d.termino.trim() || d.definicion.trim()),
      raci: smart.raci.filter((r) => r.actividad.trim()),
      documentos_relacionados: smart.documentos_relacionados.filter((d) => d.documento.trim()),
      procedimiento: smart.procedimiento
        .filter((p) => p.accion.trim() || p.nombre.trim())
        .map((p, i) => ({ ...p, paso: i + 1 })),
      evidencia_requerida: smart.evidencia_requerida.filter((e) => e.evidencia.trim()),
      controles_clave: smart.controles_clave.filter((c) => c.control.trim()),
      kpis: smart.kpis.filter((k) => k.indicador.trim()),
      excepciones: smart.excepciones.filter((x) => x.excepcion.trim()),
      control_versiones: smart.control_versiones.filter((v) => v.version.trim()),
      checklist: smart.checklist.filter((c) => c.punto.trim()).map((c, i) => ({ ...c, n: i + 1 })),
    };
    try {
      if (override) {
        await override.guardar(limpio);
      } else {
        await guardar.mutateAsync({
          smart: limpio,
          nota_cambio: nota.trim() || undefined,
          // Sello de concurrencia: si otro guardó mientras editabas, el backend da 409.
          base_actualizado_en: sop!.actualizado_en,
        });
      }
      notify("Capa SMART guardada.");
      onDone();
    } catch (err) {
      // El 409 trae el motivo exacto (SOP firmado, o pisado por otro usuario).
      notify(err instanceof ApiError ? err.detail : "No se pudo guardar.", "error");
    }
  }

  const pendientes = smart.pendiente_confirmar.length;

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {override?.encabezado ?? (
          <div>
            <h2 className="text-sm font-semibold text-petrol-oscuro">Editar capa SMART</h2>
            <p className="text-xs text-carbon-suave">
              Los 9 campos base no se tocan desde acá. Al guardar se escribe un snapshot de versión.
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
        n="F."
        titulo="Información pendiente de confirmar"
        ayuda="Vacíos que el reformateo NO inventó. Al resolver uno: escribí el dato en su sección y quitá la línea de acá."
      >
        <ListaTexto
          items={smart.pendiente_confirmar}
          onChange={(v) => campo("pendiente_confirmar", v)}
          etiquetaAgregar="pendiente"
          placeholder="Ej: Aprobador final pendiente de confirmar"
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

      <Seccion n="3." titulo="Objetivo">
        <Textarea
          rows={3}
          value={smart.objetivo}
          onChange={(e) => campo("objetivo", e.target.value)}
          aria-label="Objetivo"
        />
      </Seccion>

      <Seccion n="4." titulo="Alcance">
        <Textarea
          rows={3}
          value={smart.alcance}
          onChange={(e) => campo("alcance", e.target.value)}
          aria-label="Alcance"
        />
      </Seccion>

      <Seccion n="5." titulo="Definiciones clave">
        <TablaEditable
          cols={[
            { key: "termino", label: "Término", ancho: "w-1/4" },
            { key: "definicion", label: "Definición", tipo: "area" },
          ]}
          filas={smart.definiciones as unknown as Fila[]}
          onChange={(f) => campo("definiciones", f as unknown as SopSmart["definiciones"])}
          filaVacia={() => ({ termino: "", definicion: "" })}
          etiquetaAgregar="definición"
        />
      </Seccion>

      <Seccion
        n="6."
        titulo="Responsables / Matriz RACI"
        ayuda="R = ejecuta · A = rinde cuentas · C = consultado · I = informado. Dejá vacío lo que el SOP no atribuya."
      >
        <TablaEditable
          cols={[
            { key: "actividad", label: "Actividad", ancho: "w-1/3" },
            { key: "responsible", label: "R" },
            { key: "accountable", label: "A" },
            { key: "consulted", label: "C" },
            { key: "informed", label: "I" },
          ]}
          filas={smart.raci as unknown as Fila[]}
          onChange={(f) => campo("raci", f as unknown as SopSmart["raci"])}
          filaVacia={() => ({
            actividad: "",
            responsible: "",
            accountable: "",
            consulted: "",
            informed: "",
          })}
          etiquetaAgregar="actividad"
        />
      </Seccion>

      <Seccion n="7." titulo="Frecuencia y deadlines">
        <Textarea
          rows={3}
          value={smart.frecuencia_deadlines}
          onChange={(e) => campo("frecuencia_deadlines", e.target.value)}
          aria-label="Frecuencia y deadlines"
        />
      </Seccion>

      <Seccion
        n="8."
        titulo="Sistemas y herramientas"
        ayuda="Descripción narrativa. Los sistemas enlazados del catálogo se editan en el formato base."
      >
        <ListaTexto
          items={smart.sistemas}
          onChange={(v) => campo("sistemas", v)}
          etiquetaAgregar="sistema"
        />
      </Seccion>

      <Seccion n="9." titulo="Documentos, reportes y formatos">
        <TablaEditable
          cols={[
            { key: "documento", label: "Documento", ancho: "w-1/4" },
            { key: "responsable", label: "Responsable" },
            { key: "frecuencia", label: "Frecuencia" },
            { key: "ubicacion", label: "Ubicación" },
            { key: "retencion", label: "Retención" },
          ]}
          filas={smart.documentos_relacionados as unknown as Fila[]}
          onChange={(f) => campo("documentos_relacionados", f as unknown as SopSmart["documentos_relacionados"])}
          filaVacia={() => ({
            documento: "",
            responsable: "",
            frecuencia: "",
            ubicacion: "",
            retencion: "",
          })}
          etiquetaAgregar="documento"
        />
      </Seccion>

      <Seccion
        n="10."
        titulo="Procedimiento paso a paso"
        ayuda="Cada paso debe decir qué se hace, quién, contra qué fuente y qué resultado se espera. El número se renumera solo."
      >
        <TablaEditable
          auto="paso"
          cols={[
            { key: "nombre", label: "Nombre" },
            { key: "responsable", label: "Responsable" },
            { key: "accion", label: "Acción", tipo: "area", ancho: "w-1/3" },
            { key: "sistema_documento", label: "Sistema / doc." },
            { key: "evidencia", label: "Evidencia" },
            { key: "control", label: "Control" },
          ]}
          filas={smart.procedimiento as unknown as Fila[]}
          onChange={(f) => campo("procedimiento", f as unknown as SopSmart["procedimiento"])}
          filaVacia={() => ({
            paso: 0,
            nombre: "",
            responsable: "",
            accion: "",
            sistema_documento: "",
            evidencia: "",
            control: "",
          })}
          etiquetaAgregar="paso"
        />
      </Seccion>

      <Seccion n="11." titulo="Evidencia requerida">
        <TablaEditable
          cols={[
            { key: "evidencia", label: "Evidencia", ancho: "w-1/4" },
            { key: "responsable", label: "Responsable" },
            { key: "revisor", label: "Revisor" },
            { key: "archivo", label: "Archivo" },
            { key: "retencion", label: "Retención" },
          ]}
          filas={smart.evidencia_requerida as unknown as Fila[]}
          onChange={(f) => campo("evidencia_requerida", f as unknown as SopSmart["evidencia_requerida"])}
          filaVacia={() => ({
            evidencia: "",
            responsable: "",
            revisor: "",
            archivo: "",
            retencion: "",
          })}
          etiquetaAgregar="evidencia"
        />
      </Seccion>

      <Seccion n="12." titulo="Controles clave">
        <TablaEditable
          cols={[
            { key: "control", label: "Control", ancho: "w-1/5" },
            { key: "riesgo", label: "Riesgo que mitiga" },
            { key: "responsable", label: "Responsable" },
            { key: "frecuencia", label: "Frecuencia" },
            { key: "evidencia", label: "Evidencia" },
            { key: "accion_correctiva", label: "Acción correctiva" },
          ]}
          filas={smart.controles_clave as unknown as Fila[]}
          onChange={(f) => campo("controles_clave", f as unknown as SopSmart["controles_clave"])}
          filaVacia={() => ({
            control: "",
            riesgo: "",
            responsable: "",
            frecuencia: "",
            evidencia: "",
            accion_correctiva: "",
          })}
          etiquetaAgregar="control"
        />
      </Seccion>

      <Seccion
        n="13."
        titulo="KPIs / criterios de cumplimiento"
        ayuda='Marcá "Recomendado" cuando el indicador no venía en el SOP original: así se distingue lo normativo de lo propuesto.'
      >
        <TablaEditable
          cols={[
            { key: "indicador", label: "Indicador", ancho: "w-2/5" },
            { key: "meta", label: "Meta" },
            { key: "recomendado", label: "Recomendado", tipo: "check" },
          ]}
          filas={smart.kpis as unknown as Fila[]}
          onChange={(f) => campo("kpis", f as unknown as SopSmart["kpis"])}
          filaVacia={() => ({ indicador: "", meta: "", recomendado: true })}
          etiquetaAgregar="KPI"
        />
      </Seccion>

      <Seccion n="14." titulo="Riesgos mitigados">
        <ListaTexto
          items={smart.riesgos_mitigados}
          onChange={(v) => campo("riesgos_mitigados", v)}
          etiquetaAgregar="riesgo"
        />
      </Seccion>

      <Seccion n="15." titulo="Excepciones y escalamiento">
        <TablaEditable
          cols={[
            { key: "excepcion", label: "Excepción", ancho: "w-1/4" },
            { key: "responsable_escalar", label: "Escala a" },
            { key: "aprobador", label: "Aprobador" },
            { key: "evidencia", label: "Evidencia" },
            { key: "tiempo_maximo", label: "Tiempo máx." },
          ]}
          filas={smart.excepciones as unknown as Fila[]}
          onChange={(f) => campo("excepciones", f as unknown as SopSmart["excepciones"])}
          filaVacia={() => ({
            excepcion: "",
            responsable_escalar: "",
            aprobador: "",
            evidencia: "",
            tiempo_maximo: "",
          })}
          etiquetaAgregar="excepción"
        />
      </Seccion>

      <Seccion n="16." titulo="Archivo y retención documental">
        <Textarea
          rows={2}
          value={smart.archivo_retencion}
          onChange={(e) => campo("archivo_retencion", e.target.value)}
          aria-label="Archivo y retención"
        />
      </Seccion>

      <Seccion n="17." titulo="Entrenamiento requerido">
        <Textarea
          rows={2}
          value={smart.entrenamiento}
          onChange={(e) => campo("entrenamiento", e.target.value)}
          aria-label="Entrenamiento"
        />
      </Seccion>

      <Seccion
        n="18."
        titulo="Revisión, aprobación y control de versiones"
        ayuda='El reformateo dejó "Reformateo SMART (IA) — validar" como preparado_por: reemplazalo al validar.'
      >
        <TablaEditable
          cols={[
            { key: "version", label: "Versión", ancho: "w-20" },
            { key: "fecha", label: "Fecha" },
            { key: "preparado_por", label: "Preparado por" },
            { key: "revisado_por", label: "Revisado por" },
            { key: "aprobado_por", label: "Aprobado por" },
            { key: "cambios", label: "Cambios", tipo: "area" },
            { key: "proxima_revision", label: "Próxima revisión" },
          ]}
          filas={smart.control_versiones as unknown as Fila[]}
          onChange={(f) => campo("control_versiones", f as unknown as SopSmart["control_versiones"])}
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

      <Seccion n="B." titulo="Checklist de cumplimiento">
        <TablaEditable
          auto="n"
          cols={[
            { key: "punto", label: "Punto", ancho: "w-1/2" },
            { key: "cumplido", label: "Cumplido" },
            { key: "comentarios", label: "Comentarios" },
          ]}
          filas={smart.checklist as unknown as Fila[]}
          onChange={(f) => campo("checklist", f as unknown as SopSmart["checklist"])}
          filaVacia={() => ({ n: 0, punto: "", cumplido: "", comentarios: "" })}
          etiquetaAgregar="punto"
        />
      </Seccion>

      {!override && (
        <div className="border-t border-linea pt-5">
          <Etiqueta htmlFor="nota_cambio">Nota de cambio (queda en la auditoría)</Etiqueta>
          <Input id="nota_cambio" value={nota} onChange={(e) => setNota(e.target.value)} />
        </div>
      )}

      <div className="flex gap-2 border-t border-linea pt-4">
        <Button type="submit" disabled={guardando}>
          {guardando ? "Guardando…" : "Guardar capa SMART"}
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
