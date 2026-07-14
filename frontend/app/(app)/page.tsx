"use client";

import Link from "next/link";

import { Card, PageHeader } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useDescriptores, useSops } from "@/lib/hooks";

function Metrica({ valor, etiqueta }: { valor: number | string; etiqueta: string }) {
  return (
    <div>
      <p className="text-2xl font-semibold text-petrol-oscuro">{valor}</p>
      <p className="text-sm text-carbon-suave">{etiqueta}</p>
    </div>
  );
}

const ACCESOS = [
  {
    href: "/biblioteca",
    titulo: "Librería maestra",
    desc: "SOPs y políticas con el formato único de 9 campos.",
  },
  {
    href: "/descriptores",
    titulo: "Descriptores de puesto",
    desc: "Perfiles, responsabilidades, KPIs y jerarquía.",
  },
  {
    href: "/organigrama",
    titulo: "Organigrama",
    desc: "Estructura jerárquica derivada de «reporta a».",
  },
  {
    href: "/busqueda",
    titulo: "Búsqueda global",
    desc: "Buscá en SOPs, políticas y descriptores a la vez.",
  },
];

export default function Dashboard() {
  const { user } = useAuth();
  const sops = useSops({ limit: 1 });
  const politicas = useSops({ tipo: "politica", limit: 1 });
  const firmados = useSops({ estado: "firmado", limit: 1 });
  const descriptores = useDescriptores({ limit: 1 });

  return (
    <div>
      <PageHeader
        titulo={`Hola, ${user?.nombre?.split(" ")[0] ?? ""}`.trim()}
        descripcion="Resumen de la librería maestra de The Costa Rica Collection."
      />

      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card className="p-5">
          <Metrica valor={sops.data?.total ?? "—"} etiqueta="SOPs y políticas" />
        </Card>
        <Card className="p-5">
          <Metrica valor={politicas.data?.total ?? "—"} etiqueta="Políticas" />
        </Card>
        <Card className="p-5">
          <Metrica valor={firmados.data?.total ?? "—"} etiqueta="Firmados" />
        </Card>
        <Card className="p-5">
          <Metrica valor={descriptores.data?.total ?? "—"} etiqueta="Descriptores" />
        </Card>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {ACCESOS.map((a) => (
          <Link key={a.href} href={a.href}>
            <Card className="h-full p-5 transition-colors hover:border-petrol hover:bg-petrol-tint/30">
              <p className="font-medium text-petrol-oscuro">{a.titulo}</p>
              <p className="mt-1 text-sm text-carbon-suave">{a.desc}</p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
