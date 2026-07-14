"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { useToast } from "@/components/toast";
import { Button, CargandoBloque, Card } from "@/components/ui";
import { ApiError } from "@/lib/api";
import {
  useDepartamentos,
  useDivisiones,
  useFijarDepartamentos,
  usePropiedadDepartamentos,
} from "@/lib/hooks";
import type { Departamento, Division } from "@/lib/types";

interface Grupo {
  division: Division | null;
  subs: { division: Division; deptos: Departamento[] }[];
  deptos: Departamento[];
}

function construirGrupos(deptos: Departamento[], divisiones: Division[]): Grupo[] {
  const porOrden = (a: Division, b: Division) => a.orden - b.orden || a.codigo.localeCompare(b.codigo);
  const porDivision = (id: string | null) =>
    deptos.filter((d) => d.division_id === id).sort((a, b) => a.codigo.localeCompare(b.codigo));

  const grupos: Grupo[] = divisiones
    .filter((d) => !d.parent_id)
    .sort(porOrden)
    .map((top) => ({
      division: top,
      subs: divisiones
        .filter((d) => d.parent_id === top.id)
        .sort(porOrden)
        .map((sub) => ({ division: sub, deptos: porDivision(sub.id) })),
      deptos: porDivision(top.id),
    }));

  const sinDiv = porDivision(null);
  if (sinDiv.length) grupos.push({ division: null, subs: [], deptos: sinDiv });
  return grupos;
}

export function ArmadorDepartamentos({
  propId,
  puedeGestionar,
}: {
  propId: string;
  puedeGestionar: boolean;
}) {
  const { notify } = useToast();
  const { data: todos } = useDepartamentos();
  const { data: divisiones } = useDivisiones();
  const { data: asignados, isLoading } = usePropiedadDepartamentos(propId);
  const fijar = useFijarDepartamentos(propId);

  const [sel, setSel] = useState<Set<string>>(new Set());
  const [base, setBase] = useState<Set<string>>(new Set());
  const dirty = useRef(false);

  useEffect(() => {
    if (!asignados) return;
    const server = new Set(asignados.map((d) => d.id));
    setBase(server);
    // Un refetch en background no debe pisar toggles sin guardar del usuario.
    if (!dirty.current) setSel(new Set(server));
  }, [asignados]);

  const grupos = useMemo(() => construirGrupos(todos ?? [], divisiones ?? []), [todos, divisiones]);
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
      notify("Departamentos de la propiedad actualizados.");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo guardar.", "error");
    }
  }

  function chip(d: Departamento) {
    const on = sel.has(d.id);
    return (
      <button
        key={d.id}
        type="button"
        onClick={() => toggle(d.id)}
        disabled={!puedeGestionar}
        className={`rounded-full border px-3 py-1 text-xs transition-colors disabled:cursor-default ${
          on
            ? "border-petrol bg-petrol text-white"
            : "border-linea bg-superficie text-carbon-suave hover:bg-petrol-tint"
        }`}
      >
        {d.codigo} — {d.nombre}
      </button>
    );
  }

  if (isLoading) return <CargandoBloque />;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-carbon-suave">
          Elegí qué departamentos del catálogo maestro operan en esta propiedad.{" "}
          <span className="font-medium text-carbon">{sel.size}</span> seleccionados.
        </p>
        {puedeGestionar && (
          <Button onClick={guardar} disabled={!cambios || fijar.isPending}>
            {fijar.isPending ? "Guardando…" : "Guardar cambios"}
          </Button>
        )}
      </div>

      <div className="space-y-4">
        {grupos.map((g, i) => (
          <Card key={g.division?.id ?? `sin-${i}`} className="p-4">
            <h3 className="text-sm font-semibold text-petrol-oscuro">
              {g.division ? `${g.division.codigo} — ${g.division.nombre}` : "Sin división (cúpula)"}
            </h3>
            {g.deptos.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">{g.deptos.map(chip)}</div>
            )}
            {g.subs.map((s) => (
              <div key={s.division.id} className="mt-3 border-t border-linea pt-3">
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-carbon-suave">
                  {s.division.nombre}
                </p>
                {s.deptos.length ? (
                  <div className="flex flex-wrap gap-2">{s.deptos.map(chip)}</div>
                ) : (
                  <p className="text-xs text-carbon-suave/70">Sin departamentos.</p>
                )}
              </div>
            ))}
          </Card>
        ))}
      </div>
    </div>
  );
}
