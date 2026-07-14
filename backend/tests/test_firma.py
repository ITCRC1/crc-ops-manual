"""Pruebas del flujo de firma electrónica y documento controlado (E4.3):
designación con nivel, orden de firma, cierre automático + PDF/hash, rechazo que
invalida firmas parciales, reasignación, segregación de funciones."""

import pytest
import pytest_asyncio

from app.core.rate_limit import _intentos

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ADMIN_PASS = "CambiarCRC2026!"
FPASS = "Firma123!"
FIRMANTES = [
    ("firmante1@test.crc", "Firmante Uno", 2),
    ("firmante2@test.crc", "Firmante Dos", 3),
    ("operativo@test.crc", "Operativo", 4),
]


@pytest.fixture(autouse=True)
def _reset_rl():
    _intentos.clear()
    yield
    _intentos.clear()


@pytest_asyncio.fixture(loop_scope="session")
async def usuarios_firma():
    """Crea (idempotente) usuarios firmantes de prueba y devuelve {email: id}."""
    from sqlalchemy import select

    from app.core.db import AsyncSessionLocal
    from app.core.seguridad import hash_password
    from app.models.usuarios import Usuario

    ids = {}
    async with AsyncSessionLocal() as db:
        for email, nombre, nivel in FIRMANTES:
            u = (await db.execute(select(Usuario).where(Usuario.email == email))).scalar_one_or_none()
            if not u:
                u = Usuario(nombre=nombre, email=email, password_hash=hash_password(FPASS),
                            nivel_jerarquico=nivel, activo=True)
                db.add(u)
                await db.flush()
            ids[email] = str(u.id)
        await db.commit()
    return ids


async def _token(client, email, password):
    r = await client.post("/api/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


async def _h(client, email=ADMIN_EMAIL, password=ADMIN_PASS):
    return {"Authorization": f"Bearer {await _token(client, email, password)}"}


async def _crear_sop(client, h):
    r = await client.post("/api/sops", json={"area_codigo": "GOV", "nombre": "SOP firma"}, headers=h)
    return r.json()


async def test_flujo_firma_completo(client, usuarios_firma):
    admin = await _h(client)
    sop = await _crear_sop(client, admin)
    sid = sop["id"]
    # designar 2 firmantes elegibles en orden
    for email, orden in [("firmante1@test.crc", 1), ("firmante2@test.crc", 2)]:
        r = await client.post(f"/api/sops/{sid}/firmantes",
                              json={"usuario_id": usuarios_firma[email], "orden": orden},
                              headers=admin)
        assert r.status_code == 201, r.text
    # flujo de estados
    assert (await client.post(f"/api/sops/{sid}/enviar-revision", headers=admin)).status_code == 204
    assert (await client.post(f"/api/sops/{sid}/enviar-firma", headers=admin)).status_code == 204

    h1 = await _h(client, "firmante1@test.crc", FPASS)
    h2 = await _h(client, "firmante2@test.crc", FPASS)
    # firmante2 no puede firmar antes que el de orden 1
    assert (await client.post(f"/api/sops/{sid}/firmar", json={}, headers=h2)).status_code == 409
    # firma en orden
    r1 = await client.post(f"/api/sops/{sid}/firmar", json={}, headers=h1)
    assert r1.status_code == 200 and r1.json()["documento_controlado"] is False, r1.text
    r2 = await client.post(f"/api/sops/{sid}/firmar", json={}, headers=h2)
    assert r2.status_code == 200 and r2.json()["documento_controlado"] is True, r2.text
    # documento controlado con hash + descarga PDF
    doc = await client.get(f"/api/sops/{sid}/documento-controlado", headers=admin)
    assert doc.status_code == 200 and len(doc.json()["hash_pdf"]) == 64
    dl = await client.get(f"/api/sops/{sid}/documento-controlado/descargar", headers=admin)
    assert dl.status_code == 200 and dl.content[:4] == b"%PDF"
    # ya firmado: no se puede editar directo
    assert (await client.put(f"/api/sops/{sid}", json={"proposito": "x"}, headers=admin)).status_code == 409


async def test_firmante_debe_cumplir_nivel(client, usuarios_firma):
    admin = await _h(client)
    sop = await _crear_sop(client, admin)
    r = await client.post(f"/api/sops/{sop['id']}/firmantes",
                          json={"usuario_id": usuarios_firma["operativo@test.crc"]}, headers=admin)
    assert r.status_code == 409  # nivel 4 > mínimo 3


async def test_segregacion_autor_unico_firmante(client, usuarios_firma):
    admin = await _h(client)
    me = (await client.get("/api/auth/me", headers=admin)).json()
    sop = await _crear_sop(client, admin)  # creado_por = admin
    # designar al propio admin como ÚNICO firmante obligatorio
    await client.post(f"/api/sops/{sop['id']}/firmantes",
                      json={"usuario_id": me["id"], "orden": 1}, headers=admin)
    await client.post(f"/api/sops/{sop['id']}/enviar-revision", headers=admin)
    r = await client.post(f"/api/sops/{sop['id']}/enviar-firma", headers=admin)
    assert r.status_code == 409  # segregación de funciones


async def test_pendientes_firma_cola_del_firmante(client, usuarios_firma):
    admin = await _h(client)
    sop = await _crear_sop(client, admin)
    sid = sop["id"]
    await client.post(f"/api/sops/{sid}/firmantes",
                      json={"usuario_id": usuarios_firma["firmante1@test.crc"], "orden": 1}, headers=admin)
    await client.post(f"/api/sops/{sid}/enviar-revision", headers=admin)
    assert (await client.post(f"/api/sops/{sid}/enviar-firma", headers=admin)).status_code == 204
    # el firmante lo ve en su cola; el admin (no designado) no
    h1 = await _h(client, "firmante1@test.crc", FPASS)
    cola = (await client.get("/api/sops/pendientes-firma", headers=h1)).json()
    assert any(s["id"] == sid for s in cola), cola
    cola_admin = (await client.get("/api/sops/pendientes-firma", headers=admin)).json()
    assert all(s["id"] != sid for s in cola_admin)
    # tras firmar, sale de la cola (queda firmado)
    assert (await client.post(f"/api/sops/{sid}/firmar", json={}, headers=h1)).status_code == 200
    cola2 = (await client.get("/api/sops/pendientes-firma", headers=h1)).json()
    assert all(s["id"] != sid for s in cola2)


async def test_rechazo_invalida_firmas_parciales(client, usuarios_firma):
    admin = await _h(client)
    sop = await _crear_sop(client, admin)
    sid = sop["id"]
    for email, orden in [("firmante1@test.crc", 1), ("firmante2@test.crc", 2)]:
        await client.post(f"/api/sops/{sid}/firmantes",
                          json={"usuario_id": usuarios_firma[email], "orden": orden}, headers=admin)
    await client.post(f"/api/sops/{sid}/enviar-revision", headers=admin)
    await client.post(f"/api/sops/{sid}/enviar-firma", headers=admin)
    h1 = await _h(client, "firmante1@test.crc", FPASS)
    h2 = await _h(client, "firmante2@test.crc", FPASS)
    await client.post(f"/api/sops/{sid}/firmar", json={}, headers=h1)  # firma parcial
    # sin comentario → 422
    sin_com = await client.post(f"/api/sops/{sid}/rechazar", json={"comentario": ""}, headers=h2)
    assert sin_com.status_code == 422
    r = await client.post(f"/api/sops/{sid}/rechazar",
                          json={"comentario": "Falta detalle en el paso 3"}, headers=h2)
    assert r.status_code == 204, r.text
    # estado rechazado y firmas invalidadas (firmante1 aparece como no-firmado)
    firmantes = (await client.get(f"/api/sops/{sid}/firmantes", headers=admin)).json()
    assert all(not f["firmado"] for f in firmantes)
