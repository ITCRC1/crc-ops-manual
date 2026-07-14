"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useState } from "react";

import { AccionesEstado } from "@/components/AccionesEstado";
import { EstadoBadge, TipoBadge } from "@/components/EstadoBadge";
import { HistorialVersiones } from "@/components/HistorialVersiones";
import { PanelFirmas } from "@/components/PanelFirmas";
import { ProgramacionPanel } from "@/components/ProgramacionPanel";
import { SopForm } from "@/components/SopForm";
import { SopSmartForm } from "@/components/SopSmartForm";
import { SopSmartView } from "@/components/SopSmartView";
import { Button, Campo, Card, CargandoBloque, Chip, EstadoError, Vacio } from "@/components/ui";
import { apiDownload, guardarBlob } from "@/lib/api";
import { tieneRol, useAuth } from "@/lib/auth";
import { confirmarSalida } from "@/lib/cambios-sin-guardar";
import { useColaboradores, useDepartamentos, useSop } from "@/lib/hooks";

const FRECUENCIA_LABEL: Record<string, string> = {
  mensual: "Mensual",
  trimestral: "Trimestral",
  semestral: "Semestral",
  anual: "Anual",
  por_cambio: "Por cambio",
};
const EDITABLES = new Set(["borrador", "en_revision", "rechazado"]);

function Texto({ valor }: { valor: string | null }) {
  if (!valor) return <Vacio />;
  return <p className="whitespace-pre-line">{valor}</p>;
}

function Procedimiento({ valor }: { valor: unknown }) {
  if (!valor) return <Vacio />;
  if (typeof valor === "string") return <p className="whitespace-pre-line">{valor}</p>;
  const obj = valor as Record<string, unknown>;
  const lista = obj.secciones ?? obj.pasos ?? obj.contenido;
  if (Array.isArray(lista)) {
    return (
      <ul className="list-disc space-y-1 pl-5">
        {lista.map((s, i) => (
          <li key={i}>{String(s)}</li>
        ))}
      </ul>
    );
  }
  return (
    <pre className="overflow-x-auto whitespace-pre-wrap rounded bg-fondo p-3 text-xs">
      {JSON.stringify(valor, null, 2)}
    </pre>
  );
}

export default function SopDetallePage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { data: sop, isLoading, isError, error } = useSop(id);
  const { data: departamentos } = useDepartamentos();
  // Al crear un SOP se llega con ?smart=nuevo: política de "todo SOP es SMART" → abrimos
  // directo el editor SMART para completar el contenido, sin pasar por el formato base.
  const abrirSmartNuevo = useSearchParams().get("smart") === "nuevo";
  const [editando, setEditando] = useState(false);
  const [editandoSmart, setEditandoSmart] = useState(abrirSmartNuevo);
  const [verBase, setVerBase] = useState(false);
  const [descargando, setDescargando] = useState(false);

  async function descargarPdf() {
    if (!sop) return;
    setDescargando(true);
    try {
      const { blob, filename } = await apiDownload(`/api/sops/${sop.id}/export.pdf`);
      guardarBlob(blob, filename);
    } catch (e) {
      alert(`No se pudo generar el PDF: ${(e as Error)?.message ?? "error"}`);
    } finally {
      setDescargando(false);
    }
  }

  const puedeGestionar = tieneRol(user, "editor_corporativo", "super_admin");
  const puedeEditar = puedeGestionar && !!sop && EDITABLES.has(sop.estado);
  const dueno = departamentos?.find((d) => d.id === sop?.departamento_id);

  // La capa SMART la edita también el colaborador `redactor` invitado a ESTE SOP: es el
  // mecanismo para que cada área complete sus pendientes sin darle el master entero.
  // El backend vuelve a verificarlo al guardar; esto solo decide si se ve el botón.
  const { data: colaboradores } = useColaboradores(id);
  const soyRedactor = !!colaboradores?.some(
    (c) => c.usuario_id === user?.id && c.rol_colaboracion === "redactor",
  );
  const puedeEditarSmart =
    (puedeGestionar || soyRedactor) && !!sop && EDITABLES.has(sop.estado);

  // Quien llega desde una lista con `?volver=` regresa a ella, no a la librería.
  // `foco` (no un ancla #) porque la lista carga async: el ancla se evalúa antes de
  // que exista la fila. La lista lee `foco` cuando ya tiene datos y la centra.
  const desde = useSearchParams().get("volver");
  const volver =
    desde === "amarena"
      ? {
          href: sop ? `/amarena?foco=${sop.codigo}` : "/amarena",
          texto: "← Volver a SOPs de Amarena",
        }
      : { href: "/biblioteca", texto: "← Volver a la librería" };

  return (
    <div>
      <Link
        href={volver.href}
        onClick={(e) => {
          if (!confirmarSalida()) e.preventDefault();
        }}
        className="mb-4 inline-block text-sm text-petrol-oscuro hover:underline"
      >
        {volver.texto}
      </Link>

      {isLoading ? (
        <CargandoBloque />
      ) : isError || !sop ? (
        <EstadoError mensaje={(error as Error)?.message} />
      ) : (
        <>
          <div className="mb-6 flex flex-wrap items-center gap-3">
            <span className="font-mono text-sm text-carbon-suave">{sop.codigo}</span>
            <h1 className="text-xl font-semibold text-petrol-oscuro">{sop.nombre}</h1>
            <TipoBadge tipo={sop.tipo} />
            <EstadoBadge estado={sop.estado} />
            <Chip>v{sop.version_actual}</Chip>
            <Chip>Área {sop.area_codigo}</Chip>
            {dueno && <Chip>Depto. {dueno.codigo}</Chip>}
            {!editando && !editandoSmart && (
              <div className="ml-auto flex gap-2">
                {/* Visible para cualquier usuario: PDF de la versión actual para compartir
                    (WhatsApp, correo) y pedir validación en la plataforma. */}
                <Button variant="secondary" onClick={descargarPdf} disabled={descargando}>
                  {descargando ? "Generando…" : "Descargar PDF"}
                </Button>
                {puedeEditarSmart && (
                  <Button onClick={() => setEditandoSmart(true)}>
                    {sop.smart ? "Editar SMART" : "Crear capa SMART"}
                  </Button>
                )}
                {/* El formato base y el master siguen siendo del corporativo. */}
                {puedeEditar && (
                  <Button variant="secondary" onClick={() => setEditando(true)}>
                    Editar formato base
                  </Button>
                )}
              </div>
            )}
          </div>

          {sop.departamentos_afectados.length > 0 && (
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wide text-carbon-suave">
                También afecta a:
              </span>
              {sop.departamentos_afectados.map((d) => (
                <Chip key={d.id}>{d.codigo}</Chip>
              ))}
            </div>
          )}

          {sop.sistemas_codigos.length > 0 && (
            <div className="mb-6 flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wide text-carbon-suave">
                Sistemas:
              </span>
              {sop.sistemas_codigos.map((c) => (
                <Chip key={c}>{c}</Chip>
              ))}
            </div>
          )}

          <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
            <div className="space-y-6">
            <Card className="p-6">
              {editando ? (
                <SopForm sop={sop} onDone={() => setEditando(false)} />
              ) : editandoSmart ? (
                <SopSmartForm sop={sop} onDone={() => setEditandoSmart(false)} />
              ) : sop.smart && !verBase ? (
                <>
                  <div className="mb-4 flex justify-end">
                    <button
                      type="button"
                      onClick={() => setVerBase(true)}
                      className="text-xs text-petrol hover:underline"
                    >
                      Ver formato base (9 campos)
                    </button>
                  </div>
                  <SopSmartView smart={sop.smart} />
                </>
              ) : (
                <>
                {sop.smart && (
                  <div className="mb-4 flex justify-end">
                    <button
                      type="button"
                      onClick={() => setVerBase(false)}
                      className="text-xs text-petrol hover:underline"
                    >
                      ← Ver formato SMART
                    </button>
                  </div>
                )}
                <dl>
                  <Campo etiqueta="Propósito">
                    <Texto valor={sop.proposito} />
                  </Campo>
                  <Campo etiqueta="Evaluación de riesgos">
                    <Texto valor={sop.evaluacion_riesgos} />
                  </Campo>
                  <Campo etiqueta="Controles existentes">
                    <Texto valor={sop.controles_existentes} />
                  </Campo>
                  <Campo etiqueta="Procedimiento">
                    <Procedimiento valor={sop.procedimiento} />
                  </Campo>
                  <Campo etiqueta="Responsables">
                    <Texto valor={sop.responsables} />
                  </Campo>
                  <Campo etiqueta="Puestos responsables directos">
                    {sop.puestos_responsables.length === 0 ? (
                      <Vacio />
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {sop.puestos_responsables.map((p) => (
                          <Link
                            key={p.id}
                            href={`/descriptores/${p.id}`}
                            className="inline-flex items-center rounded-full border border-linea bg-petrol-tint px-2.5 py-0.5 text-xs font-medium text-petrol-oscuro hover:underline"
                          >
                            {p.codigo} — {p.titulo}
                          </Link>
                        ))}
                      </div>
                    )}
                  </Campo>
                  <Campo etiqueta="Evidencia / reportes">
                    <Texto valor={sop.evidencia} />
                  </Campo>
                  <Campo etiqueta="Frecuencia de revisión">
                    {sop.frecuencia_revision ? (
                      FRECUENCIA_LABEL[sop.frecuencia_revision] ?? sop.frecuencia_revision
                    ) : (
                      <Vacio />
                    )}
                  </Campo>
                </dl>
                </>
              )}
            </Card>

            {!editando && <ProgramacionPanel sopId={sop.id} puedeGestionar={puedeGestionar} />}
            </div>

            <div className="space-y-4">
              {puedeGestionar && <AccionesEstado sop={sop} />}
              <PanelFirmas sop={sop} puedeGestionar={puedeGestionar} />
              <Card className="p-4">
                <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-carbon-suave">
                  Historial
                </h2>
                <HistorialVersiones sopId={sop.id} puedeRestaurar={puedeEditar} />
              </Card>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
