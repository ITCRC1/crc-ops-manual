"use client";

import { useState } from "react";

import { Button, CargandoBloque, EstadoError } from "./ui";
import { useToast } from "./toast";
import { ApiError } from "@/lib/api";
import { useRestaurarSmart, useVersiones } from "@/lib/hooks";

function cuando(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("es-CR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Historial de snapshots del SOP. Cada guardado deja una fila; restaurar devuelve la
 * capa SMART a ese punto (los 9 campos base no se tocan) y deja su propio snapshot,
 * así que la restauración también se puede deshacer.
 */
export function HistorialVersiones({
  sopId,
  puedeRestaurar,
}: {
  sopId: string;
  puedeRestaurar: boolean;
}) {
  const [abierto, setAbierto] = useState(false);
  const { data, isLoading, isError, error } = useVersiones(sopId, abierto);
  const restaurar = useRestaurarSmart(sopId);
  const { notify } = useToast();

  async function onRestaurar(versionId: string, fecha: string) {
    if (
      !window.confirm(
        `Se va a reemplazar la capa SMART actual por la del ${cuando(fecha)}.\n\n` +
          "Los 9 campos base no se tocan, y esta restauración queda guardada como una " +
          "versión más, así que se puede deshacer.\n\n¿Continuar?",
      )
    )
      return;
    try {
      await restaurar.mutateAsync(versionId);
      notify("Capa SMART restaurada.");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo restaurar.", "error");
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => setAbierto((v) => !v)}
        className="text-xs text-petrol hover:underline"
      >
        {abierto ? "Ocultar historial" : "Ver historial de versiones"}
      </button>

      {abierto && (
        <div className="mt-3">
          {isLoading ? (
            <CargandoBloque />
          ) : isError ? (
            <EstadoError mensaje={(error as Error)?.message} />
          ) : !data || data.length === 0 ? (
            <p className="text-xs text-carbon-suave">Sin versiones guardadas todavía.</p>
          ) : (
            <ul className="space-y-3">
              {data.map((v, i) => (
                <li key={v.id} className="border-l-2 border-linea pl-3">
                  <p className="text-xs font-medium text-carbon">
                    {cuando(v.creado_en)}
                    {i === 0 && (
                      <span className="ml-2 rounded-full bg-petrol-tint px-2 py-0.5 text-[10px] font-semibold text-petrol-oscuro">
                        actual
                      </span>
                    )}
                  </p>
                  <p className="mt-0.5 text-xs text-carbon-suave">
                    {v.nota_cambio ?? "Sin nota"}
                  </p>
                  <p className="mt-0.5 text-[11px] text-carbon-suave/80">
                    {v.creado_por_nombre ?? "Autor desconocido"} · v{v.version}
                    {!v.tiene_smart && " · sin capa SMART"}
                  </p>
                  {puedeRestaurar && v.tiene_smart && i > 0 && (
                    <Button
                      variant="ghost"
                      className="mt-1 px-0 text-xs"
                      disabled={restaurar.isPending}
                      onClick={() => onRestaurar(v.id, v.creado_en)}
                    >
                      Restaurar esta capa SMART
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
