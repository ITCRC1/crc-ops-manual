"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { ChipMultiSelect } from "@/components/ChipMultiSelect";
import { Button, Card, Etiqueta, EstadoVacio, Input, PageHeader, Select } from "@/components/ui";
import { useToast } from "@/components/toast";
import { ApiError } from "@/lib/api";
import { tieneRol, useAuth } from "@/lib/auth";
import { useAreas, useCrearSop, useDepartamentos, useDescriptores, useSistemas } from "@/lib/hooks";
import type { SopDetalle } from "@/lib/types";

export default function NuevoSopPage() {
  const router = useRouter();
  const { notify } = useToast();
  const { user } = useAuth();
  const { data: areas } = useAreas();
  const { data: sistemas } = useSistemas();
  const { data: departamentos } = useDepartamentos();
  const { data: descriptores } = useDescriptores({ limit: 200 });
  const crear = useCrearSop();

  const [area, setArea] = useState("");
  const [tipo, setTipo] = useState("sop");
  const [nombre, setNombre] = useState("");
  const [sels, setSels] = useState<Set<string>>(new Set());
  const [dueno, setDueno] = useState("");
  const [afectados, setAfectados] = useState<string[]>([]);
  const [responsables, setResponsables] = useState<string[]>([]);

  const puede = tieneRol(user, "editor_corporativo", "super_admin");

  const depUnicos = useMemo(() => {
    const m = new Map<string, { id: string; codigo: string; nombre: string }>();
    for (const d of departamentos ?? []) if (!m.has(d.codigo)) m.set(d.codigo, d);
    return [...m.values()];
  }, [departamentos]);
  const opcionesAfectados = depUnicos
    .filter((d) => d.id !== dueno)
    .map((d) => ({ id: d.id, etiqueta: `${d.codigo} — ${d.nombre}` }));
  const opcionesPuestos = (descriptores?.items ?? []).map((p) => ({
    id: p.id,
    etiqueta: `${p.codigo} — ${p.titulo}`,
  }));

  if (!puede) {
    return (
      <div>
        <PageHeader titulo="Nuevo documento" />
        <EstadoVacio
          titulo="Sin permisos"
          descripcion="Solo el editor corporativo o el super administrador pueden crear documentos."
        />
      </div>
    );
  }

  function toggle(cod: string) {
    setSels((prev) => {
      const n = new Set(prev);
      if (n.has(cod)) n.delete(cod);
      else n.add(cod);
      return n;
    });
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!area || !nombre.trim()) return notify("Área y nombre son obligatorios.", "error");
    try {
      const sop = (await crear.mutateAsync({
        area_codigo: area,
        tipo,
        nombre: nombre.trim(),
        sistemas_codigos: [...sels],
        departamento_id: dueno || null,
        departamentos_afectados_ids: afectados.filter((id) => id !== dueno),
        puestos_responsables_ids: responsables,
      })) as SopDetalle;
      notify(`Creado ${sop.codigo}. Completá la capa SMART.`);
      // Política: todo SOP queda en formato SMART → abrimos el editor SMART al crear.
      router.push(`/biblioteca/${sop.id}?smart=nuevo`);
    } catch (err) {
      notify(err instanceof ApiError ? err.detail : "No se pudo crear.", "error");
    }
  }

  return (
    <div className="max-w-2xl">
      <Link href="/biblioteca" className="mb-4 inline-block text-sm text-petrol-oscuro hover:underline">
        ← Volver a la librería
      </Link>
      <PageHeader
        titulo="Nuevo documento SMART"
        descripcion="Se asigna el código automáticamente por área. Todo SOP se crea en formato SMART: al guardar, se abre el editor SMART para completar el contenido."
      />
      <Card className="p-6">
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Etiqueta htmlFor="area">Área *</Etiqueta>
              <Select id="area" value={area} onChange={(e) => setArea(e.target.value)}>
                <option value="">Elegí un área…</option>
                {areas?.map((a) => (
                  <option key={a.id} value={a.codigo}>
                    {a.codigo} — {a.nombre}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Etiqueta htmlFor="tipo">Tipo</Etiqueta>
              <Select id="tipo" value={tipo} onChange={(e) => setTipo(e.target.value)}>
                <option value="sop">SOP</option>
                <option value="politica">Política</option>
              </Select>
            </div>
          </div>
          <div>
            <Etiqueta htmlFor="nombre">Nombre *</Etiqueta>
            <Input id="nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Etiqueta htmlFor="dueno">Departamento dueño (opcional)</Etiqueta>
              <Select id="dueno" value={dueno} onChange={(e) => setDueno(e.target.value)}>
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
            <Etiqueta>Puestos responsables directos (opcional)</Etiqueta>
            <ChipMultiSelect
              opciones={opcionesPuestos}
              seleccionados={responsables}
              onChange={setResponsables}
              vacio="No hay descriptores de puesto cargados."
            />
          </div>

          <div>
            <Etiqueta>Sistemas que asume (opcional)</Etiqueta>
            <div className="flex flex-wrap gap-2">
              {sistemas?.map((s) => (
                <button
                  type="button"
                  key={s.id}
                  onClick={() => toggle(s.codigo)}
                  className={`rounded-full border px-3 py-1 text-xs ${
                    sels.has(s.codigo)
                      ? "border-petrol bg-petrol text-white"
                      : "border-linea bg-superficie text-carbon-suave hover:bg-petrol-tint"
                  }`}
                >
                  {s.codigo}
                </button>
              ))}
            </div>
          </div>
          <div className="border-t border-linea pt-4">
            <Button type="submit" disabled={crear.isPending}>
              {crear.isPending ? "Creando…" : "Crear documento"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
