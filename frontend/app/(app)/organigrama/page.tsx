"use client";

import { useState } from "react";

import { OrgTree } from "@/components/OrgTree";
import { Card, CargandoBloque, EstadoError, EstadoVacio, PageHeader } from "@/components/ui";
import { useOrganigrama } from "@/lib/hooks";

export default function OrganigramaPage() {
  const [vista, setVista] = useState<"sistema" | "referencia">("sistema");
  const { data, isLoading, isError, error } = useOrganigrama();

  return (
    <div>
      <PageHeader
        titulo="Organigrama"
        descripcion={
          vista === "sistema"
            ? "Estructura jerárquica del master de descriptores, derivada de «reporta a»."
            : "Organigrama gráfico oficial de Corcovado Wilderness Lodge (referencia de la dirección)."
        }
      />

      <div className="mb-4 inline-flex rounded-md border border-linea bg-superficie p-1">
        <button
          onClick={() => setVista("sistema")}
          className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
            vista === "sistema" ? "bg-petrol text-white" : "text-carbon-suave hover:bg-petrol-tint"
          }`}
        >
          Sistema
        </button>
        <button
          onClick={() => setVista("referencia")}
          className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
            vista === "referencia" ? "bg-petrol text-white" : "text-carbon-suave hover:bg-petrol-tint"
          }`}
        >
          Organigrama gráfico (CWL)
        </button>
      </div>

      {vista === "referencia" ? (
        <Card className="p-5">
          <h2 className="mb-4 text-center text-lg font-semibold text-rechazado">
            Corcovado Wilderness Lodge — Organizational Chart
          </h2>
          <div className="overflow-x-auto">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/organigrama-crc.png"
              alt="Organigrama oficial de Corcovado Wilderness Lodge"
              className="mx-auto h-auto max-w-none"
              style={{ width: "min(100%, 1200px)" }}
            />
          </div>
        </Card>
      ) : isLoading ? (
        <CargandoBloque />
      ) : isError ? (
        <EstadoError mensaje={(error as Error)?.message} />
      ) : !data || data.length === 0 ? (
        <EstadoVacio
          titulo="Sin descriptores"
          descripcion="Todavía no hay puestos cargados para construir el organigrama."
        />
      ) : (
        <Card className="p-5">
          <OrgTree raices={data} />
        </Card>
      )}
    </div>
  );
}
