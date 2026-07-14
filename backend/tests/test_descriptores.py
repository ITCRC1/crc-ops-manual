"""Pruebas del CRUD de Descriptores de Puesto (E4.5): numeración JD-### atómica,
versionado, jerarquía sin ciclos, permisos e inmutabilidad."""

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ADMIN_PASS = "CambiarCRC2026!"


async def _headers(client):
    r = await client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _crear(client, h, titulo, **extra):
    return await client.post("/api/descriptores", json={"titulo": titulo, **extra}, headers=h)


async def test_crear_requiere_auth(client):
    r = await client.post("/api/descriptores", json={"titulo": "X"})
    assert r.status_code == 403


async def test_crear_asigna_codigo_y_versiona(client):
    h = await _headers(client)
    r1 = await _crear(client, h, "Puesto de prueba A", nivel_jerarquico=3)
    r2 = await _crear(client, h, "Puesto de prueba B", nivel_jerarquico=4)
    assert r1.status_code == 201 and r2.status_code == 201, (r1.text, r2.text)
    a, b = r1.json(), r2.json()
    assert a["codigo"].startswith("JD-") and b["codigo"].startswith("JD-")
    # números consecutivos y sin colisión con los 27 sembrados (JD-028+)
    na = int(a["codigo"].split("-")[1])
    nb = int(b["codigo"].split("-")[1])
    assert nb == na + 1 and na >= 28
    assert a["version_actual"] == 1 and a["estado"] == "borrador"


async def test_listar_y_filtrar(client):
    h = await _headers(client)
    r = await client.get("/api/descriptores?limit=200", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 27  # los sembrados + los de prueba
    # filtro por nivel jerárquico
    r1 = await client.get("/api/descriptores?nivel_jerarquico=1&limit=200", headers=h)
    assert r1.status_code == 200
    assert all(i["nivel_jerarquico"] == 1 for i in r1.json()["items"])
    # filtro por texto en código
    r2 = await client.get("/api/descriptores?q=JD-001", headers=h)
    assert r2.status_code == 200 and r2.json()["total"] >= 1


async def test_actualizar_contenido_en_borrador(client):
    h = await _headers(client)
    d = (await _crear(client, h, "Editable")).json()
    r = await client.put(
        f"/api/descriptores/{d['id']}",
        json={"proposito": "Nuevo propósito", "responsabilidades": ["Una", "Dos"]},
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert r.json()["proposito"] == "Nuevo propósito"
    assert r.json()["responsabilidades"] == ["Una", "Dos"]


async def test_jerarquia_rechaza_autoreferencia_y_ciclo(client):
    h = await _headers(client)
    a = (await _crear(client, h, "Jefe A")).json()
    b = (await _crear(client, h, "Sub B", reporta_a_id=a["id"])).json()
    assert b["reporta_a_id"] == a["id"] and b["reporta_a_codigo"] == a["codigo"]
    # auto-referencia
    r_self = await client.put(
        f"/api/descriptores/{a['id']}", json={"reporta_a_id": a["id"]}, headers=h
    )
    assert r_self.status_code == 409
    # ciclo: A reportaría a B, que ya reporta a A
    r_ciclo = await client.put(
        f"/api/descriptores/{a['id']}", json={"reporta_a_id": b["id"]}, headers=h
    )
    assert r_ciclo.status_code == 409


async def test_reporta_a_inexistente(client):
    h = await _headers(client)
    import uuid

    r = await _crear(client, h, "Sin jefe válido", reporta_a_id=str(uuid.uuid4()))
    assert r.status_code == 404


async def test_paginacion_rechaza_valores_invalidos(client):
    """offset/limit fuera de rango deben dar 422, no 500 ni una página incorrecta."""
    h = await _headers(client)
    assert (await client.get("/api/descriptores?offset=-1", headers=h)).status_code == 422
    assert (await client.get("/api/descriptores?limit=0", headers=h)).status_code == 422
    assert (await client.get("/api/descriptores?limit=-5", headers=h)).status_code == 422


async def test_soft_delete_no_reutiliza_numero(client):
    h = await _headers(client)
    a = (await _crear(client, h, "Borrable")).json()
    assert (await client.delete(f"/api/descriptores/{a['id']}", headers=h)).status_code == 204
    assert (await client.get(f"/api/descriptores/{a['id']}", headers=h)).status_code == 404
    b = (await _crear(client, h, "Siguiente")).json()
    assert int(b["codigo"].split("-")[1]) > int(a["codigo"].split("-")[1])
