"use client";

import Link from "next/link";

import { CargandoBloque, Card, EstadoError, EstadoVacio, PageHeader } from "@/components/ui";
import { useResumenPropiedades } from "@/lib/hooks";

function Metrica({ label, valor }: { label: string; valor: number }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <span>{label}</span>
      <span className="font-semibold text-carbon">{valor}</span>
    </div>
  );
}

export default function ArmadorPage() {
  const { data, isLoading, isError, error } = useResumenPropiedades();

  return (
    <div>
      <PageHeader
        titulo="Armador por propiedad"
        descripcion="Cada hotel arma su operación eligiendo del catálogo maestro: departamentos, organigrama de puestos con sus titulares, SOPs y sistemas."
      />
      {isLoading ? (
        <CargandoBloque />
      ) : isError ? (
        <EstadoError mensaje={(error as Error)?.message} />
      ) : !data || data.length === 0 ? (
        <EstadoVacio titulo="Sin propiedades" descripcion="No hay propiedades registradas todavía." />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((p) => (
            <Link key={p.id} href={`/armador/${p.id}`} className="block">
              <Card className="p-5 transition-colors hover:border-petrol">
                <div className="flex items-center gap-2">
                  <span className="rounded bg-petrol-tint px-2 py-0.5 text-xs font-medium text-petrol-oscuro">
                    {p.codigo}
                  </span>
                  <h2 className="min-w-0 flex-1 truncate text-sm font-semibold text-carbon">
                    {p.nombre}
                  </h2>
                </div>
                <dl className="mt-4 space-y-1 text-xs text-carbon-suave">
                  <Metrica label="Departamentos" valor={p.departamentos} />
                  <Metrica label="Puestos" valor={p.puestos} />
                  <Metrica label="Titulares" valor={p.ocupantes} />
                  <Metrica label="SOPs" valor={p.sops} />
                  <Metrica label="Sistemas" valor={p.sistemas} />
                </dl>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
