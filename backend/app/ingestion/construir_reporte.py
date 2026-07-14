"""Etapa 3 — Construcción del reporte de reconciliación (§10.3, §10.4).

Combina de forma determinística:
  - seed/ingesta/excel_index.json          (74 SOPs curados)
  - seed/ingesta/word_index.json           (152 SOPs del manual Word)
  - seed/ingesta/reconciliation_matches.json  (decisiones de emparejamiento semántico
        producidas por el workflow LLM con verificación adversarial; ver README)
El emparejamiento por nombre exacto (52) se recalcula aquí; los 22 ambiguos vienen
del workflow. Escribe seed/reconciliation_report.csv.

Uso:
    python -m app.ingestion.construir_reporte
"""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
ING = RAIZ / "seed" / "ingesta"
CSV_OUT = RAIZ / "seed" / "reconciliation_report.csv"

COLS = ["codigo_excel", "nombre_excel", "area", "codigo_word", "nombre_word_emparejado",
        "confianza", "estado", "conflicto_codigo", "tipo_relacion", "nota"]


def cargar() -> tuple[list, list, dict]:
    excel = json.loads((ING / "excel_index.json").read_text(encoding="utf-8"))
    word = json.loads((ING / "word_index.json").read_text(encoding="utf-8"))
    wf = json.loads((ING / "reconciliation_matches.json").read_text(encoding="utf-8"))
    return excel, word, wf


def construir() -> list[dict]:
    excel, word, wf = cargar()
    word_nombre = {w["codigo"]: w["nombre"] for w in word}
    word_norm = defaultdict(list)
    for w in word:
        word_norm[w["norm"]].append(w["codigo"])
    word_codes = set(word_nombre)

    # 1) Emparejamientos por nombre exacto (recalculados) + ambiguos (del workflow)
    match = {}
    for e in excel:
        if e["norm"] in word_norm:
            wc = word_norm[e["norm"]][0]
            match[e["codigo"]] = {
                "word": [wc], "tipo": "igual", "confianza": "alta",
                "razon": "Nombre idéntico (match exacto normalizado).",
            }
    for r in wf["resultados"]:
        v = r["verdicto"]
        match[r["codigo"]] = {
            "word": v["word_matches_final"], "tipo": v["tipo_relacion_final"],
            "confianza": v["confianza"], "razon": v["razon"],
        }

    reverse = defaultdict(list)
    for ec, m in match.items():
        for wc in m["word"]:
            reverse[wc].append(ec)
    sospechoso = {s["excel_codigo"]: s["problema"] for s in wf["auditoria"]["sospechosos"]}

    filas = []
    for e in excel:
        ec = e["codigo"]
        m = match.get(ec, {"word": [], "tipo": "ninguno", "confianza": "baja", "razon": ""})
        words, tipo = m["word"], m["tipo"]
        conflicto_codigo = ec in word_codes and ec not in words

        if not words or tipo == "ninguno":
            estado = "solo_excel"
        elif len(words) >= 2 or tipo == "superconjunto_de_words":
            estado = "fusion"
        elif any(len(reverse[wc]) >= 2 for wc in words) or tipo == "subconjunto_de_word":
            estado = "division"
        elif conflicto_codigo:
            estado = "conflicto"
        else:
            estado = "emparejado"

        nota = m.get("razon", "")[:200]
        if ec in sospechoso:
            estado = "conflicto"  # la auditoría adversarial detectó posible falso positivo
            nota = "AUDITORÍA: " + sospechoso[ec]

        filas.append({
            "codigo_excel": ec, "nombre_excel": e["nombre"], "area": e["area"],
            "codigo_word": ";".join(words),
            "nombre_word_emparejado": " | ".join(word_nombre.get(w, "?") for w in words),
            "confianza": m["confianza"], "estado": estado,
            "conflicto_codigo": "sí" if conflicto_codigo else "no",
            "tipo_relacion": tipo, "nota": nota,
        })

    # 2) solo_word: SOPs del Word que ningún Excel reclamó
    for w in word:
        if w["codigo"] not in reverse:
            filas.append({
                "codigo_excel": "", "nombre_excel": "", "area": "",
                "codigo_word": w["codigo"], "nombre_word_emparejado": w["nombre"],
                "confianza": "alta", "estado": "solo_word", "conflicto_codigo": "no",
                "tipo_relacion": "", "nota": "SOP del manual Word ausente del índice curado de 74.",
            })
    return filas


def main() -> None:
    filas = construir()
    with open(CSV_OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(filas)
    est = Counter(f["estado"] for f in filas)
    cf = Counter(f["conflicto_codigo"] for f in filas if f["codigo_excel"])
    print(f"CSV: {CSV_OUT}")
    print(f"filas: {len(filas)}  por estado: {dict(est)}")
    print(f"conflicto_codigo (74 Excel): {dict(cf)}")


if __name__ == "__main__":
    main()
