"use client";

import { useEffect, useMemo, useState } from "react";

import { Button, Card, Select } from "./ui";
import { useToast } from "./toast";
import { ApiError } from "@/lib/api";
import {
  useDepartamentos,
  useInvitarColaboradoresLote,
  useSops,
  useUsuarios,
} from "@/lib/hooks";
import type { SopItem } from "@/lib/types";

/**
 * Invita a N personas como colaboradores `redactor` de M SOPs, de una sola vez.
 *
 * Dos modos:
 *  - `sopsFijos` dado (sección de Amarena): trabaja sobre esa lista.
 *  - sin `sopsFijos` (Librería maestra): muestra un selector de departamento y carga los
 *    SOPs de ese departamento — los propios Y los que lo afectan (`departamento_relacionado_id`).
 *
 * Un redactor puede editar la capa SMART de los SOPs a los que lo invitaron, y nada más:
 * crear, borrar y editar los 9 campos base siguen siendo del corporativo. Es idempotente.
 */
export function InvitarColaboradoresLote({ sopsFijos }: { sopsFijos?: SopItem[] }) {
  const porDepartamento = !sopsFijos;
  const [abierto, setAbierto] = useState(false);
  const [departamentoId, setDepartamentoId] = useState("");
  const [personas, setPersonas] = useState<string[]>([]);
  const [elegidos, setElegidos] = useState<string[]>(() => (sopsFijos ?? []).map((s) => s.id));

  const { data: usuarios } = useUsuarios();
  const { data: departamentos } = useDepartamentos();
  const invitar = useInvitarColaboradoresLote();
  const { notify } = useToast();

  // Departamentos únicos por código (el catálogo puede repetir por propiedad).
  const depUnicos = useMemo(() => {
    const m = new Map<string, { id: string; codigo: string; nombre: string }>();
    for (const d of departamentos ?? []) if (!m.has(d.codigo)) m.set(d.codigo, d);
    return [...m.values()].sort((a, b) => a.codigo.localeCompare(b.codigo));
  }, [departamentos]);

  // En modo departamento: SOPs propios + los que ese departamento afecta. Solo cuando hay uno elegido.
  const { data: porDepto, isFetching } = useSops(
    { departamento_relacionado_id: departamentoId || undefined, limit: 200 },
    porDepartamento && !!departamentoId,
  );

  const sops = useMemo<SopItem[]>(
    () => (porDepartamento ? (departamentoId ? (porDepto?.items ?? []) : []) : (sopsFijos ?? [])),
    [porDepartamento, departamentoId, porDepto, sopsFijos],
  );

  // Al cambiar el conjunto de SOPs (otro departamento), re-preseleccionar todos.
  const idsKey = sops.map((s) => s.id).join(",");
  useEffect(() => {
    setElegidos(sops.map((s) => s.id));
  }, [idsKey]); // eslint-disable-line react-hooks/exhaustive-deps

  function alternar(lista: string[], set: (v: string[]) => void, id: string) {
    set(lista.includes(id) ? lista.filter((x) => x !== id) : [...lista, id]);
  }

  async function onInvitar() {
    try {
      const r = await invitar.mutateAsync({
        sop_ids: elegidos,
        usuario_ids: personas,
        rol_colaboracion: "redactor",
      });
      notify(
        `${r.creados} invitación${r.creados === 1 ? "" : "es"} creada${r.creados === 1 ? "" : "s"}` +
          (r.ya_existian ? ` · ${r.ya_existian} ya existían` : ""),
      );
      setPersonas([]);
      setAbierto(false);
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo invitar.", "error");
    }
  }

  if (!abierto) {
    return (
      <Button variant="secondary" onClick={() => setAbierto(true)}>
        Invitar colaboradores
      </Button>
    );
  }

  return (
    <Card className="mb-4 p-4">
      <div className="mb-3 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold text-petrol-oscuro">Invitar colaboradores</h2>
          <p className="mt-0.5 text-xs text-carbon-suave">
            Un redactor puede editar la capa SMART de los SOPs elegidos, mientras no estén
            firmados. No puede crear, borrar ni tocar el formato base.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setAbierto(false)}
          className="shrink-0 text-xs text-carbon-suave hover:underline"
        >
          Cerrar
        </button>
      </div>

      {porDepartamento && (
        <div className="mb-4">
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-carbon-suave">
            Departamento
          </label>
          <Select
            value={departamentoId}
            onChange={(e) => setDepartamentoId(e.target.value)}
            className="sm:w-96"
          >
            <option value="">Elegí un departamento…</option>
            {depUnicos.map((d) => (
              <option key={d.id} value={d.id}>
                {d.codigo} — {d.nombre}
              </option>
            ))}
          </Select>
          <p className="mt-1 text-xs text-carbon-suave">
            Se incluyen los SOPs de ese departamento y los que lo afectan, aunque su dueño sea otro.
          </p>
        </div>
      )}

      {porDepartamento && !departamentoId ? (
        <p className="text-sm text-carbon-suave">Elegí un departamento para ver sus SOPs.</p>
      ) : isFetching ? (
        <p className="text-sm text-carbon-suave">Cargando SOPs…</p>
      ) : sops.length === 0 ? (
        <p className="text-sm text-carbon-suave">Ese departamento no tiene SOPs.</p>
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-carbon-suave">
                Personas ({personas.length})
              </p>
              <div className="max-h-56 space-y-1 overflow-y-auto rounded-md border border-linea p-2">
                {(usuarios ?? []).map((u) => (
                  <label key={u.id} className="flex cursor-pointer items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={personas.includes(u.id)}
                      onChange={() => alternar(personas, setPersonas, u.id)}
                      className="h-4 w-4"
                    />
                    <span className="text-carbon">{u.nombre}</span>
                    <span className="text-xs text-carbon-suave">{u.email}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wide text-carbon-suave">
                  SOPs ({elegidos.length} de {sops.length})
                </p>
                <button
                  type="button"
                  onClick={() =>
                    setElegidos(elegidos.length === sops.length ? [] : sops.map((s) => s.id))
                  }
                  className="text-xs text-petrol hover:underline"
                >
                  {elegidos.length === sops.length ? "Ninguno" : "Todos"}
                </button>
              </div>
              <div className="max-h-56 space-y-1 overflow-y-auto rounded-md border border-linea p-2">
                {sops.map((s) => (
                  <label key={s.id} className="flex cursor-pointer items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={elegidos.includes(s.id)}
                      onChange={() => alternar(elegidos, setElegidos, s.id)}
                      className="h-4 w-4"
                    />
                    <span className="font-mono text-xs text-carbon-suave">{s.codigo}</span>
                    <span className="truncate text-carbon">{s.nombre}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-4 flex items-center gap-3 border-t border-linea pt-3">
            <Button
              onClick={onInvitar}
              disabled={invitar.isPending || personas.length === 0 || elegidos.length === 0}
            >
              {invitar.isPending ? "Invitando…" : "Invitar como redactores"}
            </Button>
            <span className="text-xs text-carbon-suave">
              {personas.length === 0 || elegidos.length === 0
                ? "Elegí al menos una persona y un SOP."
                : `${personas.length} × ${elegidos.length} = ${personas.length * elegidos.length} invitaciones`}
            </span>
          </div>
        </>
      )}
    </Card>
  );
}
