"use client";

import { ReactNode } from "react";

import type { TrainingSmart } from "@/lib/types";
import { Vacio } from "@/components/ui";

function Seccion({ n, titulo, children }: { n: string; titulo: string; children: ReactNode }) {
  return (
    <section className="border-t border-linea py-5 first:border-t-0 first:pt-0">
      <h3 className="mb-2.5 flex items-baseline gap-2 text-sm font-semibold text-petrol-oscuro">
        <span className="font-mono text-xs text-carbon-suave">{n}</span>
        <span className="uppercase tracking-wide">{titulo}</span>
      </h3>
      <div className="text-sm leading-relaxed text-carbon">{children}</div>
    </section>
  );
}

function Texto({ valor }: { valor?: string | null }) {
  if (!valor || !valor.trim()) return <Vacio />;
  return <p className="whitespace-pre-line">{valor}</p>;
}

function Tabla({ columnas, filas }: { columnas: string[]; filas: ReactNode[][] }) {
  if (filas.length === 0) return <Vacio />;
  return (
    <div className="overflow-x-auto rounded-md border border-linea">
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="bg-petrol-tint/60">
            {columnas.map((c) => (
              <th
                key={c}
                className="whitespace-nowrap px-3 py-2 text-xs font-semibold uppercase tracking-wide text-petrol-oscuro"
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map((fila, i) => (
            <tr key={i} className="border-t border-linea align-top">
              {fila.map((celda, j) => (
                <td key={j} className="px-3 py-2 text-carbon">
                  {celda === "" || celda == null ? (
                    <span className="text-carbon-suave/60">—</span>
                  ) : (
                    celda
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Vinetas({ items }: { items?: string[] }) {
  const limpio = (items || []).filter((s) => s && s.trim());
  if (limpio.length === 0) return <Vacio />;
  return (
    <ul className="list-disc space-y-1 pl-5">
      {limpio.map((s, i) => (
        <li key={i}>{s}</li>
      ))}
    </ul>
  );
}

const tiene = (v: unknown) =>
  Array.isArray(v) ? v.length > 0 : typeof v === "string" ? v.trim().length > 0 : !!v;

/**
 * Vista nativa de la capa Training SMART de un manual de capacitación.
 * Solo renderiza secciones con contenido; los vacíos quedan en "pendiente de
 * confirmar". No inventa datos.
 */
export function TrainingSmartView({ smart }: { smart: TrainingSmart }) {
  const vig = smart.vigencia || {};
  const tieneVigencia =
    tiene(vig.vigencia_meses) || tiene(vig.condiciones_recert) || vig.requiere_recertificacion;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center rounded-full bg-petrol px-2.5 py-0.5 text-xs font-semibold text-white">
          Formato Training SMART
        </span>
        <span className="font-mono text-xs text-carbon-suave">
          {smart.formato || "TRAIN-SMART-1.0"}
        </span>
        {smart.obligatoria && (
          <span className="inline-flex items-center rounded-full border border-linea bg-petrol-tint px-2 py-0.5 text-xs font-medium text-petrol-oscuro">
            Obligatoria
          </span>
        )}
      </div>

      {tiene(smart.pendiente_confirmar) && (
        <div className="mb-5 rounded-md border border-amber-400/50 bg-amber-50 px-4 py-3 dark:bg-amber-950/30">
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400">
            ⚠ Información pendiente de confirmar / validar
          </p>
          <ul className="list-disc space-y-0.5 pl-5 text-sm text-carbon">
            {smart.pendiente_confirmar!.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {tiene(smart.resumen_ejecutivo) && (
        <div className="mb-5 rounded-md border-l-4 border-petrol bg-petrol-tint/40 px-4 py-3">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-petrol-oscuro">
            Resumen ejecutivo
          </p>
          <p className="whitespace-pre-line text-sm leading-relaxed text-carbon">
            {smart.resumen_ejecutivo}
          </p>
        </div>
      )}

      <div>
        {tiene(smart.objetivo) && (
          <Seccion n="1." titulo="Objetivo de la capacitación">
            <Texto valor={smart.objetivo} />
          </Seccion>
        )}

        {(tiene(smart.modalidad) || tiene(smart.duracion) || tiene(smart.imparte)) && (
          <Seccion n="2." titulo="Modalidad, duración e instructor">
            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <p className="mb-1 text-xs font-semibold text-carbon-suave">Modalidad</p>
                <Texto valor={smart.modalidad} />
              </div>
              <div>
                <p className="mb-1 text-xs font-semibold text-carbon-suave">Duración</p>
                <Texto valor={smart.duracion} />
              </div>
              <div>
                <p className="mb-1 text-xs font-semibold text-carbon-suave">Imparte</p>
                <Texto valor={smart.imparte} />
              </div>
            </div>
          </Seccion>
        )}

        {tiene(smart.dirigido_a) && (
          <Seccion n="3." titulo="Dirigido a">
            <Vinetas items={smart.dirigido_a} />
          </Seccion>
        )}

        {tiene(smart.prerequisitos) && (
          <Seccion n="4." titulo="Prerequisitos">
            <Vinetas items={smart.prerequisitos} />
          </Seccion>
        )}

        {tiene(smart.contenidos) && (
          <Seccion n="5." titulo="Contenidos / temario">
            <Tabla
              columnas={["#", "Tema", "Descripción", "Material ref."]}
              filas={smart.contenidos!.map((c) => [
                c.n != null ? String(c.n) : "",
                c.tema,
                c.descripcion,
                c.material_ref,
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.materiales) && (
          <Seccion n="6." titulo="Materiales y recursos">
            <Tabla
              columnas={["Material", "Tipo", "Referencia"]}
              filas={smart.materiales!.map((m) => [m.material, m.tipo, m.referencia])}
            />
          </Seccion>
        )}

        {tiene(smart.evaluacion) && (
          <Seccion n="7." titulo="Evaluación">
            <Tabla
              columnas={["Método", "Criterio de aprobación", "Nota mínima"]}
              filas={smart.evaluacion!.map((e) => [
                e.metodo,
                e.criterio_aprobacion,
                e.nota_minima,
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.evidencia) && (
          <Seccion n="8." titulo="Evidencia y registros">
            <Tabla
              columnas={["Evidencia", "Responsable", "Archivo", "Retención"]}
              filas={smart.evidencia!.map((e) => [
                e.evidencia,
                e.responsable,
                e.archivo,
                e.retencion,
              ])}
            />
          </Seccion>
        )}

        {tieneVigencia && (
          <Seccion n="9." titulo="Vigencia y recertificación">
            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <p className="mb-1 text-xs font-semibold text-carbon-suave">Vigencia (meses)</p>
                <Texto valor={vig.vigencia_meses} />
              </div>
              <div>
                <p className="mb-1 text-xs font-semibold text-carbon-suave">
                  Requiere recertificación
                </p>
                <p>{vig.requiere_recertificacion ? "Sí" : "No"}</p>
              </div>
              <div>
                <p className="mb-1 text-xs font-semibold text-carbon-suave">
                  Condiciones de recert.
                </p>
                <Texto valor={vig.condiciones_recert} />
              </div>
            </div>
          </Seccion>
        )}

        {(smart.obligatoria || tiene(smart.base_obligatoriedad)) && (
          <Seccion n="10." titulo="Obligatoriedad">
            <p className="mb-1">
              <span className="font-medium">
                {smart.obligatoria ? "Capacitación obligatoria" : "Capacitación opcional"}
              </span>
            </p>
            {tiene(smart.base_obligatoriedad) ? (
              <Texto valor={smart.base_obligatoriedad} />
            ) : (
              <p className="text-xs text-carbon-suave">Base de obligatoriedad pendiente de validar.</p>
            )}
          </Seccion>
        )}

        {tiene(smart.kpis) && (
          <Seccion n="11." titulo="KPIs / indicadores">
            <Tabla
              columnas={["Indicador", "Meta", "Origen"]}
              filas={smart.kpis!.map((k) => [
                k.indicador,
                k.meta,
                k.recomendado ? (
                  <span
                    key="r"
                    className="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700 dark:bg-amber-950/40 dark:text-amber-400"
                  >
                    Recomendado (validar)
                  </span>
                ) : (
                  "Definido"
                ),
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.control_versiones) && (
          <Seccion n="12." titulo="Revisión, aprobación y control de versiones">
            <Tabla
              columnas={["Versión", "Fecha", "Preparado", "Revisado", "Aprobado", "Cambios", "Próx. rev."]}
              filas={smart.control_versiones!.map((v) => [
                v.version,
                v.fecha,
                v.preparado_por,
                v.revisado_por,
                v.aprobado_por,
                v.cambios,
                v.proxima_revision,
              ])}
            />
          </Seccion>
        )}
      </div>
    </div>
  );
}
