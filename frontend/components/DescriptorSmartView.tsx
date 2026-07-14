"use client";

import { ReactNode } from "react";

import type { JdSmart } from "@/lib/types";
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

function Chips({ items }: { items: string[] }) {
  if (items.length === 0) return <Vacio />;
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((s, i) => (
        <span
          key={i}
          className="inline-flex items-center rounded-full border border-linea bg-petrol-tint px-2 py-0.5 text-xs font-medium text-petrol-oscuro"
        >
          {s}
        </span>
      ))}
    </div>
  );
}

const tiene = (v: unknown) =>
  Array.isArray(v) ? v.length > 0 : typeof v === "string" ? v.trim().length > 0 : !!v;

/**
 * Vista nativa del documento JD SMART (~30 secciones + crosswalk a SOPs).
 * Solo renderiza secciones con contenido; los vacíos quedan en "pendiente de
 * confirmar". No inventa datos.
 */
export function DescriptorSmartView({ smart }: { smart: JdSmart }) {
  const funciones = smart.funciones || {};
  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center rounded-full bg-petrol px-2.5 py-0.5 text-xs font-semibold text-white">
          Formato JD SMART
        </span>
        <span className="font-mono text-xs text-carbon-suave">{smart.formato || "JD-SMART-1.0"}</span>
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
        {tiene(smart.resumen_puesto) && (
          <Seccion n="6." titulo="Resumen del puesto">
            <Texto valor={smart.resumen_puesto} />
          </Seccion>
        )}

        {tiene(smart.objetivo) && (
          <Seccion n="7." titulo="Objetivo del puesto">
            <Texto valor={smart.objetivo} />
          </Seccion>
        )}

        {tiene(smart.responsabilidades_smart) && (
          <Seccion n="8." titulo="Responsabilidades SMART">
            <Tabla
              columnas={["#", "Responsabilidad", "SOP", "Rol", "Frec.", "Evidencia", "KPI"]}
              filas={smart.responsabilidades_smart!.map((r) => [
                r.n != null ? String(r.n) : "",
                r.responsabilidad,
                r.sop_relacionado,
                r.rol_sop,
                r.frecuencia,
                r.evidencia,
                r.kpi,
              ])}
            />
          </Seccion>
        )}

        {(tiene(funciones.diarias) ||
          tiene(funciones.semanales) ||
          tiene(funciones.mensuales) ||
          tiene(funciones.por_evento)) && (
          <Seccion n="9." titulo="Funciones por frecuencia">
            <div className="grid gap-3 sm:grid-cols-2">
              {tiene(funciones.diarias) && (
                <div>
                  <p className="mb-1 text-xs font-semibold text-carbon-suave">Diarias</p>
                  <Vinetas items={funciones.diarias} />
                </div>
              )}
              {tiene(funciones.semanales) && (
                <div>
                  <p className="mb-1 text-xs font-semibold text-carbon-suave">Semanales</p>
                  <Vinetas items={funciones.semanales} />
                </div>
              )}
              {tiene(funciones.mensuales) && (
                <div>
                  <p className="mb-1 text-xs font-semibold text-carbon-suave">Mensuales</p>
                  <Vinetas items={funciones.mensuales} />
                </div>
              )}
              {tiene(funciones.por_evento) && (
                <div>
                  <p className="mb-1 text-xs font-semibold text-carbon-suave">Por evento</p>
                  <Vinetas items={funciones.por_evento} />
                </div>
              )}
            </div>
          </Seccion>
        )}

        {tiene(smart.sops_relacionados) && (
          <Seccion n="10." titulo="SOPs SMART relacionados">
            <Tabla
              columnas={["Cód.", "Nombre SOP", "Rol", "Frec.", "Evidencia", "Estado"]}
              filas={smart.sops_relacionados!.map((s) => [
                <span key="c" className="font-mono text-xs">
                  {s.codigo_sop}
                </span>,
                s.nombre_sop,
                s.rol,
                s.frecuencia,
                s.evidencia,
                s.estado,
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.sops_recomendados) && (
          <Seccion n="12." titulo="SOPs recomendados para creación">
            <Tabla
              columnas={["Responsabilidad sin SOP", "SOP recomendado", "Prioridad", "Depto."]}
              filas={smart.sops_recomendados!.map((s) => [
                s.responsabilidad_sin_sop,
                s.sop_recomendado,
                s.prioridad,
                s.depto,
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.kpis) && (
          <Seccion n="13." titulo="KPIs / indicadores de desempeño">
            <Tabla
              columnas={["KPI", "Meta", "Frecuencia", "Fuente", "Origen"]}
              filas={smart.kpis!.map((k) => [
                k.kpi,
                k.meta,
                k.frecuencia,
                k.fuente,
                k.recomendado ? (
                  <span
                    key="r"
                    className="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700 dark:bg-amber-950/40 dark:text-amber-400"
                  >
                    Recomendado (validar)
                  </span>
                ) : (
                  "Del JD original"
                ),
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.autoridad) && (
          <Seccion n="14." titulo="Autoridad y nivel de decisión">
            <Tabla
              columnas={["Tipo de decisión", "Puede aprobar", "Debe consultar", "Debe escalar"]}
              filas={smart.autoridad!.map((a) => [
                a.tipo_decision,
                a.puede_aprobar,
                a.debe_consultar,
                a.debe_escalar,
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.relaciones_internas) && (
          <Seccion n="15." titulo="Relaciones internas clave">
            <Tabla
              columnas={["Área / Puesto", "Motivo", "Frecuencia"]}
              filas={smart.relaciones_internas!.map((r) => [r.area_puesto, r.motivo, r.frecuencia])}
            />
          </Seccion>
        )}

        {tiene(smart.relaciones_externas) && (
          <Seccion n="16." titulo="Relaciones externas clave">
            <Vinetas items={smart.relaciones_externas} />
          </Seccion>
        )}

        {tiene(smart.sistemas) && (
          <Seccion n="17." titulo="Sistemas, herramientas y reportes">
            <Tabla
              columnas={["Sistema / Reporte", "Uso", "Frecuencia", "SOP"]}
              filas={smart.sistemas!.map((s) => [
                s.sistema,
                s.uso,
                s.frecuencia,
                s.sop_relacionado,
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.documentos) && (
          <Seccion n="18." titulo="Documentos y entregables">
            <Tabla
              columnas={["Documento", "Responsable", "Frecuencia", "Revisor", "Ubicación", "SOP"]}
              filas={smart.documentos!.map((d) => [
                d.documento,
                d.responsable,
                d.frecuencia,
                d.revisor,
                d.ubicacion,
                d.sop_relacionado,
              ])}
            />
          </Seccion>
        )}

        {tiene(smart.competencias_tecnicas) && (
          <Seccion n="19." titulo="Competencias técnicas">
            <Vinetas items={smart.competencias_tecnicas} />
          </Seccion>
        )}

        {tiene(smart.competencias_conductuales) && (
          <Seccion n="20." titulo="Competencias conductuales">
            <Vinetas items={smart.competencias_conductuales} />
          </Seccion>
        )}

        {tiene(smart.experiencia_formacion) && (
          <Seccion n="21." titulo="Experiencia y formación">
            <Texto valor={smart.experiencia_formacion} />
          </Seccion>
        )}

        {tiene(smart.cumplimiento_confidencialidad) && (
          <Seccion n="22." titulo="Cumplimiento, control interno y confidencialidad">
            <Vinetas items={smart.cumplimiento_confidencialidad} />
          </Seccion>
        )}

        {tiene(smart.estandares_servicio) && (
          <Seccion n="23." titulo="Estándares de servicio y cultura">
            <Vinetas items={smart.estandares_servicio} />
          </Seccion>
        )}

        {tiene(smart.horario_condiciones) && (
          <Seccion n="24." titulo="Horario y condiciones operativas">
            <Texto valor={smart.horario_condiciones} />
          </Seccion>
        )}

        {tiene(smart.perfil_exito) && (
          <Seccion n="25." titulo="Perfil de éxito">
            <Texto valor={smart.perfil_exito} />
          </Seccion>
        )}

        {tiene(smart.ciclo_revision) && (
          <Seccion n="26." titulo="Ciclo de revisión del desempeño">
            <Texto valor={smart.ciclo_revision} />
          </Seccion>
        )}

        {tiene(smart.control_versiones) && (
          <Seccion n="27." titulo="Revisión, aprobación y control de versiones">
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

        {tiene(smart.checklist) && (
          <Seccion n="29." titulo="Checklist de validación">
            <Tabla
              columnas={["#", "Punto de validación", "Cumplido", "Comentarios"]}
              filas={smart.checklist!.map((c) => [
                c.n != null ? String(c.n) : "",
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
