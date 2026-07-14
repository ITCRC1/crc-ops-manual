"""Pruebas de programación de SOPs y calendario consolidado.

Cubre la lógica pura de expansión de recurrencias (ancladas a la fecha de ejecución)
y el formato .ics (sin DB), más el ciclo CRUD, el calendario y el export por API.
Requiere DB sembrada + ingesta."""

from datetime import date, datetime, time
from types import SimpleNamespace

import pytest

from app.services.programacion import expandir_ocurrencias, generar_ics

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ADMIN_PASS = "CambiarCRC2026!"


def _prog(**kw):
    base = dict(
        id="00000000-0000-0000-0000-000000000001",
        tipo_recurrencia="unica", fecha=None, hora=None, fecha_fin=None,
        titulo="X", descripcion=None, responsable_texto=None, responsable_puesto_id=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


# --- Lógica pura de expansión (ancla = fecha de ejecución) ---


def test_unica_dentro_y_fuera_de_rango():
    p = _prog(tipo_recurrencia="unica", fecha=date(2027, 3, 10))
    assert expandir_ocurrencias(p, date(2027, 3, 1), date(2027, 3, 31)) == [date(2027, 3, 10)]
    assert expandir_ocurrencias(p, date(2027, 4, 1), date(2027, 4, 30)) == []


def test_diaria_desde_el_ancla():
    p = _prog(tipo_recurrencia="diaria", fecha=date(2027, 1, 3))
    fechas = expandir_ocurrencias(p, date(2027, 1, 1), date(2027, 1, 7))
    # no hay ocurrencias antes del ancla
    assert fechas == [date(2027, 1, d) for d in (3, 4, 5, 6, 7)]


def test_semanal_cae_en_el_mismo_dia_que_el_ancla():
    # 2027-01-04 es lunes
    p = _prog(tipo_recurrencia="semanal", fecha=date(2027, 1, 4))
    fechas = expandir_ocurrencias(p, date(2027, 1, 1), date(2027, 1, 31))
    assert fechas == [date(2027, 1, d) for d in (4, 11, 18, 25)]


def test_quincenal_cada_14_dias():
    p = _prog(tipo_recurrencia="quincenal", fecha=date(2027, 1, 4))
    fechas = expandir_ocurrencias(p, date(2027, 1, 1), date(2027, 2, 28))
    assert fechas == [date(2027, 1, 4), date(2027, 1, 18), date(2027, 2, 1), date(2027, 2, 15)]


def test_mensual_acota_dia_al_ultimo_del_mes():
    p = _prog(tipo_recurrencia="mensual", fecha=date(2027, 1, 31))
    fechas = expandir_ocurrencias(p, date(2027, 1, 1), date(2027, 3, 31))
    assert fechas == [date(2027, 1, 31), date(2027, 2, 28), date(2027, 3, 31)]


def test_trimestral_cada_3_meses():
    p = _prog(tipo_recurrencia="trimestral", fecha=date(2027, 1, 15))
    fechas = expandir_ocurrencias(p, date(2027, 1, 1), date(2027, 12, 31))
    assert fechas == [date(2027, 1, 15), date(2027, 4, 15), date(2027, 7, 15), date(2027, 10, 15)]


def test_anual_mismo_mes_y_dia():
    p = _prog(tipo_recurrencia="anual", fecha=date(2027, 12, 25))
    fechas = expandir_ocurrencias(p, date(2027, 1, 1), date(2028, 12, 31))
    assert fechas == [date(2027, 12, 25), date(2028, 12, 25)]


def test_fecha_fin_acota_la_repeticion():
    p = _prog(tipo_recurrencia="diaria", fecha=date(2027, 1, 3), fecha_fin=date(2027, 1, 5))
    fechas = expandir_ocurrencias(p, date(2027, 1, 1), date(2027, 1, 31))
    assert fechas == [date(2027, 1, 3), date(2027, 1, 4), date(2027, 1, 5)]


def test_ics_recurrente_tiene_rrule_y_escapa_texto():
    p = _prog(
        id="abc", tipo_recurrencia="quincenal", fecha=date(2027, 1, 4), hora=time(9, 0),
        titulo="Pago; proveedores", descripcion="línea1\nlínea2", responsable_texto="Contador",
    )
    ics = generar_ics([(p, "FIN-0001", "Pagos")], dtstamp=datetime(2027, 1, 1, 12, 0, 0))
    assert "BEGIN:VCALENDAR" in ics and "END:VCALENDAR" in ics
    assert "RRULE:FREQ=WEEKLY;INTERVAL=2" in ics
    assert "UID:abc@crc-ops-manual" in ics
    assert "DTSTART;TZID=America/Costa_Rica:20270104T090000" in ics
    assert "Pago\\; proveedores" in ics  # ';' escapado
    assert "BEGIN:VALARM" in ics  # tiene hora → recordatorio
    assert ics.endswith("\r\n")


def test_ics_unica_sin_rrule_y_dia_completo():
    p = _prog(id="xyz", tipo_recurrencia="unica", fecha=date(2027, 5, 20), hora=None, titulo="Inventario")
    ics = generar_ics([(p, "FIN-0002", "Conteo")], dtstamp=datetime(2027, 1, 1, 0, 0, 0))
    assert "RRULE" not in ics
    assert "DTSTART;VALUE=DATE:20270520" in ics
    assert "BEGIN:VALARM" not in ics  # día completo → sin alarma


def test_ics_trimestral_usa_interval_3():
    p = _prog(id="t1", tipo_recurrencia="trimestral", fecha=date(2027, 1, 15), titulo="Revisión")
    ics = generar_ics([(p, "FIN-0003", "Rev")], dtstamp=datetime(2027, 1, 1, 0, 0, 0))
    assert "RRULE:FREQ=MONTHLY;INTERVAL=3" in ics


# --- API ---


async def _headers(client):
    r = await client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _crear_sop(client, h) -> str:
    r = await client.post("/api/sops", json={"area_codigo": "GOV", "nombre": "SOP con agenda"}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_programacion_requiere_auth(client):
    assert (await client.get("/api/calendario?desde=2027-01-01&hasta=2027-01-31")).status_code == 403


async def test_ciclo_crud_programacion(client):
    h = await _headers(client)
    sop_id = await _crear_sop(client, h)
    try:
        # crear una actividad quincenal con fecha de ejecución
        r = await client.post(
            f"/api/sops/{sop_id}/programacion",
            json={
                "titulo": "Pago a proveedores", "tipo_recurrencia": "quincenal",
                "fecha": "2027-01-04", "hora": "09:00:00", "responsable_texto": "Finanzas",
            },
            headers=h,
        )
        assert r.status_code == 201, r.text
        prog = r.json()
        assert prog["orden"] == 0 and prog["tipo_recurrencia"] == "quincenal"
        assert prog["fecha"] == "2027-01-04"

        # listar
        lista = (await client.get(f"/api/sops/{sop_id}/programacion", headers=h)).json()
        assert len(lista) == 1

        # editar
        r_ed = await client.put(
            f"/api/sops/{sop_id}/programacion/{prog['id']}",
            json={"titulo": "Pago a proveedores (revisado)"}, headers=h,
        )
        assert r_ed.status_code == 200 and "revisado" in r_ed.json()["titulo"]

        # el calendario del bimestre lo expande cada 14 días
        cal = (
            await client.get("/api/calendario?desde=2027-01-01&hasta=2027-02-28", headers=h)
        ).json()
        mios = [e for e in cal["eventos"] if e["sop_id"] == sop_id]
        assert [e["fecha"] for e in mios] == ["2027-01-04", "2027-01-18", "2027-02-01", "2027-02-15"]

        # export .ics incluye el evento recurrente quincenal
        ics = await client.get(f"/api/calendario/export.ics?sop_id={sop_id}", headers=h)
        assert ics.status_code == 200
        assert "text/calendar" in ics.headers["content-type"]
        assert "RRULE:FREQ=WEEKLY;INTERVAL=2" in ics.text

        # borrar
        assert (
            await client.delete(f"/api/sops/{sop_id}/programacion/{prog['id']}", headers=h)
        ).status_code == 204
        assert len((await client.get(f"/api/sops/{sop_id}/programacion", headers=h)).json()) == 0
    finally:
        await client.delete(f"/api/sops/{sop_id}", headers=h)


async def test_fecha_obligatoria(client):
    h = await _headers(client)
    sop_id = await _crear_sop(client, h)
    try:
        # sin fecha de ejecución → 422
        r = await client.post(
            f"/api/sops/{sop_id}/programacion",
            json={"titulo": "Sin fecha", "tipo_recurrencia": "mensual"}, headers=h,
        )
        assert r.status_code == 422
        # fecha_fin anterior a la fecha de ejecución → 422
        r2 = await client.post(
            f"/api/sops/{sop_id}/programacion",
            json={"titulo": "Mal fin", "tipo_recurrencia": "mensual",
                  "fecha": "2027-06-01", "fecha_fin": "2027-05-01"},
            headers=h,
        )
        assert r2.status_code == 422
    finally:
        await client.delete(f"/api/sops/{sop_id}", headers=h)


async def test_calendario_rango_invalido(client):
    h = await _headers(client)
    r = await client.get("/api/calendario?desde=2027-02-01&hasta=2027-01-01", headers=h)
    assert r.status_code == 400
