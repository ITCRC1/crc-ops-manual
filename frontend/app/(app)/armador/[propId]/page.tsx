"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { ArmadorCapacitaciones } from "@/components/armador/ArmadorCapacitaciones";
import { ArmadorDepartamentos } from "@/components/armador/ArmadorDepartamentos";
import { ArmadorOrganigrama } from "@/components/armador/ArmadorOrganigrama";
import { ArmadorSistemas } from "@/components/armador/ArmadorSistemas";
import { ArmadorSops } from "@/components/armador/ArmadorSops";
import { EstadoVacio, PageHeader } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { usePropiedades, useResumenPropiedades } from "@/lib/hooks";
import type { Me } from "@/lib/types";

const TABS = [
  { key: "departamentos", label: "Departamentos" },
  { key: "organigrama", label: "Organigrama" },
  { key: "sops", label: "SOPs" },
  { key: "capacitaciones", label: "Capacitaciones" },
  { key: "sistemas", label: "Sistemas" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

function puedeGestionarPropiedad(user: Me | null, propId: string): boolean {
  if (!user) return false;
  return user.roles.some(
    (r) =>
      r.rol === "super_admin" ||
      r.rol === "editor_corporativo" ||
      (r.rol === "editor_propiedad" && (r.propiedad_id === null || r.propiedad_id === propId)),
  );
}

export default function ArmadorPropiedadPage() {
  const { propId } = useParams<{ propId: string }>();
  const { user } = useAuth();
  const { data: propiedades } = usePropiedades();
  const { data: resumen } = useResumenPropiedades();
  const [tab, setTab] = useState<TabKey>("departamentos");

  const prop = propiedades?.find((p) => p.id === propId);
  const puedeGestionar = puedeGestionarPropiedad(user, propId);
  // El resumen viene filtrado por el alcance del usuario; si cargó y no incluye esta
  // propiedad, no tiene acceso (§14).
  const sinAcceso = resumen !== undefined && !resumen.some((p) => p.id === propId);

  if (sinAcceso) {
    return (
      <div>
        <Link href="/armador" className="mb-4 inline-block text-sm text-petrol-oscuro hover:underline">
          ← Volver a propiedades
        </Link>
        <EstadoVacio
          titulo="Sin acceso a esta propiedad"
          descripcion="Tu usuario no tiene alcance sobre este hotel. Pedí acceso a un administrador."
        />
      </div>
    );
  }

  return (
    <div>
      <Link
        href="/armador"
        className="mb-4 inline-block text-sm text-petrol-oscuro hover:underline"
      >
        ← Volver a propiedades
      </Link>
      <PageHeader
        titulo={prop ? `${prop.codigo} — ${prop.nombre}` : "Propiedad"}
        descripcion="Armá la operación de esta propiedad a partir del catálogo maestro."
      />

      <div className="mb-5 flex flex-wrap gap-1 border-b border-linea">
        {TABS.map((t) => {
          const on = tab === t.key;
          return (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
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

      {tab === "departamentos" && (
        <ArmadorDepartamentos propId={propId} puedeGestionar={puedeGestionar} />
      )}
      {tab === "organigrama" && (
        <ArmadorOrganigrama propId={propId} puedeGestionar={puedeGestionar} />
      )}
      {tab === "sops" && <ArmadorSops propId={propId} puedeGestionar={puedeGestionar} />}
      {tab === "capacitaciones" && (
        <ArmadorCapacitaciones propId={propId} puedeGestionar={puedeGestionar} />
      )}
      {tab === "sistemas" && <ArmadorSistemas propId={propId} puedeGestionar={puedeGestionar} />}
    </div>
  );
}
