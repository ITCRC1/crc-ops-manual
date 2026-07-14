"""Pruebas del núcleo de autenticación (E4.1). Requieren la DB con el admin sembrado."""

import pytest

from app.core.rate_limit import _intentos

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ADMIN_PASS = "CambiarCRC2026!"


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    _intentos.clear()
    yield
    _intentos.clear()


async def _login(client, password=ADMIN_PASS):
    return await client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": password})


async def test_login_ok_devuelve_tokens(client):
    r = await _login(client)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["access_token"] and data["refresh_token"]
    assert data["token_type"] == "bearer"


async def test_login_password_incorrecto(client):
    r = await _login(client, "malo")
    assert r.status_code == 401


async def test_me_requiere_token(client):
    assert (await client.get("/api/auth/me")).status_code == 403  # sin bearer


async def test_me_con_token_ok(client):
    tok = (await _login(client)).json()["access_token"]
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"].lower() == ADMIN_EMAIL.lower()
    assert any(rol["rol"] == "super_admin" for rol in body["roles"])


async def test_refresh_rota_token(client):
    refresh = (await _login(client)).json()["refresh_token"]
    r = await client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200, r.text
    assert r.json()["access_token"]


async def test_refresh_token_invalido(client):
    r = await client.post("/api/auth/refresh", json={"refresh_token": "no-válido"})
    assert r.status_code == 401


async def test_access_token_no_sirve_como_refresh(client):
    access = (await _login(client)).json()["access_token"]
    r = await client.post("/api/auth/refresh", json={"refresh_token": access})
    assert r.status_code == 401


async def test_rate_limit_login(client):
    # el límite es 10/5min; el intento 11 debe cortar con 429
    for _ in range(10):
        await _login(client, "malo")
    r = await _login(client, "malo")
    assert r.status_code == 429
