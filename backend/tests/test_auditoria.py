"""Pruebas de auditoría y custodia documental (E4.5, §8.8, §8.18, §7.7)."""

import uuid

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ADMIN_PASS = "CambiarCRC2026!"


async def _headers(client):
    r = await client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_auditoria_requiere_auth(client):
    assert (await client.get("/api/auditoria")).status_code == 403


async def test_auditoria_registra_acciones(client):
    h = await _headers(client)
    # genera un evento auditable determinístico
    await client.post("/api/descriptores", json={"titulo": "Auditable"}, headers=h)
    r = await client.get("/api/auditoria?entidad=descriptor_puesto_master&limit=200", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert all(i["entidad"] == "descriptor_puesto_master" for i in data["items"])


async def test_documentos_controlados_lista(client):
    h = await _headers(client)
    r = await client.get("/api/documentos-controlados", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "total" in data and isinstance(data["items"], list)


async def test_paginacion_rechaza_valores_invalidos(client):
    """offset negativo no debe llegar a SQL (evita 500 por 'OFFSET must not be negative')."""
    h = await _headers(client)
    assert (await client.get("/api/auditoria?offset=-1", headers=h)).status_code == 422
    assert (await client.get("/api/documentos-controlados?offset=-1", headers=h)).status_code == 422


async def test_bitacora_doc_inexistente(client):
    h = await _headers(client)
    r = await client.get(f"/api/documentos-controlados/{uuid.uuid4()}/bitacora", headers=h)
    assert r.status_code == 404


async def test_verificar_integridad_doc_inexistente(client):
    h = await _headers(client)
    r = await client.post(
        f"/api/documentos-controlados/{uuid.uuid4()}/verificar-integridad", headers=h
    )
    assert r.status_code == 404


async def test_lector_no_accede_auditoria(client):
    """La traza es solo para roles corporativos y custodio (§14, §8.18)."""
    from sqlalchemy import delete, select

    from app.core.db import AsyncSessionLocal
    from app.core.seguridad import hash_password
    from app.models.base import RolUsuario
    from app.models.usuarios import RolUsuarioAsignado, Usuario

    email = "lector.e45@test.crc"
    passwd = "LectorCRC2026!"
    async with AsyncSessionLocal() as db:
        u = (await db.execute(select(Usuario).where(Usuario.email == email))).scalar_one_or_none()
        if not u:
            u = Usuario(
                nombre="Lector Prueba", email=email, password_hash=hash_password(passwd),
                nivel_jerarquico=4, activo=True,
            )
            db.add(u)
            await db.flush()
            db.add(RolUsuarioAsignado(usuario_id=u.id, rol=RolUsuario.lector, propiedad_id=None))
            await db.commit()
        uid = u.id
    try:
        r = await client.post("/api/auth/login", json={"email": email, "password": passwd})
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        assert (await client.get("/api/auditoria", headers=h)).status_code == 403
        assert (await client.get("/api/documentos-controlados", headers=h)).status_code == 403
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(RolUsuarioAsignado).where(RolUsuarioAsignado.usuario_id == uid))
            await db.execute(delete(Usuario).where(Usuario.id == uid))
            await db.commit()
