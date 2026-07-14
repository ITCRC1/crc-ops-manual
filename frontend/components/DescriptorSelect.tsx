"use client";

import { Select } from "./ui";
import { useDescriptores } from "@/lib/hooks";

export function DescriptorSelect({
  value,
  onChange,
  excludeId,
  placeholder = "— sin jefe (raíz) —",
}: {
  value: string;
  onChange: (id: string) => void;
  excludeId?: string;
  placeholder?: string;
}) {
  const { data } = useDescriptores({ limit: 200 });
  const opciones = (data?.items ?? []).filter((d) => d.id !== excludeId);
  return (
    <Select value={value} onChange={(e) => onChange(e.target.value)} aria-label="Reporta a">
      <option value="">{placeholder}</option>
      {opciones.map((d) => (
        <option key={d.id} value={d.id}>
          {d.codigo} — {d.titulo}
        </option>
      ))}
    </Select>
  );
}
