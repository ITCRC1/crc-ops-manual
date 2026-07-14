"use client";

import { useMemo, useState } from "react";

import type {
  Departamento,
  DescriptorItem,
  Division,
  NodoOrganigrama,
} from "@/lib/types";

import { OrgTree } from "./OrgTree";
import { Card } from "./ui";

/**
 * Vista del organigrama por estructura: División → Subdivisión → Departamento → puestos.
 * Dentro de cada departamento se arma el árbol jerárquico según `reporta_a`. Un miembro
 * cuyo jefe no pertenece al mismo departamento se trata como raíz de ese departamento.
 */
function construirArbolDepto(
  miembros: DescriptorItem[],
  deptoCodigo: string | undefined,
): NodoOrganigrama[] {
  const idsGrupo = new Set(miembros.map((m) => m.id));
  const nodos = new Map<string, NodoOrganigrama>();
  for (const m of miembros) {
    nodos.set(m.id, {
      id: m.id,
      codigo: m.codigo,
      titulo: m.titulo,
      nivel_jerarquico: m.nivel_jerarquico,
      categoria: m.categoria,
      estado: m.estado,
      departamento_id: m.departamento_id,
      departamento_codigo: deptoCodigo ?? null,
      hijos: [],
    });
  }
  const raices: NodoOrganigrama[] = [];
  for (const m of miembros) {
    const nodo = nodos.get(m.id)!;
    if (m.reporta_a_id && idsGrupo.has(m.reporta_a_id)) {
      nodos.get(m.reporta_a_id)!.hijos.push(nodo);
    } else {
      raices.push(nodo);
    }
  }
  const ordenar = (arr: NodoOrganigrama[]) => {
    arr.sort((a, b) => a.nivel_jerarquico - b.nivel_jerarquico || a.codigo.localeCompare(b.codigo));
    for (const n of arr) ordenar(n.hijos);
  };
  ordenar(raices);
  return raices;
}

function DeptoCard({
  depto,
  miembros,
}: {
  depto: Departamento;
  miembros: DescriptorItem[];
}) {
  const [abierto, setAbierto] = useState(true);
  return (
    <Card className="overflow-hidden">
      <button
        onClick={() => setAbierto((v) => !v)}
        aria-expanded={abierto}
        className="flex w-full items-center justify-between gap-3 border-b border-linea bg-petrol-tint/40 px-4 py-2.5 text-left"
      >
        <span className="flex items-center gap-2">
          <span className="inline-flex h-6 min-w-[3rem] items-center justify-center rounded bg-petrol px-1.5 text-xs font-medium text-white">
            {depto.codigo}
          </span>
          <span className="text-sm font-semibold text-petrol-oscuro">{depto.nombre}</span>
        </span>
        <span className="text-xs text-carbon-suave">
          {miembros.length} {miembros.length === 1 ? "puesto" : "puestos"} {abierto ? "▾" : "▸"}
        </span>
      </button>
      {abierto && (
        <div className="p-4">
          {miembros.length === 0 ? (
            <p className="text-sm text-carbon-suave/70">Sin puestos asignados aún.</p>
          ) : (
            <OrgTree raices={construirArbolDepto(miembros, depto.codigo)} />
          )}
        </div>
      )}
    </Card>
  );
}

export function DescriptoresPorDepartamento({
  descriptores,
  departamentos,
  divisiones,
  modo = "division",
}: {
  descriptores: DescriptorItem[];
  departamentos: Departamento[];
  divisiones: Division[];
  modo?: "division" | "departamento";
}) {
  // Sub-tab activo en la vista por división (hook siempre presente, antes de returns).
  const [divTab, setDivTab] = useState<string | null>(null);

  // Departamentos únicos por código (el catálogo puede traer duplicados por propiedad).
  const deptos = useMemo(() => {
    const m = new Map<string, Departamento>();
    for (const d of departamentos) if (!m.has(d.codigo)) m.set(d.codigo, d);
    return [...m.values()];
  }, [departamentos]);

  // Descriptores por departamento.
  const { porDepto, sinDepto } = useMemo(() => {
    const porDepto = new Map<string, DescriptorItem[]>();
    const sinDepto: DescriptorItem[] = [];
    for (const d of descriptores) {
      if (d.departamento_id) {
        const lista = porDepto.get(d.departamento_id) ?? [];
        lista.push(d);
        porDepto.set(d.departamento_id, lista);
      } else {
        sinDepto.push(d);
      }
    }
    return { porDepto, sinDepto };
  }, [descriptores]);

  const deptosConMiembros = (divId: string | null) =>
    deptos
      .filter((d) => (divId === null ? !d.division_id : d.division_id === divId))
      .filter((d) => (porDepto.get(d.id)?.length ?? 0) > 0)
      .sort((a, b) => a.nombre.localeCompare(b.nombre));

  // Todos los departamentos de una división/subdivisión (incl. vacíos): la vista por
  // división muestra la estructura completa del organigrama, no solo los que tienen gente.
  const deptosDeDiv = (divId: string | null) =>
    deptos
      .filter((d) => (divId === null ? !d.division_id : d.division_id === divId))
      .sort((a, b) => a.nombre.localeCompare(b.nombre));

  const fallbackSinDepto =
    sinDepto.length > 0 ? (
      <Card className="overflow-hidden">
        <div className="border-b border-linea bg-fondo px-4 py-2.5 text-sm font-semibold text-carbon-suave">
          Puestos sin departamento asignado ({sinDepto.length})
        </div>
        <div className="p-4">
          <OrgTree raices={construirArbolDepto(sinDepto, undefined)} />
        </div>
      </Card>
    ) : null;

  // Modo "departamento": lista plana de departamentos (sin la capa de divisiones).
  if (modo === "departamento") {
    const todos = deptos
      .filter((d) => (porDepto.get(d.id)?.length ?? 0) > 0)
      .sort((a, b) => a.nombre.localeCompare(b.nombre));
    return (
      <div className="space-y-4">
        {todos.map((d) => (
          <DeptoCard key={d.id} depto={d} miembros={porDepto.get(d.id) ?? []} />
        ))}
        {fallbackSinDepto}
      </div>
    );
  }

  const topDivs = divisiones
    .filter((v) => !v.parent_id)
    .sort((a, b) => a.orden - b.orden || a.nombre.localeCompare(b.nombre));
  const subDivs = (parentId: string) =>
    divisiones
      .filter((v) => v.parent_id === parentId)
      .sort((a, b) => a.orden - b.orden || a.nombre.localeCompare(b.nombre));

  const deptosSinDivision = deptosDeDiv(null);

  // Un tab por división grande que tenga estructura (departamentos y/o subdivisiones),
  // más "Gerencia General" para puestos de dirección sin departamento.
  const tabs: { key: string; label: string }[] = [];
  for (const div of topDivs) {
    const directos = deptosDeDiv(div.id);
    const subs = subDivs(div.id);
    if (directos.length > 0 || subs.length > 0) {
      tabs.push({ key: div.id, label: div.nombre });
    }
  }
  // Los puestos de dirección sin departamento se muestran en la vista "Dirección
  // General", no acá; por eso la vista por división no incluye un tab de Gerencia General.

  if (tabs.length === 0) {
    return <p className="text-sm text-carbon-suave">Sin puestos para mostrar.</p>;
  }
  const activa = tabs.some((t) => t.key === divTab) ? divTab! : tabs[0].key;
  const divActiva = topDivs.find((d) => d.id === activa);

  return (
    <div>
      <div className="mb-5 flex flex-wrap gap-2 border-b border-linea">
        {tabs.map((t) => {
          const on = t.key === activa;
          return (
            <button
              key={t.key}
              onClick={() => setDivTab(t.key)}
              aria-current={on ? "page" : undefined}
              className={`-mb-px rounded-t-md border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
                on
                  ? "border-petrol text-petrol-oscuro"
                  : "border-transparent text-carbon-suave hover:text-petrol-oscuro"
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      {divActiva ? (
        <div className="space-y-4">
          {deptosDeDiv(divActiva.id).map((d) => (
            <DeptoCard key={d.id} depto={d} miembros={porDepto.get(d.id) ?? []} />
          ))}
          {subDivs(divActiva.id).map((s) => {
            const deps = deptosDeDiv(s.id);
            return (
              <div key={s.id} className="rounded-lg border border-dashed border-linea p-3">
                <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-carbon-suave">
                  Subdivisión · {s.nombre}
                </p>
                {deps.length === 0 ? (
                  <p className="text-sm text-carbon-suave/70">Sin departamentos aún.</p>
                ) : (
                  <div className="space-y-3">
                    {deps.map((d) => (
                      <DeptoCard key={d.id} depto={d} miembros={porDepto.get(d.id) ?? []} />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="space-y-4">
          {deptosSinDivision.map((d) => (
            <DeptoCard key={d.id} depto={d} miembros={porDepto.get(d.id) ?? []} />
          ))}
          {fallbackSinDepto}
        </div>
      )}
    </div>
  );
}
