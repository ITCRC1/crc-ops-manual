"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { EstadoBadge } from "@/components/EstadoBadge";
import { useToast } from "@/components/toast";
import {
  Button,
  Card,
  Etiqueta,
  EstadoVacio,
  Input,
  PageHeader,
  Select,
  Textarea,
} from "@/components/ui";
import { ApiError } from "@/lib/api";
import { tieneRol, useAuth } from "@/lib/auth";
import { useAnalizarIntake, useAreas, useCrearSop, useExtraerIntake } from "@/lib/hooks";
import type { SopDetalle, TriageIntake } from "@/lib/types";

export default function IntakePage() {
  const router = useRouter();
  const { user } = useAuth();
  const { notify } = useToast();
  const puede = tieneRol(user, "editor_corporativo", "super_admin");

  const { data: areas } = useAreas();
  const analizar = useAnalizarIntake();
  const extraer = useExtraerIntake();
  const crear = useCrearSop();

  const [nombre, setNombre] = useState("");
  const [texto, setTexto] = useState("");
  const [areaSel, setAreaSel] = useState("");
  const [triage, setTriage] = useState<TriageIntake | null>(null);

  if (!puede) {
    return (
      <div>
        <PageHeader titulo="Laboratorio de intake" />
        <EstadoVacio
          titulo="Sin permisos"
          descripcion="Solo el admin o el editor corporativo puede ingresar procedimientos."
        />
      </div>
    );
  }

  async function onArchivo(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f) return;
    try {
      const r = await extraer.mutateAsync(f);
      setNombre(r.nombre);
      setTexto(r.texto);
      setTriage(null);
      notify("Texto extraído del archivo.");
    } catch (err) {
      notify(err instanceof ApiError ? err.detail : "No se pudo leer el archivo.", "error");
    }
  }

  async function onAnalizar() {
    if (!nombre.trim()) {
      notify("Poné un nombre para el procedimiento.", "error");
      return;
    }
    try {
      setTriage(await analizar.mutateAsync({ nombre: nombre.trim(), texto }));
    } catch (err) {
      notify(err instanceof ApiError ? err.detail : "No se pudo analizar.", "error");
    }
  }

  async function onCrear() {
    if (!areaSel) {
      notify("Elegí un área para el nuevo SOP.", "error");
      return;
    }
    try {
      const sop = (await crear.mutateAsync({
        area_codigo: areaSel,
        nombre: nombre.trim(),
        proposito: texto.trim() || null,
      })) as SopDetalle;
      notify(`Creado ${sop.codigo}. Completalo en la Librería.`);
      router.push(`/biblioteca/${sop.id}`);
    } catch (err) {
      notify(err instanceof ApiError ? err.detail : "No se pudo crear el SOP.", "error");
    }
  }

  return (
    <div className="max-w-3xl">
      <PageHeader
        titulo="Laboratorio de intake"
        descripcion="Pegá o subí un procedimiento: el sistema chequea si ya existe algo parecido y, si es nuevo, lo creás como SOP borrador."
      />

      <Card className="space-y-4 p-6">
        <div>
          <Etiqueta htmlFor="in-nombre">Nombre del procedimiento *</Etiqueta>
          <Input id="in-nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} />
        </div>
        <div>
          <Etiqueta htmlFor="in-texto">Contenido</Etiqueta>
          <Textarea id="in-texto" rows={8} value={texto} onChange={(e) => setTexto(e.target.value)} />
        </div>
        <div className="flex flex-wrap items-center gap-4 border-t border-linea pt-4">
          <Button onClick={onAnalizar} disabled={analizar.isPending}>
            {analizar.isPending ? "Analizando…" : "Analizar"}
          </Button>
          <label className="cursor-pointer text-sm text-petrol-oscuro hover:underline">
            {extraer.isPending ? "Leyendo archivo…" : "o subí un archivo (.docx / .pdf / .txt)"}
            <input type="file" accept=".docx,.pdf,.txt" onChange={onArchivo} className="hidden" />
          </label>
        </div>
      </Card>

      {triage && (
        <div className="mt-6 space-y-4">
          {triage.verdict === "posible_duplicado" ? (
            <Card className="border-en-firma/40 bg-en-firma/5 p-4">
              <p className="text-sm font-semibold text-en-firma">Posible duplicado</p>
              <p className="mt-1 text-sm text-carbon-suave">
                Ya hay SOPs muy parecidos. Revisá si conviene mejorar uno existente en vez de crear
                otro.
              </p>
            </Card>
          ) : (
            <Card className="border-firmado/40 bg-firmado/5 p-4">
              <p className="text-sm font-semibold text-firmado">Parece nuevo</p>
              <p className="mt-1 text-sm text-carbon-suave">
                No encontramos un SOP muy parecido. Podés crearlo como borrador.
              </p>
            </Card>
          )}

          {triage.similares.length > 0 && (
            <Card>
              <p className="border-b border-linea px-4 py-2 text-xs font-semibold uppercase tracking-wide text-carbon-suave">
                SOPs más parecidos
              </p>
              <ul>
                {triage.similares.map((s) => (
                  <li
                    key={s.id}
                    className="flex flex-wrap items-center gap-2 border-b border-linea px-4 py-2 last:border-0"
                  >
                    <span className="font-mono text-xs text-carbon-suave">{s.codigo}</span>
                    <Link
                      href={`/biblioteca/${s.id}`}
                      className="flex-1 text-sm text-carbon hover:underline"
                    >
                      {s.nombre}
                    </Link>
                    <span className="text-xs font-medium text-carbon-suave">
                      {Math.round(s.score * 100)}%
                    </span>
                    <EstadoBadge estado={s.estado} />
                  </li>
                ))}
              </ul>
            </Card>
          )}

          <Card className="p-4">
            <p className="mb-3 text-sm font-medium text-carbon">Crear como SOP nuevo (borrador)</p>
            <div className="flex flex-wrap items-end gap-3">
              <div className="min-w-[16rem]">
                <Etiqueta htmlFor="in-area">Área</Etiqueta>
                <Select id="in-area" value={areaSel} onChange={(e) => setAreaSel(e.target.value)}>
                  <option value="">Elegí un área…</option>
                  {areas?.map((a) => (
                    <option key={a.id} value={a.codigo}>
                      {a.codigo} — {a.nombre}
                    </option>
                  ))}
                </Select>
              </div>
              <Button onClick={onCrear} disabled={crear.isPending || !areaSel}>
                {crear.isPending ? "Creando…" : "Crear SOP borrador"}
              </Button>
            </div>
            <p className="mt-2 text-xs text-carbon-suave">
              Se crea con el nombre y el contenido como propósito; después lo estructurás y firmás
              desde la Librería.
            </p>
          </Card>
        </div>
      )}
    </div>
  );
}
