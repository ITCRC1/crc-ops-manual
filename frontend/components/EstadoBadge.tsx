// Badge de estado del documento/asignación (§9). Clases completas y estáticas para
// que Tailwind no las purgue.

const ESTILOS: Record<string, { clase: string; label: string }> = {
  borrador: { clase: "bg-borrador", label: "Borrador" },
  en_revision: { clase: "bg-en-firma", label: "En revisión" },
  en_firma: { clase: "bg-en-firma", label: "En firma" },
  firmado: { clase: "bg-firmado", label: "Firmado" },
  vigente: { clase: "bg-firmado", label: "Vigente" },
  rechazado: { clase: "bg-rechazado", label: "Rechazado" },
  archivado: { clase: "bg-archivado", label: "Archivado" },
};

export function EstadoBadge({ estado }: { estado: string }) {
  const e = ESTILOS[estado] ?? { clase: "bg-archivado", label: estado };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium text-white ${e.clase}`}
    >
      {e.label}
    </span>
  );
}

const TIPO_LABEL: Record<string, string> = {
  sop: "SOP",
  politica: "Política",
  descriptor: "Descriptor",
};

export function TipoBadge({ tipo }: { tipo: string }) {
  return (
    <span className="inline-flex items-center rounded-full border border-linea bg-petrol-tint px-2.5 py-0.5 text-xs font-medium text-petrol-oscuro">
      {TIPO_LABEL[tipo] ?? tipo}
    </span>
  );
}
