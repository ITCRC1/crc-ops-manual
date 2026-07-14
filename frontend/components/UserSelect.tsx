"use client";

import { Select } from "./ui";
import { useUsuarios } from "@/lib/hooks";

export function UserSelect({
  value,
  onChange,
  elegiblesFirmante = false,
  excludeIds = [],
  placeholder = "Elegí un usuario…",
}: {
  value: string;
  onChange: (id: string) => void;
  elegiblesFirmante?: boolean;
  excludeIds?: string[];
  placeholder?: string;
}) {
  const { data } = useUsuarios(elegiblesFirmante ? { elegibles_firmante: true } : {});
  const opciones = (data ?? []).filter((u) => !excludeIds.includes(u.id));
  return (
    <Select value={value} onChange={(e) => onChange(e.target.value)} aria-label="Usuario">
      <option value="">{placeholder}</option>
      {opciones.map((u) => (
        <option key={u.id} value={u.id}>
          {u.nombre} · {u.email} (n{u.nivel_jerarquico})
        </option>
      ))}
    </Select>
  );
}
