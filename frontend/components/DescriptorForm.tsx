"use client";

import { useMemo, useState } from "react";

import { DescriptorSelect } from "./DescriptorSelect";
import { Button, Etiqueta, Input, Select, Textarea } from "./ui";
import { useToast } from "./toast";
import { ApiError } from "@/lib/api";
import { CATEGORIA_LABEL, CATEGORIA_ORDEN } from "@/lib/categorias";
import { useActualizarDescriptor, useCrearDescriptor, useDepartamentos } from "@/lib/hooks";
import type { DescriptorDetalle } from "@/lib/types";

const NIVELES: [number, string][] = [
  [1, "1 · Alta dirección"],
  [2, "2 · Dirección funcional"],
  [3, "3 · Jefatura / gerencia"],
  [4, "4 · Operativo"],
];

function lineas(texto: string): string[] {
  return texto
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
}

export function DescriptorForm({
  descriptor,
  onSaved,
  onCancel,
}: {
  descriptor?: DescriptorDetalle;
  onSaved: (id: string) => void;
  onCancel?: () => void;
}) {
  const esNuevo = !descriptor;
  const { notify } = useToast();
  const { data: departamentos } = useDepartamentos();
  const crear = useCrearDescriptor();
  const actualizar = useActualizarDescriptor(descriptor?.id ?? "");

  const [titulo, setTitulo] = useState(descriptor?.titulo ?? "");
  const [nivel, setNivel] = useState(descriptor?.nivel_jerarquico ?? 4);
  const [categoria, setCategoria] = useState(descriptor?.categoria ?? "");
  const [departamento, setDepartamento] = useState(descriptor?.departamento_id ?? "");
  const [reportaA, setReportaA] = useState(descriptor?.reporta_a_id ?? "");
  const [proposito, setProposito] = useState(descriptor?.proposito ?? "");
  const [respons, setRespons] = useState((descriptor?.responsabilidades ?? []).join("\n"));
  const [autoridad, setAutoridad] = useState(descriptor?.nivel_autoridad ?? "");
  const [kpis, setKpis] = useState((descriptor?.kpis ?? []).join("\n"));
  const [requisitos, setRequisitos] = useState(descriptor?.requisitos ?? "");

  const depUnicos = useMemo(() => {
    const m = new Map<string, { id: string; codigo: string; nombre: string }>();
    for (const d of departamentos ?? []) if (!m.has(d.codigo)) m.set(d.codigo, d);
    return [...m.values()];
  }, [departamentos]);

  const pendiente = crear.isPending || actualizar.isPending;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!titulo.trim()) return notify("El título es obligatorio.", "error");
    const body = {
      titulo: titulo.trim(),
      nivel_jerarquico: Number(nivel),
      categoria: categoria || null,
      departamento_id: departamento || null,
      reporta_a_id: reportaA || null,
      proposito: proposito.trim() || null,
      responsabilidades: lineas(respons).length ? lineas(respons) : null,
      nivel_autoridad: autoridad.trim() || null,
      kpis: lineas(kpis).length ? lineas(kpis) : null,
      requisitos: requisitos.trim() || null,
    };
    try {
      if (esNuevo) {
        const d = await crear.mutateAsync(body);
        notify(`Creado ${d.codigo}.`);
        onSaved(d.id);
      } else {
        await actualizar.mutateAsync(body);
        notify("Cambios guardados.");
        onSaved(descriptor!.id);
      }
    } catch (err) {
      notify(err instanceof ApiError ? err.detail : "No se pudo guardar.", "error");
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Etiqueta htmlFor="titulo">Título *</Etiqueta>
          <Input id="titulo" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
        </div>
        <div>
          <Etiqueta htmlFor="nivel">Nivel jerárquico</Etiqueta>
          <Select id="nivel" value={nivel} onChange={(e) => setNivel(Number(e.target.value))}>
            {NIVELES.map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Etiqueta htmlFor="categoria">Categoría</Etiqueta>
          <Select id="categoria" value={categoria} onChange={(e) => setCategoria(e.target.value)}>
            <option value="">— automática por nivel/título —</option>
            {CATEGORIA_ORDEN.map((c) => (
              <option key={c} value={c}>
                {CATEGORIA_LABEL[c]}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Etiqueta htmlFor="depto">Departamento</Etiqueta>
          <Select id="depto" value={departamento} onChange={(e) => setDepartamento(e.target.value)}>
            <option value="">— sin asignar —</option>
            {depUnicos.map((d) => (
              <option key={d.id} value={d.id}>
                {d.codigo} — {d.nombre}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Etiqueta>Reporta a</Etiqueta>
          <DescriptorSelect value={reportaA} onChange={setReportaA} excludeId={descriptor?.id} />
        </div>
      </div>

      <div>
        <Etiqueta htmlFor="proposito">Propósito</Etiqueta>
        <Textarea id="proposito" rows={3} value={proposito} onChange={(e) => setProposito(e.target.value)} />
      </div>
      <div>
        <Etiqueta htmlFor="respons">Responsabilidades (una por línea)</Etiqueta>
        <Textarea id="respons" rows={5} value={respons} onChange={(e) => setRespons(e.target.value)} />
      </div>
      <div>
        <Etiqueta htmlFor="autoridad">Nivel de autoridad</Etiqueta>
        <Textarea id="autoridad" rows={2} value={autoridad} onChange={(e) => setAutoridad(e.target.value)} />
      </div>
      <div>
        <Etiqueta htmlFor="kpis">KPIs (uno por línea)</Etiqueta>
        <Textarea id="kpis" rows={4} value={kpis} onChange={(e) => setKpis(e.target.value)} />
      </div>
      <div>
        <Etiqueta htmlFor="requisitos">Requisitos</Etiqueta>
        <Textarea id="requisitos" rows={3} value={requisitos} onChange={(e) => setRequisitos(e.target.value)} />
      </div>

      <div className="flex gap-2 border-t border-linea pt-4">
        <Button type="submit" disabled={pendiente}>
          {pendiente ? "Guardando…" : esNuevo ? "Crear descriptor" : "Guardar cambios"}
        </Button>
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancelar
          </Button>
        )}
      </div>
    </form>
  );
}
