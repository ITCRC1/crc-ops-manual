"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { useToast } from "@/components/toast";
import {
  Button,
  Card,
  CargandoBloque,
  EstadoError,
  EstadoVacio,
  Input,
  PageHeader,
  Select,
} from "@/components/ui";
import { apiDownload, guardarBlob, qs } from "@/lib/api";
import { useAreas, useCalendario, useDepartamentos } from "@/lib/hooks";
import type { EventoCalendario } from "@/lib/types";

function iso(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate(),
  ).padStart(2, "0")}`;
}

function rangoMesActual(): { desde: string; hasta: string } {
  const hoy = new Date();
  return {
    desde: iso(new Date(hoy.getFullYear(), hoy.getMonth(), 1)),
    hasta: iso(new Date(hoy.getFullYear(), hoy.getMonth() + 1, 0)),
  };
}

const DIAS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
const MESES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

function fechaLarga(f: string): string {
  const [y, m, d] = f.split("-").map(Number);
  const dt = new Date(y, m - 1, d);
  return `${DIAS[dt.getDay()]} ${d} de ${MESES[m - 1]} de ${y}`;
}

export default function CalendarioPage() {
  const { notify } = useToast();
  const inicial = useMemo(rangoMesActual, []);
  const [desde, setDesde] = useState(inicial.desde);
  const [hasta, setHasta] = useState(inicial.hasta);
  const [area, setArea] = useState("");
  const [departamentoId, setDepartamentoId] = useState("");
  const [descargando, setDescargando] = useState(false);

  const { data: areas } = useAreas();
  const { data: departamentos } = useDepartamentos();
  const depUnicos = useMemo(() => {
    const m = new Map<string, { id: string; codigo: string; nombre: string }>();
    for (const d of departamentos ?? []) if (!m.has(d.codigo)) m.set(d.codigo, d);
    return [...m.values()];
  }, [departamentos]);

  const { data, isLoading, isError, error } = useCalendario({
    desde,
    hasta,
    area: area || undefined,
    departamento_id: departamentoId || undefined,
  });

  const grupos = useMemo(() => {
    const g = new Map<string, EventoCalendario[]>();
    for (const e of data?.eventos ?? []) {
      const lista = g.get(e.fecha) ?? [];
      lista.push(e);
      g.set(e.fecha, lista);
    }
    return [...g.entries()];
  }, [data]);

  async function descargarIcs() {
    setDescargando(true);
    try {
      const { blob, filename } = await apiDownload(
        `/api/calendario/export.ics${qs({ area: area || undefined, departamento_id: departamentoId || undefined })}`,
      );
      guardarBlob(blob, filename || "crc-ops-calendario.ics");
    } catch {
      notify("No se pudo descargar el calendario.", "error");
    } finally {
      setDescargando(false);
    }
  }

  return (
    <div>
      <PageHeader
        titulo="Calendario general"
        descripcion="Actividades programadas de todos los SOPs, expandidas por fecha. Descargá el .ics para suscribirte en Google Calendar."
        accion={
          <Button variant="secondary" onClick={descargarIcs} disabled={descargando}>
            {descargando ? "Generando…" : "Descargar .ics"}
          </Button>
        }
      />

      <Card className="mb-4 p-4">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-carbon-suave">Desde</label>
            <Input type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-carbon-suave">Hasta</label>
            <Input type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-carbon-suave">Área</label>
            <Select value={area} onChange={(e) => setArea(e.target.value)} aria-label="Área">
              <option value="">Todas</option>
              {areas?.map((a) => (
                <option key={a.id} value={a.codigo}>
                  {a.codigo} — {a.nombre}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-carbon-suave">Departamento</label>
            <Select
              value={departamentoId}
              onChange={(e) => setDepartamentoId(e.target.value)}
              aria-label="Departamento"
            >
              <option value="">Todos</option>
              {depUnicos.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.codigo} — {d.nombre}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </Card>

      {isLoading ? (
        <CargandoBloque />
      ) : isError ? (
        <EstadoError mensaje={(error as Error)?.message} />
      ) : grupos.length === 0 ? (
        <EstadoVacio
          titulo="Sin actividades en el rango"
          descripcion="Ajustá las fechas o agregá programación en los SOPs desde la librería."
        />
      ) : (
        <div className="space-y-5">
          {grupos.map(([fecha, eventos]) => (
            <Card key={fecha} className="overflow-hidden">
              <div className="border-b border-linea bg-petrol-tint/40 px-4 py-2 text-sm font-semibold capitalize text-petrol-oscuro">
                {fechaLarga(fecha)}
              </div>
              <ul>
                {eventos.map((e, i) => (
                  <li
                    key={`${e.programacion_id}-${i}`}
                    className="flex items-start gap-4 border-b border-linea px-4 py-3 last:border-0"
                  >
                    <div className="w-16 shrink-0 text-sm font-medium text-carbon-suave">
                      {e.dia_completo ? "Todo el día" : (e.hora ?? "").slice(0, 5)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-carbon">{e.titulo}</p>
                      <p className="mt-0.5 text-xs text-carbon-suave">
                        <Link
                          href={`/biblioteca/${e.sop_id}`}
                          className="font-mono text-petrol-oscuro hover:underline"
                        >
                          {e.sop_codigo}
                        </Link>{" "}
                        · {e.sop_nombre}
                        {e.responsable ? ` · ${e.responsable}` : ""}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
