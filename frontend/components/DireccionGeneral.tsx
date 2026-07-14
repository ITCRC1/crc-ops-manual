"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

import { CATEGORIA_LABEL, CATEGORIA_ORDEN, categoriaCodigo } from "@/lib/categorias";
import type { Departamento, DescriptorItem, Division, NodoOrganigrama } from "@/lib/types";

import { OrgTree } from "./OrgTree";
import { Card } from "./ui";

// Árbol jerárquico (reporta_a) dentro de un conjunto de puestos (para la cúpula).
function construirArbol(items: DescriptorItem[]): NodoOrganigrama[] {
  const ids = new Set(items.map((i) => i.id));
  const nodos = new Map<string, NodoOrganigrama>();
  for (const m of items) {
    nodos.set(m.id, {
      id: m.id, codigo: m.codigo, titulo: m.titulo, nivel_jerarquico: m.nivel_jerarquico,
      categoria: m.categoria, estado: m.estado, departamento_id: m.departamento_id,
      departamento_codigo: null, hijos: [],
    });
  }
  const raices: NodoOrganigrama[] = [];
  for (const m of items) {
    const n = nodos.get(m.id)!;
    if (m.reporta_a_id && ids.has(m.reporta_a_id)) nodos.get(m.reporta_a_id)!.hijos.push(n);
    else raices.push(n);
  }
  const ord = (arr: NodoOrganigrama[]) => {
    arr.sort((a, b) => a.nivel_jerarquico - b.nivel_jerarquico || a.codigo.localeCompare(b.codigo));
    for (const n of arr) ord(n.hijos);
  };
  ord(raices);
  return raices;
}

// Fila colapsable genérica del árbol de líneas divisionales.
function Rama({
  etiqueta,
  sub,
  count,
  fuerte,
  children,
}: {
  etiqueta: string;
  sub?: string;
  count?: number;
  fuerte?: boolean;
  children: React.ReactNode;
}) {
  const [abierto, setAbierto] = useState(false);
  return (
    <div>
      <button
        onClick={() => setAbierto((v) => !v)}
        aria-expanded={abierto}
        className="flex w-full items-center gap-2 rounded px-1 py-1.5 text-left hover:bg-petrol-tint/40"
      >
        <span className="w-4 shrink-0 text-xs text-carbon-suave">{abierto ? "▾" : "▸"}</span>
        <span
          className={
            fuerte
              ? "text-sm font-bold text-petrol-oscuro"
              : "text-sm font-medium text-carbon"
          }
        >
          {etiqueta}
        </span>
        {sub && (
          <span className="rounded-full bg-fondo px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-carbon-suave">
            {sub}
          </span>
        )}
        {count != null && (
          <span className="text-xs text-carbon-suave">
            {count} {count === 1 ? "puesto" : "puestos"}
          </span>
        )}
      </button>
      {abierto && <div className="ml-3 border-l border-linea pl-3">{children}</div>}
    </div>
  );
}

export function DireccionGeneral({
  descriptores,
  departamentos,
  divisiones,
}: {
  descriptores: DescriptorItem[];
  departamentos: Departamento[];
  divisiones: Division[];
}) {
  const deptos = useMemo(() => {
    const m = new Map<string, Departamento>();
    for (const d of departamentos) if (!m.has(d.codigo)) m.set(d.codigo, d);
    return [...m.values()];
  }, [departamentos]);

  const cupula = useMemo(() => descriptores.filter((d) => !d.departamento_id), [descriptores]);

  // Puestos por departamento.
  const puestosPorDepto = useMemo(() => {
    const m = new Map<string, DescriptorItem[]>();
    for (const d of descriptores) {
      if (!d.departamento_id) continue;
      const l = m.get(d.departamento_id) ?? [];
      l.push(d);
      m.set(d.departamento_id, l);
    }
    return m;
  }, [descriptores]);

  const topDivs = divisiones
    .filter((v) => !v.parent_id)
    .sort((a, b) => a.orden - b.orden || a.nombre.localeCompare(b.nombre));
  const subDivs = (pid: string) =>
    divisiones
      .filter((v) => v.parent_id === pid)
      .sort((a, b) => a.orden - b.orden || a.nombre.localeCompare(b.nombre));
  const deptosDe = (divId: string) =>
    deptos.filter((d) => d.division_id === divId).sort((a, b) => a.nombre.localeCompare(b.nombre));

  const countDivision = (divId: string) => {
    let n = deptosDe(divId).reduce((a, d) => a + (puestosPorDepto.get(d.id)?.length ?? 0), 0);
    for (const s of subDivs(divId))
      n += deptosDe(s.id).reduce((a, d) => a + (puestosPorDepto.get(d.id)?.length ?? 0), 0);
    return n;
  };

  // Departamento colapsable → puestos agrupados por categoría.
  const RamaDepto = ({ dep }: { dep: Departamento }) => {
    const puestos = (puestosPorDepto.get(dep.id) ?? []).slice();
    return (
      <Rama etiqueta={dep.nombre} count={puestos.length}>
        {puestos.length === 0 ? (
          <p className="py-1 text-xs text-carbon-suave/70">Sin puestos aún.</p>
        ) : (
          CATEGORIA_ORDEN.map((cat) => {
            const items = puestos
              .filter((p) => categoriaCodigo(p.categoria, p.nivel_jerarquico) === cat)
              .sort((a, b) => a.codigo.localeCompare(b.codigo));
            if (items.length === 0) return null;
            return (
              <div key={cat} className="py-1">
                <p className="text-[10px] font-semibold uppercase tracking-wide text-carbon-suave">
                  {CATEGORIA_LABEL[cat]}
                </p>
                <ul className="mt-0.5 space-y-0.5">
                  {items.map((p) => (
                    <li key={p.id} className="flex items-center gap-2 text-sm">
                      <span className="inline-flex h-5 min-w-[3.25rem] items-center justify-center rounded bg-petrol-tint px-1 text-[11px] font-medium text-petrol-oscuro">
                        {p.codigo}
                      </span>
                      <Link
                        href={`/descriptores/${p.id}`}
                        className="text-carbon hover:text-petrol-oscuro hover:underline"
                      >
                        {p.titulo}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })
        )}
      </Rama>
    );
  };

  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-3 border-b-2 border-petrol pb-1 text-base font-bold uppercase tracking-wide text-petrol-oscuro">
          Gerencia General
        </h2>
        {cupula.length > 0 ? (
          <OrgTree raices={construirArbol(cupula)} colapsable />
        ) : (
          <p className="text-sm text-carbon-suave/70">Sin puestos de dirección corporativa.</p>
        )}
      </section>

      <section>
        <h2 className="mb-3 border-b-2 border-linea pb-1 text-base font-bold uppercase tracking-wide text-carbon-suave">
          Líneas divisionales
        </h2>
        <Card className="divide-y divide-linea p-2">
          {topDivs.map((div) => (
            <div key={div.id} className="py-1">
              <Rama etiqueta={div.nombre} count={countDivision(div.id)} fuerte>
                {deptosDe(div.id).map((d) => (
                  <RamaDepto key={d.id} dep={d} />
                ))}
                {subDivs(div.id).map((s) => (
                  <Rama key={s.id} etiqueta={s.nombre} sub="subdivisión">
                    {deptosDe(s.id).map((d) => (
                      <RamaDepto key={d.id} dep={d} />
                    ))}
                  </Rama>
                ))}
              </Rama>
            </div>
          ))}
        </Card>
      </section>
    </div>
  );
}
