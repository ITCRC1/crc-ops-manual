"""Pruebas de los catálogos de solo-lectura (§8.4)."""

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ADMIN_PASS = "CambiarCRC2026!"


async def _headers(client):
    r = await client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_requiere_auth(client):
    assert (await client.get("/api/catalogos/areas")).status_code == 403


async def test_areas(client):
    h = await _headers(client)
    r = await client.get("/api/catalogos/areas", headers=h)
    assert r.status_code == 200
    codigos = {a["codigo"] for a in r.json()}
    assert {"FIN", "GOV", "HR"}.issubset(codigos)


async def test_propiedades(client):
    h = await _headers(client)
    r = await client.get("/api/catalogos/propiedades", headers=h)
    assert r.status_code == 200
    assert any(p["codigo"] == "CWL" for p in r.json())


async def test_departamentos_y_sistemas(client):
    h = await _headers(client)
    r_dep = await client.get("/api/catalogos/departamentos", headers=h)
    assert r_dep.status_code == 200
    # los departamentos exponen su división (puede ser null en el ápice)
    assert all("division_id" in d for d in r_dep.json())
    r = await client.get("/api/catalogos/sistemas", headers=h)
    assert r.status_code == 200
    assert any(s["codigo"] == "OPERA" for s in r.json())


async def test_divisiones(client):
    h = await _headers(client)
    r = await client.get("/api/catalogos/divisiones", headers=h)
    assert r.status_code == 200
    porcod = {d["codigo"]: d for d in r.json()}
    # las 4 divisiones funcionales existen y son raíz
    for cod in ("OPS", "DMV", "DFIN", "DRH"):
        assert cod in porcod and porcod[cod]["parent_id"] is None
    # las subdivisiones de Operaciones cuelgan de OPS
    assert porcod["SD-HAB"]["parent_id"] == porcod["OPS"]["id"]
    assert porcod["SD-AYB"]["parent_id"] == porcod["OPS"]["id"]
    assert porcod["SD-MNT"]["parent_id"] == porcod["OPS"]["id"]
