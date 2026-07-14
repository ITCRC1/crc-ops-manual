"""Pruebas del módulo de Capacitación / Training (manuales + secciones)."""

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ADMIN_PASS = "CambiarCRC2026!"


async def _headers(client):
    r = await client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_requiere_auth(client):
    assert (await client.get("/api/capacitacion/manuales")).status_code == 403


async def test_ciclo_completo_manual_y_secciones(client):
    h = await _headers(client)
    # crear manual
    r = await client.post("/api/capacitacion/manuales", json={"titulo": "Manual de prueba"}, headers=h)
    assert r.status_code == 201, r.text
    mid = r.json()["id"]
    try:
        # agregar dos secciones
        s1 = (
            await client.post(
                f"/api/capacitacion/manuales/{mid}/secciones",
                json={"titulo": "Sección A", "contenido": "Contenido A"},
                headers=h,
            )
        ).json()
        s2 = (
            await client.post(
                f"/api/capacitacion/manuales/{mid}/secciones",
                json={"titulo": "Sección B", "contenido": "Contenido B"},
                headers=h,
            )
        ).json()
        assert s1["orden"] == 0 and s2["orden"] == 1

        # editar sección
        r_ed = await client.put(
            f"/api/capacitacion/manuales/{mid}/secciones/{s1['id']}",
            json={"contenido": "Contenido A editado"},
            headers=h,
        )
        assert r_ed.status_code == 200 and r_ed.json()["contenido"] == "Contenido A editado"

        # reordenar (B antes que A)
        r_re = await client.post(
            f"/api/capacitacion/manuales/{mid}/reordenar",
            json={"orden_ids": [s2["id"], s1["id"]]},
            headers=h,
        )
        assert r_re.status_code == 200
        orden = [(s["id"], s["orden"]) for s in r_re.json()["secciones"]]
        pos = {sid: o for sid, o in orden}
        assert pos[s2["id"]] < pos[s1["id"]]

        # borrar una sección
        assert (
            await client.delete(
                f"/api/capacitacion/manuales/{mid}/secciones/{s1['id']}", headers=h
            )
        ).status_code == 204
        det = (await client.get(f"/api/capacitacion/manuales/{mid}", headers=h)).json()
        assert det["total_secciones"] == 1
    finally:
        # borrar manual (soft delete)
        assert (await client.delete(f"/api/capacitacion/manuales/{mid}", headers=h)).status_code == 204
        assert (await client.get(f"/api/capacitacion/manuales/{mid}", headers=h)).status_code == 404


async def test_lector_no_puede_crear(client):
    """Un lector no puede crear manuales (solo editor/super_admin)."""
    from sqlalchemy import delete, select

    from app.core.db import AsyncSessionLocal
    from app.core.seguridad import hash_password
    from app.models.base import RolUsuario
    from app.models.usuarios import RolUsuarioAsignado, Usuario

    email = "lector.train@test.crc"
    passwd = "LectorCRC2026!"
    async with AsyncSessionLocal() as db:
        u = (await db.execute(select(Usuario).where(Usuario.email == email))).scalar_one_or_none()
        if not u:
            u = Usuario(
                nombre="Lector Train", email=email, password_hash=hash_password(passwd),
                nivel_jerarquico=4, activo=True,
            )
            db.add(u)
            await db.flush()
            db.add(RolUsuarioAsignado(usuario_id=u.id, rol=RolUsuario.lector, propiedad_id=None))
            await db.commit()
        uid = u.id
    try:
        tok = (await client.post("/api/auth/login", json={"email": email, "password": passwd})).json()[
            "access_token"
        ]
        h = {"Authorization": f"Bearer {tok}"}
        assert (
            await client.post("/api/capacitacion/manuales", json={"titulo": "X"}, headers=h)
        ).status_code == 403
        # pero sí puede leer
        assert (await client.get("/api/capacitacion/manuales", headers=h)).status_code == 200
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(RolUsuarioAsignado).where(RolUsuarioAsignado.usuario_id == uid))
            await db.execute(delete(Usuario).where(Usuario.id == uid))
            await db.commit()
