"use client";

import { useState } from "react";

import { EstadoBadge } from "./EstadoBadge";
import { UserSelect } from "./UserSelect";
import { Button, Card, Chip, Input, Select, Textarea } from "./ui";
import { useToast } from "./toast";
import { ApiError, apiDownload, guardarBlob } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  useDesignarFirmante,
  useDocumentoControlado,
  useFirmantes,
  useFirmar,
  useInvitarColaborador,
  useRechazar,
  useUsuarios,
} from "@/lib/hooks";
import type { SopDetalle } from "@/lib/types";

function err(e: unknown): string {
  return e instanceof ApiError ? e.detail : "Ocurrió un error.";
}

export function PanelFirmas({
  sop,
  puedeGestionar,
}: {
  sop: SopDetalle;
  puedeGestionar: boolean;
}) {
  const { user } = useAuth();
  const { notify } = useToast();
  const { data: firmantes } = useFirmantes(sop.id);
  const { data: usuarios } = useUsuarios();
  const docCtrl = useDocumentoControlado(sop.id, sop.estado === "firmado");

  const designar = useDesignarFirmante(sop.id);
  const firmar = useFirmar(sop.id);
  const rechazar = useRechazar(sop.id);
  const invitar = useInvitarColaborador(sop.id);

  const [nuevoFirmante, setNuevoFirmante] = useState("");
  const [orden, setOrden] = useState(1);
  const [obligatorio, setObligatorio] = useState(true);
  const [comentario, setComentario] = useState("");
  const [colab, setColab] = useState("");
  const [rolColab, setRolColab] = useState("redactor");

  const nombrePorId = new Map((usuarios ?? []).map((u) => [u.id, u.nombre]));
  const designados = (firmantes ?? []).map((f) => f.usuario_id);
  const puedeDesignar =
    puedeGestionar && (sop.estado === "borrador" || sop.estado === "en_revision");
  const soyFirmantePendiente =
    sop.estado === "en_firma" &&
    !!firmantes?.some((f) => f.usuario_id === user?.id && !f.firmado);

  async function onDesignar() {
    if (!nuevoFirmante) return notify("Elegí un usuario.", "error");
    try {
      await designar.mutateAsync({ usuario_id: nuevoFirmante, orden, obligatorio });
      notify("Firmante designado.");
      setNuevoFirmante("");
    } catch (e) {
      notify(err(e), "error");
    }
  }

  async function onFirmar() {
    try {
      const r = (await firmar.mutateAsync({ metodo: "clave" })) as {
        documento_controlado?: boolean;
      };
      notify(r?.documento_controlado ? "Firmado. Documento controlado emitido." : "Firma registrada.");
    } catch (e) {
      notify(err(e), "error");
    }
  }

  async function onRechazar() {
    if (!comentario.trim()) return notify("El comentario es obligatorio.", "error");
    try {
      await rechazar.mutateAsync({ comentario });
      notify("Documento rechazado.");
      setComentario("");
    } catch (e) {
      notify(err(e), "error");
    }
  }

  async function onInvitar() {
    if (!colab) return notify("Elegí un usuario.", "error");
    try {
      await invitar.mutateAsync({ usuario_id: colab, rol_colaboracion: rolColab });
      notify("Colaborador invitado.");
      setColab("");
    } catch (e) {
      notify(err(e), "error");
    }
  }

  async function onDescargar() {
    try {
      const { blob, filename } = await apiDownload(
        `/api/sops/${sop.id}/documento-controlado/descargar`,
      );
      guardarBlob(blob, filename);
    } catch {
      notify("No se pudo descargar el PDF.", "error");
    }
  }

  return (
    <Card className="p-4">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-carbon-suave">Firmas</p>

      {/* Lista de firmantes */}
      {firmantes && firmantes.length > 0 ? (
        <ul className="space-y-2">
          {firmantes.map((f) => (
            <li key={f.id} className="flex items-center justify-between gap-2 text-sm">
              <span className="min-w-0 truncate">
                <span className="text-carbon">{nombrePorId.get(f.usuario_id) ?? f.usuario_id}</span>
                <span className="ml-1 text-xs text-carbon-suave">
                  #{f.orden}
                  {f.obligatorio ? " · obligatorio" : " · opcional"}
                </span>
              </span>
              {f.firmado ? (
                <EstadoBadge estado="firmado" />
              ) : (
                <Chip>Pendiente</Chip>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-carbon-suave">Sin firmantes designados.</p>
      )}

      {/* Designar firmante */}
      {puedeDesignar && (
        <div className="mt-4 space-y-2 border-t border-linea pt-4">
          <p className="text-xs font-medium text-carbon">Designar firmante</p>
          <UserSelect
            value={nuevoFirmante}
            onChange={setNuevoFirmante}
            elegiblesFirmante
            excludeIds={designados}
            placeholder="Firmante elegible…"
          />
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-1 text-sm text-carbon-suave">
              Orden
              <Input
                type="number"
                min={1}
                value={orden}
                onChange={(e) => setOrden(Number(e.target.value) || 1)}
                className="w-16"
              />
            </label>
            <label className="flex items-center gap-2 text-sm text-carbon-suave">
              <input
                type="checkbox"
                checked={obligatorio}
                onChange={(e) => setObligatorio(e.target.checked)}
              />
              Obligatorio
            </label>
          </div>
          <Button onClick={onDesignar} disabled={designar.isPending}>
            Designar
          </Button>
        </div>
      )}

      {/* Firmar / rechazar (firmante en turno) */}
      {soyFirmantePendiente && (
        <div className="mt-4 space-y-2 border-t border-linea pt-4">
          <p className="text-xs font-medium text-carbon">Sos firmante de este documento</p>
          <div className="flex gap-2">
            <Button onClick={onFirmar} disabled={firmar.isPending}>
              Firmar
            </Button>
          </div>
          <Textarea
            rows={2}
            placeholder="Comentario para rechazar (obligatorio)…"
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
          />
          <Button variant="secondary" onClick={onRechazar} disabled={rechazar.isPending}>
            Rechazar
          </Button>
        </div>
      )}

      {/* Invitar colaborador */}
      {puedeDesignar && (
        <div className="mt-4 space-y-2 border-t border-linea pt-4">
          <p className="text-xs font-medium text-carbon">Invitar colaborador</p>
          <UserSelect value={colab} onChange={setColab} placeholder="Colaborador…" />
          <div className="flex gap-2">
            <Select
              value={rolColab}
              onChange={(e) => setRolColab(e.target.value)}
              className="w-40"
              aria-label="Rol de colaboración"
            >
              <option value="redactor">Redactor</option>
              <option value="revisor">Revisor</option>
            </Select>
            <Button variant="secondary" onClick={onInvitar} disabled={invitar.isPending}>
              Invitar
            </Button>
          </div>
        </div>
      )}

      {/* Documento controlado */}
      {sop.estado === "firmado" && (
        <div className="mt-4 space-y-2 border-t border-linea pt-4">
          <p className="text-xs font-medium text-carbon">Documento controlado</p>
          {docCtrl.data?.hash_pdf && (
            <p className="break-all font-mono text-[11px] text-carbon-suave">
              SHA-256: {docCtrl.data.hash_pdf}
            </p>
          )}
          <Button onClick={onDescargar}>Descargar PDF firmado</Button>
        </div>
      )}
    </Card>
  );
}
