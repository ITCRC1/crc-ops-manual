"use client";

import { ReactNode } from "react";

import type { SopSmart } from "@/lib/types";
import { Vacio } from "@/components/ui";

/** Sección numerada del estándar SOP SMART. */
function Seccion({
  n,
  titulo,
  children,
}: {
  n: string;
  titulo: string;
  children: ReactNode;
}) {
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

/** Párrafo con saltos de línea preservados; muestra Vacío si no hay texto. */
function Texto({ valor }: { valor?: string | null }) {
  if (!valor || !valor.trim()) return <Vacio />;
  return <p className="whitespace-pre-line">{valor}</p>;
}

/** Tabla genérica auditables con scroll horizontal en móvil. */
function Tabla({
  columnas,
  filas,
}: {
  columnas: string[];
  filas: (ReactNode[])[];
}) {
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
                  {celda === "" || celda == null ? <span className="text-carbon-suave/60">—</span> : celda}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Vinetas({ items }: { items: string[] }) {
  const limpio = items.filter((s) => s && s.trim());
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
 * Vista nativa del documento SOP SMART (18 secciones + apéndices A–F).
 * §1 (código) y §2 (nombre) los muestra el encabezado de la página.
 * Solo renderiza secciones con contenido; los vacíos quedan en "Información
 * pendiente de confirmar" (apéndice F). No inventa datos.
 */
export function SopSmartView({ smart }: { smart: SopSmart }) {
  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center rounded-full bg-petrol px-2.5 py-0.5 text-xs font-semibold text-white">
          Formato SOP SMART
        </span>
        <span className="font-mono text-xs text-carbon-suave">{smart.formato || "SMART-1.0"}</span>
      </div>

      {/* Apéndice F destacado arriba: qué falta confirmar */}
      {tiene(smart.pendiente_confirmar) && (
        <div className="mb-5 rounded-md border border-amber-400/50 bg-amber-50 px-4 py-3 dark:bg-amber-950/30">
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400">
            ⚠ Información pendiente de confirmar
          </p>
          <ul className="list-disc space-y-0.5 pl-5 text-sm text-carbon">
            {smart.pendiente_confirmar.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Apéndice A: resumen ejecutivo */}
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
        <Seccion n="3." titulo="Objetivo">
          <Texto valor={smart.objetivo} />
        </Seccion>

        <Seccion n="4." titulo="Alcance">
          <Texto valor={smart.alcance} />
        </Seccion>

        {tiene(smart.definiciones) && (
          <Seccion n="5." titulo="Definiciones clave">
            <Tabla
              columnas={["Término", "Definición"]}
              filas={smart.definiciones.map((d) => [d.termino, d.definicion])}
            />
          </Seccion>
        )}

        {tiene(smart.raci) && (
          <Seccion n="6." titulo="Responsables / Matriz RACI">
            <Tabla
              columnas={["Actividad", "R", "A", "C", "I"]}
              filas={smart.raci.map((r) => [
                r.actividad,
                r.responsible,
                r.accountable,
                r.consulted,
                r.informed,
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.frecuencia_deadlines) && (
          <Seccion n="7." titulo="Frecuencia y deadlines">
            <Texto valor={smart.frecuencia_deadlines} />
          </Seccion>
        )}

        {tiene(smart.sistemas) && (
          <Seccion n="8." titulo="Sistemas y herramientas">
            <div className="flex flex-wrap gap-2">
              {smart.sistemas.map((s, i) => (
                <span
                  key={i}
                  className="inline-flex items-center rounded-full border border-linea bg-petrol-tint px-2 py-0.5 text-xs font-medium text-petrol-oscuro"
                >
                  {s}
                </span>
              ))}
            </div>
          </Seccion>
        )}

        {tiene(smart.documentos_relacionados) && (
          <Seccion n="9." titulo="Documentos, reportes y formatos">
            <Tabla
              columnas={["Documento", "Responsable", "Frecuencia", "Ubicación", "Retención"]}
              filas={smart.documentos_relacionados.map((d) => [
                d.documento,
                d.responsable,
                d.frecuencia,
                d.ubicacion,
                d.retencion,
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.procedimiento) && (
          <Seccion n="10." titulo="Procedimiento paso a paso">
            <ol className="space-y-3">
              {smart.procedimiento.map((p, i) => (
                <li key={i} className="rounded-md border border-linea bg-fondo/40 p-3">
                  <p className="mb-1.5 text-sm font-semibold text-petrol-oscuro">
                    Paso {p.paso}
                    {p.nombre ? ` — ${p.nombre}` : ""}
                  </p>
                  {p.accion && <p className="mb-2 whitespace-pre-line text-sm text-carbon">{p.accion}</p>}
                  <dl className="grid gap-x-4 gap-y-1 text-xs sm:grid-cols-2">
                    {p.responsable && (
                      <div>
                        <dt className="inline font-semibold text-carbon-suave">Responsable: </dt>
                        <dd className="inline text-carbon">{p.responsable}</dd>
                      </div>
                    )}
                    {p.sistema_documento && (
                      <div>
                        <dt className="inline font-semibold text-carbon-suave">Sistema / doc: </dt>
                        <dd className="inline text-carbon">{p.sistema_documento}</dd>
                      </div>
                    )}
                    {p.evidencia && (
                      <div>
                        <dt className="inline font-semibold text-carbon-suave">Evidencia: </dt>
                        <dd className="inline text-carbon">{p.evidencia}</dd>
                      </div>
                    )}
                    {p.control && (
                      <div>
                        <dt className="inline font-semibold text-carbon-suave">Control: </dt>
                        <dd className="inline text-carbon">{p.control}</dd>
                      </div>
                    )}
                  </dl>
                </li>
              ))}
            </ol>
          </Seccion>
        )}

        {tiene(smart.evidencia_requerida) && (
          <Seccion n="11." titulo="Evidencia requerida">
            <Tabla
              columnas={["Evidencia", "Responsable", "Revisor", "Archivo", "Retención"]}
              filas={smart.evidencia_requerida.map((e) => [
                e.evidencia,
                e.responsable,
                e.revisor,
                e.archivo,
                e.retencion,
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.controles_clave) && (
          <Seccion n="12." titulo="Controles clave">
            <Tabla
              columnas={[
                "Control",
                "Riesgo mitigado",
                "Responsable",
                "Frecuencia",
                "Evidencia",
                "Acción correctiva",
              ]}
              filas={smart.controles_clave.map((c) => [
                c.control,
                c.riesgo,
                c.responsable,
                c.frecuencia,
                c.evidencia,
                c.accion_correctiva,
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.kpis) && (
          <Seccion n="13." titulo="KPIs / criterios de cumplimiento">
            <Tabla
              columnas={["Indicador", "Meta", "Origen"]}
              filas={smart.kpis.map((k) => [
                k.indicador,
                k.meta,
                k.recomendado ? (
                  <span className="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700 dark:bg-amber-950/40 dark:text-amber-400">
                    Recomendado (validar)
                  </span>
                ) : (
                  "Del SOP original"
                ),
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.riesgos_mitigados) && (
          <Seccion n="14." titulo="Riesgos mitigados">
            <Vinetas items={smart.riesgos_mitigados} />
          </Seccion>
        )}

        {tiene(smart.excepciones) && (
          <Seccion n="15." titulo="Excepciones y escalamiento">
            <Tabla
              columnas={["Excepción", "Escala", "Aprobador", "Evidencia", "Tiempo máx."]}
              filas={smart.excepciones.map((e) => [
                e.excepcion,
                e.responsable_escalar,
                e.aprobador,
                e.evidencia,
                e.tiempo_maximo,
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.archivo_retencion) && (
          <Seccion n="16." titulo="Archivo y retención documental">
            <Texto valor={smart.archivo_retencion} />
          </Seccion>
        )}

        {tiene(smart.entrenamiento) && (
          <Seccion n="17." titulo="Entrenamiento requerido">
            <Texto valor={smart.entrenamiento} />
          </Seccion>
        )}

        {tiene(smart.control_versiones) && (
          <Seccion n="18." titulo="Revisión, aprobación y control de versiones">
            <Tabla
              columnas={[
                "Versión",
                "Fecha",
                "Preparado",
                "Revisado",
                "Aprobado",
                "Cambios",
                "Próxima rev.",
              ]}
              filas={smart.control_versiones.map((v) => [
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

        {tiene(smart.checklist) && (
          <Seccion n="B." titulo="Checklist de cumplimiento">
            <Tabla
              columnas={["#", "Punto de control", "Cumplido", "Comentarios"]}
              filas={smart.checklist.map((c) => [
                String(c.n),
                c.punto,
                c.cumplido,
                c.comentarios,
              ])}
            />
          </Seccion>
        )}
      </div>
    </div>
  );
}
