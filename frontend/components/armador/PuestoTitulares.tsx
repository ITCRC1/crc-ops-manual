"use client";

import { useState } from "react";

import { useToast } from "@/components/toast";
import { Button, Select, Spinner } from "@/components/ui";
import { ApiError } from "@/lib/api";
import {
  useAgregarOcupante,
  useOcupantes,
  useQuitarOcupante,
  useUsuarios,
} from "@/lib/hooks";

export function PuestoTitulares({
  propId,
  ppId,
  puedeGestionar,
}: {
  propId: string;
  ppId: string;
  puedeGestionar: boolean;
}) {
  const { notify } = useToast();
  const { data: ocupantes, isLoading } = useOcupantes(propId, ppId);
  const { data: usuarios } = useUsuarios();
  const agregar = useAgregarOcupante(propId, ppId);
  const quitar = useQuitarOcupante(propId, ppId);
  const [usuarioId, setUsuarioId] = useState("");
  const [principal, setPrincipal] = useState(true);

  const yaAsignados = new Set((ocupantes ?? []).map((o) => o.usuario_id));
  const disponibles = (usuarios ?? []).filter((u) => !yaAsignados.has(u.id));

  async function onAgregar() {
    if (!usuarioId) return;
    try {
      await agregar.mutateAsync({ usuario_id: usuarioId, es_principal: principal });
      setUsuarioId("");
      notify("Titular asignado.");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo asignar.", "error");
    }
  }

  async function onQuitar(id: string) {
    try {
      await quitar.mutateAsync(id);
      notify("Titular removido.");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo remover.", "error");
    }
  }

  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-carbon-suave">
        Titulares
      </p>
      {isLoading ? (
        <Spinner />
      ) : (ocupantes ?? []).length === 0 ? (
        <p className="text-sm text-carbon-suave/80">Sin titulares asignados.</p>
      ) : (
        <ul className="space-y-1.5">
          {ocupantes!.map((o) => (
            <li
              key={o.id}
              className="flex items-center justify-between rounded-md border border-linea px-3 py-2"
            >
              <span className="min-w-0">
                <span className="block truncate text-sm text-carbon">
                  {o.usuario_nombre}
                  {o.es_principal && (
                    <span className="ml-2 rounded-full bg-petrol-tint px-2 py-0.5 text-[10px] font-medium text-petrol-oscuro">
                      Principal
                    </span>
                  )}
                </span>
                <span className="block truncate text-xs text-carbon-suave">{o.usuario_email}</span>
              </span>
              {puedeGestionar && (
                <button
                  type="button"
                  onClick={() => onQuitar(o.id)}
                  disabled={quitar.isPending}
                  className="shrink-0 text-xs text-rechazado hover:underline disabled:opacity-50"
                >
                  Quitar
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      {puedeGestionar && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Select
            className="max-w-[14rem]"
            value={usuarioId}
            onChange={(e) => setUsuarioId(e.target.value)}
          >
            <option value="">— Elegí una persona —</option>
            {disponibles.map((u) => (
              <option key={u.id} value={u.id}>
                {u.nombre}
              </option>
            ))}
          </Select>
          <label className="flex items-center gap-1 text-xs text-carbon-suave">
            <input
              type="checkbox"
              checked={principal}
              onChange={(e) => setPrincipal(e.target.checked)}
            />
            principal
          </label>
          <Button onClick={onAgregar} disabled={!usuarioId || agregar.isPending}>
            {agregar.isPending ? "Asignando…" : "Asignar titular"}
          </Button>
        </div>
      )}
    </div>
  );
}
