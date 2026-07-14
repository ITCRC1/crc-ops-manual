"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { ChipMultiSelect } from "./ChipMultiSelect";
import { Button, Etiqueta, Input, Select, Textarea } from "./ui";
import { useToast } from "./toast";
import { ApiError } from "@/lib/api";
import { useActualizarSop, useDepartamentos, useDescriptores } from "@/lib/hooks";
import type { SopDetalle } from "@/lib/types";

const FRECUENCIAS: [string, string][] = [
  ["", "— sin definir —"],
  ["mensual", "Mensual"],
  ["trimestral", "Trimestral"],
  ["semestral", "Semestral"],
  ["anual", "Anual"],
  ["por_cambio", "Por cambio"],
];

function procedimientoATexto(v: unknown): string {
  if (!v) return "";
  if (typeof v === "string") return v;
  const o = v as Record<string, unknown>;
  const l = o.secciones ?? o.pasos ?? o.contenido;
  return Array.isArray(l) ? l.map(String).join("\n") : "";
}

interface Valores {
  nombre: string;
  departamento_id: string;
  proposito: string;
  evaluacion_riesgos: string;
  controles_existentes: string;
  procedimientoTexto: string;
  responsables: string;
  evidencia: string;
  frecuencia_revision: string;
}

export function SopForm({ sop, onDone }: { sop: SopDetalle; onDone: () => void }) {
  const { data: departamentos } = useDepartamentos();
  const { data: descriptores } = useDescriptores({ limit: 200 });
  const { notify } = useToast();
  const actualizar = useActualizarSop(sop.id);

  const [afectados, setAfectados] = useState<string[]>(
    sop.departamentos_afectados.map((d) => d.id),
  );
  const [responsables, setResponsablesPuestos] = useState<string[]>(
    sop.puestos_responsables.map((p) => p.id),
  );

  const depUnicos = useMemo(() => {
    const m = new Map<string, { id: string; codigo: string; nombre: string }>();
    for (const d of departamentos ?? []) if (!m.has(d.codigo)) m.set(d.codigo, d);
    return [...m.values()];
  }, [departamentos]);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<Valores>({
    defaultValues: {
      nombre: sop.nombre,
      departamento_id: sop.departamento_id ?? "",
      proposito: sop.proposito ?? "",
      evaluacion_riesgos: sop.evaluacion_riesgos ?? "",
      controles_existentes: sop.controles_existentes ?? "",
      procedimientoTexto: procedimientoATexto(sop.procedimiento),
      responsables: sop.responsables ?? "",
      evidencia: sop.evidencia ?? "",
      frecuencia_revision: sop.frecuencia_revision ?? "",
    },
  });

  const dueno = watch("departamento_id");
  const opcionesAfectados = depUnicos
    .filter((d) => d.id !== dueno)
    .map((d) => ({ id: d.id, etiqueta: `${d.codigo} — ${d.nombre}` }));
  const opcionesPuestos = (descriptores?.items ?? []).map((p) => ({
    id: p.id,
    etiqueta: `${p.codigo} — ${p.titulo}`,
  }));

  async function onSubmit(v: Valores) {
    const lineas = v.procedimientoTexto
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
    const body = {
      nombre: v.nombre.trim(),
      departamento_id: v.departamento_id || null,
      proposito: v.proposito.trim() || null,
      evaluacion_riesgos: v.evaluacion_riesgos.trim() || null,
      controles_existentes: v.controles_existentes.trim() || null,
      procedimiento: lineas.length ? { secciones: lineas } : null,
      responsables: v.responsables.trim() || null,
      evidencia: v.evidencia.trim() || null,
      frecuencia_revision: v.frecuencia_revision || null,
      departamentos_afectados_ids: afectados.filter((id) => id !== v.departamento_id),
      puestos_responsables_ids: responsables,
    };
    try {
      await actualizar.mutateAsync(body);
      notify("Cambios guardados.");
      onDone();
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo guardar.", "error");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Etiqueta htmlFor="nombre">Nombre *</Etiqueta>
          <Input id="nombre" {...register("nombre", { required: true })} />
          {errors.nombre && <p className="mt-1 text-xs text-rechazado">El nombre es obligatorio.</p>}
        </div>
        <div>
          <Etiqueta htmlFor="departamento_id">Departamento dueño</Etiqueta>
          <Select id="departamento_id" {...register("departamento_id")}>
            <option value="">— sin asignar —</option>
            {depUnicos.map((d) => (
              <option key={d.id} value={d.id}>
                {d.codigo} — {d.nombre}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div>
        <Etiqueta>Departamentos que también afecta</Etiqueta>
        <ChipMultiSelect
          opciones={opcionesAfectados}
          seleccionados={afectados}
          onChange={setAfectados}
          vacio="No hay otros departamentos cargados."
        />
      </div>

      <div>
        <Etiqueta htmlFor="proposito">Propósito</Etiqueta>
        <Textarea id="proposito" rows={3} {...register("proposito")} />
      </div>
      <div>
        <Etiqueta htmlFor="evaluacion_riesgos">Evaluación de riesgos</Etiqueta>
        <Textarea id="evaluacion_riesgos" rows={3} {...register("evaluacion_riesgos")} />
      </div>
      <div>
        <Etiqueta htmlFor="controles_existentes">Controles existentes</Etiqueta>
        <Textarea id="controles_existentes" rows={3} {...register("controles_existentes")} />
      </div>
      <div>
        <Etiqueta htmlFor="procedimientoTexto">Procedimiento (una línea por paso/sección)</Etiqueta>
        <Textarea id="procedimientoTexto" rows={6} {...register("procedimientoTexto")} />
      </div>
      <div>
        <Etiqueta htmlFor="responsables">Responsables (descripción)</Etiqueta>
        <Textarea id="responsables" rows={2} {...register("responsables")} />
      </div>
      <div>
        <Etiqueta>Puestos responsables directos</Etiqueta>
        <ChipMultiSelect
          opciones={opcionesPuestos}
          seleccionados={responsables}
          onChange={setResponsablesPuestos}
          vacio="No hay descriptores de puesto cargados."
        />
      </div>
      <div>
        <Etiqueta htmlFor="evidencia">Evidencia / reportes</Etiqueta>
        <Textarea id="evidencia" rows={2} {...register("evidencia")} />
      </div>
      <div className="sm:w-64">
        <Etiqueta htmlFor="frecuencia_revision">Frecuencia de revisión</Etiqueta>
        <Select id="frecuencia_revision" {...register("frecuencia_revision")}>
          {FRECUENCIAS.map(([v, l]) => (
            <option key={v} value={v}>
              {l}
            </option>
          ))}
        </Select>
      </div>

      <div className="flex gap-2 border-t border-linea pt-4">
        <Button type="submit" disabled={actualizar.isPending}>
          {actualizar.isPending ? "Guardando…" : "Guardar cambios"}
        </Button>
        <Button type="button" variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
      </div>
    </form>
  );
}
