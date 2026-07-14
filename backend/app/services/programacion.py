"""Expansión de recurrencias y export iCalendar del calendario consolidado.

La 'fecha de ejecución' (`prog.fecha`) es el ancla: primera ocurrencia y punto desde
el que se deriva la cadencia. Puro (sin DB ni FastAPI) para testear la lógica de
fechas y el formato .ics de forma aislada."""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

# Cota dura de expansión para que un rango absurdo no genere millones de fechas.
MAX_DIAS_RANGO = 400

# Cadencias basadas en un intervalo fijo de días.
_INTERVALO_DIAS = {"diaria": 1, "semanal": 7, "quincenal": 14}
# Cadencias basadas en un paso de meses (mismo día de mes que el ancla).
_INTERVALO_MESES = {"mensual": 1, "trimestral": 3, "anual": 12}


@dataclass
class Ocurrencia:
    """Una instancia concreta de una actividad programada en el calendario."""

    programacion_id: str
    sop_id: str
    sop_codigo: str
    sop_nombre: str
    titulo: str
    descripcion: str | None
    fecha: date
    hora: time | None
    dia_completo: bool
    responsable: str | None


def _ultimo_dia(anio: int, mes: int) -> int:
    return monthrange(anio, mes)[1]


def _tipo(prog) -> str:
    t = prog.tipo_recurrencia
    return t.value if hasattr(t, "value") else str(t)


def _sumar_meses(ancla: date, meses: int) -> date:
    """Ancla + N meses, acotando el día al último del mes destino."""
    total = (ancla.year * 12 + (ancla.month - 1)) + meses
    anio, mes = divmod(total, 12)
    mes += 1
    return date(anio, mes, min(ancla.day, _ultimo_dia(anio, mes)))


def expandir_ocurrencias(prog, desde: date, hasta: date) -> list[date]:
    """Fechas en que la programación `prog` ocurre dentro de [desde, hasta].

    Todas las ocurrencias parten de la fecha de ejecución (ancla) y respetan el
    tope opcional `fecha_fin`."""
    ancla = prog.fecha
    if ancla is None or desde > hasta:
        return []
    tipo = _tipo(prog)

    if tipo == "unica":
        return [ancla] if desde <= ancla <= hasta else []

    hi = hasta
    if prog.fecha_fin and prog.fecha_fin < hi:
        hi = prog.fecha_fin
    lo = max(desde, ancla)  # nunca antes del ancla
    if lo > hi:
        return []

    out: list[date] = []
    if tipo in _INTERVALO_DIAS:
        paso = _INTERVALO_DIAS[tipo]
        atraso = (lo - ancla).days
        saltos = (atraso + paso - 1) // paso if atraso > 0 else 0  # ceil
        d = ancla + timedelta(days=saltos * paso)
        while d <= hi:
            out.append(d)
            d += timedelta(days=paso)
    elif tipo in _INTERVALO_MESES:
        paso = _INTERVALO_MESES[tipo]
        k = 0
        while True:
            d = _sumar_meses(ancla, k * paso)
            if d > hi:
                break
            if d >= lo:
                out.append(d)
            k += 1
    return out


# --- iCalendar (.ics) ---


def _escape(texto: str) -> str:
    return (
        texto.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _rrule(prog) -> str | None:
    """RRULE anclada al DTSTART (= fecha de ejecución); no necesita BYDAY/BYMONTHDAY."""
    tipo = _tipo(prog)
    reglas = {
        "diaria": "FREQ=DAILY",
        "semanal": "FREQ=WEEKLY",
        "quincenal": "FREQ=WEEKLY;INTERVAL=2",
        "mensual": "FREQ=MONTHLY",
        "trimestral": "FREQ=MONTHLY;INTERVAL=3",
        "anual": "FREQ=YEARLY",
    }
    base = reglas.get(tipo)
    if base is None:
        return None
    if prog.fecha_fin:
        base += f";UNTIL={prog.fecha_fin.strftime('%Y%m%d')}T235959Z"
    return "RRULE:" + base


def _vevento(prog, sop_codigo: str, sop_nombre: str, dtstamp: str, tz: str) -> list[str]:
    ancla = prog.fecha
    if ancla is None:
        return []
    resumen = f"[{sop_codigo}] {prog.titulo}"
    desc_parts = [f"SOP: {sop_codigo} — {sop_nombre}"]
    if prog.descripcion:
        desc_parts.append(prog.descripcion)
    if prog.responsable_texto:
        desc_parts.append(f"Responsable: {prog.responsable_texto}")
    descripcion = "\n".join(desc_parts)

    lineas = ["BEGIN:VEVENT", f"UID:{prog.id}@crc-ops-manual", f"DTSTAMP:{dtstamp}"]
    if prog.hora is not None:
        ini = datetime.combine(ancla, prog.hora)
        fin = ini + timedelta(hours=1)
        lineas.append(f"DTSTART;TZID={tz}:{ini.strftime('%Y%m%dT%H%M%S')}")
        lineas.append(f"DTEND;TZID={tz}:{fin.strftime('%Y%m%dT%H%M%S')}")
    else:
        lineas.append(f"DTSTART;VALUE=DATE:{ancla.strftime('%Y%m%d')}")
        lineas.append(f"DTEND;VALUE=DATE:{(ancla + timedelta(days=1)).strftime('%Y%m%d')}")
    rrule = _rrule(prog)
    if rrule:
        lineas.append(rrule)
    lineas.append(f"SUMMARY:{_escape(resumen)}")
    lineas.append(f"DESCRIPTION:{_escape(descripcion)}")
    if prog.hora is not None:
        lineas += [
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{_escape(resumen)}",
            "TRIGGER:-PT1H",
            "END:VALARM",
        ]
    lineas.append("END:VEVENT")
    return lineas


def generar_ics(items: list[tuple], dtstamp: datetime, tz: str = "America/Costa_Rica") -> str:
    """Genera un documento iCalendar con un VEVENT (recurrente vía RRULE) por programación.

    `items` = lista de (prog, sop_codigo, sop_nombre)."""
    stamp = dtstamp.strftime("%Y%m%dT%H%M%SZ")
    lineas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//The Costa Rica Collection//CRC Ops Manual//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Calendario CRC Ops Manual",
    ]
    for prog, sop_codigo, sop_nombre in items:
        lineas += _vevento(prog, sop_codigo, sop_nombre, stamp, tz)
    lineas.append("END:VCALENDAR")
    return "\r\n".join(lineas) + "\r\n"
