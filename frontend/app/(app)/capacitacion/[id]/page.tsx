"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { Button, Card, CargandoBloque, Chip, EstadoError, Etiqueta, Input, Textarea } from "@/components/ui";
import { TrainingSmartForm } from "@/components/TrainingSmartForm";
import { TrainingSmartView } from "@/components/TrainingSmartView";
import { useToast } from "@/components/toast";
import { ApiError } from "@/lib/api";
import { tieneRol, useAuth } from "@/lib/auth";
import {
  useActualizarManual,
  useActualizarSeccion,
  useCrearSeccion,
  useEliminarManual,
  useEliminarSeccion,
  useManual,
  useReordenarSecciones,
} from "@/lib/hooks";
import type { TrainingSeccion } from "@/lib/types";

function SeccionCard({
  seccion,
  manualId,
  puedeEditar,
  esPrimera,
  esUltima,
  onMover,
}: {
  seccion: TrainingSeccion;
  manualId: string;
  puedeEditar: boolean;
  esPrimera: boolean;
  esUltima: boolean;
  onMover: (dir: -1 | 1) => void;
}) {
  const { notify } = useToast();
  const actualizar = useActualizarSeccion(manualId);
  const eliminar = useEliminarSeccion(manualId);
  const [editando, setEditando] = useState(false);
  const [titulo, setTitulo] = useState(seccion.titulo);
  const [contenido, setContenido] = useState(seccion.contenido ?? "");

  async function guardar() {
    if (!titulo.trim()) return notify("El título es obligatorio.", "error");
    try {
      await actualizar.mutateAsync({ seccionId: seccion.id, titulo: titulo.trim(), contenido });
      notify("Sección guardada.");
      setEditando(false);
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo guardar.", "error");
    }
  }

  async function borrar() {
    if (!window.confirm(`¿Eliminar la sección «${seccion.titulo}»?`)) return;
    try {
      await eliminar.mutateAsync(seccion.id);
      notify("Sección eliminada.");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo eliminar.", "error");
    }
  }

  if (editando) {
    return (
      <Card className="p-5">
        <Etiqueta htmlFor={`t-${seccion.id}`}>Título</Etiqueta>
        <Input id={`t-${seccion.id}`} value={titulo} onChange={(e) => setTitulo(e.target.value)} />
        <div className="mt-3">
          <Etiqueta htmlFor={`c-${seccion.id}`}>Contenido</Etiqueta>
          <Textarea
            id={`c-${seccion.id}`}
            rows={12}
            value={contenido}
            onChange={(e) => setContenido(e.target.value)}
          />
        </div>
        <div className="mt-3 flex gap-2">
          <Button onClick={guardar} disabled={actualizar.isPending}>
            {actualizar.isPending ? "Guardando…" : "Guardar"}
          </Button>
          <Button variant="secondary" onClick={() => setEditando(false)}>
            Cancelar
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-base font-semibold text-petrol-oscuro">{seccion.titulo}</h3>
        {puedeEditar && (
          <div className="flex shrink-0 items-center gap-1">
            <button
              onClick={() => onMover(-1)}
              disabled={esPrimera}
              title="Subir"
              className="rounded px-2 py-1 text-sm text-carbon-suave hover:bg-petrol-tint disabled:opacity-30"
            >
              ↑
            </button>
            <button
              onClick={() => onMover(1)}
              disabled={esUltima}
              title="Bajar"
              className="rounded px-2 py-1 text-sm text-carbon-suave hover:bg-petrol-tint disabled:opacity-30"
            >
              ↓
            </button>
            <Button variant="secondary" onClick={() => setEditando(true)}>
              Editar
            </Button>
            <Button variant="ghost" onClick={borrar} disabled={eliminar.isPending}>
              Eliminar
            </Button>
          </div>
        )}
      </div>
      {seccion.contenido && (
        <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-carbon">
          {seccion.contenido}
        </p>
      )}
    </Card>
  );
}

export default function ManualDetallePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { notify } = useToast();
  const { user } = useAuth();
  const puedeEditar = tieneRol(user, "editor_corporativo", "super_admin");

  const { data: manual, isLoading, isError, error } = useManual(id);
  const crearSeccion = useCrearSeccion(id);
  const reordenar = useReordenarSecciones(id);
  const actualizarManual = useActualizarManual(id);
  const eliminarManual = useEliminarManual();

  const [agregando, setAgregando] = useState(false);
  const [nuevoTitulo, setNuevoTitulo] = useState("");
  const [editandoManual, setEditandoManual] = useState(false);
  const [manualTitulo, setManualTitulo] = useState("");
  const [manualDesc, setManualDesc] = useState("");
  const [editandoSmart, setEditandoSmart] = useState(false);
  const [verBase, setVerBase] = useState(false);

  async function onAgregar(e: React.FormEvent) {
    e.preventDefault();
    if (!nuevoTitulo.trim()) return notify("El título es obligatorio.", "error");
    try {
      await crearSeccion.mutateAsync({ titulo: nuevoTitulo.trim(), contenido: "" });
      notify("Sección agregada.");
      setNuevoTitulo("");
      setAgregando(false);
    } catch (err) {
      notify(err instanceof ApiError ? err.detail : "No se pudo agregar.", "error");
    }
  }

  async function mover(index: number, dir: -1 | 1) {
    if (!manual) return;
    const ids = manual.secciones.map((s) => s.id);
    const destino = index + dir;
    if (destino < 0 || destino >= ids.length) return;
    [ids[index], ids[destino]] = [ids[destino], ids[index]];
    try {
      await reordenar.mutateAsync(ids);
    } catch {
      notify("No se pudo reordenar.", "error");
    }
  }

  async function guardarManual() {
    if (!manualTitulo.trim()) return notify("El título es obligatorio.", "error");
    try {
      await actualizarManual.mutateAsync({ titulo: manualTitulo.trim(), descripcion: manualDesc });
      notify("Manual actualizado.");
      setEditandoManual(false);
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo guardar.", "error");
    }
  }

  async function borrarManual() {
    if (!manual) return;
    if (!window.confirm(`¿Eliminar el manual «${manual.titulo}» y todas sus secciones?`)) return;
    try {
      await eliminarManual.mutateAsync(manual.id);
      notify("Manual eliminado.");
      router.push("/capacitacion");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo eliminar.", "error");
    }
  }

  return (
    <div>
      <Link href="/capacitacion" className="mb-4 inline-block text-sm text-petrol-oscuro hover:underline">
        ← Volver a Capacitación
      </Link>

      {isLoading ? (
        <CargandoBloque />
      ) : isError || !manual ? (
        <EstadoError mensaje={(error as Error)?.message} />
      ) : (
        <>
          <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
            <div>
              {editandoManual ? (
                <div className="space-y-2">
                  <Input value={manualTitulo} onChange={(e) => setManualTitulo(e.target.value)} />
                  <Textarea
                    rows={2}
                    placeholder="Descripción (opcional)"
                    value={manualDesc}
                    onChange={(e) => setManualDesc(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <Button onClick={guardarManual} disabled={actualizarManual.isPending}>
                      Guardar
                    </Button>
                    <Button variant="secondary" onClick={() => setEditandoManual(false)}>
                      Cancelar
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <h1 className="text-xl font-semibold text-petrol-oscuro">{manual.titulo}</h1>
                  <div className="mt-1 flex items-center gap-2">
                    {manual.departamento_codigo && <Chip>Depto. {manual.departamento_codigo}</Chip>}
                    <span className="text-sm text-carbon-suave">
                      {manual.secciones.length} sección{manual.secciones.length === 1 ? "" : "es"}
                    </span>
                  </div>
                  {manual.descripcion && (
                    <p className="mt-2 max-w-2xl text-sm text-carbon-suave">{manual.descripcion}</p>
                  )}
                </>
              )}
            </div>
            {puedeEditar && !editandoManual && !editandoSmart && (
              <div className="flex shrink-0 gap-2">
                <Button onClick={() => setEditandoSmart(true)}>
                  {manual.smart ? "Editar SMART" : "Crear ficha SMART"}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setManualTitulo(manual.titulo);
                    setManualDesc(manual.descripcion ?? "");
                    setEditandoManual(true);
                  }}
                >
                  Editar manual
                </Button>
                <Button variant="ghost" onClick={borrarManual} disabled={eliminarManual.isPending}>
                  Eliminar
                </Button>
              </div>
            )}
          </div>

          {editandoSmart ? (
            <Card className="p-6">
              <TrainingSmartForm manual={manual} onDone={() => setEditandoSmart(false)} />
            </Card>
          ) : manual.smart && !verBase ? (
            <Card className="p-6">
              <div className="mb-4 flex justify-end">
                <button
                  type="button"
                  onClick={() => setVerBase(true)}
                  className="text-xs text-petrol hover:underline"
                >
                  Ver secciones base
                </button>
              </div>
              <TrainingSmartView smart={manual.smart} />
            </Card>
          ) : (
            <>
              {manual.smart && (
                <div className="mb-3 flex justify-end">
                  <button
                    type="button"
                    onClick={() => setVerBase(false)}
                    className="text-xs text-petrol hover:underline"
                  >
                    ← Ver ficha SMART
                  </button>
                </div>
              )}

              <div className="space-y-3">
                {manual.secciones.map((s, i) => (
                  <SeccionCard
                    key={s.id}
                    seccion={s}
                    manualId={manual.id}
                    puedeEditar={puedeEditar}
                    esPrimera={i === 0}
                    esUltima={i === manual.secciones.length - 1}
                    onMover={(dir) => mover(i, dir)}
                  />
                ))}
                {manual.secciones.length === 0 && (
                  <p className="rounded-lg border border-dashed border-linea bg-superficie px-6 py-8 text-center text-sm text-carbon-suave">
                    Este manual todavía no tiene secciones.
                  </p>
                )}
              </div>

              {puedeEditar && (
                <div className="mt-4">
                  {agregando ? (
                    <Card className="p-4">
                      <form onSubmit={onAgregar} className="flex gap-2">
                        <Input
                          placeholder="Título de la nueva sección…"
                          value={nuevoTitulo}
                          onChange={(e) => setNuevoTitulo(e.target.value)}
                          autoFocus
                        />
                        <Button type="submit" disabled={crearSeccion.isPending}>
                          Agregar
                        </Button>
                        <Button type="button" variant="secondary" onClick={() => setAgregando(false)}>
                          Cancelar
                        </Button>
                      </form>
                    </Card>
                  ) : (
                    <Button variant="secondary" onClick={() => setAgregando(true)}>
                      + Agregar sección
                    </Button>
                  )}
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
