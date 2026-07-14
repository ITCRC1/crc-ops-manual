"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { EstadoBadge, TipoBadge } from "@/components/EstadoBadge";
import { InvitarColaboradoresLote } from "@/components/InvitarColaboradoresLote";
import {
  Card,
  CargandoBloque,
  EstadoError,
  EstadoVacio,
  Input,
  PageHeader,
} from "@/components/ui";
import { tieneRol, useAuth } from "@/lib/auth";
import { useSops } from "@/lib/hooks";
import type { SopItem } from "@/lib/types";

// `origen_propiedad` es la huella interna que marca los SOPs nacidos en Amarena.
// No se expone en la ficha ni en la librería: solo se consulta con este filtro.
const ORIGEN = "AMA";
// Son pocos y caben en una sola página: sin paginación se leen de un vistazo.
const LIMIT = 200;

const ESTADO_LABEL: Record<string, string> = {
  borrador: "Borrador",
  en_revision: "En revisión",
  en_firma: "En firma",
  firmado: "Firmado",
  rechazado: "Rechazado",
  archivado: "Archivado",
};
// Orden del ciclo de vida, para que el resumen se lea como un avance.
const ESTADO_ORDEN = ["borrador", "en_revision", "en_firma", "firmado", "rechazado", "archivado"];

function agruparPorArea(items: SopItem[]): [string, SopItem[]][] {
  const grupos = new Map<string, SopItem[]>();
  for (const s of items) {
    const g = grupos.get(s.area_codigo);
    if (g) g.push(s);
    else grupos.set(s.area_codigo, [s]);
  }
  return [...grupos.entries()].sort(([a], [b]) => a.localeCompare(b));
}

export default function AmarenaPage() {
  const router = useRouter();
  const { user } = useAuth();
  // La marca de origen es curaduría interna, igual que el tab "Por Origen" de la librería.
  const puede = tieneRol(user, "editor_corporativo", "super_admin");
  const [q, setQ] = useState("");

  const { data, isLoading, isError, error } = useSops({
    origen_propiedad: ORIGEN,
    limit: LIMIT,
  });

  const items = useMemo(() => data?.items ?? [], [data]);

  const conteos = useMemo(() => {
    const c = new Map<string, number>();
    for (const s of items) c.set(s.estado, (c.get(s.estado) ?? 0) + 1);
    return ESTADO_ORDEN.filter((e) => c.has(e)).map((e) => [e, c.get(e) as number] as const);
  }, [items]);

  const filtrados = useMemo(() => {
    const t = q.trim().toLowerCase();
    if (!t) return items;
    return items.filter(
      (s) => s.codigo.toLowerCase().includes(t) || s.nombre.toLowerCase().includes(t),
    );
  }, [items, q]);

  const grupos = useMemo(() => agruparPorArea(filtrados), [filtrados]);
  const aprobados = items.filter((s) => s.estado === "firmado").length;

  // Al volver desde la ficha (`?foco=<codigo>`), centrar y resaltar esa fila.
  // Se lee de window en un efecto, no con useSearchParams, para no forzar a esta
  // página a renderizarse bajo demanda. Corre cuando la tabla ya existe en el DOM.
  const [foco, setFoco] = useState<string | null>(null);
  useEffect(() => {
    if (items.length === 0) return;
    const codigo = new URLSearchParams(window.location.search).get("foco");
    if (!codigo) return;
    setFoco(codigo);
    document.getElementById(codigo)?.scrollIntoView({ block: "center" });
    // Limpiar el parámetro: al recargar o compartir la URL no debe quedar pegado.
    window.history.replaceState(null, "", "/amarena");
    const t = setTimeout(() => setFoco(null), 2200);
    return () => clearTimeout(t);
  }, [items.length]);

  if (!puede) {
    return (
      <div>
        <PageHeader titulo="SOPs de Amarena" />
        <EstadoVacio
          titulo="Sin permisos"
          descripcion="La marca de origen es curaduría interna: solo el admin o el editor corporativo la ve."
        />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        titulo="SOPs de Amarena"
        descripcion="Los documentos marcados con origen AMA: la primera tanda a asignar, una vez revisada y aprobada. Vista de solo lectura — hacé clic en cualquiera para abrirlo."
        accion={items.length > 0 ? <InvitarColaboradoresLote sopsFijos={items} /> : undefined}
      />

      {isLoading ? (
        <CargandoBloque />
      ) : isError ? (
        <EstadoError mensaje={(error as Error)?.message} />
      ) : items.length === 0 ? (
        <EstadoVacio
          titulo="Ningún SOP marcado como Amarena"
          descripcion="La marca `origen_propiedad = AMA` se asigna al ingresar el documento."
        />
      ) : (
        <>
          <Card className="mb-4 p-4">
            <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
              <div>
                <p className="text-2xl font-semibold leading-none text-petrol-oscuro">
                  {items.length}
                </p>
                <p className="mt-1 text-xs text-carbon-suave">documentos</p>
              </div>
              <div>
                <p className="text-2xl font-semibold leading-none text-petrol-oscuro">
                  {aprobados}
                  <span className="text-base font-normal text-carbon-suave"> / {items.length}</span>
                </p>
                <p className="mt-1 text-xs text-carbon-suave">aprobados (firmados)</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {conteos.map(([estado, n]) => (
                  <span
                    key={estado}
                    className="inline-flex items-center gap-1.5 rounded-full border border-linea px-2.5 py-1 text-xs text-carbon-suave"
                  >
                    <span className="font-semibold text-carbon">{n}</span>
                    {ESTADO_LABEL[estado] ?? estado}
                  </span>
                ))}
              </div>
            </div>
          </Card>

          <Card className="mb-4 p-4">
            <Input
              placeholder="Buscar por nombre o código…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              aria-label="Buscar"
            />
          </Card>

          {filtrados.length === 0 ? (
            <EstadoVacio titulo="Sin resultados" descripcion="Probá con otro nombre o código." />
          ) : (
            <Card>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-linea bg-petrol-tint/40 text-left text-xs uppercase tracking-wide text-carbon-suave">
                      <th className="px-4 py-3 font-semibold">Código</th>
                      <th className="px-4 py-3 font-semibold">Nombre</th>
                      <th className="px-4 py-3 font-semibold">Tipo</th>
                      <th className="px-4 py-3 font-semibold">Estado</th>
                      <th className="px-4 py-3 font-semibold">Ver.</th>
                    </tr>
                  </thead>
                  {/* Un <tbody> por área: agrupa sin romper la semántica de la tabla. */}
                  {grupos.map(([area, sops]) => (
                    <tbody key={area}>
                      <tr className="border-b border-linea bg-superficie">
                        <td
                          colSpan={5}
                          className="px-4 py-2 text-xs font-semibold uppercase tracking-wide text-petrol-oscuro"
                        >
                          {area}
                          <span className="ml-2 font-normal normal-case text-carbon-suave">
                            {sops.length} {sops.length === 1 ? "documento" : "documentos"}
                          </span>
                        </td>
                      </tr>
                      {sops.map((s) => (
                        <tr
                          key={s.id}
                          // `volver` hace que la ficha regrese acá y deje esta fila a la
                          // vista: revisar 17 seguidos sin perder el lugar.
                          id={s.codigo}
                          onClick={() => router.push(`/biblioteca/${s.id}?volver=amarena`)}
                          className={`scroll-mt-24 cursor-pointer border-b border-linea transition-colors hover:bg-petrol-tint/30 ${
                            foco === s.codigo ? "bg-petrol-tint" : ""
                          }`}
                        >
                          <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-carbon-suave">
                            {s.codigo}
                          </td>
                          <td className="px-4 py-3 font-medium text-carbon">{s.nombre}</td>
                          <td className="px-4 py-3">
                            <TipoBadge tipo={s.tipo} />
                          </td>
                          <td className="px-4 py-3">
                            <EstadoBadge estado={s.estado} />
                          </td>
                          <td className="px-4 py-3 text-carbon-suave">v{s.version_actual}</td>
                        </tr>
                      ))}
                    </tbody>
                  ))}
                </table>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
