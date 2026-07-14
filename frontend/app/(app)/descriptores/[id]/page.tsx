"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { DescriptorForm } from "@/components/DescriptorForm";
import { DescriptorSmartForm } from "@/components/DescriptorSmartForm";
import { DescriptorSmartView } from "@/components/DescriptorSmartView";
import { EstadoBadge } from "@/components/EstadoBadge";
import { Button, Campo, Card, CargandoBloque, Chip, EstadoError, Vacio } from "@/components/ui";
import { useToast } from "@/components/toast";
import { ApiError } from "@/lib/api";
import { tieneRol, useAuth } from "@/lib/auth";
import { categoriaLabel } from "@/lib/categorias";
import { useDescriptor, useEliminarDescriptor } from "@/lib/hooks";

const EDITABLES = new Set(["borrador", "en_revision", "rechazado"]);

function Lista({ items }: { items: string[] | null }) {
  if (!items || items.length === 0) return <Vacio />;
  return (
    <ul className="list-disc space-y-1 pl-5">
      {items.map((s, i) => (
        <li key={i}>{s}</li>
      ))}
    </ul>
  );
}

function Texto({ valor }: { valor: string | null }) {
  if (!valor) return <Vacio />;
  return <p className="whitespace-pre-line">{valor}</p>;
}

export default function DescriptorDetallePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const { notify } = useToast();
  const { data: d, isLoading, isError, error } = useDescriptor(id);
  const eliminar = useEliminarDescriptor();
  const [editando, setEditando] = useState(false);
  const [editandoSmart, setEditandoSmart] = useState(false);
  const [verBase, setVerBase] = useState(false);

  const puedeGestionar = tieneRol(user, "editor_corporativo", "super_admin");
  const puedeEditar = puedeGestionar && !!d && EDITABLES.has(d.estado);

  async function onEliminar() {
    if (!d) return;
    if (!window.confirm(`¿Eliminar el descriptor ${d.codigo}? Es un borrado lógico.`)) return;
    try {
      await eliminar.mutateAsync(d.id);
      notify(`${d.codigo} eliminado.`);
      router.push("/descriptores");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo eliminar.", "error");
    }
  }

  return (
    <div>
      <Link
        href="/descriptores"
        className="mb-4 inline-block text-sm text-petrol-oscuro hover:underline"
      >
        ← Volver a descriptores
      </Link>

      {isLoading ? (
        <CargandoBloque />
      ) : isError || !d ? (
        <EstadoError mensaje={(error as Error)?.message} />
      ) : (
        <>
          <div className="mb-6 flex flex-wrap items-center gap-3">
            <span className="font-mono text-sm text-carbon-suave">{d.codigo}</span>
            <h1 className="text-xl font-semibold text-petrol-oscuro">{d.titulo}</h1>
            <EstadoBadge estado={d.estado} />
            <Chip>v{d.version_actual}</Chip>
            <Chip>{categoriaLabel(d.categoria, d.nivel_jerarquico)}</Chip>
            {d.departamento_codigo && <Chip>Depto. {d.departamento_codigo}</Chip>}
            {puedeEditar && !editando && !editandoSmart && (
              <div className="ml-auto flex gap-2">
                <Button onClick={() => setEditandoSmart(true)}>
                  {d.smart ? "Editar SMART" : "Crear capa SMART"}
                </Button>
                <Button variant="secondary" onClick={() => setEditando(true)}>
                  Editar formato base
                </Button>
                <Button variant="ghost" onClick={onEliminar} disabled={eliminar.isPending}>
                  Eliminar
                </Button>
              </div>
            )}
          </div>

          {!editando && d.reporta_a_codigo && (
            <p className="mb-6 text-sm text-carbon-suave">
              Reporta a: <span className="font-medium text-carbon">{d.reporta_a_codigo}</span>
              {d.reporta_a_id && (
                <>
                  {" · "}
                  <Link
                    href={`/descriptores/${d.reporta_a_id}`}
                    className="text-petrol-oscuro hover:underline"
                  >
                    ver puesto
                  </Link>
                </>
              )}
            </p>
          )}

          <Card className="p-6">
            {editando ? (
              <DescriptorForm
                descriptor={d}
                onSaved={() => setEditando(false)}
                onCancel={() => setEditando(false)}
              />
            ) : editandoSmart ? (
              <DescriptorSmartForm descriptor={d} onDone={() => setEditandoSmart(false)} />
            ) : d.smart && !verBase ? (
              <>
                <div className="mb-4 flex justify-end">
                  <button
                    type="button"
                    onClick={() => setVerBase(true)}
                    className="text-xs text-petrol hover:underline"
                  >
                    Ver formato base
                  </button>
                </div>
                <DescriptorSmartView smart={d.smart} />
              </>
            ) : (
              <>
                {d.smart && (
                  <div className="mb-4 flex justify-end">
                    <button
                      type="button"
                      onClick={() => setVerBase(false)}
                      className="text-xs text-petrol hover:underline"
                    >
                      ← Ver formato SMART
                    </button>
                  </div>
                )}
                <dl>
                  <Campo etiqueta="Propósito">
                    <Texto valor={d.proposito} />
                  </Campo>
                  <Campo etiqueta="Responsabilidades">
                    <Lista items={d.responsabilidades} />
                  </Campo>
                  <Campo etiqueta="Nivel de autoridad">
                    <Texto valor={d.nivel_autoridad} />
                  </Campo>
                  <Campo etiqueta="Indicadores clave (KPIs)">
                    <Lista items={d.kpis} />
                  </Campo>
                  <Campo etiqueta="Requisitos">
                    <Texto valor={d.requisitos} />
                  </Campo>
                </dl>
              </>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
