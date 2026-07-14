"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { EstadoBadge, TipoBadge } from "@/components/EstadoBadge";
import {
  Card,
  CargandoBloque,
  EstadoError,
  EstadoVacio,
  Input,
  PageHeader,
  Select,
} from "@/components/ui";
import { useBusqueda } from "@/lib/hooks";
import { useDebouncedValue } from "@/lib/use-debounce";

export default function BusquedaPage() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [entidad, setEntidad] = useState("todos");
  const qDebounced = useDebouncedValue(q, 350);

  const { data, isLoading, isError, error, isFetching } = useBusqueda({
    q: qDebounced,
    entidad: entidad === "todos" ? undefined : entidad,
  });

  function abrir(entidad: string, id: string) {
    if (entidad === "descriptor") router.push(`/descriptores/${id}`);
    else router.push(`/biblioteca/${id}`);
  }

  const hayConsulta = qDebounced.trim().length > 0;

  return (
    <div>
      <PageHeader
        titulo="Búsqueda global"
        descripcion="Buscá simultáneamente en SOPs, políticas y descriptores de puesto."
      />

      <Card className="mb-4 p-4">
        <div className="grid gap-3 sm:grid-cols-[1fr_14rem]">
          <Input
            placeholder="Escribí para buscar (código, título, propósito)…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            aria-label="Buscar"
            autoFocus
          />
          <Select value={entidad} onChange={(e) => setEntidad(e.target.value)} aria-label="Entidad">
            <option value="todos">Todo</option>
            <option value="sop">SOPs</option>
            <option value="politica">Políticas</option>
            <option value="descriptor">Descriptores</option>
          </Select>
        </div>
      </Card>

      {!hayConsulta ? (
        <EstadoVacio
          titulo="Empezá a escribir"
          descripcion="Los resultados aparecen a medida que escribís."
        />
      ) : isLoading || isFetching ? (
        <CargandoBloque texto="Buscando…" />
      ) : isError ? (
        <EstadoError mensaje={(error as Error)?.message} />
      ) : !data || data.items.length === 0 ? (
        <EstadoVacio titulo="Sin coincidencias" descripcion={`No hay resultados para «${qDebounced}».`} />
      ) : (
        <Card>
          <div className="border-b border-linea px-4 py-2 text-xs text-carbon-suave">
            {data.total} resultado{data.total === 1 ? "" : "s"}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-linea bg-petrol-tint/40 text-left text-xs uppercase tracking-wide text-carbon-suave">
                  <th className="px-4 py-3 font-semibold">Tipo</th>
                  <th className="px-4 py-3 font-semibold">Código</th>
                  <th className="px-4 py-3 font-semibold">Título</th>
                  <th className="px-4 py-3 font-semibold">Área</th>
                  <th className="px-4 py-3 font-semibold">Estado</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((r) => (
                  <tr
                    key={`${r.entidad}-${r.id}`}
                    onClick={() => abrir(r.entidad, r.id)}
                    className="cursor-pointer border-b border-linea last:border-0 hover:bg-petrol-tint/30"
                  >
                    <td className="px-4 py-3">
                      <TipoBadge tipo={r.entidad} />
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-carbon-suave">
                      {r.codigo}
                    </td>
                    <td className="px-4 py-3 font-medium text-carbon">{r.titulo}</td>
                    <td className="px-4 py-3 text-carbon-suave">{r.area_codigo ?? "—"}</td>
                    <td className="px-4 py-3">
                      <EstadoBadge estado={r.estado} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
