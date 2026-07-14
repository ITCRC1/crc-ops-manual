"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { DescriptorForm } from "@/components/DescriptorForm";
import { Card, EstadoVacio, PageHeader } from "@/components/ui";
import { tieneRol, useAuth } from "@/lib/auth";

export default function NuevoDescriptorPage() {
  const router = useRouter();
  const { user } = useAuth();
  const puede = tieneRol(user, "editor_corporativo", "super_admin");

  return (
    <div className="max-w-3xl">
      <Link
        href="/descriptores"
        className="mb-4 inline-block text-sm text-petrol-oscuro hover:underline"
      >
        ← Volver a descriptores
      </Link>
      <PageHeader
        titulo="Nuevo descriptor de puesto"
        descripcion="Se asigna el código automáticamente (JD-###). Arranca en borrador."
      />
      {puede ? (
        <Card className="p-6">
          <DescriptorForm onSaved={(id) => router.push(`/descriptores/${id}`)} />
        </Card>
      ) : (
        <EstadoVacio
          titulo="Sin permisos"
          descripcion="Solo el editor corporativo o el super administrador pueden crear descriptores."
        />
      )}
    </div>
  );
}
