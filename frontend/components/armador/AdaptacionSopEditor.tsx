"use client";

import { useState } from "react";

import { EstadoBadge } from "@/components/EstadoBadge";
import { SopSmartForm } from "@/components/SopSmartForm";
import { SopSmartView } from "@/components/SopSmartView";
import { useToast } from "@/components/toast";
import {
  Button,
  CargandoBloque,
  Card,
  Chip,
  EstadoError,
  Input,
  Select,
  Textarea,
} from "@/components/ui";
import { ApiError } from "@/lib/api";
import {
  useActualizarOverridesSop,
  useActualizarSmartOverridesSop,
  useAdaptarSop,
  usePropiedadSop,
} from "@/lib/hooks";
import type { SopSmart } from "@/lib/types";

type Tipo = "nombre" | "texto" | "proc" | "frecuencia";

// SMART efectiva → deltas por sección contra el master (solo top-level keys que difieren).
// `formato` no es una sección editable. En `local` se guarda la SMART completa (sin master).
function diffSmartPorSeccion(
  local: Record<string, unknown>,
  master: Record<string, unknown>,
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const k of Object.keys(local)) {
    if (k === "formato") continue;
    if (JSON.stringify(local[k]) !== JSON.stringify(master[k] ?? null)) out[k] = local[k];
  }
  return out;
}

const SECCIONES: { key: string; label: string; tipo: Tipo }[] = [
  { key: "nombre", label: "Nombre", tipo: "nombre" },
  { key: "proposito", label: "Propósito", tipo: "texto" },
  { key: "evaluacion_riesgos", label: "Evaluación de riesgos", tipo: "texto" },
  { key: "controles_existentes", label: "Controles existentes", tipo: "texto" },
  { key: "procedimiento", label: "Procedimiento", tipo: "proc" },
  { key: "responsables", label: "Responsables", tipo: "texto" },
  { key: "evidencia", label: "Evidencia / reportes", tipo: "texto" },
  { key: "frecuencia_revision", label: "Frecuencia de revisión", tipo: "frecuencia" },
];

const FREQ: [string, string][] = [
  ["", "— sin definir —"],
  ["mensual", "Mensual"],
  ["trimestral", "Trimestral"],
  ["semestral", "Semestral"],
  ["anual", "Anual"],
  ["por_cambio", "Por cambio"],
];
const FREQ_LABEL = Object.fromEntries(FREQ);

function procALineas(v: unknown): string[] {
  if (!v) return [];
  if (typeof v === "string") return v.split("\n").filter((s) => s.trim());
  const o = v as Record<string, unknown>;
  const l = o.secciones ?? o.pasos ?? o.contenido;
  return Array.isArray(l) ? l.map(String) : [];
}

function valorATexto(tipo: Tipo, v: unknown): string {
  if (tipo === "proc") return procALineas(v).join("\n");
  return v == null ? "" : String(v);
}

function textoAValor(tipo: Tipo, texto: string): unknown {
  if (tipo === "proc") {
    const lineas = texto.split("\n").map((s) => s.trim()).filter(Boolean);
    return lineas.length ? { secciones: lineas } : null;
  }
  if (tipo === "frecuencia") return texto || null;
  return texto.trim() || "";
}

export function AdaptacionSopEditor({
  propId,
  psId,
  codigo,
  nombre,
  puedeGestionar,
  onVolver,
}: {
  propId: string;
  psId: string;
  codigo: string;
  nombre: string;
  puedeGestionar: boolean;
  onVolver: () => void;
}) {
  const { notify } = useToast();
  const { data: det, isLoading, isError, error } = usePropiedadSop(psId);
  const actualizar = useActualizarOverridesSop(propId, psId);
  const guardarSmart = useActualizarSmartOverridesSop(propId, psId);
  const adaptar = useAdaptarSop(propId, psId);
  const [editando, setEditando] = useState<string | null>(null);
  const [borrador, setBorrador] = useState("");
  const [vista, setVista] = useState<"base" | "smart">("base");

  if (isLoading) return <CargandoBloque />;
  if (isError || !det) return <EstadoError mensaje={(error as Error)?.message} />;

  const esLocalPuro = det.modo === "local";
  const esAdaptado = det.modo === "adaptado";
  const esAdoptado = det.modo === "adoptado";
  const overrides = det.overrides ?? {};
  const efectivo = det.contenido_efectivo ?? {};
  const master = det.contenido_master ?? {};
  const smartMaster = det.smart_master ?? {};
  const smartEfectivo = det.smart_efectivo ?? {};
  const smartOverrides = det.smart_overrides ?? {};
  const tieneSmart =
    Object.keys(smartMaster).some((k) => k !== "formato") ||
    Object.keys(smartEfectivo).some((k) => k !== "formato");
  const seccionesSmartLocales = Object.keys(smartOverrides).filter((k) => k !== "formato").length;

  async function guardarSmartOverrides(limpio: SopSmart) {
    const payload = esLocalPuro
      ? (limpio as unknown as Record<string, unknown>)
      : diffSmartPorSeccion(limpio as unknown as Record<string, unknown>, smartMaster);
    await guardarSmart.mutateAsync({ smart_overrides: payload });
  }

  function seccionEsLocal(key: string): boolean {
    if (esLocalPuro) return true;
    if (esAdaptado) return Object.prototype.hasOwnProperty.call(overrides, key);
    return false; // adoptado: todo heredado
  }

  async function guardarSeccion(key: string, tipo: Tipo) {
    const valor = textoAValor(tipo, borrador);
    try {
      if (esLocalPuro) {
        await actualizar.mutateAsync({ campos_locales: { ...(det!.campos_locales ?? {}), [key]: valor } });
      } else {
        await actualizar.mutateAsync({ overrides: { ...overrides, [key]: valor } });
      }
      setEditando(null);
      notify("Sección actualizada.");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo guardar.", "error");
    }
  }

  async function restaurarSeccion(key: string) {
    const nuevo = { ...overrides };
    delete nuevo[key];
    try {
      await actualizar.mutateAsync({ overrides: nuevo });
      notify("Sección restaurada al master.");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo restaurar.", "error");
    }
  }

  async function convertirAAdaptado() {
    try {
      await adaptar.mutateAsync();
      notify("SOP adaptado: ya podés personalizar secciones.");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo adaptar.", "error");
    }
  }

  function abrirEdicion(key: string, tipo: Tipo) {
    setBorrador(valorATexto(tipo, efectivo[key]));
    setEditando(key);
  }

  function render(tipo: Tipo, v: unknown) {
    if (tipo === "proc") {
      const l = procALineas(v);
      if (!l.length) return <span className="text-carbon-suave/70">—</span>;
      return (
        <ul className="list-disc space-y-1 pl-5">
          {l.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
      );
    }
    if (tipo === "frecuencia") return <span>{FREQ_LABEL[String(v ?? "")] ?? "—"}</span>;
    const t = v == null ? "" : String(v);
    return t ? <p className="whitespace-pre-wrap">{t}</p> : <span className="text-carbon-suave/70">—</span>;
  }

  return (
    <div>
      <button onClick={onVolver} className="mb-4 text-sm text-petrol-oscuro hover:underline">
        ← Volver a SOPs
      </button>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="font-mono text-xs text-carbon-suave">{codigo}</span>
        <h3 className="text-base font-semibold text-petrol-oscuro">{nombre}</h3>
        <EstadoBadge estado={det.estado} />
        <Chip>
          {esAdoptado ? "Adoptado" : esAdaptado ? "Adaptado" : "Local"}
        </Chip>
      </div>

      <div className="mb-4 flex gap-1 border-b border-linea">
        {(["base", "smart"] as const).map((v) => (
          <button
            key={v}
            onClick={() => setVista(v)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${
              vista === v
                ? "border-petrol-oscuro text-petrol-oscuro"
                : "border-transparent text-carbon-suave hover:text-carbon"
            }`}
          >
            {v === "base" ? "Campos base (9)" : "Capa SMART"}
            {v === "smart" && seccionesSmartLocales > 0 && (
              <span className="ml-1 rounded-full bg-petrol-tint px-1.5 text-xs text-petrol-oscuro">
                {seccionesSmartLocales}
              </span>
            )}
          </button>
        ))}
      </div>

      {esAdoptado && (
        <Card className="mb-4 border-petrol/30 bg-petrol-tint/30 p-4">
          <p className="text-sm text-carbon">
            Este SOP está <strong>adoptado</strong>: usa el documento maestro tal cual. Para cambiar
            una o más secciones en esta propiedad, adaptalo — el resto seguirá heredando del maestro.
          </p>
          {puedeGestionar && (
            <Button className="mt-3" onClick={convertirAAdaptado} disabled={adaptar.isPending}>
              {adaptar.isPending ? "Adaptando…" : "Adaptar para personalizar"}
            </Button>
          )}
        </Card>
      )}

      {vista === "base" && esAdaptado && (
        <p className="mb-4 text-xs text-carbon-suave">
          Cada sección personalizada muestra la <strong>versión local</strong> del hotel y oculta la
          del maestro. Las no personalizadas siguen heredando del maestro y se actualizan si este
          cambia. La versión adaptada queda en borrador hasta su firma local.
        </p>
      )}

      {vista === "base" && (
      <div className="space-y-3">
        {SECCIONES.map((s) => {
          const local = seccionEsLocal(s.key);
          const editable = puedeGestionar && !esAdoptado;
          const enEdicion = editando === s.key;
          return (
            <Card key={s.key} className="p-4">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <h4 className="text-sm font-semibold text-carbon">{s.label}</h4>
                {esAdaptado &&
                  (local ? (
                    <Chip>Local</Chip>
                  ) : (
                    <span className="text-xs text-carbon-suave">Heredado del maestro</span>
                  ))}
                {editable && !enEdicion && (
                  <div className="ml-auto flex gap-2">
                    <button
                      onClick={() => abrirEdicion(s.key, s.tipo)}
                      className="text-xs text-petrol-oscuro hover:underline"
                    >
                      {local ? "Editar" : "Personalizar"}
                    </button>
                    {esAdaptado && local && (
                      <button
                        onClick={() => restaurarSeccion(s.key)}
                        disabled={actualizar.isPending}
                        className="text-xs text-carbon-suave hover:text-rechazado hover:underline disabled:opacity-50"
                      >
                        Restaurar del maestro
                      </button>
                    )}
                  </div>
                )}
              </div>

              {enEdicion ? (
                <div className="space-y-2">
                  {s.tipo === "nombre" ? (
                    <Input value={borrador} onChange={(e) => setBorrador(e.target.value)} />
                  ) : s.tipo === "frecuencia" ? (
                    <Select value={borrador} onChange={(e) => setBorrador(e.target.value)}>
                      {FREQ.map(([v, l]) => (
                        <option key={v} value={v}>
                          {l}
                        </option>
                      ))}
                    </Select>
                  ) : (
                    <Textarea
                      rows={s.tipo === "proc" ? 6 : 4}
                      value={borrador}
                      onChange={(e) => setBorrador(e.target.value)}
                    />
                  )}
                  {s.tipo === "proc" && (
                    <p className="text-xs text-carbon-suave">Una línea por paso/sección.</p>
                  )}
                  {esAdaptado && (
                    <details className="text-xs text-carbon-suave">
                      <summary className="cursor-pointer">Ver versión del maestro</summary>
                      <div className="mt-1 rounded-md bg-fondo p-2">{render(s.tipo, master[s.key])}</div>
                    </details>
                  )}
                  <div className="flex gap-2">
                    <Button onClick={() => guardarSeccion(s.key, s.tipo)} disabled={actualizar.isPending}>
                      {actualizar.isPending ? "Guardando…" : "Guardar sección"}
                    </Button>
                    <Button variant="secondary" onClick={() => setEditando(null)}>
                      Cancelar
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-carbon">{render(s.tipo, efectivo[s.key])}</div>
              )}
            </Card>
          );
        })}
      </div>
      )}

      {vista === "smart" &&
        (!puedeGestionar ? (
          <Card className="p-5">
            <SopSmartView smart={smartEfectivo as unknown as SopSmart} />
          </Card>
        ) : esAdoptado ? (
          <Card className="p-4 text-sm text-carbon">
            Adaptá el SOP (botón de arriba) para personalizar su capa SMART en esta propiedad. El
            resto de las secciones seguirá heredando del maestro.
          </Card>
        ) : !esLocalPuro && !tieneSmart ? (
          <Card className="p-4 text-sm text-carbon-suave">
            Este SOP maestro todavía no tiene capa SMART, así que no hay secciones que adaptar.
          </Card>
        ) : (
          <Card className="p-5">
            <SopSmartForm
              onDone={() => setVista("base")}
              override={{
                inicial: smartEfectivo as unknown as SopSmart,
                guardar: guardarSmartOverrides,
                guardando: guardarSmart.isPending,
                sucioKey: `smart-prop:${psId}`,
                encabezado: (
                  <div>
                    <h2 className="text-sm font-semibold text-petrol-oscuro">
                      Capa SMART — {esLocalPuro ? "SOP local" : "adaptación de esta propiedad"}
                    </h2>
                    <p className="text-xs text-carbon-suave">
                      {esLocalPuro
                        ? "Editás la ficha SMART completa de este SOP local."
                        : `Cada sección que cambies se guarda como local; el resto hereda del maestro. ${seccionesSmartLocales} sección(es) personalizada(s).`}
                    </p>
                  </div>
                ),
              }}
            />
          </Card>
        ))}
    </div>
  );
}
