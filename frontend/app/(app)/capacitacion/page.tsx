"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import {
  Button,
  Card,
  CargandoBloque,
  Chip,
  EstadoError,
  EstadoVacio,
  Etiqueta,
  Input,
  PageHeader,
  Select,
} from "@/components/ui";
import { useToast } from "@/components/toast";
import { ApiError } from "@/lib/api";
import { tieneRol, useAuth } from "@/lib/auth";
import { useCrearManual, useDepartamentos, useManuales } from "@/lib/hooks";
import type { TrainingManualDetalle } from "@/lib/types";

export default function CapacitacionPage() {
  const router = useRouter();
  const { notify } = useToast();
  const { user } = useAuth();
  const puedeEditar = tieneRol(user, "editor_corporativo", "super_admin");

  const { data: manuales, isLoading, isError, error } = useManuales();
  const { data: departamentos } = useDepartamentos();
  const crear = useCrearManual();

  const [creando, setCreando] = useState(false);
  const [titulo, setTitulo] = useState("");
  const [departamentoId, setDepartamentoId] = useState("");

  const depUnicos = useMemo(() => {
    const m = new Map<string, { id: string; codigo: string; nombre: string }>();
    for (const d of departamentos ?? []) if (!m.has(d.codigo)) m.set(d.codigo, d);
    return [...m.values()];
  }, [departamentos]);
  const nombreDepto = new Map((departamentos ?? []).map((d) => [d.id, `${d.codigo} — ${d.nombre}`]));

  const porDepto = useMemo(() => {
    const grupos = new Map<string, typeof manuales>();
    for (const m of manuales ?? []) {
      const clave = m.departamento_id ?? "sin";
      if (!grupos.has(clave)) grupos.set(clave, []);
      grupos.get(clave)!.push(m);
    }
    return grupos;
  }, [manuales]);

  async function onCrear(e: React.FormEvent) {
    e.preventDefault();
    if (!titulo.trim()) return notify("El título es obligatorio.", "error");
    try {
      const m = (await crear.mutateAsync({
        titulo: titulo.trim(),
        departamento_id: departamentoId || null,
      })) as TrainingManualDetalle;
      notify("Manual creado.");
      router.push(`/capacitacion/${m.id}`);
    } catch (err) {
      notify(err instanceof ApiError ? err.detail : "No se pudo crear.", "error");
    }
  }

  return (
    <div>
      <PageHeader
        titulo="Capacitación"
        descripcion="Manuales de capacitación por departamento, según el organigrama."
        accion={
          puedeEditar ? (
            <Button onClick={() => setCreando((v) => !v)}>
              {creando ? "Cancelar" : "+ Nuevo manual"}
            </Button>
          ) : undefined
        }
      />

      {creando && puedeEditar && (
        <Card className="mb-6 p-6">
          <form onSubmit={onCrear} className="grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
            <div>
              <Etiqueta htmlFor="t">Título del manual *</Etiqueta>
              <Input id="t" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
            </div>
            <div>
              <Etiqueta htmlFor="d">Departamento</Etiqueta>
              <Select id="d" value={departamentoId} onChange={(e) => setDepartamentoId(e.target.value)}>
                <option value="">— sin asignar —</option>
                {depUnicos.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.codigo} — {d.nombre}
                  </option>
                ))}
              </Select>
            </div>
            <Button type="submit" disabled={crear.isPending}>
              {crear.isPending ? "Creando…" : "Crear"}
            </Button>
          </form>
        </Card>
      )}

      {isLoading ? (
        <CargandoBloque />
      ) : isError ? (
        <EstadoError mensaje={(error as Error)?.message} />
      ) : !manuales || manuales.length === 0 ? (
        <EstadoVacio
          titulo="Todavía no hay manuales"
          descripcion={
            puedeEditar
              ? "Creá el primer manual de capacitación con «+ Nuevo manual»."
              : "Aún no se cargaron manuales de capacitación."
          }
        />
      ) : (
        <div className="space-y-6">
          {[...porDepto.entries()].map(([deptoId, lista]) => (
            <div key={deptoId}>
              <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-carbon-suave">
                {deptoId === "sin" ? "Sin departamento" : (nombreDepto.get(deptoId) ?? "Departamento")}
              </h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {lista!.map((m) => (
                  <Link key={m.id} href={`/capacitacion/${m.id}`}>
                    <Card className="h-full p-5 transition-colors hover:border-petrol hover:bg-petrol-tint/30">
                      <p className="font-medium text-petrol-oscuro">{m.titulo}</p>
                      {m.descripcion && (
                        <p className="mt-1 line-clamp-2 text-sm text-carbon-suave">{m.descripcion}</p>
                      )}
                      <div className="mt-3">
                        <Chip>
                          {m.total_secciones} sección{m.total_secciones === 1 ? "" : "es"}
                        </Chip>
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
