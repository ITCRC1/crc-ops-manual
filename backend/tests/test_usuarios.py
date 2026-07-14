"""Pruebas de la gestión mínima de usuarios (§8.2)."""

import uuid

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ADMIN_PASS = "CambiarCRC2026!"


async def _headers(client):
    r = await client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_requiere_auth(client):
    assert (await client.get("/api/usuarios")).status_code == 403


async def test_listar_incluye_admin(client):
    h = await _headers(client)
    r = await client.get("/api/usuarios", headers=h)
    assert r.status_code == 200
    assert any(u["email"].lower() == ADMIN_EMAIL.lower() for u in r.json())


async def test_elegibles_firmante(client):
    h = await _headers(client)
    r = await client.get("/api/usuarios?elegibles_firmante=true", headers=h)
    assert r.status_code == 200
    # nivel_minimo_firmante = 3; el admin (nivel 1) debe ser elegible
    assert all(u["nivel_jerarquico"] <= 3 for u in r.json())


async def test_crear_usuario_y_unicidad(client):
    h = await _headers(client)
    email = "director.e5@test.crc"
    from sqlalchemy import delete, select

    from app.core.db import AsyncSessionLocal
    from app.models.usuarios import RolUsuarioAsignado, Usuario

    try:
        r = await client.post(
            "/api/usuarios",
            json={
                "nombre": "Director Prueba",
                "email": email,
                "password": "DirectorCRC2026!",
                "nivel_jerarquico": 2,
                "roles": [{"rol": "editor_corporativo", "propiedad_id": None}],
            },
            headers=h,
        )
        assert r.status_code == 201, r.text
        assert r.json()["email"] == email
        # correo duplicado -> 409
        dup = await client.post(
            "/api/usuarios",
            json={"nombre": "Otro", "email": email, "password": "OtroCRC2026!"},
            headers=h,
        )
        assert dup.status_code == 409
    finally:
        async with AsyncSessionLocal() as db:
            u = (
                await db.execute(select(Usuario).where(Usuario.email == email))
            ).scalar_one_or_none()
            if u:
                await db.execute(
                    delete(RolUsuarioAsignado).where(RolUsuarioAsignado.usuario_id == u.id)
                )
                await db.execute(delete(Usuario).where(Usuario.id == u.id))
                await db.commit()


async def test_actualizar_usuario_promueve_a_firmante(client):
    h = await _headers(client)
    email = "patch.e5@test.crc"
    from sqlalchemy import delete, select

    from app.core.db import AsyncSessionLocal
    from app.models.usuarios import RolUsuarioAsignado, Usuario

    try:
        u = (await client.post(
            "/api/usuarios",
            json={"nombre": "Patch Prueba", "email": email, "password": "PatchCRC2026!",
                  "nivel_jerarquico": 4, "roles": [{"rol": "lector", "propiedad_id": None}]},
            headers=h,
        )).json()
        uid = u["id"]
        # promover: nivel 4 -> 2 + rol editor_corporativo (reemplaza roles)
        r = await client.patch(
            f"/api/usuarios/{uid}",
            json={"nivel_jerarquico": 2, "roles": [{"rol": "editor_corporativo", "propiedad_id": None}]},
            headers=h,
        )
        assert r.status_code == 200, r.text
        assert r.json()["nivel_jerarquico"] == 2
        assert any(rr["rol"] == "editor_corporativo" for rr in r.json()["roles"])
        # ahora es elegible firmante
        eleg = (await client.get("/api/usuarios?elegibles_firmante=true", headers=h)).json()
        assert any(x["id"] == uid for x in eleg)
        # inexistente -> 404
        assert (await client.patch(f"/api/usuarios/{uuid.uuid4()}", json={"activo": False},
                                   headers=h)).status_code == 404
    finally:
        async with AsyncSessionLocal() as db:
            uu = (await db.execute(select(Usuario).where(Usuario.email == email))).scalar_one_or_none()
            if uu:
                await db.execute(delete(RolUsuarioAsignado).where(RolUsuarioAsignado.usuario_id == uu.id))
                await db.execute(delete(Usuario).where(Usuario.id == uu.id))
                await db.commit()


async def test_no_deja_sistema_sin_superadmin(client):
    """Guard anti-lockout: dejando un solo super_admin activo, no puede auto-desactivarse.

    Usa al 2º super_admin de respaldo (Ronald, sembrado): al desactivarlo el admin queda
    como único super y el guard debe bloquear su auto-desactivación con 409. El admin nunca
    se desactiva de verdad (el 409 lo impide); Ronald se restaura en el finally."""
    from sqlalchemy import select

    from app.core.db import AsyncSessionLocal
    from app.models.base import RolUsuario
    from app.models.usuarios import RolUsuarioAsignado, Usuario

    h = await _headers(client)
    me = (await client.get("/api/auth/me", headers=h)).json()

    async with AsyncSessionLocal() as db:
        ronald = (
            await db.execute(select(Usuario).where(Usuario.email == "ronald@example.com"))
        ).scalar_one_or_none()
        ronald_super = ronald is not None and (
            await db.execute(
                select(RolUsuarioAsignado).where(
                    RolUsuarioAsignado.usuario_id == ronald.id,
                    RolUsuarioAsignado.rol == RolUsuario.super_admin,
                )
            )
        ).first() is not None
    if not ronald_super:
        pytest.skip("no hay 2º super_admin de respaldo sembrado")

    rid = str(ronald.id)
    try:
        # con 2 supers, desactivar a Ronald está permitido (queda el admin)
        desactivar_ronald = await client.patch(f"/api/usuarios/{rid}", json={"activo": False}, headers=h)
        assert desactivar_ronald.status_code == 200, desactivar_ronald.text
        # ahora el admin es el único super activo → no puede auto-desactivarse ni auto-degradarse
        auto_off = await client.patch(f"/api/usuarios/{me['id']}", json={"activo": False}, headers=h)
        assert auto_off.status_code == 409, auto_off.text
        auto_baja = await client.patch(
            f"/api/usuarios/{me['id']}",
            json={"roles": [{"rol": "lector", "propiedad_id": None}]},
            headers=h,
        )
        assert auto_baja.status_code == 409, auto_baja.text
    finally:
        async with AsyncSessionLocal() as db:
            r = (
                await db.execute(select(Usuario).where(Usuario.email == "ronald@example.com"))
            ).scalar_one_or_none()
            if r and not r.activo:
                r.activo = True
            a = (await db.execute(select(Usuario).where(Usuario.email == ADMIN_EMAIL))).scalar_one()
            if not a.activo:
                a.activo = True
            if not (await db.execute(
                select(RolUsuarioAsignado).where(
                    RolUsuarioAsignado.usuario_id == a.id,
                    RolUsuarioAsignado.rol == RolUsuario.super_admin,
                )
            )).first():
                db.add(RolUsuarioAsignado(usuario_id=a.id, rol=RolUsuario.super_admin, propiedad_id=None))
            await db.commit()


async def test_crear_requiere_super_admin(client):
    """Un no-super_admin no puede crear usuarios."""
    from sqlalchemy import delete

    from app.core.db import AsyncSessionLocal
    from app.core.seguridad import hash_password
    from app.models.base import RolUsuario
    from app.models.usuarios import RolUsuarioAsignado, Usuario

    email = "editor.e5@test.crc"
    passwd = "EditorCRC2026!"
    async with AsyncSessionLocal() as db:
        u = Usuario(
            nombre="Editor Prueba", email=email, password_hash=hash_password(passwd),
            nivel_jerarquico=2, activo=True,
        )
        db.add(u)
        await db.flush()
        db.add(RolUsuarioAsignado(usuario_id=u.id, rol=RolUsuario.editor_corporativo, propiedad_id=None))
        await db.commit()
        uid = u.id
    try:
        tok = (await client.post("/api/auth/login", json={"email": email, "password": passwd})).json()[
            "access_token"
        ]
        h = {"Authorization": f"Bearer {tok}"}
        r = await client.post(
            "/api/usuarios",
            json={"nombre": "X", "email": f"x{uuid.uuid4().hex[:6]}@test.crc", "password": "XxxCRC2026!"},
            headers=h,
        )
        assert r.status_code == 403
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(RolUsuarioAsignado).where(RolUsuarioAsignado.usuario_id == uid))
            await db.execute(delete(Usuario).where(Usuario.id == uid))
            await db.commit()
