"use client";

import { useMemo, useState } from "react";

import { useToast } from "@/components/toast";
import {
  Button,
  CargandoBloque,
  Card,
  EstadoVacio,
  Etiqueta,
  Input,
  Select,
  Textarea,
} from "@/components/ui";
import { EstadoBadge } from "@/components/EstadoBadge";
import { DescriptorSmartForm } from "@/components/DescriptorSmartForm";
import { categoriaLabel } from "@/lib/categorias";
import { ApiError } from "@/lib/api";
import {
  useActualizarPuesto,
  useActualizarSmartOverridesPuesto,
  useCrearPuesto,
  useEliminarPuesto,
  usePropiedadDepartamentos,
  usePropiedadPuesto,
  usePropiedadPuestos,
  useSembrarDesdeMaestro,
} from "@/lib/hooks";
import type { JdSmart, PuestoArmador, PuestoArmadorDetalle } from "@/lib/types";

import { PuestoTitulares } from "./PuestoTitulares";

// SMART efectiva → deltas por sección contra el master (top-level keys que difieren).
function diffJdSmartPorSeccion(
  local: Record<string, unknown>,
  master: Record<string, unknown>,
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const k of Object.keys(local)) {
    if (k === "formato") continue;
    if (JSON.stringify(local[k]) !== JSON.stringify(master[k] ?? null)) out[k] = local[k];
  }
  return out;
}

interface NodoP extends PuestoArmador {
  hijos: NodoP[];
}

function construirArbol(puestos: PuestoArmador[]): NodoP[] {
  const porId = new Map<string, NodoP>(puestos.map((p) => [p.id, { ...p, hijos: [] }]));

  // Padre efectivo: solo si existe en el conjunto y no es uno mismo.
  const padre = new Map<string, string | null>();
  for (const [id, n] of porId) {
    const pid = n.reporta_a_id;
    padre.set(id, pid && porId.has(pid) && pid !== id ? pid : null);
  }
  // Cortar ciclos: subiendo por la cadena, si se revisita un nodo se corta ahí (queda raíz).
  for (const id of padre.keys()) {
    const visto = new Set<string>();
    let cur: string | null = id;
    while (cur !== null) {
      if (visto.has(cur)) {
        padre.set(cur, null);
        break;
      }
      visto.add(cur);
      cur = padre.get(cur) ?? null;
    }
  }

  const raices: NodoP[] = [];
  for (const [id, nodo] of porId) {
    const pid = padre.get(id);
    if (pid) porId.get(pid)!.hijos.push(nodo);
    else raices.push(nodo);
  }
  const ordenar = (lst: NodoP[]) => {
    lst.sort(
      (a, b) => a.nivel_jerarquico - b.nivel_jerarquico || (a.codigo ?? "").localeCompare(b.codigo ?? ""),
    );
    lst.forEach((n) => ordenar(n.hijos));
  };
  ordenar(raices);
  return raices;
}

const MODO_LABEL: Record<string, string> = {
  adoptado: "Adoptado",
  adaptado: "Adaptado",
  local: "Local",
  no_aplica: "No aplica",
};

function Nodo({
  nodo,
  seleccion,
  onSelect,
}: {
  nodo: NodoP;
  seleccion: string | null;
  onSelect: (id: string) => void;
}) {
  const activo = seleccion === nodo.id;
  return (
    <li>
      <button
        type="button"
        onClick={() => onSelect(nodo.id)}
        className={`flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left transition-colors ${
          activo
            ? "border-petrol bg-petrol-tint"
            : "border-linea bg-superficie hover:bg-petrol-tint/40"
        }`}
      >
        {nodo.codigo && (
          <span className="inline-flex h-6 min-w-[3.5rem] items-center justify-center rounded bg-petrol-tint px-1.5 text-xs font-medium text-petrol-oscuro">
            {nodo.codigo}
          </span>
        )}
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-medium text-carbon">{nodo.titulo}</span>
          <span className="block text-xs text-carbon-suave">
            {categoriaLabel(nodo.categoria, nodo.nivel_jerarquico)}
            {nodo.departamento_codigo ? ` · ${nodo.departamento_codigo}` : ""}
            {nodo.dotacion ? ` · ${nodo.dotacion} plaza${nodo.dotacion === 1 ? "" : "s"}` : ""}
          </span>
        </span>
        <span className="shrink-0 text-xs text-carbon-suave">
          {MODO_LABEL[nodo.modo]}
          {nodo.ocupantes_count > 0 && ` · ${nodo.ocupantes_count} titular${nodo.ocupantes_count === 1 ? "" : "es"}`}
        </span>
      </button>
      {nodo.hijos.length > 0 && (
        <ul className="ml-6 mt-2 space-y-2 border-l border-linea pl-4">
          {nodo.hijos.map((h) => (
            <Nodo key={h.id} nodo={h} seleccion={seleccion} onSelect={onSelect} />
          ))}
        </ul>
      )}
    </li>
  );
}

export function ArmadorOrganigrama({
  propId,
  puedeGestionar,
}: {
  propId: string;
  puedeGestionar: boolean;
}) {
  const { notify } = useToast();
  const { data: puestos, isLoading } = usePropiedadPuestos(propId);
  const { data: departamentos } = usePropiedadDepartamentos(propId);
  const sembrar = useSembrarDesdeMaestro(propId);

  const [seleccion, setSeleccion] = useState<string | null>(null);
  const [creando, setCreando] = useState(false);
  const [incluirCupula, setIncluirCupula] = useState(false);

  const arbol = useMemo(() => construirArbol(puestos ?? []), [puestos]);

  async function onSembrar() {
    if (!departamentos || departamentos.length === 0) {
      notify("Primero asigná departamentos a la propiedad.", "error");
      return;
    }
    if (!window.confirm("¿Adoptar el organigrama maestro de los departamentos asignados?")) return;
    try {
      const r = await sembrar.mutateAsync({
        departamento_ids: null,
        incluir_sin_departamento: incluirCupula,
      });
      notify(`Sembrado: ${r.creados} puesto(s) nuevo(s), ${r.omitidos} ya existían.`);
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo sembrar.", "error");
    }
  }

  if (isLoading) return <CargandoBloque />;

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr,26rem]">
      <div>
        {puedeGestionar && (
          <div className="mb-3 flex flex-wrap items-center gap-3">
            <Button
              variant="secondary"
              onClick={onSembrar}
              disabled={sembrar.isPending}
            >
              {sembrar.isPending ? "Sembrando…" : "Sembrar desde maestro"}
            </Button>
            <label className="flex items-center gap-1.5 text-xs text-carbon-suave">
              <input
                type="checkbox"
                checked={incluirCupula}
                onChange={(e) => setIncluirCupula(e.target.checked)}
              />
              incluir cúpula (puestos sin departamento)
            </label>
            <Button
              onClick={() => {
                setCreando(true);
                setSeleccion(null);
              }}
            >
              + Puesto
            </Button>
          </div>
        )}

        {arbol.length === 0 ? (
          <EstadoVacio
            titulo="Sin puestos todavía"
            descripcion="Sembrá desde el maestro o agregá un puesto para armar el organigrama."
          />
        ) : (
          <ul className="space-y-2">
            {arbol.map((n) => (
              <Nodo key={n.id} nodo={n} seleccion={seleccion} onSelect={(id) => {
                setSeleccion(id);
                setCreando(false);
              }} />
            ))}
          </ul>
        )}
      </div>

      <div>
        {creando ? (
          <PuestoNuevoForm
            propId={propId}
            puestos={puestos ?? []}
            onHecho={(id) => {
              setCreando(false);
              setSeleccion(id);
            }}
            onCancel={() => setCreando(false)}
          />
        ) : seleccion ? (
          <PuestoPanel
            key={seleccion}
            propId={propId}
            ppId={seleccion}
            puestos={puestos ?? []}
            puedeGestionar={puedeGestionar}
            onEliminado={() => setSeleccion(null)}
          />
        ) : (
          <Card className="p-6 text-sm text-carbon-suave">
            Seleccioná un puesto del organigrama para ver su detalle, editar la jerarquía o
            asignar titulares.
          </Card>
        )}
      </div>
    </div>
  );
}

function opcionesJefe(puestos: PuestoArmador[], excluir?: string) {
  return puestos.filter((p) => p.id !== excluir);
}

function PuestoNuevoForm({
  propId,
  puestos,
  onHecho,
  onCancel,
}: {
  propId: string;
  puestos: PuestoArmador[];
  onHecho: (id: string) => void;
  onCancel: () => void;
}) {
  const { notify } = useToast();
  const crear = useCrearPuesto(propId);
  const [titulo, setTitulo] = useState("");
  const [nivel, setNivel] = useState(4);
  const [proposito, setProposito] = useState("");
  const [reportaA, setReportaA] = useState("");
  const [dotacion, setDotacion] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!titulo.trim()) {
      notify("El título es obligatorio.", "error");
      return;
    }
    try {
      const nuevo = await crear.mutateAsync({
        modo: "local",
        overrides: {
          titulo: titulo.trim(),
          nivel_jerarquico: Number(nivel),
          ...(proposito.trim() ? { proposito: proposito.trim() } : {}),
        },
        reporta_a_id: reportaA || null,
        dotacion: dotacion ? Number(dotacion) : null,
      });
      notify("Puesto local creado.");
      onHecho(nuevo.id);
    } catch (err) {
      notify(err instanceof ApiError ? err.detail : "No se pudo crear.", "error");
    }
  }

  return (
    <Card className="p-5">
      <h3 className="mb-1 text-sm font-semibold text-petrol-oscuro">Nuevo puesto local</h3>
      <p className="mb-4 text-xs text-carbon-suave">
        Para puestos del catálogo maestro usá “Sembrar desde maestro”. Acá creás un puesto propio
        de la propiedad.
      </p>
      <form onSubmit={onSubmit} className="space-y-3">
        <div>
          <Etiqueta htmlFor="np-titulo">Título *</Etiqueta>
          <Input id="np-titulo" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Etiqueta htmlFor="np-nivel">Nivel jerárquico</Etiqueta>
            <Select id="np-nivel" value={nivel} onChange={(e) => setNivel(Number(e.target.value))}>
              <option value={1}>1 — Dirección</option>
              <option value={2}>2 — Dirección funcional</option>
              <option value={3}>3 — Jefatura/Gerencia</option>
              <option value={4}>4 — Línea</option>
            </Select>
          </div>
          <div>
            <Etiqueta htmlFor="np-dotacion">Dotación (plazas)</Etiqueta>
            <Input
              id="np-dotacion"
              type="number"
              min={0}
              value={dotacion}
              onChange={(e) => setDotacion(e.target.value)}
            />
          </div>
        </div>
        <div>
          <Etiqueta htmlFor="np-jefe">Reporta a</Etiqueta>
          <Select id="np-jefe" value={reportaA} onChange={(e) => setReportaA(e.target.value)}>
            <option value="">— Sin superior (raíz) —</option>
            {opcionesJefe(puestos).map((p) => (
              <option key={p.id} value={p.id}>
                {p.titulo}
                {p.codigo ? ` (${p.codigo})` : ""}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Etiqueta htmlFor="np-prop">Propósito</Etiqueta>
          <Textarea id="np-prop" rows={3} value={proposito} onChange={(e) => setProposito(e.target.value)} />
        </div>
        <div className="flex gap-2 border-t border-linea pt-3">
          <Button type="submit" disabled={crear.isPending}>
            {crear.isPending ? "Creando…" : "Crear puesto"}
          </Button>
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancelar
          </Button>
        </div>
      </form>
    </Card>
  );
}

function PuestoPanel({
  propId,
  ppId,
  puestos,
  puedeGestionar,
  onEliminado,
}: {
  propId: string;
  ppId: string;
  puestos: PuestoArmador[];
  puedeGestionar: boolean;
  onEliminado: () => void;
}) {
  const { notify } = useToast();
  const { data: puesto, isLoading } = usePropiedadPuesto(propId, ppId);
  const eliminar = useEliminarPuesto(propId);
  const guardarSmart = useActualizarSmartOverridesPuesto(propId, ppId);
  const [editando, setEditando] = useState(false);
  const [editandoSmart, setEditandoSmart] = useState(false);

  if (isLoading || !puesto) return <CargandoBloque />;

  const ce = puesto.contenido_efectivo as Record<string, unknown>;
  const responsabilidades = Array.isArray(ce.responsabilidades) ? (ce.responsabilidades as string[]) : [];
  const esLocalPuro = puesto.modo === "local";
  const puedeAdaptarSmart = puesto.modo === "adaptado" || esLocalPuro;
  const smartMaster = puesto.smart_master ?? {};
  const smartEfectivo = puesto.smart_efectivo ?? {};
  const tieneSmart =
    Object.keys(smartMaster).some((k) => k !== "formato") ||
    Object.keys(smartEfectivo).some((k) => k !== "formato");
  const seccionesSmartLocales = Object.keys(puesto.smart_overrides ?? {}).filter(
    (k) => k !== "formato",
  ).length;

  async function guardarSmartOverrides(limpio: JdSmart) {
    const payload = esLocalPuro
      ? (limpio as unknown as Record<string, unknown>)
      : diffJdSmartPorSeccion(limpio as unknown as Record<string, unknown>, smartMaster);
    await guardarSmart.mutateAsync({ smart_overrides: payload });
  }

  async function onEliminar() {
    if (!window.confirm(`¿Eliminar el puesto “${puesto!.titulo}” de esta propiedad?`)) return;
    try {
      await eliminar.mutateAsync(ppId);
      notify("Puesto eliminado.");
      onEliminado();
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo eliminar.", "error");
    }
  }

  if (editando) {
    return (
      <PuestoEditForm
        propId={propId}
        puesto={puesto}
        puestos={puestos}
        onHecho={() => setEditando(false)}
        onCancel={() => setEditando(false)}
      />
    );
  }

  if (editandoSmart) {
    return (
      <Card className="p-5">
        <button
          onClick={() => setEditandoSmart(false)}
          className="mb-4 text-sm text-petrol-oscuro hover:underline"
        >
          ← Volver al puesto
        </button>
        {puedeAdaptarSmart && (esLocalPuro || tieneSmart) ? (
          <DescriptorSmartForm
            onDone={() => setEditandoSmart(false)}
            override={{
              inicial: smartEfectivo as unknown as JdSmart,
              guardar: guardarSmartOverrides,
              guardando: guardarSmart.isPending,
              sucioKey: `jd-smart-prop:${ppId}`,
              encabezado: (
                <div>
                  <h2 className="text-sm font-semibold text-petrol-oscuro">
                    Capa JD SMART — {esLocalPuro ? "puesto local" : "adaptación de esta propiedad"}
                  </h2>
                  <p className="text-xs text-carbon-suave">
                    {esLocalPuro
                      ? "Editás la ficha JD SMART completa de este puesto local."
                      : `Cada sección que cambies se guarda como local; el resto hereda del maestro. ${seccionesSmartLocales} sección(es) personalizada(s).`}
                  </p>
                </div>
              ),
            }}
          />
        ) : (
          <p className="text-sm text-carbon-suave">
            Este descriptor maestro todavía no tiene capa JD SMART para adaptar.
          </p>
        )}
      </Card>
    );
  }

  return (
    <Card className="p-5">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {puesto.codigo && <span className="font-mono text-xs text-carbon-suave">{puesto.codigo}</span>}
        <h3 className="text-base font-semibold text-petrol-oscuro">{puesto.titulo}</h3>
        <EstadoBadge estado={puesto.estado} />
      </div>
      <p className="text-xs text-carbon-suave">
        {MODO_LABEL[puesto.modo]}
        {puesto.departamento_codigo ? ` · ${puesto.departamento_codigo}` : ""}
        {" · "}
        {categoriaLabel(puesto.categoria, puesto.nivel_jerarquico)}
        {puesto.dotacion ? ` · ${puesto.dotacion} plaza(s)` : ""}
      </p>

      {puedeGestionar && (
        <div className="mt-3 flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => setEditando(true)}>
            Editar
          </Button>
          {puedeAdaptarSmart && (
            <Button variant="secondary" onClick={() => setEditandoSmart(true)}>
              Editar SMART
              {seccionesSmartLocales > 0 ? ` (${seccionesSmartLocales})` : ""}
            </Button>
          )}
          <Button variant="ghost" onClick={onEliminar} disabled={eliminar.isPending}>
            Eliminar
          </Button>
        </div>
      )}

      {typeof ce.proposito === "string" && ce.proposito && (
        <div className="mt-4 border-t border-linea pt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-carbon-suave">Propósito</p>
          <p className="mt-1 text-sm leading-relaxed text-carbon">{ce.proposito as string}</p>
        </div>
      )}
      {responsabilidades.length > 0 && (
        <div className="mt-3 border-t border-linea pt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-carbon-suave">
            Responsabilidades
          </p>
          <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-carbon">
            {responsabilidades.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 border-t border-linea pt-3">
        <PuestoTitulares propId={propId} ppId={ppId} puedeGestionar={puedeGestionar} />
      </div>
    </Card>
  );
}

function PuestoEditForm({
  propId,
  puesto,
  puestos,
  onHecho,
  onCancel,
}: {
  propId: string;
  puesto: PuestoArmador & { contenido_efectivo: Record<string, unknown> };
  puestos: PuestoArmador[];
  onHecho: () => void;
  onCancel: () => void;
}) {
  const { notify } = useToast();
  const actualizar = useActualizarPuesto(propId);
  const editableContenido = puesto.modo !== "adoptado";
  const [titulo, setTitulo] = useState(puesto.titulo);
  const [proposito, setProposito] = useState(
    typeof puesto.contenido_efectivo.proposito === "string"
      ? (puesto.contenido_efectivo.proposito as string)
      : "",
  );
  const [reportaA, setReportaA] = useState(puesto.reporta_a_id ?? "");
  const [dotacion, setDotacion] = useState(puesto.dotacion?.toString() ?? "");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const body: Record<string, unknown> = {
      reporta_a_id: reportaA || null,
      dotacion: dotacion ? Number(dotacion) : null,
    };
    if (editableContenido) {
      body.overrides = {
        titulo: titulo.trim(),
        nivel_jerarquico: puesto.nivel_jerarquico,
        ...(proposito.trim() ? { proposito: proposito.trim() } : {}),
      };
    }
    try {
      await actualizar.mutateAsync({ ppId: puesto.id, body });
      notify("Puesto actualizado.");
      onHecho();
    } catch (err) {
      notify(err instanceof ApiError ? err.detail : "No se pudo guardar.", "error");
    }
  }

  return (
    <Card className="p-5">
      <h3 className="mb-3 text-sm font-semibold text-petrol-oscuro">Editar puesto</h3>
      <form onSubmit={onSubmit} className="space-y-3">
        {editableContenido ? (
          <div>
            <Etiqueta htmlFor="ep-titulo">Título</Etiqueta>
            <Input id="ep-titulo" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
          </div>
        ) : (
          <p className="rounded-md bg-petrol-tint/40 px-3 py-2 text-xs text-carbon-suave">
            Puesto adoptado: el título y el contenido se heredan del maestro. Podés editar la
            jerarquía y la dotación.
          </p>
        )}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Etiqueta htmlFor="ep-jefe">Reporta a</Etiqueta>
            <Select id="ep-jefe" value={reportaA} onChange={(e) => setReportaA(e.target.value)}>
              <option value="">— Sin superior (raíz) —</option>
              {opcionesJefe(puestos, puesto.id).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.titulo}
                  {p.codigo ? ` (${p.codigo})` : ""}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Etiqueta htmlFor="ep-dotacion">Dotación (plazas)</Etiqueta>
            <Input
              id="ep-dotacion"
              type="number"
              min={0}
              value={dotacion}
              onChange={(e) => setDotacion(e.target.value)}
            />
          </div>
        </div>
        {editableContenido && (
          <div>
            <Etiqueta htmlFor="ep-prop">Propósito</Etiqueta>
            <Textarea id="ep-prop" rows={3} value={proposito} onChange={(e) => setProposito(e.target.value)} />
          </div>
        )}
        <div className="flex gap-2 border-t border-linea pt-3">
          <Button type="submit" disabled={actualizar.isPending}>
            {actualizar.isPending ? "Guardando…" : "Guardar"}
          </Button>
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancelar
          </Button>
        </div>
      </form>
    </Card>
  );
}
