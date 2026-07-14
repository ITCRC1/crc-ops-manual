"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { EstadoBadge, TipoBadge } from "@/components/EstadoBadge";
import { InvitarColaboradoresLote } from "@/components/InvitarColaboradoresLote";
import {
  Button,
  Card,
  CargandoBloque,
  EstadoError,
  EstadoVacio,
  Input,
  PageHeader,
  Select,
} from "@/components/ui";
import { tieneRol, useAuth } from "@/lib/auth";
import { useAreas, useDepartamentos, usePropiedades, useSops } from "@/lib/hooks";
import { useDebouncedValue } from "@/lib/use-debounce";
import type { RelacionDepartamento } from "@/lib/types";

const ESTADOS = ["borrador", "en_revision", "en_firma", "firmado", "rechazado", "archivado"];
const ESTADO_LABEL: Record<string, string> = {
  borrador: "Borrador",
  en_revision: "En revisión",
  en_firma: "En firma",
  firmado: "Firmado",
  rechazado: "Rechazado",
  archivado: "Archivado",
};
const RELACION_LABEL: Record<RelacionDepartamento, string> = {
  propio: "Propio",
  afecta: "Afecta",
  ambos: "Propio + afecta",
};
const LIMIT = 25;

function RelacionChip({ relacion }: { relacion: RelacionDepartamento | null }) {
  if (!relacion) return null;
  const clase =
    relacion === "afecta"
      ? "bg-en-firma/15 text-en-firma"
      : relacion === "ambos"
        ? "bg-petrol text-white"
        : "bg-petrol-tint text-petrol-oscuro";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${clase}`}>
      {RELACION_LABEL[relacion]}
    </span>
  );
}

export default function BibliotecaPage() {
  const router = useRouter();
  const [vista, setVista] = useState<"area" | "departamento" | "origen">("area");
  const [q, setQ] = useState("");
  const [area, setArea] = useState("");
  const [departamentoId, setDepartamentoId] = useState("");
  const [origen, setOrigen] = useState("AMA");
  const [estado, setEstado] = useState("");
  const [tipo, setTipo] = useState("");
  const [page, setPage] = useState(0);

  const { user } = useAuth();
  const puedeCrear = tieneRol(user, "editor_corporativo", "super_admin");
  // La marca de origen es curaduría interna: solo admin/corporativo ve el tab "Por Origen".
  const puedeCuraduria = tieneRol(user, "editor_corporativo", "super_admin");
  const qDebounced = useDebouncedValue(q, 300);
  const { data: areas } = useAreas();
  const { data: departamentos } = useDepartamentos();
  const { data: propiedades } = usePropiedades();
  const depUnicos = useMemo(() => {
    const m = new Map<string, { id: string; codigo: string; nombre: string }>();
    for (const d of departamentos ?? []) if (!m.has(d.codigo)) m.set(d.codigo, d);
    return [...m.values()];
  }, [departamentos]);

  const { data, isLoading, isError, error } = useSops({
    q: qDebounced || undefined,
    area: vista === "area" ? area || undefined : undefined,
    departamento_relacionado_id: vista === "departamento" ? departamentoId || undefined : undefined,
    origen_propiedad: vista === "origen" ? origen || undefined : undefined,
    estado: estado || undefined,
    tipo: tipo || undefined,
    limit: LIMIT,
    offset: page * LIMIT,
  });

  function cambiarVista(v: "area" | "departamento" | "origen") {
    setVista(v);
    setPage(0);
  }

  function cambiarFiltro(setter: (v: string) => void, value: string) {
    setter(value);
    setPage(0);
  }

  const total = data?.total ?? 0;
  const desde = total === 0 ? 0 : page * LIMIT + 1;
  const hasta = Math.min((page + 1) * LIMIT, total);

  return (
    <div>
      <PageHeader
        titulo="Librería maestra"
        descripcion="SOPs y políticas del grupo, con el formato único de 9 campos."
        accion={
          puedeCrear ? (
            <Link href="/biblioteca/nuevo">
              <Button>+ Nuevo documento SMART</Button>
            </Link>
          ) : undefined
        }
      />

      {/* Dar acceso de edición SMART por departamento: elegí el depto, se cargan sus SOPs. */}
      {puedeCrear && <InvitarColaboradoresLote />}

      <div className="mb-4 inline-flex rounded-md border border-linea bg-superficie p-1">
        <button
          onClick={() => cambiarVista("area")}
          className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
            vista === "area" ? "bg-petrol text-white" : "text-carbon-suave hover:bg-petrol-tint"
          }`}
        >
          Por Área
        </button>
        <button
          onClick={() => cambiarVista("departamento")}
          className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
            vista === "departamento" ? "bg-petrol text-white" : "text-carbon-suave hover:bg-petrol-tint"
          }`}
        >
          Por Departamento
        </button>
        {puedeCuraduria && (
          <button
            onClick={() => cambiarVista("origen")}
            className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
              vista === "origen" ? "bg-petrol text-white" : "text-carbon-suave hover:bg-petrol-tint"
            }`}
          >
            Por Origen
          </button>
        )}
      </div>

      <Card className="mb-4 p-4">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Input
            placeholder="Buscar por nombre o código…"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(0);
            }}
            aria-label="Buscar"
          />
          {vista === "area" ? (
            <Select
              value={area}
              onChange={(e) => cambiarFiltro(setArea, e.target.value)}
              aria-label="Área"
            >
              <option value="">Todas las áreas</option>
              {areas?.map((a) => (
                <option key={a.id} value={a.codigo}>
                  {a.codigo} — {a.nombre}
                </option>
              ))}
            </Select>
          ) : vista === "departamento" ? (
            <Select
              value={departamentoId}
              onChange={(e) => cambiarFiltro(setDepartamentoId, e.target.value)}
              aria-label="Departamento"
            >
              <option value="">Elegí un departamento…</option>
              {depUnicos.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.codigo} — {d.nombre}
                </option>
              ))}
            </Select>
          ) : (
            <Select
              value={origen}
              onChange={(e) => cambiarFiltro(setOrigen, e.target.value)}
              aria-label="Propiedad de origen"
            >
              {(propiedades ?? []).map((p) => (
                <option key={p.id} value={p.codigo}>
                  {p.codigo} — {p.nombre}
                </option>
              ))}
            </Select>
          )}
          <Select value={tipo} onChange={(e) => cambiarFiltro(setTipo, e.target.value)} aria-label="Tipo">
            <option value="">Todos los tipos</option>
            <option value="sop">SOP</option>
            <option value="politica">Política</option>
          </Select>
          <Select
            value={estado}
            onChange={(e) => cambiarFiltro(setEstado, e.target.value)}
            aria-label="Estado"
          >
            <option value="">Todos los estados</option>
            {ESTADOS.map((e) => (
              <option key={e} value={e}>
                {ESTADO_LABEL[e]}
              </option>
            ))}
          </Select>
        </div>
      </Card>

      {vista === "departamento" && !departamentoId ? (
        <EstadoVacio
          titulo="Elegí un departamento"
          descripcion="Vas a ver los SOPs propios de ese departamento y los que lo afectan, aunque pertenezcan a otro."
        />
      ) : isLoading ? (
        <CargandoBloque />
      ) : isError ? (
        <EstadoError mensaje={(error as Error)?.message} />
      ) : !data || data.items.length === 0 ? (
        <EstadoVacio
          titulo="Sin resultados"
          descripcion="Ajustá los filtros para encontrar documentos."
        />
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-linea bg-petrol-tint/40 text-left text-xs uppercase tracking-wide text-carbon-suave">
                  <th className="px-4 py-3 font-semibold">Código</th>
                  <th className="px-4 py-3 font-semibold">Nombre</th>
                  <th className="px-4 py-3 font-semibold">Área</th>
                  {vista === "departamento" && (
                    <th className="px-4 py-3 font-semibold">Relación</th>
                  )}
                  <th className="px-4 py-3 font-semibold">Tipo</th>
                  <th className="px-4 py-3 font-semibold">Estado</th>
                  <th className="px-4 py-3 font-semibold">Ver.</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((s) => (
                  <tr
                    key={s.id}
                    onClick={() => router.push(`/biblioteca/${s.id}`)}
                    className="cursor-pointer border-b border-linea last:border-0 hover:bg-petrol-tint/30"
                  >
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-carbon-suave">
                      {s.codigo}
                    </td>
                    <td className="px-4 py-3 font-medium text-carbon">{s.nombre}</td>
                    <td className="px-4 py-3 text-carbon-suave">{s.area_codigo}</td>
                    {vista === "departamento" && (
                      <td className="px-4 py-3">
                        <RelacionChip relacion={s.relacion_departamento} />
                      </td>
                    )}
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
            </table>
          </div>
          <div className="flex items-center justify-between border-t border-linea px-4 py-3 text-sm text-carbon-suave">
            <span>
              {desde}–{hasta} de {total}
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                Anterior
              </Button>
              <Button
                variant="secondary"
                disabled={hasta >= total}
                onClick={() => setPage((p) => p + 1)}
              >
                Siguiente
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
