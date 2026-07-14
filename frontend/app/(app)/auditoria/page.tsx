"use client";

import { useState } from "react";

import { EstadoBadge } from "@/components/EstadoBadge";
import {
  Button,
  Card,
  CargandoBloque,
  Chip,
  EstadoError,
  EstadoVacio,
  Input,
  PageHeader,
} from "@/components/ui";
import { useToast } from "@/components/toast";
import { ApiError } from "@/lib/api";
import { tieneRol, useAuth } from "@/lib/auth";
import {
  useAuditoria,
  useBitacora,
  useDocumentosControlados,
  useUsuarios,
  useVerificarIntegridad,
} from "@/lib/hooks";
import { useDebouncedValue } from "@/lib/use-debounce";

function fecha(iso: string): string {
  return new Date(iso).toLocaleString("es-CR", { dateStyle: "short", timeStyle: "short" });
}

export default function AuditoriaPage() {
  const { user } = useAuth();
  const { notify } = useToast();
  const [entidad, setEntidad] = useState("");
  const [accion, setAccion] = useState("");
  const entidadD = useDebouncedValue(entidad, 300);
  const accionD = useDebouncedValue(accion, 300);

  const { data: usuarios } = useUsuarios();
  const nombrePorId = new Map((usuarios ?? []).map((u) => [u.id, u.nombre]));

  const auditoria = useAuditoria({
    entidad: entidadD || undefined,
    accion: accionD || undefined,
    limit: 100,
  });
  const docs = useDocumentosControlados();
  const [docSel, setDocSel] = useState<string | null>(null);
  const bitacora = useBitacora(docSel);
  const verificar = useVerificarIntegridad();

  if (!tieneRol(user, "super_admin", "editor_corporativo", "custodio_documental")) {
    return (
      <div>
        <PageHeader titulo="Auditoría y custodia" />
        <EstadoVacio
          titulo="Sin permisos"
          descripcion="Reservado a roles corporativos y al custodio documental."
        />
      </div>
    );
  }

  async function onVerificar(docId: string) {
    try {
      const r = await verificar.mutateAsync(docId);
      notify(r.mensaje, r.integro ? "ok" : "error");
    } catch (e) {
      notify(e instanceof ApiError ? e.detail : "No se pudo verificar.", "error");
    }
  }

  return (
    <div className="space-y-8">
      <PageHeader
        titulo="Auditoría y custodia"
        descripcion="Trazabilidad transversal y control de los documentos firmados (§7.7, §7.18)."
      />

      {/* Documentos controlados */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-carbon-suave">
          Documentos controlados
        </h2>
        {docs.isLoading ? (
          <CargandoBloque />
        ) : docs.isError ? (
          <EstadoError mensaje={(docs.error as Error)?.message} />
        ) : !docs.data || docs.data.items.length === 0 ? (
          <EstadoVacio
            titulo="Aún no hay documentos controlados"
            descripcion="Aparecen cuando un SOP completa sus firmas obligatorias."
          />
        ) : (
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-linea bg-petrol-tint/40 text-left text-xs uppercase tracking-wide text-carbon-suave">
                    <th className="px-4 py-3 font-semibold">Código</th>
                    <th className="px-4 py-3 font-semibold">Documento</th>
                    <th className="px-4 py-3 font-semibold">Ver.</th>
                    <th className="px-4 py-3 font-semibold">Firmado</th>
                    <th className="px-4 py-3 font-semibold">Vigente</th>
                    <th className="px-4 py-3 font-semibold">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {docs.data.items.map((doc) => (
                    <tr key={doc.id} className="border-b border-linea last:border-0">
                      <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-carbon-suave">
                        {doc.sop_codigo ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-carbon">{doc.sop_nombre ?? "—"}</td>
                      <td className="px-4 py-3 text-carbon-suave">v{doc.version}</td>
                      <td className="px-4 py-3 text-carbon-suave">
                        {doc.fecha_firma ? fecha(doc.fecha_firma) : "—"}
                      </td>
                      <td className="px-4 py-3">
                        {doc.es_vigente ? <EstadoBadge estado="vigente" /> : <Chip>No vigente</Chip>}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <Button
                            variant="secondary"
                            onClick={() => setDocSel(docSel === doc.id ? null : doc.id)}
                          >
                            {docSel === doc.id ? "Ocultar bitácora" : "Bitácora"}
                          </Button>
                          <Button
                            variant="ghost"
                            disabled={verificar.isPending}
                            onClick={() => onVerificar(doc.id)}
                          >
                            Verificar integridad
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {docSel && (
          <Card className="mt-3 p-4">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-carbon-suave">
              Bitácora del documento
            </p>
            {bitacora.isLoading ? (
              <CargandoBloque />
            ) : !bitacora.data || bitacora.data.length === 0 ? (
              <p className="text-sm text-carbon-suave">Sin movimientos registrados.</p>
            ) : (
              <ul className="space-y-1 text-sm">
                {bitacora.data.map((b) => (
                  <li key={b.id} className="flex gap-3">
                    <span className="w-32 shrink-0 text-xs text-carbon-suave">{fecha(b.creado_en)}</span>
                    <span className="font-medium text-carbon">{b.accion}</span>
                    {b.detalle && (
                      <span className="truncate text-xs text-carbon-suave">
                        {JSON.stringify(b.detalle)}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        )}
      </section>

      {/* Registro de auditoría */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-carbon-suave">
          Registro de auditoría
        </h2>
        <Card className="mb-3 p-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <Input
              placeholder="Entidad (ej. sop_master, descriptor_puesto_master)…"
              value={entidad}
              onChange={(e) => setEntidad(e.target.value)}
              aria-label="Entidad"
            />
            <Input
              placeholder="Acción (ej. crear, firma, estado)…"
              value={accion}
              onChange={(e) => setAccion(e.target.value)}
              aria-label="Acción"
            />
          </div>
        </Card>

        {auditoria.isLoading ? (
          <CargandoBloque />
        ) : auditoria.isError ? (
          <EstadoError mensaje={(auditoria.error as Error)?.message} />
        ) : !auditoria.data || auditoria.data.items.length === 0 ? (
          <EstadoVacio titulo="Sin registros" descripcion="No hay acciones para esos filtros." />
        ) : (
          <Card>
            <div className="border-b border-linea px-4 py-2 text-xs text-carbon-suave">
              {auditoria.data.total} evento{auditoria.data.total === 1 ? "" : "s"}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-linea bg-petrol-tint/40 text-left text-xs uppercase tracking-wide text-carbon-suave">
                    <th className="px-4 py-3 font-semibold">Fecha</th>
                    <th className="px-4 py-3 font-semibold">Usuario</th>
                    <th className="px-4 py-3 font-semibold">Entidad</th>
                    <th className="px-4 py-3 font-semibold">Acción</th>
                    <th className="px-4 py-3 font-semibold">Detalle</th>
                  </tr>
                </thead>
                <tbody>
                  {auditoria.data.items.map((r) => (
                    <tr key={r.id} className="border-b border-linea last:border-0 align-top">
                      <td className="whitespace-nowrap px-4 py-3 text-xs text-carbon-suave">
                        {fecha(r.creado_en)}
                      </td>
                      <td className="px-4 py-3 text-carbon-suave">
                        {r.usuario_id ? (nombrePorId.get(r.usuario_id) ?? "—") : "sistema"}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-carbon-suave">{r.entidad}</td>
                      <td className="px-4 py-3 text-carbon">{r.accion}</td>
                      <td className="px-4 py-3 text-xs text-carbon-suave">
                        {r.detalle ? JSON.stringify(r.detalle) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </section>
    </div>
  );
}
