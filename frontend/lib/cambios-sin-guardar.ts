"use client";

// Registro global de formularios con cambios sin guardar.
//
// Existe porque el editor SMART es una página larga: perder veinte minutos de trabajo
// por un clic en el menú lateral es fácil y no tiene deshacer. Cubre las tres salidas
// reales: recargar/cerrar la pestaña (beforeunload), el enlace "Volver" y el menú.
//
// Es un módulo y no un contexto de React para que `AppShell` pueda consultarlo sin que
// cada formulario tenga que estar dentro de un provider.

import { useEffect } from "react";

const sucios = new Set<string>();

export function hayCambiosSinGuardar(): boolean {
  return sucios.size > 0;
}

const MENSAJE =
  "Tenés cambios sin guardar. Si salís ahora se pierden.\n\n¿Salir de todos modos?";

/** `true` si se puede navegar: no hay cambios, o el usuario confirmó perderlos. */
export function confirmarSalida(): boolean {
  if (!hayCambiosSinGuardar()) return true;
  return window.confirm(MENSAJE);
}

/**
 * Marca este formulario como sucio mientras `sucio` sea true.
 * `id` distingue formularios simultáneos (ej. base y SMART en la misma ficha).
 */
export function useCambiosSinGuardar(id: string, sucio: boolean) {
  useEffect(() => {
    if (!sucio) {
      sucios.delete(id);
      return;
    }
    sucios.add(id);

    // El navegador ignora el texto personalizado, pero exige preventDefault para preguntar.
    const alSalir = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", alSalir);
    return () => {
      window.removeEventListener("beforeunload", alSalir);
      sucios.delete(id);
    };
  }, [id, sucio]);

  // Al desmontar (guardar, cancelar, cambiar de página) el formulario deja de estar sucio.
  useEffect(() => () => void sucios.delete(id), [id]);
}
