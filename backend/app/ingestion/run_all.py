"""Etapa 3 — Orquestador de la ingesta completa (reproducible, idempotente).

Ejecuta en orden los pasos determinísticos. El emparejamiento semántico Excel↔Word
lo produce un workflow LLM y queda congelado en seed/ingesta/reconciliation_matches.json,
que este pipeline consume (no lo recalcula).

Uso:
    python -m app.ingestion.run_all
"""

import asyncio
from pathlib import Path

from app.ingestion import (
    cargar_brechas,
    cargar_descriptores,
    cargar_descriptores_finanzas,
    cargar_posiciones,
    cargar_sop_departamentos,
    cargar_sops,
    cargar_sops_amarena,
    cargar_sops_generados,
    cargar_sops_nuevos,
    cargar_usali,
    categorizar_puestos,
    construir_reporte,
    enriquecer_ge_sops,
    etiquetar_sistemas_sops,
    parse_fuentes,
    reclasificar_bodegas,
)

_ING = Path(__file__).resolve().parents[2].parent / "seed" / "ingesta"

# SOPs operativos generados (contenido original CRC), congelados en seed/ingesta.
OPERATIVOS = [
    ("cocina_rest_final.json", "SOP de Cocina/Restaurante (requisitos del dueño)"),
    ("mant_train_final.json", "SOP operativo (mantenimiento/entrenamiento)"),
    ("empleados_final.json", "SOP de Alimentación de Empleados"),
]


async def main() -> None:
    print("== 1. Parseo de fuentes ==")
    parse_fuentes.main()
    print("== 2. Reporte de reconciliación ==")
    construir_reporte.main()
    print("== 3. Carga de SOPs (cuerpos) ==")
    await cargar_sops.cargar()
    print("== 4. Carga de Descriptores de Puesto ==")
    await cargar_descriptores.cargar()
    print("== 4b. Descriptores de Finanzas (adaptados) ==")
    await cargar_descriptores_finanzas.cargar()
    print("== 4c. Posiciones USALI + particularidades (líneas/supervisión) ==")
    await cargar_posiciones.cargar()
    print("== 5. Borradores del pack financiero USALI ==")
    await cargar_usali.cargar()
    print("== 6. Borradores para brechas de control (gap analysis) ==")
    await cargar_brechas.cargar()
    print("== 6b. Enriquecimiento de SOPs de Guest Experience (OPERA Cloud) ==")
    await enriquecer_ge_sops.cargar()
    print("== 6b2. SOPs operativos generados (cocina/rest, mantenimiento, entrenamiento, empleados) ==")
    for archivo, origen in OPERATIVOS:
        ruta = _ING / archivo
        if ruta.exists():
            await cargar_sops_generados.cargar(str(ruta), origen)
    print("== 6c. Reclasificar bodegas FBS->FIN (bodegas/compras son de Finanzas) ==")
    await reclasificar_bodegas.cargar()
    print("== 6d. Etiquetar sistemas asumidos por cada SOP (§7.13) ==")
    await etiquetar_sistemas_sops.etiquetar()
    print("== 7. Categorizar puestos (director/gerente/supervisor/línea) ==")
    await categorizar_puestos.categorizar(recompute=True)
    print("== 8. Reorganizar SOPs por departamento (dueño + afectados) ==")
    await cargar_sop_departamentos.cargar()
    print("== 9. SOPs nuevos para departamentos nuevos (Spa/Lavandería/etc.) ==")
    await cargar_sops_nuevos.cargar()
    print("== 10. SOPs de política de Amarena (contabilidad): marcar + crear ==")
    await cargar_sops_amarena.cargar()
    # NOTA: las propiedades arrancan EN BLANCO. Cada hotel se arma gradualmente desde el
    # Armador (UI). Los loaders cargar_asignaciones_cwl / cargar_asignaciones_amarena quedan
    # disponibles como utilidades manuales, pero YA NO corren en la ingesta por defecto
    # (decisión del owner 2026-07-05: asignar poco a poco).
    print("== Ingesta completa (propiedades en blanco) ==")


if __name__ == "__main__":
    asyncio.run(main())
