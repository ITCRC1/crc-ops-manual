"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { DescriptoresPorDepartamento } from "@/components/DescriptoresPorDepartamento";
import { DireccionGeneral } from "@/components/DireccionGeneral";
import { EstadoBadge } from "@/components/EstadoBadge";
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
import { CATEGORIA_LABEL, CATEGORIA_ORDEN, categoriaLabel } from "@/lib/categorias";
import { useDepartamentos, useDescriptores, useDivisiones } from "@/lib/hooks";
import { useDebouncedValue } from "@/lib/use-debounce";

const LIMIT = 25;

export default function DescriptoresPage() {
  const router = useRouter();
  const [vista, setVista] = useState<"lista" | "departamento" | "division" | "direccion">("lista");
  const [q, setQ] = useState("");
  const [categoria, setCategoria] = useState("");
  const [departamento, setDepartamento] = useState("");
  const [estado, setEstado] = useState("");
  const [page, setPage] = useState(0);

  const { user } = useAuth();
  const puedeCrear = tieneRol(user, "editor_corporativo", "super_admin");
  const qDebounced = useDebouncedValue(q, 300);
  const { data: departamentos } = useDepartamentos();
  const { data: divisiones } = useDivisiones();

  // Vista "Por Departamento": trae todos los descriptores y los agrupa según el organigrama.
  const porDepto = useDescriptores({ limit: 200 });
  const departamentosUnicos = useMemo(() => {
    const vistos = new Map<string, { id: string; codigo: string; nombre: string }>();
    for (const d of departamentos ?? []) if (!vistos.has(d.codigo)) vistos.set(d.codigo, d);
    return [...vistos.values()];
  }, [departamentos]);

  const { data, isLoading, isError, error } = useDescriptores({
    q: qDebounced || undefined,
    categoria: categoria || undefined,
    departamento_id: departamento || undefined,
    estado: estado || undefined,
    limit: LIMIT,
    offset: page * LIMIT,
  });

  const total = data?.total ?? 0;
  const desde = total === 0 ? 0 : page * LIMIT + 1;
  const hasta = Math.min((page + 1) * LIMIT, total);
  const codPorId = new Map((departamentos ?? []).map((d) => [d.id, d.codigo]));

  return (
    <div>
      <PageHeader
        titulo="Descriptores de puesto"
        descripcion="Perfiles con propósito, responsabilidades, KPIs y jerarquía."
        accion={
          puedeCrear ? (
            <Link href="/descriptores/nuevo">
              <Button>+ Nuevo descriptor</Button>
            </Link>
          ) : undefined
        }
      />

      <div className="mb-4 inline-flex rounded-md border border-linea bg-superficie p-1">
        <button
          onClick={() => setVista("lista")}
          className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
            vista === "lista" ? "bg-petrol text-white" : "text-carbon-suave hover:bg-petrol-tint"
          }`}
        >
          Lista
        </button>
        <button
          onClick={() => setVista("departamento")}
          className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
            vista === "departamento" ? "bg-petrol text-white" : "text-carbon-suave hover:bg-petrol-tint"
          }`}
        >
          Por Departamento
        </button>
        <button
          onClick={() => setVista("division")}
          className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
            vista === "division" ? "bg-petrol text-white" : "text-carbon-suave hover:bg-petrol-tint"
          }`}
        >
          Por División
        </button>
        <button
          onClick={() => setVista("direccion")}
          className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
            vista === "direccion" ? "bg-petrol text-white" : "text-carbon-suave hover:bg-petrol-tint"
          }`}
        >
          Dirección General
        </button>
      </div>

      {vista === "departamento" || vista === "division" || vista === "direccion" ? (
        porDepto.isLoading ? (
          <CargandoBloque />
        ) : porDepto.isError ? (
          <EstadoError mensaje={(porDepto.error as Error)?.message} />
        ) : vista === "direccion" ? (
          <DireccionGeneral
            descriptores={porDepto.data?.items ?? []}
            departamentos={departamentos ?? []}
            divisiones={divisiones ?? []}
          />
        ) : (
          <DescriptoresPorDepartamento
            descriptores={porDepto.data?.items ?? []}
            departamentos={departamentos ?? []}
            divisiones={divisiones ?? []}
            modo={vista === "division" ? "division" : "departamento"}
          />
        )
      ) : (
        <ListaDescriptores />
      )}
    </div>
  );

  function ListaDescriptores() {
    return (
      <>
      <Card className="mb-4 p-4">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Input
            placeholder="Buscar por título o código…"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(0);
            }}
            aria-label="Buscar"
          />
          <Select
            value={categoria}
            onChange={(e) => {
              setCategoria(e.target.value);
              setPage(0);
            }}
            aria-label="Categoría"
          >
            <option value="">Todas las categorías</option>
            {CATEGORIA_ORDEN.map((c) => (
              <option key={c} value={c}>
                {CATEGORIA_LABEL[c]}
              </option>
            ))}
          </Select>
          <Select
            value={departamento}
            onChange={(e) => {
              setDepartamento(e.target.value);
              setPage(0);
            }}
            aria-label="Departamento"
          >
            <option value="">Todos los departamentos</option>
            {departamentosUnicos.map((d) => (
              <option key={d.id} value={d.id}>
                {d.codigo} — {d.nombre}
              </option>
            ))}
          </Select>
          <Select
            value={estado}
            onChange={(e) => {
              setEstado(e.target.value);
              setPage(0);
            }}
            aria-label="Estado"
          >
            <option value="">Todos los estados</option>
            <option value="borrador">Borrador</option>
            <option value="en_revision">En revisión</option>
            <option value="firmado">Firmado</option>
            <option value="archivado">Archivado</option>
          </Select>
        </div>
      </Card>

      {isLoading ? (
        <CargandoBloque />
      ) : isError ? (
        <EstadoError mensaje={(error as Error)?.message} />
      ) : !data || data.items.length === 0 ? (
        <EstadoVacio titulo="Sin resultados" descripcion="Ajustá los filtros." />
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-linea bg-petrol-tint/40 text-left text-xs uppercase tracking-wide text-carbon-suave">
                  <th className="px-4 py-3 font-semibold">Código</th>
                  <th className="px-4 py-3 font-semibold">Título</th>
                  <th className="px-4 py-3 font-semibold">Categoría</th>
                  <th className="px-4 py-3 font-semibold">Depto.</th>
                  <th className="px-4 py-3 font-semibold">Estado</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((d) => (
                  <tr
                    key={d.id}
                    onClick={() => router.push(`/descriptores/${d.id}`)}
                    className="cursor-pointer border-b border-linea last:border-0 hover:bg-petrol-tint/30"
                  >
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-carbon-suave">
                      {d.codigo}
                    </td>
                    <td className="px-4 py-3 font-medium text-carbon">{d.titulo}</td>
                    <td className="px-4 py-3 text-carbon-suave">
                      {categoriaLabel(d.categoria, d.nivel_jerarquico)}
                    </td>
                    <td className="px-4 py-3 text-carbon-suave">
                      {d.departamento_id ? (codPorId.get(d.departamento_id) ?? "—") : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <EstadoBadge estado={d.estado} />
                    </td>
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
      </>
    );
  }
}
