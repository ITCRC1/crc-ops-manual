"""Pruebas de la búsqueda global (E4.5, §8.16)."""

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ADMIN_PASS = "CambiarCRC2026!"


async def _headers(client):
    r = await client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_requiere_auth(client):
    assert (await client.get("/api/busqueda?q=JD")).status_code == 403


async def test_q_es_obligatorio(client):
    h = await _headers(client)
    assert (await client.get("/api/busqueda", headers=h)).status_code == 422


async def test_busca_descriptores(client):
    h = await _headers(client)
    r = await client.get("/api/busqueda?q=JD&entidad=descriptor&limit=200", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 27
    assert all(i["entidad"] == "descriptor" for i in data["items"])
    assert all(i["area_codigo"] is None for i in data["items"])


async def test_busca_sops_por_area(client):
    h = await _headers(client)
    # el filtro por área excluye descriptores y limita a SOPs/políticas del área
    r = await client.get("/api/busqueda?q=FIN&area=FIN&limit=200", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert all(i["area_codigo"] == "FIN" for i in data["items"])
    assert all(i["entidad"] in ("sop", "politica") for i in data["items"])


async def test_area_inexistente(client):
    h = await _headers(client)
    assert (await client.get("/api/busqueda?q=x&area=NOEXISTE", headers=h)).status_code == 404


async def test_paginacion_rechaza_valores_invalidos(client):
    """offset negativo no debe devolver una página incorrecta (slicing negativo)."""
    h = await _headers(client)
    assert (await client.get("/api/busqueda?q=JD&offset=-3", headers=h)).status_code == 422
    assert (await client.get("/api/busqueda?q=JD&limit=-1", headers=h)).status_code == 422
