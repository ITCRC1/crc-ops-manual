"use client";

import Link from "next/link";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { EstadoBadge } from "@/components/EstadoBadge";
import { useToast } from "@/components/toast";
import {
  Button,
  CargandoBloque,
  Card,
  EstadoVacio,
  Input,
  PageHeader,
  Select,
} from "@/components/ui";
import { UserSelect } from "@/components/UserSelect";
import { api, ApiError } from "@/lib/api";
import { tieneRol, useAuth } from "@/lib/auth";
import { useAreas, usePendientesFirma, useSops } from "@/lib/hooks";

const ESTADOS: [string, string][] = [
  ["", "Todos los estados"],
  ["borrador", "Borrador"],
  ["en_revision", "En revisión"],
  ["en_firma", "En firma"],
  ["firmado", "Firmado"],
  ["rechazado", "Rechazado"],
];

const LIMIT = 200;

export default function FirmasPage() {
  const { user } = useAuth();
  const { notify } = useToast();
  const qc = useQueryClient();
  const puedeGestionar = tieneRol(user, "editor_corporativo", "super_admin");

  const { data: areas } = useAreas();
  const [estado, setEstado] = useState("en_revision");
  const [area, setArea] = useState("");
  const { data: lista, isLoading } = useSops({
    estado: estado || undefined,
    area: area || undefined,
    limit: LIMIT,
  });

  const pend = usePendientesFirma();

  const [sel, setSel] = useState<Set<string>>(new Set());
  const [designando, setDesignando] = useState(false);
  const [firmante, setFirmante] = useState("");
  const [orden, setOrden] = useState(1);
  const [obligatorio, setObligatorio] = useState(true);
  const [ocupada, setOcupada] = useState(false);

  const items = lista?.items ?? [];
  const todosSel = items.length > 0 && items.every((s) => sel.has(s.id));

  function toggle(id: string) {
    setSel((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  }
  function toggleTodos() {
    setSel(todosSel ? new Set() : new Set(items.map((s) => s.id)));
  }

  function invalidar() {
    qc.invalidateQueries({ queryKey: ["sops"] });
    qc.invalidateQueries({ queryKey: ["pendientes-firma"] });
  }

  async function lote(fn: (id: string) => Promise<unknown>, label: string) {
    // Defensa: sólo actuar sobre SOPs visibles en el filtro actual (evita mover ids ocultos).
    const ids = [...sel].filter((id) => items.some((s) => s.id === id));
    if (!ids.length) return;
    setOcupada(true);
    const res = await Promise.allSettled(ids.map(fn));
    const ok = res.filter((r) => r.status === "fulfilled").length;
    const fail = res.length - ok;
    const primerError = res.find((r) => r.status === "rejected") as PromiseRejectedResult | undefined;
    const detalle =
      fail && primerError?.reason instanceof ApiError ? ` (ej.: ${primerError.reason.detail})` : "";
    notify(`${label}: ${ok} ok${fail ? `, ${fail} con error${detalle}` : ""}.`, fail ? "error" : "ok");
    setSel(new Set());
    setOcupada(false);
    invalidar();
  }

  const transicion = (accion: string, label: string) => () =>
    lote((id) => api(`/api/sops/${id}/${accion}`, { method: "POST" }), label);

  async function aplicarDesignacion() {
    if (!firmante) {
      notify("Elegí un firmante.", "error");
      return;
    }
    await lote(
      (id) =>
        api(`/api/sops/${id}/firmantes`, {
          method: "POST",
          body: { usuario_id: firmante, orden, obligatorio },
        }),
      "Designar firmante",
    );
    setDesignando(false);
    setFirmante("");
  }

  async function firmar(id: string) {
    setOcupada(true);
    try {
      await api(`/api/sops/${id}/firmar`, { method: "POST", body: { metodo: "clave" } });
      notify("Firma registrada.");
      invalidar();
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo firmar.", "error");
    } finally {
      setOcupada(false);
    }
  }

  const cola = pend.data ?? [];

  return (
    <div>
      <PageHeader
        titulo="Centro de firmas"
        descripcion="Mové los SOPs por el flujo de aprobación y firmá los que te corresponden. Para adoptarlos en una propiedad, el SOP debe quedar firmado."
      />

      {/* Pendientes de mi firma */}
      <Card className="mb-6 p-5">
        <h3 className="mb-3 text-sm font-semibold text-petrol-oscuro">
          Pendientes de mi firma ({cola.length})
        </h3>
        {pend.isLoading ? (
          <CargandoBloque />
        ) : cola.length === 0 ? (
          <p className="text-sm text-carbon-suave">No tenés SOPs esperando tu firma.</p>
        ) : (
          <ul className="space-y-2">
            {cola.map((s) => (
              <li
                key={s.id}
                className="flex flex-wrap items-center gap-2 rounded-md border border-linea px-3 py-2"
              >
                <span className="font-mono text-xs text-carbon-suave">{s.codigo}</span>
                <Link href={`/biblioteca/${s.id}`} className="flex-1 text-sm text-carbon hover:underline">
                  {s.nombre}
                </Link>
                <Button onClick={() => firmar(s.id)} disabled={ocupada}>
                  Firmar
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* Pipeline */}
      <Card className="p-5">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div className="flex flex-wrap gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-carbon-suave">Estado</label>
              <Select
                value={estado}
                onChange={(e) => {
                  setEstado(e.target.value);
                  setSel(new Set());
                }}
                className="w-48"
              >
                {ESTADOS.map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </Select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-carbon-suave">Área</label>
              <Select
                value={area}
                onChange={(e) => {
                  setArea(e.target.value);
                  setSel(new Set());
                }}
                className="w-48"
              >
                <option value="">Todas</option>
                {(areas ?? []).map((a) => (
                  <option key={a.id} value={a.codigo}>{a.codigo} — {a.nombre}</option>
                ))}
              </Select>
            </div>
          </div>
          <span className="text-sm text-carbon-suave">{lista?.total ?? 0} SOP(s)</span>
        </div>

        {/* Barra de acciones en lote */}
        {puedeGestionar && sel.size > 0 && (
          <div className="mb-3 flex flex-wrap items-center gap-2 rounded-md bg-petrol-tint/40 px-3 py-2">
            <span className="text-sm font-medium text-carbon">{sel.size} seleccionado(s):</span>
            <Button variant="secondary" onClick={transicion("enviar-revision", "Enviar a revisión")} disabled={ocupada}>
              Enviar a revisión
            </Button>
            <Button variant="secondary" onClick={() => setDesignando((v) => !v)} disabled={ocupada}>
              Designar firmante
            </Button>
            <Button variant="secondary" onClick={transicion("enviar-firma", "Enviar a firma")} disabled={ocupada}>
              Enviar a firma
            </Button>
            <Button variant="ghost" onClick={transicion("volver-borrador", "Volver a borrador")} disabled={ocupada}>
              Volver a borrador
            </Button>
          </div>
        )}
        {puedeGestionar && designando && sel.size > 0 && (
          <div className="mb-3 flex flex-wrap items-center gap-2 rounded-md border border-linea px-3 py-2">
            <span className="text-xs text-carbon-suave">Designar a los {sel.size} seleccionados:</span>
            <div className="w-64">
              <UserSelect value={firmante} onChange={setFirmante} elegiblesFirmante placeholder="Firmante elegible…" />
            </div>
            <label className="flex items-center gap-1 text-xs text-carbon-suave">
              Orden
              <Input
                type="number"
                min={1}
                value={orden}
                onChange={(e) => setOrden(Number(e.target.value) || 1)}
                className="w-16"
              />
            </label>
            <label className="flex items-center gap-1 text-xs text-carbon-suave">
              <input type="checkbox" checked={obligatorio} onChange={(e) => setObligatorio(e.target.checked)} />
              obligatorio
            </label>
            <Button onClick={aplicarDesignacion} disabled={ocupada || !firmante}>
              Aplicar
            </Button>
          </div>
        )}

        {isLoading ? (
          <CargandoBloque />
        ) : items.length === 0 ? (
          <EstadoVacio titulo="Sin SOPs" descripcion="Ajustá los filtros de estado o área." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-linea bg-petrol-tint/40 text-left text-xs uppercase tracking-wide text-carbon-suave">
                  {puedeGestionar && (
                    <th className="px-3 py-3">
                      <input type="checkbox" checked={todosSel} onChange={toggleTodos} aria-label="Seleccionar todos" />
                    </th>
                  )}
                  <th className="px-4 py-3 font-semibold">Código</th>
                  <th className="px-4 py-3 font-semibold">Nombre</th>
                  <th className="px-4 py-3 font-semibold">Área</th>
                  <th className="px-4 py-3 font-semibold">Estado</th>
                </tr>
              </thead>
              <tbody>
                {items.map((s) => (
                  <tr key={s.id} className="border-b border-linea last:border-0 hover:bg-petrol-tint/20">
                    {puedeGestionar && (
                      <td className="px-3 py-3">
                        <input
                          type="checkbox"
                          checked={sel.has(s.id)}
                          onChange={() => toggle(s.id)}
                          aria-label={`Seleccionar ${s.codigo}`}
                        />
                      </td>
                    )}
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-carbon-suave">
                      {s.codigo}
                    </td>
                    <td className="px-4 py-3">
                      <Link href={`/biblioteca/${s.id}`} className="font-medium text-carbon hover:underline">
                        {s.nombre}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-carbon-suave">{s.area_codigo}</td>
                    <td className="px-4 py-3">
                      <EstadoBadge estado={s.estado} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
