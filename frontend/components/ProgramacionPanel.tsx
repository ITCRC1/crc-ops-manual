"use client";

import { useState } from "react";

import { ApiError } from "@/lib/api";
import {
  useActualizarProgramacion,
  useCrearProgramacion,
  useEliminarProgramacion,
  useProgramacion,
} from "@/lib/hooks";
import type { ProgramacionSop, TipoRecurrencia } from "@/lib/types";

import { DescriptorSelect } from "./DescriptorSelect";
import { useToast } from "./toast";
import { Button, Card, Chip, Etiqueta, Input, Select, Textarea, Vacio } from "./ui";

const TIPO_LABEL: Record<TipoRecurrencia, string> = {
  unica: "Una sola vez",
  diaria: "Diaria",
  semanal: "Semanal",
  quincenal: "Quincenal",
  mensual: "Mensual",
  trimestral: "Trimestral",
  anual: "Anual",
};
const ORDEN_TIPOS: TipoRecurrencia[] = [
  "unica", "diaria", "semanal", "quincenal", "mensual", "trimestral", "anual",
];

function fechaCorta(f: string): string {
  const [y, m, d] = f.split("-");
  return `${d}/${m}/${y}`;
}

export function describirRecurrencia(p: ProgramacionSop): string {
  const inicio = fechaCorta(p.fecha);
  let base: string;
  switch (p.tipo_recurrencia) {
    case "unica":
      base = inicio;
      break;
    case "diaria":
    case "semanal":
    case "quincenal":
    case "mensual":
    case "trimestral":
    case "anual":
      base = `${TIPO_LABEL[p.tipo_recurrencia]} · desde ${inicio}`;
      break;
    default:
      base = inicio;
  }
  if (p.hora) base += ` · ${p.hora.slice(0, 5)}`;
  if (p.fecha_fin) base += ` · hasta ${fechaCorta(p.fecha_fin)}`;
  return base;
}

interface FormState {
  titulo: string;
  descripcion: string;
  tipo_recurrencia: TipoRecurrencia;
  fecha: string;
  hora: string;
  fecha_fin: string;
  responsable_texto: string;
  responsable_puesto_id: string;
}

function estadoInicial(p?: ProgramacionSop): FormState {
  return {
    titulo: p?.titulo ?? "",
    descripcion: p?.descripcion ?? "",
    tipo_recurrencia: p?.tipo_recurrencia ?? "unica",
    fecha: p?.fecha ?? "",
    hora: p?.hora ? p.hora.slice(0, 5) : "",
    fecha_fin: p?.fecha_fin ?? "",
    responsable_texto: p?.responsable_texto ?? "",
    responsable_puesto_id: p?.responsable_puesto_id ?? "",
  };
}

function aBody(f: FormState): Record<string, unknown> {
  const recurrente = f.tipo_recurrencia !== "unica";
  return {
    titulo: f.titulo.trim(),
    descripcion: f.descripcion.trim() || null,
    tipo_recurrencia: f.tipo_recurrencia,
    fecha: f.fecha,
    hora: f.hora ? `${f.hora}:00` : null,
    fecha_fin: recurrente && f.fecha_fin ? f.fecha_fin : null,
    responsable_texto: f.responsable_texto.trim() || null,
    responsable_puesto_id: f.responsable_puesto_id || null,
  };
}

function ProgramacionForm({
  sopId,
  inicial,
  onDone,
  onCancel,
}: {
  sopId: string;
  inicial?: ProgramacionSop;
  onDone: () => void;
  onCancel: () => void;
}) {
  const { notify } = useToast();
  const [f, setF] = useState<FormState>(() => estadoInicial(inicial));
  const crear = useCrearProgramacion(sopId);
  const actualizar = useActualizarProgramacion(sopId);
  const guardando = crear.isPending || actualizar.isPending;

  const set = <K extends keyof FormState>(k: K, v: FormState[K]) => setF((s) => ({ ...s, [k]: v }));

  async function guardar() {
    if (!f.titulo.trim()) {
      notify("El nombre de la actividad es obligatorio.", "error");
      return;
    }
    if (!f.fecha) {
      notify("La fecha de ejecución es obligatoria.", "error");
      return;
    }
    try {
      const body = aBody(f);
      if (inicial) await actualizar.mutateAsync({ progId: inicial.id, body });
      else await crear.mutateAsync(body);
      notify(inicial ? "Actividad actualizada." : "Actividad agregada.");
      onDone();
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo guardar.", "error");
    }
  }

  const recurrente = f.tipo_recurrencia !== "unica";
  return (
    <div className="space-y-3 rounded-md border border-linea bg-fondo p-4">
      <div>
        <Etiqueta>Nombre de la actividad</Etiqueta>
        <Input
          value={f.titulo}
          onChange={(e) => set("titulo", e.target.value)}
          placeholder="Ej. Pago a proveedores"
        />
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <div>
          <Etiqueta>Fecha de ejecución</Etiqueta>
          <Input type="date" value={f.fecha} onChange={(e) => set("fecha", e.target.value)} />
        </div>
        <div>
          <Etiqueta>Frecuencia</Etiqueta>
          <Select
            value={f.tipo_recurrencia}
            onChange={(e) => set("tipo_recurrencia", e.target.value as TipoRecurrencia)}
          >
            {ORDEN_TIPOS.map((k) => (
              <option key={k} value={k}>
                {TIPO_LABEL[k]}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Etiqueta>Hora (opcional)</Etiqueta>
          <Input type="time" value={f.hora} onChange={(e) => set("hora", e.target.value)} />
        </div>
      </div>

      {recurrente && (
        <div className="sm:w-1/3">
          <Etiqueta>Repetir hasta (opcional)</Etiqueta>
          <Input type="date" value={f.fecha_fin} onChange={(e) => set("fecha_fin", e.target.value)} />
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <Etiqueta>Responsable (texto)</Etiqueta>
          <Input
            value={f.responsable_texto}
            onChange={(e) => set("responsable_texto", e.target.value)}
            placeholder="Ej. Departamento de Finanzas"
          />
        </div>
        <div>
          <Etiqueta>Puesto responsable (opcional)</Etiqueta>
          <DescriptorSelect
            value={f.responsable_puesto_id}
            onChange={(id) => set("responsable_puesto_id", id)}
            placeholder="— sin puesto vinculado —"
          />
        </div>
      </div>
      <div>
        <Etiqueta>Descripción (opcional)</Etiqueta>
        <Textarea
          rows={2}
          value={f.descripcion}
          onChange={(e) => set("descripcion", e.target.value)}
        />
      </div>

      <div className="flex gap-2">
        <Button onClick={guardar} disabled={guardando}>
          {inicial ? "Guardar cambios" : "Agregar actividad"}
        </Button>
        <Button variant="ghost" onClick={onCancel} disabled={guardando}>
          Cancelar
        </Button>
      </div>
    </div>
  );
}

export function ProgramacionPanel({
  sopId,
  puedeGestionar,
}: {
  sopId: string;
  puedeGestionar: boolean;
}) {
  const { notify } = useToast();
  const { data: progs, isLoading } = useProgramacion(sopId);
  const eliminar = useEliminarProgramacion(sopId);
  const [creando, setCreando] = useState(false);
  const [editando, setEditando] = useState<string | null>(null);

  async function borrar(p: ProgramacionSop) {
    if (!confirm(`¿Eliminar la actividad "${p.titulo}"?`)) return;
    try {
      await eliminar.mutateAsync(p.id);
      notify("Actividad eliminada.");
    } catch {
      notify("No se pudo eliminar.", "error");
    }
  }

  return (
    <Card className="p-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-carbon-suave">
            Programación
          </h2>
          <p className="mt-0.5 text-xs text-carbon-suave">
            Actividades de este SOP con su fecha de ejecución y frecuencia. Aparecen en el{" "}
            <a href="/calendario" className="text-petrol-oscuro hover:underline">
              calendario general
            </a>
            .
          </p>
        </div>
        {puedeGestionar && !creando && (
          <Button variant="secondary" onClick={() => setCreando(true)}>
            + Agregar
          </Button>
        )}
      </div>

      {creando && (
        <div className="mb-4">
          <ProgramacionForm
            sopId={sopId}
            onDone={() => setCreando(false)}
            onCancel={() => setCreando(false)}
          />
        </div>
      )}

      {isLoading ? (
        <p className="text-sm text-carbon-suave">Cargando…</p>
      ) : !progs || progs.length === 0 ? (
        <Vacio>Sin actividades programadas.</Vacio>
      ) : (
        <ul className="space-y-3">
          {progs.map((p) =>
            editando === p.id ? (
              <li key={p.id}>
                <ProgramacionForm
                  sopId={sopId}
                  inicial={p}
                  onDone={() => setEditando(null)}
                  onCancel={() => setEditando(null)}
                />
              </li>
            ) : (
              <li
                key={p.id}
                className="flex items-start justify-between gap-3 rounded-md border border-linea p-3"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-carbon">{p.titulo}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <Chip>{describirRecurrencia(p)}</Chip>
                    {(p.responsable_puesto_titulo || p.responsable_texto) && (
                      <span className="text-xs text-carbon-suave">
                        {p.responsable_puesto_titulo ?? p.responsable_texto}
                      </span>
                    )}
                    {!p.activo && <Chip className="bg-fondo">inactiva</Chip>}
                  </div>
                  {p.descripcion && (
                    <p className="mt-1 text-xs text-carbon-suave">{p.descripcion}</p>
                  )}
                </div>
                {puedeGestionar && (
                  <div className="flex shrink-0 gap-1">
                    <Button variant="ghost" onClick={() => setEditando(p.id)}>
                      Editar
                    </Button>
                    <Button variant="ghost" onClick={() => borrar(p)}>
                      Eliminar
                    </Button>
                  </div>
                )}
              </li>
            ),
          )}
        </ul>
      )}
    </Card>
  );
}
