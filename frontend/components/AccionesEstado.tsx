"use client";

import { Button, Card } from "./ui";
import { useToast } from "./toast";
import { ApiError } from "@/lib/api";
import { useAccionSop } from "@/lib/hooks";
import type { SopDetalle } from "@/lib/types";

interface AccionDef {
  a: string;
  label: string;
  ok: string;
  variant?: "primary" | "secondary";
}

function accionesDe(estado: string): AccionDef[] {
  switch (estado) {
    case "borrador":
      return [{ a: "enviar-revision", label: "Enviar a revisión", ok: "Enviado a revisión." }];
    case "en_revision":
      return [
        { a: "enviar-firma", label: "Enviar a firma", ok: "Enviado a firma." },
        { a: "volver-borrador", label: "Volver a borrador", ok: "Volvió a borrador.", variant: "secondary" },
      ];
    case "rechazado":
      return [{ a: "retomar-revision", label: "Retomar revisión", ok: "De nuevo en revisión." }];
    case "firmado":
      return [
        { a: "nueva-version", label: "Nueva versión", ok: "Nueva versión creada." },
        { a: "archivar", label: "Archivar", ok: "Documento archivado.", variant: "secondary" },
      ];
    default:
      return [];
  }
}

export function AccionesEstado({ sop }: { sop: SopDetalle }) {
  const { notify } = useToast();
  const accion = useAccionSop(sop.id);
  const acciones = accionesDe(sop.estado);

  async function run(def: AccionDef) {
    try {
      await accion.mutateAsync(def.a);
      notify(def.ok);
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo completar la acción.", "error");
    }
  }

  return (
    <Card className="p-4">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-carbon-suave">
        Ciclo de vida
      </p>
      {acciones.length === 0 ? (
        <p className="text-sm text-carbon-suave">
          {sop.estado === "en_firma"
            ? "En proceso de firma."
            : sop.estado === "archivado"
              ? "Documento archivado."
              : "Sin acciones disponibles."}
        </p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {acciones.map((def) => (
            <Button
              key={def.a}
              variant={def.variant ?? "primary"}
              disabled={accion.isPending}
              onClick={() => run(def)}
            >
              {def.label}
            </Button>
          ))}
        </div>
      )}
    </Card>
  );
}
