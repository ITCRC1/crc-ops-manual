"""Pruebas del organigrama derivado de `reporta_a` (E4.5, §8.14)."""

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ADMIN_PASS = "CambiarCRC2026!"


async def _headers(client):
    r = await client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _contar(nodos):
    return sum(1 + _contar(n["hijos"]) for n in nodos)


def _codigos(nodos):
    out = []
    for n in nodos:
        out.append(n["codigo"])
        out.extend(_codigos(n["hijos"]))
    return out


async def test_organigrama_requiere_auth(client):
    assert (await client.get("/api/organigrama")).status_code == 403


async def test_organigrama_master_es_arbol(client):
    h = await _headers(client)
    r = await client.get("/api/organigrama", headers=h)
    assert r.status_code == 200
    arbol = r.json()
    assert isinstance(arbol, list) and len(arbol) >= 1
    # cada puesto aparece una sola vez; el total cubre los sembrados
    assert _contar(arbol) >= 27
    codigos = _codigos(arbol)
    assert len(codigos) == len(set(codigos))  # sin duplicados (sin ciclos)
    # el General Manager (JD-001, nivel 1) es raíz y tiene subordinados
    raiz_gm = next((n for n in arbol if n["codigo"] == "JD-001"), None)
    assert raiz_gm is not None and len(raiz_gm["hijos"]) >= 1


async def test_organigrama_propiedad(client):
    h = await _headers(client)
    # id de una propiedad real (CWL) desde la DB
    from sqlalchemy import select

    from app.core.db import AsyncSessionLocal
    from app.models.catalogos import Propiedad

    async with AsyncSessionLocal() as db:
        prop = (await db.execute(select(Propiedad).where(Propiedad.codigo == "CWL"))).scalar_one()
        prop_id = str(prop.id)

    r = await client.get(f"/api/propiedades/{prop_id}/organigrama", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)  # sin dotación cargada aún → lista (posiblemente vacía)


async def test_organigrama_propiedad_inexistente(client):
    import uuid

    h = await _headers(client)
    r = await client.get(f"/api/propiedades/{uuid.uuid4()}/organigrama", headers=h)
    assert r.status_code == 404
