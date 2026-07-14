"""Pruebas del Armador por propiedad: departamentos, puestos (local + siembra desde
maestro), titulares (ocupantes), sistemas y resumen por hotel."""

import uuid as _uuid

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ADMIN_PASS = "CambiarCRC2026!"


async def _headers(client):
    r = await client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _cwl_id():
    from sqlalchemy import select

    from app.core.db import AsyncSessionLocal
    from app.models.catalogos import Propiedad

    async with AsyncSessionLocal() as db:
        p = (await db.execute(select(Propiedad).where(Propiedad.codigo == "CWL"))).scalar_one()
        return str(p.id)


async def _departamento_con_puestos():
    """(depto_id, cantidad_descriptores) del departamento con más descriptores master."""
    from sqlalchemy import func, select

    from app.core.db import AsyncSessionLocal
    from app.models.puesto import DescriptorPuestoMaster

    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(DescriptorPuestoMaster.departamento_id, func.count())
                .where(
                    DescriptorPuestoMaster.departamento_id.is_not(None),
                    DescriptorPuestoMaster.eliminado_en.is_(None),
                )
                .group_by(DescriptorPuestoMaster.departamento_id)
                .order_by(func.count().desc())
            )
        ).first()
        return str(row[0]), int(row[1])


async def _un_usuario_id():
    from sqlalchemy import select

    from app.core.db import AsyncSessionLocal
    from app.models.usuarios import Usuario

    async with AsyncSessionLocal() as db:
        u = (await db.execute(select(Usuario).limit(1))).scalars().first()
        return str(u.id)


async def test_requiere_auth(client):
    assert (await client.get("/api/propiedades/resumen")).status_code == 403


async def test_resumen(client):
    h = await _headers(client)
    r = await client.get("/api/propiedades/resumen", headers=h)
    assert r.status_code == 200, r.text
    props = r.json()
    cwl = next((p for p in props if p["codigo"] == "CWL"), None)
    assert cwl is not None
    assert {"departamentos", "puestos", "ocupantes", "sops", "sistemas"} <= set(cwl)


async def test_departamentos_set_y_restore(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    dep_id, _ = await _departamento_con_puestos()
    r = await client.put(
        f"/api/propiedades/{cwl}/departamentos", json={"departamento_ids": [dep_id]}, headers=h
    )
    assert r.status_code == 200, r.text
    assert any(d["id"] == dep_id for d in r.json())
    r2 = await client.get(f"/api/propiedades/{cwl}/departamentos", headers=h)
    assert any(d["id"] == dep_id for d in r2.json())
    # restaurar a vacío (no dejar basura en la config de CWL)
    await client.put(f"/api/propiedades/{cwl}/departamentos", json={"departamento_ids": []}, headers=h)


async def test_departamentos_invalido(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    r = await client.put(
        f"/api/propiedades/{cwl}/departamentos",
        json={"departamento_ids": [str(_uuid.uuid4())]},
        headers=h,
    )
    assert r.status_code == 422


async def test_puesto_local_ciclo_vida(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    r = await client.post(
        f"/api/propiedades/{cwl}/puestos",
        json={
            "modo": "local",
            "overrides": {"titulo": "Puesto local X", "nivel_jerarquico": 4},
            "dotacion": 2,
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    pp = r.json()
    assert pp["titulo"] == "Puesto local X" and pp["modo"] == "local" and pp["dotacion"] == 2
    pid = pp["id"]
    det = (await client.get(f"/api/propiedades/{cwl}/puestos/{pid}", headers=h)).json()
    assert det["contenido_efectivo"]["titulo"] == "Puesto local X"
    up = await client.put(f"/api/propiedades/{cwl}/puestos/{pid}", json={"dotacion": 5}, headers=h)
    assert up.status_code == 200 and up.json()["dotacion"] == 5
    assert (await client.delete(f"/api/propiedades/{cwl}/puestos/{pid}", headers=h)).status_code == 204
    assert (await client.get(f"/api/propiedades/{cwl}/puestos/{pid}", headers=h)).status_code == 404


async def test_reporta_a_rechaza_ciclo(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    a = (
        await client.post(
            f"/api/propiedades/{cwl}/puestos",
            json={"modo": "local", "overrides": {"titulo": "Jefe A"}},
            headers=h,
        )
    ).json()
    b = (
        await client.post(
            f"/api/propiedades/{cwl}/puestos",
            json={"modo": "local", "overrides": {"titulo": "Sub B"}, "reporta_a_id": a["id"]},
            headers=h,
        )
    ).json()
    # A -> B cerraría el ciclo A -> B -> A
    r = await client.put(
        f"/api/propiedades/{cwl}/puestos/{a['id']}", json={"reporta_a_id": b["id"]}, headers=h
    )
    assert r.status_code == 409, r.text
    # auto-referencia
    rs = await client.put(
        f"/api/propiedades/{cwl}/puestos/{a['id']}", json={"reporta_a_id": a["id"]}, headers=h
    )
    assert rs.status_code == 422
    # limpiar
    await client.delete(f"/api/propiedades/{cwl}/puestos/{b['id']}", headers=h)
    await client.delete(f"/api/propiedades/{cwl}/puestos/{a['id']}", headers=h)


async def test_puesto_local_requiere_titulo(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    r = await client.post(
        f"/api/propiedades/{cwl}/puestos", json={"modo": "local", "overrides": {}}, headers=h
    )
    assert r.status_code == 422


async def test_sembrar_desde_maestro_idempotente(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    dep_id, n = await _departamento_con_puestos()
    r = await client.post(
        f"/api/propiedades/{cwl}/puestos/sembrar-desde-maestro",
        json={"departamento_ids": [dep_id]},
        headers=h,
    )
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["creados"] + res["omitidos"] == n
    # segunda corrida: todo omitido (idempotente)
    r2 = await client.post(
        f"/api/propiedades/{cwl}/puestos/sembrar-desde-maestro",
        json={"departamento_ids": [dep_id]},
        headers=h,
    )
    assert r2.json()["creados"] == 0 and r2.json()["omitidos"] == n
    puestos = (await client.get(f"/api/propiedades/{cwl}/puestos", headers=h)).json()
    assert len(puestos) >= n


async def test_ocupante_ciclo_vida(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    uid = await _un_usuario_id()
    pp = (
        await client.post(
            f"/api/propiedades/{cwl}/puestos",
            json={"modo": "local", "overrides": {"titulo": "Puesto con titular"}},
            headers=h,
        )
    ).json()
    pid = pp["id"]
    r = await client.post(
        f"/api/propiedades/{cwl}/puestos/{pid}/ocupantes",
        json={"usuario_id": uid, "es_principal": True},
        headers=h,
    )
    assert r.status_code == 201, r.text
    oc = r.json()
    assert oc["usuario_id"] == uid and oc["es_principal"] is True and oc["usuario_nombre"]
    # duplicado
    dup = await client.post(
        f"/api/propiedades/{cwl}/puestos/{pid}/ocupantes", json={"usuario_id": uid}, headers=h
    )
    assert dup.status_code == 409
    # el detalle del puesto trae los titulares
    det = (await client.get(f"/api/propiedades/{cwl}/puestos/{pid}", headers=h)).json()
    assert det["ocupantes_count"] == 1 and len(det["ocupantes"]) == 1
    assert (
        await client.delete(
            f"/api/propiedades/{cwl}/puestos/{pid}/ocupantes/{oc['id']}", headers=h
        )
    ).status_code == 204
    await client.delete(f"/api/propiedades/{cwl}/puestos/{pid}", headers=h)


async def test_visibilidad_por_propiedad(client):
    """Un usuario con alcance a una propiedad ve SOLO esa; el corporativo (admin) ve todas."""
    from sqlalchemy import delete, select

    from app.core.db import AsyncSessionLocal
    from app.core.seguridad import hash_password
    from app.models.base import RolUsuario
    from app.models.catalogos import Propiedad
    from app.models.usuarios import RolUsuarioAsignado, Usuario

    email = "scoped.cwl@test.crc"
    passwd = "ScopedCRC2026!"
    async with AsyncSessionLocal() as db:
        cwl = (await db.execute(select(Propiedad).where(Propiedad.codigo == "CWL"))).scalar_one()
        otra = (
            await db.execute(select(Propiedad).where(Propiedad.codigo != "CWL"))
        ).scalars().first()
        cwl_id, otra_id = str(cwl.id), str(otra.id)
        u = (await db.execute(select(Usuario).where(Usuario.email == email))).scalar_one_or_none()
        if not u:
            u = Usuario(
                nombre="Scoped CWL", email=email, password_hash=hash_password(passwd),
                nivel_jerarquico=3, activo=True,
            )
            db.add(u)
            await db.flush()
            db.add(RolUsuarioAsignado(usuario_id=u.id, rol=RolUsuario.lector, propiedad_id=cwl.id))
            await db.commit()
    try:
        tok = (await client.post(
            "/api/auth/login", json={"email": email, "password": passwd}
        )).json()["access_token"]
        h = {"Authorization": f"Bearer {tok}"}
        # resumen: solo su hotel
        res = (await client.get("/api/propiedades/resumen", headers=h)).json()
        assert [p["codigo"] for p in res] == ["CWL"], res
        # su hotel: 200; otra propiedad: 403
        assert (await client.get(f"/api/propiedades/{cwl_id}/departamentos", headers=h)).status_code == 200
        assert (await client.get(f"/api/propiedades/{otra_id}/departamentos", headers=h)).status_code == 403
        assert (await client.get(f"/api/propiedades/{otra_id}/asignaciones", headers=h)).status_code == 403
        assert (await client.get(f"/api/propiedades/{otra_id}/organigrama", headers=h)).status_code == 403
        # el admin (corporativo) ve todas
        allres = (await client.get("/api/propiedades/resumen", headers=await _headers(client))).json()
        assert len(allres) >= 4
    finally:
        async with AsyncSessionLocal() as db:
            uu = (await db.execute(select(Usuario).where(Usuario.email == email))).scalar_one_or_none()
            if uu:
                await db.execute(delete(RolUsuarioAsignado).where(RolUsuarioAsignado.usuario_id == uu.id))
                await db.execute(delete(Usuario).where(Usuario.id == uu.id))
                await db.commit()


async def test_sistemas_roundtrip(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    base = (await client.get(f"/api/propiedades/{cwl}/sistemas", headers=h)).json()
    ids = [s["id"] for s in base]
    # PUT del mismo conjunto: idempotente y no destruye la config sembrada
    r = await client.put(f"/api/propiedades/{cwl}/sistemas", json={"sistema_ids": ids}, headers=h)
    assert r.status_code == 200, r.text
    assert {s["id"] for s in r.json()} == set(ids)
