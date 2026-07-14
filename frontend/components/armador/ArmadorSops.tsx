"use client";

import { useMemo, useState } from "react";

import { EstadoBadge } from "@/components/EstadoBadge";
import { useToast } from "@/components/toast";
import { Button, CargandoBloque, Card, Chip, EstadoVacio } from "@/components/ui";
import { ApiError } from "@/lib/api";
import {
  useAsignacionesSop,
  useAsignarSop,
  useSops,
  useSugerenciasSop,
} from "@/lib/hooks";
import type { SopItem } from "@/lib/types";

import { AdaptacionSopEditor } from "./AdaptacionSopEditor";

const MODO_LABEL: Record<string, string> = {
  adoptado: "Adoptado",
  adaptado: "Adaptado",
  local: "Local",
  no_aplica: "No aplica",
};

export function ArmadorSops({
  propId,
  puedeGestionar,
}: {
  propId: string;
  puedeGestionar: boolean;
}) {
  const { notify } = useToast();
  const { data: asignaciones, isLoading: cargandoAsig } = useAsignacionesSop(propId);
  const { data: sugerencias, isLoading: cargandoSug } = useSugerenciasSop(propId);
  const { data: masters } = useSops({ estado: "firmado", limit: 500 });
  const asignar = useAsignarSop(propId);
  const [sel, setSel] = useState<{ psId: string; codigo: string; nombre: string } | null>(null);

  const masterMap = useMemo(() => {
    const m = new Map<string, SopItem>();
    for (const s of masters?.items ?? []) m.set(s.id, s);
    return m;
  }, [masters]);

  async function onAsignar(sopMasterId: string, modo: "adoptado" | "adaptado") {
    try {
      await asignar.mutateAsync({ modo, sop_master_id: sopMasterId });
      notify(modo === "adoptado" ? "SOP adoptado." : "SOP adaptado (queda en borrador).");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo asignar.", "error");
    }
  }

  if (sel) {
    return (
      <AdaptacionSopEditor
        propId={propId}
        psId={sel.psId}
        codigo={sel.codigo}
        nombre={sel.nombre}
        puedeGestionar={puedeGestionar}
        onVolver={() => setSel(null)}
      />
    );
  }

  if (cargandoAsig || cargandoSug) return <CargandoBloque />;

  const asigns = asignaciones ?? [];
  const sugs = sugerencias ?? [];

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card className="p-5">
        <h3 className="mb-1 text-sm font-semibold text-petrol-oscuro">Sugerencias por sistemas</h3>
        <p className="mb-4 text-xs text-carbon-suave">
          SOPs maestros firmados aún no asignados. La sugerencia compara los sistemas que asume
          cada SOP con los de la propiedad. Nunca es automático: vos decidís.
        </p>
        {sugs.length === 0 ? (
          <EstadoVacio titulo="Nada por sugerir" descripcion="No hay SOPs firmados pendientes de asignar." />
        ) : (
          <ul className="space-y-2">
            {sugs.map((s) => (
              <li key={s.sop_master_id} className="rounded-md border border-linea px-3 py-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs text-carbon-suave">{s.codigo}</span>
                  <span className="flex-1 text-sm font-medium text-carbon">{s.nombre}</span>
                  <Chip>{`Sugerido: ${MODO_LABEL[s.sugerencia]}`}</Chip>
                </div>
                <p className="mt-1 text-xs text-carbon-suave">{s.motivo}</p>
                {s.sistemas_faltantes.length > 0 && (
                  <p className="mt-1 text-xs text-en-firma">
                    Faltan {s.sistemas_faltantes.length} sistema(s) que el SOP asume.
                  </p>
                )}
                {puedeGestionar && (
                  <div className="mt-2 flex gap-2">
                    <Button
                      onClick={() => onAsignar(s.sop_master_id, "adoptado")}
                      disabled={asignar.isPending}
                    >
                      Adoptar
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => onAsignar(s.sop_master_id, "adaptado")}
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

      <Card className="p-5">
        <h3 className="mb-4 text-sm font-semibold text-petrol-oscuro">
          Asignados a la propiedad ({asigns.length})
        </h3>
        {asigns.length === 0 ? (
          <EstadoVacio titulo="Sin SOPs asignados" descripcion="Adoptá o adaptá desde las sugerencias." />
        ) : (
          <ul className="space-y-2">
            {asigns.map((a) => {
              const master = a.sop_master_id ? masterMap.get(a.sop_master_id) : undefined;
              const codigo = master?.codigo ?? a.codigo_local ?? "—";
              const nombre = master?.nombre ?? "(SOP local)";
              return (
                <li key={a.id}>
                  <button
                    type="button"
                    onClick={() => setSel({ psId: a.id, codigo, nombre })}
                    className="flex w-full flex-wrap items-center gap-2 rounded-md border border-linea px-3 py-2 text-left transition-colors hover:bg-petrol-tint/40"
                  >
                    <span className="font-mono text-xs text-carbon-suave">{codigo}</span>
                    <span className="flex-1 text-sm text-carbon">{nombre}</span>
                    <Chip>{MODO_LABEL[a.modo]}</Chip>
                    <EstadoBadge estado={a.estado} />
                    {a.master_retirado && (
                      <Chip className="border-rechazado/40 text-rechazado">Maestro retirado</Chip>
                    )}
                    <span className="text-xs text-petrol-oscuro">Personalizar →</span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}
