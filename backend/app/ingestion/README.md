# Pipeline de ingesta y reconciliación (Etapa 3)

Reconcilia el **índice curado de 74 SOPs** (`SOP_MASTER_Corcovado_74_FIXED.xlsx`) con el
**manual desarrollado** (`Manual_Sop___Hotel_Corcovado_FINAL__SOP_.docx`, ~150 SOPs con 9 campos).

**Regla central (§10.3):** el emparejamiento se hace por **NOMBRE/SIGNIFICADO, nunca por código.**
De 57 códigos comunes, 36 apuntan a un SOP distinto → unir por código corrompería ~60%.

## Pasos

1. **`parse_fuentes.py`** (determinístico) — `python -m app.ingestion.parse_fuentes`
   Lee `seed/source/` y escribe en `seed/ingesta/`:
   - `excel_index.json` — 74 SOPs curados (codigo, nombre, area, prefijo).
   - `word_index.json` — 150 SOPs del manual **con cuerpo real** (excluye 2 títulos sin desarrollar).
   - `word_bodies.json` — los 9 campos de cada SOP del manual.

2. **Emparejamiento semántico** (workflow LLM con verificación adversarial).
   Los 52 match por nombre idéntico se resuelven determinísticamente; los 22 ambiguos
   (renombres, divisiones, fusiones) los resuelve un workflow: un agente propone y un
   verificador adversarial refuta/corrige cada uno; más un auditor de los 52 exactos.
   El resultado (congelado) vive en `seed/ingesta/reconciliation_matches.json`.

3. **`construir_reporte.py`** (determinístico) — `python -m app.ingestion.construir_reporte`
   Combina los tres artefactos y produce **`seed/reconciliation_report.csv`** con columnas:
   `codigo_excel, nombre_excel, area, codigo_word, nombre_word_emparejado, confianza,
   estado, conflicto_codigo, tipo_relacion, nota`.

## Estados

| estado | significado |
|--------|-------------|
| `emparejado` | 1:1 limpio por nombre |
| `conflicto` | 1:1 pero el código del Excel colisiona con otro SOP del Word (o auditoría lo marcó dudoso) |
| `division` | un SOP del Word que el Excel separó en varios |
| `fusion` | un SOP del Excel que agrupa varios del Word |
| `solo_excel` | SOP del índice curado **sin cuerpo** en el manual |
| `solo_word` | SOP desarrollado en el manual, ausente del índice curado |

## PUNTO DE APROBACIÓN

Tras revisar `reconciliation_report.csv`, la carga de cuerpos en `sop_master` (estado inicial
`borrador`) se ejecuta solo con aprobación explícita (§10.5).
