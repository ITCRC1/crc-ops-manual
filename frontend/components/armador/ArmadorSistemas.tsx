"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { useToast } from "@/components/toast";
import { Button, CargandoBloque, Card } from "@/components/ui";
import { ApiError } from "@/lib/api";
import { useFijarSistemas, usePropiedadSistemas, useSistemas } from "@/lib/hooks";
import type { Sistema } from "@/lib/types";

export function ArmadorSistemas({
  propId,
  puedeGestionar,
}: {
  propId: string;
  puedeGestionar: boolean;
}) {
  const { notify } = useToast();
  const { data: todos } = useSistemas();
  const { data: asignados, isLoading } = usePropiedadSistemas(propId);
  const fijar = useFijarSistemas(propId);

  const [sel, setSel] = useState<Set<string>>(new Set());
  const [base, setBase] = useState<Set<string>>(new Set());
  const dirty = useRef(false);

  useEffect(() => {
    if (!asignados) return;
    const server = new Set(asignados.map((x) => x.id));
    setBase(server);
    if (!dirty.current) setSel(new Set(server));
  }, [asignados]);

  const grupos = useMemo(() => {
    const porCat = new Map<string, Sistema[]>();
    for (const s of todos ?? []) {
      const cat = s.categoria ?? "Otros";
      if (!porCat.has(cat)) porCat.set(cat, []);
      porCat.get(cat)!.push(s);
    }
    return [...porCat.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [todos]);

  const cambios = sel.size !== base.size || [...sel].some((id) => !base.has(id));

  function toggle(id: string) {
    if (!puedeGestionar) return;
    dirty.current = true;
    setSel((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  }

  async function guardar() {
    try {
      await fijar.mutateAsync([...sel]);
      dirty.current = false;
      setBase(new Set(sel));
      notify("Sistemas de la propiedad actualizados.");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo guardar.", "error");
    }
  }

  if (isLoading) return <CargandoBloque />;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-carbon-suave">
          Sistemas operativos y financieros que usa la propiedad (alimentan las sugerencias de
          SOPs). <span className="font-medium text-carbon">{sel.size}</span> seleccionados.
        </p>
        {puedeGestionar && (
          <Button onClick={guardar} disabled={!cambios || fijar.isPending}>
            {fijar.isPending ? "Guardando…" : "Guardar cambios"}
          </Button>
        )}
      </div>

      <div className="space-y-4">
        {grupos.map(([cat, sistemas]) => (
          <Card key={cat} className="p-4">
            <h3 className="mb-3 text-sm font-semibold text-petrol-oscuro">{cat}</h3>
            <div className="flex flex-wrap gap-2">
              {sistemas.map((s) => {
                const on = sel.has(s.id);
                return (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => toggle(s.id)}
                    disabled={!puedeGestionar}
                    className={`rounded-full border px-3 py-1 text-xs transition-colors disabled:cursor-default ${
                      on
                        ? "border-petrol bg-petrol text-white"
                        : "border-linea bg-superficie text-carbon-suave hover:bg-petrol-tint"
                    }`}
                  >
                    {s.nombre}
                  </button>
                );
              })}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
