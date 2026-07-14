"use client";

export interface OpcionChip {
  id: string;
  etiqueta: string;
}

export function ChipMultiSelect({
  opciones,
  seleccionados,
  onChange,
  vacio,
}: {
  opciones: OpcionChip[];
  seleccionados: string[];
  onChange: (ids: string[]) => void;
  vacio?: string;
}) {
  const set = new Set(seleccionados);

  function toggle(id: string) {
    const n = new Set(set);
    if (n.has(id)) n.delete(id);
    else n.add(id);
    onChange([...n]);
  }

  if (opciones.length === 0) {
    return <p className="text-sm text-carbon-suave">{vacio ?? "Sin opciones disponibles."}</p>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {opciones.map((o) => (
        <button
          type="button"
          key={o.id}
          onClick={() => toggle(o.id)}
          className={`rounded-full border px-3 py-1 text-xs ${
            set.has(o.id)
              ? "border-petrol bg-petrol text-white"
              : "border-linea bg-superficie text-carbon-suave hover:bg-petrol-tint"
          }`}
        >
          {o.etiqueta}
        </button>
      ))}
    </div>
  );
}
