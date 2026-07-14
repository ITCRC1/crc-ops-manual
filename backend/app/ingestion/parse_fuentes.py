"""Etapa 3 — Parseo determinístico de las fuentes (§10.1, §10.2).

Lee de seed/source/ y escribe artefactos JSON en seed/ingesta/:
  - excel_index.json  : 74 SOPs del índice curado (codigo, nombre, area, prefijo)
  - word_index.json   : 152 SOPs del manual Word (codigo, nombre) — cuerpos reales, sin TOC
  - word_bodies.json  : los 9 campos de cada SOP del manual Word

Uso:
    python -m app.ingestion.parse_fuentes
"""

import json
import re
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import openpyxl

RAIZ = Path(__file__).resolve().parents[3]
SRC = RAIZ / "seed" / "source"
OUT = RAIZ / "seed" / "ingesta"
NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

EXCEL = SRC / "SOP_MASTER_Corcovado_74_FIXED.xlsx"
MANUAL = SRC / "Manual_Sop___Hotel_Corcovado_FINAL__SOP_.docx"
JOBDESC = SRC / "Job_Descriptions.docx"

JD_RE = re.compile(r"^JOB DESCRIPTION\s*[—–-]\s*(.+)$", re.I)
SEC_RE = re.compile(r"^(\d+)\.\s*(.+)$")
META_RE = re.compile(
    r"Departamento:\s*(.*?)\s*Reporta a:\s*(.*?)(?:\s*Supervisa:\s*(.*))?$", re.I
)

ENC_RE = re.compile(r"^([A-Z]{2,4}-\d{3,4})\s*[–\-—]\s*(.+)$")
CAMPOS = [
    ("codigo", re.compile(r"^\d+\.\s*C[oó]digo", re.I)),
    ("departamento", re.compile(r"^\d+\.\s*Departamento", re.I)),
    ("proposito", re.compile(r"^\d+\.\s*Prop[oó]sito", re.I)),
    ("evaluacion_riesgos", re.compile(r"^\d+\.\s*Evaluaci[oó]n de Riesgos", re.I)),
    ("controles_existentes", re.compile(r"^\d+\.\s*Controles", re.I)),
    ("procedimiento", re.compile(r"^\d+\.\s*Procedimiento", re.I)),
    ("responsables", re.compile(r"^\d+\.\s*Responsables", re.I)),
    ("evidencia", re.compile(r"^\d+\.\s*(Evidencia|Reportes)", re.I)),
    ("frecuencia_revision", re.compile(r"^\d+\.\s*Frecuencia", re.I)),
]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", " y ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_excel() -> list[dict]:
    wb = openpyxl.load_workbook(EXCEL, read_only=True, data_only=True)
    ws = wb["SOP_INDEX"]
    filas = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r or not r[0]:
            continue
        codigo = str(r[0]).strip()
        filas.append({
            "codigo": codigo,
            "nombre": str(r[1]).strip() if r[1] else "",
            "area": str(r[2]).strip() if r[2] else "",
            "prefijo": codigo.split("-")[0],
            "norm": norm(str(r[1]) if r[1] else ""),
        })
    return filas


def _parrafos_word() -> list[str]:
    root = ET.fromstring(zipfile.ZipFile(MANUAL).read("word/document.xml"))
    out = []
    for para in root.iter(NS + "p"):
        out.append("".join(t.text or "" for t in para.iter(NS + "t")).strip())
    return out


def _campo(t: str) -> str | None:
    for clave, rx in CAMPOS:
        if rx.match(t):
            return clave
    return None


def parse_word() -> tuple[list[dict], dict]:
    txt = _parrafos_word()
    # Encabezados de CUERPO: "CODE – Nombre" seguido de "N. Código del SOP" en 4 párrafos
    # Un encabezado es de CUERPO si "N. Código del SOP" aparece poco después (ventana amplia:
    # algunos SOPs tienen párrafos introductorios antes del primer campo).
    body_headers = []
    for i, t in enumerate(txt):
        m = ENC_RE.match(t)
        if m and re.search(r"C[oó]digo del SOP", " || ".join(txt[i + 1 : i + 9]), re.I):
            body_headers.append((i, m.group(1), m.group(2)))

    index, bodies = {}, {}
    for k, (i, code, nombre) in enumerate(body_headers):
        fin = body_headers[k + 1][0] if k + 1 < len(body_headers) else len(txt)
        campos = {c: [] for c, _ in CAMPOS}
        actual = None
        for t in txt[i + 1 : fin]:
            if not t:
                continue
            c = _campo(t)
            if c:
                actual = c
            elif actual:
                campos[actual].append(t)
        index[code] = {"codigo": code, "nombre": nombre, "norm": norm(nombre)}
        bodies[code] = {
            "nombre_word": nombre,
            "departamento": " ".join(campos["departamento"]).strip(),
            "proposito": "\n".join(campos["proposito"]).strip(),
            "evaluacion_riesgos": "\n".join(campos["evaluacion_riesgos"]).strip(),
            "controles_existentes": "\n".join(campos["controles_existentes"]).strip(),
            "procedimiento": campos["procedimiento"],
            "responsables": "\n".join(campos["responsables"]).strip(),
            "evidencia": "\n".join(campos["evidencia"]).strip(),
            "frecuencia_revision": " ".join(campos["frecuencia_revision"]).strip(),
        }
    return list(index.values()), bodies


def parse_jobdesc() -> list[dict]:
    root = ET.fromstring(zipfile.ZipFile(JOBDESC).read("word/document.xml"))
    paras = []
    for para in root.iter(NS + "p"):
        t = "".join(x.text or "" for x in para.iter(NS + "t")).strip()
        if t:
            paras.append(t)
    starts = [i for i, t in enumerate(paras) if JD_RE.match(t)]
    jds = []
    for k, i in enumerate(starts):
        fin = starts[k + 1] if k + 1 < len(starts) else len(paras)
        bloque = paras[i:fin]
        titulo = JD_RE.match(bloque[0]).group(1).strip()
        subtitulo, secciones, actual = "", {}, None
        meta = {"departamento": "", "reporta_a": "", "supervisa": ""}
        for t in bloque[1:]:
            mm = META_RE.search(t)
            if mm and not meta["departamento"]:
                meta = {"departamento": (mm.group(1) or "").strip(),
                        "reporta_a": (mm.group(2) or "").strip(),
                        "supervisa": (mm.group(3) or "").strip()}
                continue
            sm = SEC_RE.match(t)
            if sm:
                actual = sm.group(2).strip()
                secciones[actual] = []
                continue
            if actual is None and not subtitulo and t.startswith("("):
                subtitulo = t.strip("()")
                continue
            if actual:
                secciones[actual].append(t)
        jds.append({
            "codigo": f"JD-{k + 1:03d}", "titulo": titulo, "subtitulo": subtitulo,
            "departamento": meta["departamento"], "reporta_a": meta["reporta_a"],
            "supervisa": meta["supervisa"], "secciones": secciones,
        })
    return jds


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    excel = parse_excel()
    word_index, word_bodies = parse_word()
    jds = parse_jobdesc()
    (OUT / "jds.json").write_text(
        json.dumps(jds, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "excel_index.json").write_text(
        json.dumps(excel, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "word_index.json").write_text(
        json.dumps(word_index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "word_bodies.json").write_text(
        json.dumps(word_bodies, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"excel_index: {len(excel)}  word_index: {len(word_index)}  "
        f"word_bodies: {len(word_bodies)}  jds: {len(jds)}"
    )


if __name__ == "__main__":
    main()
