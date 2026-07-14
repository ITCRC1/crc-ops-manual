// Categoría de puesto (organigrama): mapea el código de categoría a su etiqueta y
// provee un fallback por nivel jerárquico cuando la categoría no está seteada.

export const CATEGORIA_LABEL: Record<string, string> = {
  director: "Director",
  gerente_departamental: "Gerente Departamental",
  supervisor: "Supervisor",
  linea: "Empleado de Línea",
};

// Orden jerárquico de las categorías (para ordenar y para los selectores).
export const CATEGORIA_ORDEN = ["director", "gerente_departamental", "supervisor", "linea"] as const;

const FALLBACK_NIVEL: Record<number, string> = {
  1: "Director",
  2: "Director",
  3: "Supervisor",
  4: "Empleado de Línea",
};

export function categoriaLabel(
  categoria: string | null | undefined,
  nivel?: number,
): string {
  if (categoria && CATEGORIA_LABEL[categoria]) return CATEGORIA_LABEL[categoria];
  if (nivel != null) return FALLBACK_NIVEL[nivel] ?? `Nivel ${nivel}`;
  return "—";
}

const FALLBACK_COD: Record<number, string> = {
  1: "director",
  2: "director",
  3: "supervisor",
  4: "linea",
};

// Código de categoría (para agrupar), con respaldo por nivel si no está seteada.
export function categoriaCodigo(
  categoria: string | null | undefined,
  nivel?: number,
): string {
  if (categoria && CATEGORIA_LABEL[categoria]) return categoria;
  if (nivel != null) return FALLBACK_COD[nivel] ?? "linea";
  return "linea";
}
