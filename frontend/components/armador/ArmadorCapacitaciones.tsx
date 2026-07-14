"use client";

import { useState } from "react";

import { EstadoBadge } from "@/components/EstadoBadge";
import { TrainingSmartForm } from "@/components/TrainingSmartForm";
import { useToast } from "@/components/toast";
import { Button, CargandoBloque, Card, Chip, EstadoVacio } from "@/components/ui";
import { ApiError } from "@/lib/api";
import {
  useActualizarSmartOverridesTraining,
  useAdaptarCapacitacion,
  useAsignarCapacitacion,
  useEliminarCapacitacion,
  useManuales,
  usePropiedadCapacitacion,
  usePropiedadCapacitaciones,
} from "@/lib/hooks";
import type { ModoAsignacion, TrainingSmart } from "@/lib/types";

const MODO_LABEL: Record<ModoAsignacion, string> = {
  adoptado: "Adoptado",
  adaptado: "Adaptado",
  local: "Local",
  no_aplica: "No aplica",
};

// Ficha efectiva → deltas por sección contra el master (top-level keys que difieren).
function diffTrainingSmartPorSeccion(
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

export function ArmadorCapacitaciones({
  propId,
  puedeGestionar,
}: {
  propId: string;
  puedeGestionar: boolean;
}) {
  const { notify } = useToast();
  const { data: asignadas, isLoading } = usePropiedadCapacitaciones(propId);
  const { data: manuales } = useManuales();
  const asignar = useAsignarCapacitacion(propId);
  const eliminar = useEliminarCapacitacion(propId);
  const [sel, setSel] = useState<string | null>(null);

  if (sel) {
    return (
      <CapacitacionSmartEditor
        propId={propId}
        ptId={sel}
        puedeGestionar={puedeGestionar}
        onVolver={() => setSel(null)}
      />
    );
  }

  if (isLoading) return <CargandoBloque />;

  const asigns = asignadas ?? [];
  const yaAsignados = new Set(asigns.map((a) => a.training_manual_id).filter(Boolean));
  const disponibles = (manuales ?? []).filter((m) => !yaAsignados.has(m.id));

  async function onAsignar(manualId: string, modo: "adoptado" | "adaptado") {
    try {
      await asignar.mutateAsync({ modo, training_manual_id: manualId });
      notify(modo === "adoptado" ? "Manual adoptado." : "Manual adaptado (queda en borrador).");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo asignar.", "error");
    }
  }

  async function onEliminar(ptId: string, titulo: string) {
    if (!window.confirm(`¿Quitar “${titulo}” de esta propiedad?`)) return;
    try {
      await eliminar.mutateAsync(ptId);
      notify("Capacitación quitada.");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo quitar.", "error");
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card className="p-5">
        <h3 className="mb-1 text-sm font-semibold text-petrol-oscuro">Capacitaciones de la propiedad</h3>
        <p className="mb-4 text-xs text-carbon-suave">
          Manuales adoptados/adaptados por este hotel. Adaptá para personalizar la ficha SMART;
          cada sección que cambies se guarda local y el resto hereda del maestro.
        </p>
        {asigns.length === 0 ? (
          <EstadoVacio titulo="Sin capacitaciones" descripcion="Adoptá un manual del catálogo maestro." />
        ) : (
          <ul className="space-y-2">
            {asigns.map((a) => (
              <li key={a.id} className="rounded-md border border-linea px-3 py-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="flex-1 text-sm font-medium text-carbon">{a.titulo}</span>
                  <Chip>{MODO_LABEL[a.modo]}</Chip>
                  <EstadoBadge estado={a.estado} />
                </div>
                {puedeGestionar && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Button variant="secondary" onClick={() => setSel(a.id)}>
                      {a.modo === "adoptado" ? "Ver / adaptar SMART" : "Editar SMART"}
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => onEliminar(a.id, a.titulo)}
                      disabled={eliminar.isPending}
                    >
                      Quitar
                    </Button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card className="p-5">
        <h3 className="mb-1 text-sm font-semibold text-petrol-oscuro">Catálogo maestro</h3>
        <p className="mb-4 text-xs text-carbon-suave">
          Manuales de capacitación del catálogo corporativo aún no asignados a este hotel.
        </p>
        {disponibles.length === 0 ? (
          <EstadoVacio titulo="Nada por adoptar" descripcion="Todos los manuales ya están asignados." />
        ) : (
          <ul className="space-y-2">
            {disponibles.map((m) => (
              <li key={m.id} className="rounded-md border border-linea px-3 py-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="flex-1 text-sm font-medium text-carbon">{m.titulo}</span>
                  {m.departamento_codigo && (
                    <span className="font-mono text-xs text-carbon-suave">{m.departamento_codigo}</span>
                  )}
                </div>
                {puedeGestionar && (
                  <div className="mt-2 flex gap-2">
                    <Button onClick={() => onAsignar(m.id, "adoptado")} disabled={asignar.isPending}>
                      Adoptar
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => onAsignar(m.id, "adaptado")}
                      disabled={asignar.isPending}
                    >
                      Adaptar
                    </Button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function CapacitacionSmartEditor({
  propId,
  ptId,
  puedeGestionar,
  onVolver,
}: {
  propId: string;
  ptId: string;
  puedeGestionar: boolean;
  onVolver: () => void;
}) {
  const { notify } = useToast();
  const { data: det, isLoading } = usePropiedadCapacitacion(propId, ptId);
  const adaptar = useAdaptarCapacitacion(propId, ptId);
  const guardarSmart = useActualizarSmartOverridesTraining(propId, ptId);

  if (isLoading || !det) return <CargandoBloque />;

  const esLocal = det.modo === "local";
  const esAdoptado = det.modo === "adoptado";
  const smartMaster = det.smart_master ?? {};
  const smartEfectivo = det.smart_efectivo ?? {};
  const tieneSmart =
    Object.keys(smartMaster).some((k) => k !== "formato") ||
    Object.keys(smartEfectivo).some((k) => k !== "formato");
  const seccionesLocales = Object.keys(det.smart_overrides ?? {}).filter((k) => k !== "formato").length;

  async function guardarOverrides(limpio: TrainingSmart) {
    const payload = esLocal
      ? (limpio as unknown as Record<string, unknown>)
      : diffTrainingSmartPorSeccion(limpio as unknown as Record<string, unknown>, smartMaster);
    await guardarSmart.mutateAsync({ smart_overrides: payload });
  }

  async function onAdaptar() {
    try {
      await adaptar.mutateAsync();
      notify("Manual adaptado: ya podés personalizar la ficha SMART.");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo adaptar.", "error");
    }
  }

  return (
    <Card className="p-5">
      <button onClick={onVolver} className="mb-4 text-sm text-petrol-oscuro hover:underline">
        ← Volver a capacitaciones
      </button>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <h3 className="text-base font-semibold text-petrol-oscuro">{det.titulo}</h3>
        <Chip>{MODO_LABEL[det.modo]}</Chip>
        <EstadoBadge estado={det.estado} />
      </div>

      {esAdoptado ? (
        <div>
          <p className="text-sm text-carbon">
            Este manual está <strong>adoptado</strong>: usa la ficha maestra tal cual. Para
            personalizar una o más secciones en esta propiedad, adaptalo — el resto seguirá
            heredando del maestro.
          </p>
          {puedeGestionar && (
            <Button className="mt-3" onClick={onAdaptar} disabled={adaptar.isPending}>
              {adaptar.isPending ? "Adaptando…" : "Adaptar para personalizar"}
            </Button>
          )}
        </div>
      ) : !esLocal && !tieneSmart ? (
        <p className="text-sm text-carbon-suave">
          Este manual maestro todavía no tiene ficha TRAIN-SMART para adaptar.
        </p>
      ) : (
        <TrainingSmartForm
          onDone={onVolver}
          override={{
            inicial: smartEfectivo as unknown as TrainingSmart,
            guardar: guardarOverrides,
            guardando: guardarSmart.isPending,
            sucioKey: `train-smart-prop:${ptId}`,
            encabezado: (
              <div>
                <h2 className="text-sm font-semibold text-petrol-oscuro">
                  Ficha TRAIN-SMART — {esLocal ? "capacitación local" : "adaptación de esta propiedad"}
                </h2>
                <p className="text-xs text-carbon-suave">
                  {esLocal
                    ? "Editás la ficha SMART completa de esta capacitación local."
                    : `Cada sección que cambies se guarda como local; el resto hereda del maestro. ${seccionesLocales} sección(es) personalizada(s).`}
                </p>
              </div>
            ),
          }}
        />
      )}
    </Card>
  );
}
