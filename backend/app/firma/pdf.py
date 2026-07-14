"""Generación del PDF del documento controlado (ReportLab) y su hash SHA-256 (§4, A5).

También genera el PDF exportable de la versión vigente (incluye la capa SMART si existe),
pensado para compartir por fuera y pedir validación en la plataforma (no es el controlado)."""

import hashlib
import io
from datetime import datetime
from xml.sax.saxutils import escape as _xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

CAMPOS_9 = [
    ("Propósito", "proposito"),
    ("Evaluación de Riesgos", "evaluacion_riesgos"),
    ("Controles Existentes", "controles_existentes"),
    ("Procedimiento Detallado", "procedimiento"),
    ("Responsables", "responsables"),
    ("Evidencia / Reportes", "evidencia"),
    ("Frecuencia de Revisión", "frecuencia_revision"),
]


def _procedimiento_texto(valor) -> str:
    if isinstance(valor, dict):
        secciones = valor.get("secciones") or valor.get("contenido") or []
        if isinstance(secciones, list):
            return "\n".join(str(s) for s in secciones)
        return str(valor)
    return str(valor or "")


def generar_pdf_controlado(sop: dict, firmas: list[dict]) -> tuple[bytes, str]:
    """Genera el PDF del SOP firmado y devuelve (bytes, sha256_hex).

    sop: dict con codigo, nombre, area, tipo, version, y los 9 campos.
    firmas: lista de dicts con firmante, fecha_hora, metodo, ip.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title=f"{sop['codigo']} {sop['nombre']}",
    )
    ss = getSampleStyleSheet()
    h_org = ParagraphStyle("org", parent=ss["Title"], fontSize=13, textColor=colors.HexColor("#155E6D"))
    h_sec = ParagraphStyle("sec", parent=ss["Heading2"], fontSize=11, textColor=colors.HexColor("#1F7A8C"))
    cuerpo = ParagraphStyle("cuerpo", parent=ss["BodyText"], fontSize=9, leading=13)

    def p(txt, style):
        return Paragraph((txt or "").replace("\n", "<br/>"), style)

    el = [
        p("The Costa Rica Collection — Documento Controlado", h_org),
        p(f"<b>{sop['codigo']}</b> — {sop['nombre']}", ss["Heading1"]),
        p(f"Área: {sop.get('area', '')} · Tipo: {sop.get('tipo', '')} · "
          f"Versión: {sop.get('version', 1)}", cuerpo),
        Spacer(1, 0.4 * cm),
    ]
    for etiqueta, clave in CAMPOS_9:
        valor = _procedimiento_texto(sop.get(clave)) if clave == "procedimiento" else sop.get(clave)
        el.append(p(etiqueta, h_sec))
        el.append(p(str(valor or "—"), cuerpo))
        el.append(Spacer(1, 0.25 * cm))

    el.append(Spacer(1, 0.4 * cm))
    el.append(p("Firmas electrónicas", h_sec))
    filas = [["Firmante", "Fecha/Hora", "Método", "IP"]]
    for f in firmas:
        filas.append([
            f.get("firmante", ""), f.get("fecha_hora", ""),
            f.get("metodo", ""), f.get("ip", ""),
        ])
    tabla = Table(filas, colWidths=[6 * cm, 5 * cm, 2.5 * cm, 3 * cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#155E6D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DEE5E2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    el.append(tabla)
    el.append(Spacer(1, 0.3 * cm))
    el.append(p(f"Documento controlado emitido el {datetime.now().strftime('%Y-%m-%d %H:%M')}. "
                "La versión firmada es inmutable; su integridad se verifica por hash SHA-256.", cuerpo))

    doc.build(el)
    pdf = buf.getvalue()
    return pdf, hashlib.sha256(pdf).hexdigest()


# --- PDF exportable de la versión vigente (incluye capa SMART) -------------------------

_USABLE = 17.4 * cm  # ancho útil letter con márgenes de 2cm


def _anchos(pesos: list[float]) -> list[float]:
    tot = sum(pesos) or 1
    return [_USABLE * p / tot for p in pesos]


def generar_pdf_sop(sop: dict, meta: dict) -> bytes:
    """PDF de la versión actual del SOP para compartir y pedir validación.

    Refleja lo que se ve en la ficha: si hay capa SMART, renderiza las 18 secciones +
    apéndices; si no, los 9 campos base. NO es el documento controlado (ese lleva firmas y
    hash). Cuando el SOP no está firmado, estampa un sello de BORRADOR y un enlace a la
    plataforma para validar. `sop` trae los 9 campos + `smart`; `meta` trae encabezado
    (codigo, nombre, estado, version, area, departamento, afectados) y `url` de la ficha.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title=f"{meta['codigo']} {meta['nombre']}",
    )
    ss = getSampleStyleSheet()
    h_org = ParagraphStyle("org", parent=ss["Title"], fontSize=13, textColor=colors.HexColor("#155E6D"))
    h_sec = ParagraphStyle("sec", parent=ss["Heading2"], fontSize=10.5, textColor=colors.HexColor("#1F7A8C"))
    cuerpo = ParagraphStyle("cuerpo", parent=ss["BodyText"], fontSize=9, leading=13)
    pie = ParagraphStyle("pie", parent=ss["BodyText"], fontSize=7.5, leading=10,
                         textColor=colors.HexColor("#6B7A76"))
    th = ParagraphStyle("th", parent=ss["BodyText"], fontSize=7.5, leading=9,
                        textColor=colors.white, fontName="Helvetica-Bold")
    td = ParagraphStyle("td", parent=ss["BodyText"], fontSize=7.5, leading=9.5)

    def p(txt, style):
        safe = _xml_escape(str(txt if txt is not None else "")).replace("\n", "<br/>")
        return Paragraph(safe or "—", style)

    def tabla(columnas, filas, pesos):
        if not filas:
            return None
        data = [[Paragraph(_xml_escape(c), th) for c in columnas]]
        for fila in filas:
            data.append([p(v if (v is not None and str(v).strip()) else "—", td) for v in fila])
        t = Table(data, colWidths=_anchos(pesos), repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F7A8C")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DEE5E2")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F8F7")]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return t

    def tiene(v):
        return (len(v) > 0) if isinstance(v, list | str) else bool(v)

    el = [
        p("The Costa Rica Collection — Manual de Operaciones", h_org),
        # Título con negrita: escapamos solo las partes dinámicas y dejamos <b> como markup
        # (no pasa por p(), que escaparía las etiquetas).
        Paragraph(f"<b>{_xml_escape(meta['codigo'])}</b> — {_xml_escape(meta['nombre'])}", ss["Heading1"]),
        p(f"Estado: {meta.get('estado', '')} · Versión: {meta.get('version', 1)} · "
          f"Área: {meta.get('area', '')} · Departamento: {meta.get('departamento', '—')}", cuerpo),
    ]
    if meta.get("afectados"):
        el.append(p(f"También afecta a: {', '.join(meta['afectados'])}", cuerpo))

    # Sello de borrador + llamado a validar en la plataforma (si no está firmado).
    if meta.get("estado") != "firmado":
        url = meta.get("url", "")
        aviso = Table([[Paragraph(
            "<b>BORRADOR — DOCUMENTO PARA VALIDACIÓN.</b> No es un documento controlado ni "
            "firmado. Para revisar, comentar o validar este procedimiento, ingrese a la "
            f"plataforma: {_xml_escape(url)}",
            ParagraphStyle("av", parent=cuerpo, fontSize=8.5, textColor=colors.HexColor("#8A5A00")),
        )]], colWidths=[_USABLE])
        aviso.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF6E5")),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#E0B050")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        el += [Spacer(1, 0.3 * cm), aviso]
    el.append(Spacer(1, 0.4 * cm))

    smart = sop.get("smart")
    if smart:
        pend = smart.get("pendiente_confirmar") or []
        if pend:
            el.append(p("Información pendiente de confirmar (Apéndice F)", h_sec))
            el.append(p("<br/>".join(f"• {_xml_escape(str(s))}" for s in pend), cuerpo))
            el.append(Spacer(1, 0.3 * cm))
        if tiene(smart.get("resumen_ejecutivo")):
            el.append(p("Resumen ejecutivo", h_sec))
            el.append(p(smart["resumen_ejecutivo"], cuerpo))
            el.append(Spacer(1, 0.25 * cm))

        def sec(n, titulo, contenido):
            if contenido is None:
                return
            el.append(p(f"{n}  {titulo}", h_sec))
            if isinstance(contenido, str):
                el.append(p(contenido, cuerpo))
            else:
                el.append(contenido)
            el.append(Spacer(1, 0.25 * cm))

        if tiene(smart.get("objetivo")):
            sec("3.", "Objetivo", smart["objetivo"])
        if tiene(smart.get("alcance")):
            sec("4.", "Alcance", smart["alcance"])
        if tiene(smart.get("definiciones")):
            sec("5.", "Definiciones clave", tabla(
                ["Término", "Definición"],
                [[d.get("termino"), d.get("definicion")] for d in smart["definiciones"]], [3, 7]))
        if tiene(smart.get("raci")):
            sec("6.", "Responsables / Matriz RACI", tabla(
                ["Actividad", "R", "A", "C", "I"],
                [[r.get("actividad"), r.get("responsible"), r.get("accountable"),
                  r.get("consulted"), r.get("informed")] for r in smart["raci"]], [4, 2, 2, 2, 2]))
        if tiene(smart.get("frecuencia_deadlines")):
            sec("7.", "Frecuencia y deadlines", smart["frecuencia_deadlines"])
        if tiene(smart.get("sistemas")):
            sec("8.", "Sistemas y herramientas", ", ".join(str(s) for s in smart["sistemas"]))
        if tiene(smart.get("documentos_relacionados")):
            sec("9.", "Documentos, reportes y formatos", tabla(
                ["Documento", "Responsable", "Frecuencia", "Ubicación", "Retención"],
                [[d.get("documento"), d.get("responsable"), d.get("frecuencia"),
                  d.get("ubicacion"), d.get("retencion")] for d in smart["documentos_relacionados"]],
                [3, 2, 2, 2, 2]))
        if tiene(smart.get("procedimiento")):
            filas = []
            for s in smart["procedimiento"]:
                filas.append([
                    s.get("paso"),
                    f"{s.get('nombre', '') or ''}\n{s.get('accion', '') or ''}".strip(),
                    s.get("responsable"), s.get("sistema_documento"),
                    s.get("evidencia"), s.get("control"),
                ])
            sec("10.", "Procedimiento paso a paso", tabla(
                ["#", "Acción", "Responsable", "Sistema/doc", "Evidencia", "Control"],
                filas, [0.7, 5, 2.5, 2.2, 2.4, 2.4]))
        if tiene(smart.get("evidencia_requerida")):
            sec("11.", "Evidencia requerida", tabla(
                ["Evidencia", "Responsable", "Revisor", "Archivo", "Retención"],
                [[e.get("evidencia"), e.get("responsable"), e.get("revisor"),
                  e.get("archivo"), e.get("retencion")] for e in smart["evidencia_requerida"]],
                [3, 2, 2, 2, 2]))
        if tiene(smart.get("controles_clave")):
            sec("12.", "Controles clave", tabla(
                ["Control", "Riesgo", "Responsable", "Frecuencia", "Evidencia", "Acción correctiva"],
                [[c.get("control"), c.get("riesgo"), c.get("responsable"), c.get("frecuencia"),
                  c.get("evidencia"), c.get("accion_correctiva")] for c in smart["controles_clave"]],
                [3, 2.5, 2, 2, 2, 2.5]))
        if tiene(smart.get("kpis")):
            sec("13.", "KPIs / criterios de cumplimiento", tabla(
                ["Indicador", "Meta", "Origen"],
                [[k.get("indicador"), k.get("meta"),
                  "Recomendado (validar)" if k.get("recomendado") else "Del SOP original"]
                 for k in smart["kpis"]], [5, 3, 2.5]))
        if tiene(smart.get("riesgos_mitigados")):
            sec("14.", "Riesgos mitigados",
                "<br/>".join(f"• {_xml_escape(str(r))}" for r in smart["riesgos_mitigados"]))
        if tiene(smart.get("excepciones")):
            sec("15.", "Excepciones y escalamiento", tabla(
                ["Excepción", "Escala a", "Aprobador", "Evidencia", "Tiempo máx."],
                [[e.get("excepcion"), e.get("responsable_escalar"), e.get("aprobador"),
                  e.get("evidencia"), e.get("tiempo_maximo")] for e in smart["excepciones"]],
                [3, 2, 2, 2, 2]))
        if tiene(smart.get("archivo_retencion")):
            sec("16.", "Archivo y retención documental", smart["archivo_retencion"])
        if tiene(smart.get("entrenamiento")):
            sec("17.", "Entrenamiento requerido", smart["entrenamiento"])
        if tiene(smart.get("control_versiones")):
            sec("18.", "Revisión, aprobación y control de versiones", tabla(
                ["Versión", "Fecha", "Preparado", "Revisado", "Aprobado", "Cambios", "Próxima rev."],
                [[v.get("version"), v.get("fecha"), v.get("preparado_por"), v.get("revisado_por"),
                  v.get("aprobado_por"), v.get("cambios"), v.get("proxima_revision")]
                 for v in smart["control_versiones"]], [1.4, 1.6, 2, 2, 2, 3.4, 1.8]))
        if tiene(smart.get("checklist")):
            sec("B.", "Checklist de cumplimiento", tabla(
                ["#", "Punto de control", "Cumplido", "Comentarios"],
                [[c.get("n"), c.get("punto"), c.get("cumplido"), c.get("comentarios")]
                 for c in smart["checklist"]], [0.7, 5, 2, 4]))
    else:
        # Sin capa SMART: los 9 campos base.
        for etiqueta, clave in CAMPOS_9:
            valor = _procedimiento_texto(sop.get(clave)) if clave == "procedimiento" else sop.get(clave)
            el.append(p(etiqueta, h_sec))
            el.append(p(str(valor or "—"), cuerpo))
            el.append(Spacer(1, 0.2 * cm))

    el.append(Spacer(1, 0.4 * cm))
    el.append(p(
        f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        + (f" por {meta['generado_por']}" if meta.get("generado_por") else "")
        + f". Refleja la versión vigente en la plataforma al momento de la descarga. "
        f"La versión oficial, editable y firmable vive en {meta.get('url', '')}.", pie))

    doc.build(el)
    return buf.getvalue()
