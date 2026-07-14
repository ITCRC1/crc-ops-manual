"use client";

import { useState } from "react";
import Link from "next/link";

import { categoriaLabel } from "@/lib/categorias";
import type { NodoOrganigrama } from "@/lib/types";

function contarDescendientes(n: NodoOrganigrama): number {
  return n.hijos.reduce((acc, h) => acc + 1 + contarDescendientes(h), 0);
}

function Nodo({
  nodo,
  colapsable,
  abiertoInicial,
}: {
  nodo: NodoOrganigrama;
  colapsable: boolean;
  abiertoInicial: boolean;
}) {
  const tieneHijos = nodo.hijos.length > 0;
  const [abierto, setAbierto] = useState(abiertoInicial);
  const mostrarHijos = tieneHijos && (!colapsable || abierto);
  const total = tieneHijos ? contarDescendientes(nodo) : 0;

  return (
    <li className="relative">
      <div className="flex items-center gap-2 rounded-md border border-linea bg-superficie px-3 py-2">
        {colapsable && tieneHijos ? (
          <button
            onClick={() => setAbierto((v) => !v)}
            aria-expanded={abierto}
            aria-label={abierto ? "Contraer" : "Expandir"}
            className="flex h-5 w-5 shrink-0 items-center justify-center rounded text-xs text-carbon-suave hover:bg-petrol-tint hover:text-petrol-oscuro"
          >
            {abierto ? "▾" : "▸"}
          </button>
        ) : (
          <span className="w-5 shrink-0" />
        )}
        <span className="inline-flex h-6 min-w-[3.5rem] items-center justify-center rounded bg-petrol-tint px-1.5 text-xs font-medium text-petrol-oscuro">
          {nodo.codigo}
        </span>
        <div className="min-w-0 flex-1">
          <Link
            href={`/descriptores/${nodo.id}`}
            className="text-sm font-medium text-carbon hover:text-petrol-oscuro hover:underline"
          >
            {nodo.titulo}
          </Link>
          <p className="text-xs text-carbon-suave">
            {categoriaLabel(nodo.categoria, nodo.nivel_jerarquico)}
            {nodo.departamento_codigo ? ` · ${nodo.departamento_codigo}` : ""}
          </p>
        </div>
        {colapsable && tieneHijos && !abierto && (
          <button
            onClick={() => setAbierto(true)}
            className="shrink-0 rounded-full bg-petrol-tint px-2 py-0.5 text-xs font-medium text-petrol-oscuro hover:bg-petrol/20"
          >
            +{total} {total === 1 ? "puesto" : "puestos"}
          </button>
        )}
      </div>
      {mostrarHijos && (
        <ul className="ml-6 mt-2 space-y-2 border-l border-linea pl-4">
          {nodo.hijos.map((h) => (
            <Nodo key={h.id} nodo={h} colapsable={colapsable} abiertoInicial={false} />
          ))}
        </ul>
      )}
    </li>
  );
}

/**
 * Árbol del organigrama. Con `colapsable`, cada puesto con subordinados arranca cerrado
 * (salvo las raíces) y se despliega con un click — vista resumida con drill-down.
 */
export function OrgTree({
  raices,
  colapsable = false,
}: {
  raices: NodoOrganigrama[];
  colapsable?: boolean;
}) {
  return (
    <ul className="space-y-2">
      {raices.map((n) => (
        <Nodo key={n.id} nodo={n} colapsable={colapsable} abiertoInicial />
      ))}
    </ul>
  );
}
