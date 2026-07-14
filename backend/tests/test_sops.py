"""Pruebas del CRUD del master de SOPs (E4.2): numeración atómica, versionado,
búsqueda, permisos e inmutabilidad. Requieren DB sembrada + ingesta cargada."""

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ADMIN_PASS = "CambiarCRC2026!"


async def _token(client):
    r = await client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    return r.json()["access_token"]


async def _headers(client):
    return {"Authorization": f"Bearer {await _token(client)}"}


async def _crear(client, h, area, nombre):
    r = await client.post("/api/sops", json={"area_codigo": area, "nombre": nombre}, headers=h)
    return r


async def test_crear_requiere_auth(client):
    r = await client.post("/api/sops", json={"area_codigo": "FIN", "nombre": "X"})
    assert r.status_code == 403


async def test_crear_asigna_codigo_atomico_y_versiona(client):
    h = await _headers(client)
    r1 = await _crear(client, h, "GOV", "Prueba A")
    r2 = await _crear(client, h, "GOV", "Prueba B")
    assert r1.status_code == 201 and r2.status_code == 201, (r1.text, r2.text)
    a, b = r1.json(), r2.json()
    # códigos consecutivos, formato AREA-#### y versión inicial 1
    assert a["codigo"].startswith("GOV-") and b["codigo"].startswith("GOV-")
    assert b["numero"] == a["numero"] + 1
    assert a["version_actual"] == 1 and a["estado"] == "borrador"


async def test_listar_y_filtrar(client):
    h = await _headers(client)
    r = await client.get("/api/sops?area=CR&limit=100", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert all(i["area_codigo"] == "CR" for i in data["items"])
    # filtro por texto
    r2 = await client.get("/api/sops?q=Crisis&limit=100", headers=h)
    assert r2.status_code == 200


async def test_actualizar_contenido_en_borrador(client):
    h = await _headers(client)
    sop = (await _crear(client, h, "GOV", "Editable")).json()
    r = await client.put(f"/api/sops/{sop['id']}", json={"proposito": "Nuevo propósito"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["proposito"] == "Nuevo propósito"


async def test_no_editar_firmado_directo(client):
    """Un SOP firmado es inmutable: PUT debe dar 409 (§7.6)."""
    h = await _headers(client)
    # tomar un SOP existente y marcarlo firmado directamente en DB para la prueba
    from sqlalchemy import select

    from app.core.db import AsyncSessionLocal
    from app.models.base import EstadoDocumento
    from app.models.sop import SopMaster

    async with AsyncSessionLocal() as db:
        q = select(SopMaster).where(SopMaster.codigo == "GOV-0001")
        sop = (await db.execute(q)).scalar_one()
        sop.estado = EstadoDocumento.firmado
        await db.commit()
        sid = str(sop.id)
    try:
        r = await client.put(f"/api/sops/{sid}", json={"proposito": "x"}, headers=h)
        assert r.status_code == 409, r.text
        # nueva versión sí permite (vuelve a borrador)
        r2 = await client.post(f"/api/sops/{sid}/nueva-version", headers=h)
        assert r2.status_code == 200, r2.text
        assert r2.json()["estado"] == "borrador" and r2.json()["version_actual"] >= 2
    finally:
        async with AsyncSessionLocal() as db:
            q = select(SopMaster).where(SopMaster.codigo == "GOV-0001")
            sop = (await db.execute(q)).scalar_one()
            sop.estado = EstadoDocumento.borrador
            await db.commit()


async def test_soft_delete_no_reutiliza_numero(client):
    h = await _headers(client)
    a = (await _crear(client, h, "GOV", "Borrable")).json()
    assert (await client.delete(f"/api/sops/{a['id']}", headers=h)).status_code == 204
    assert (await client.get(f"/api/sops/{a['id']}", headers=h)).status_code == 404
    # el siguiente número es mayor (no reutiliza el eliminado)
    b = (await _crear(client, h, "GOV", "Siguiente")).json()
    assert b["numero"] > a["numero"]


async def _dos_departamentos(client, h):
    r = await client.get("/api/catalogos/departamentos", headers=h)
    deptos = r.json()
    return deptos[0]["id"], deptos[1]["id"]


async def _un_puesto(client, h):
    r = await client.get("/api/descriptores?limit=1", headers=h)
    return r.json()["items"][0]["id"]


async def test_crear_con_departamentos_afectados_y_puestos_responsables(client):
    """Un SOP puede tener dueño (opcional) + N departamentos afectados + puestos
    responsables directos (vínculo estructurado, distinto del texto 'responsables')."""
    h = await _headers(client)
    dueno, afectado = await _dos_departamentos(client, h)
    puesto = await _un_puesto(client, h)
    r = await client.post(
        "/api/sops",
        json={
            "area_codigo": "GOV", "nombre": "Con relaciones",
            "departamento_id": dueno,
            "departamentos_afectados_ids": [afectado],
            "puestos_responsables_ids": [puesto],
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    sop = r.json()
    assert sop["departamento_id"] == dueno
    assert [d["id"] for d in sop["departamentos_afectados"]] == [afectado]
    assert [p["id"] for p in sop["puestos_responsables"]] == [puesto]


async def test_actualizar_reemplaza_lista_de_afectados(client):
    """Actualizar la lista reemplaza el contenido anterior (no es incremental)."""
    h = await _headers(client)
    d1, d2 = await _dos_departamentos(client, h)
    sop = (await _crear(client, h, "GOV", "Reemplazable")).json()
    r1 = await client.put(
        f"/api/sops/{sop['id']}", json={"departamentos_afectados_ids": [d1, d2]}, headers=h
    )
    assert r1.status_code == 200
    assert len(r1.json()["departamentos_afectados"]) == 2
    r2 = await client.put(
        f"/api/sops/{sop['id']}", json={"departamentos_afectados_ids": [d1]}, headers=h
    )
    assert r2.status_code == 200
    afectados = r2.json()["departamentos_afectados"]
    assert [d["id"] for d in afectados] == [d1]
    # omitir el campo no lo toca
    r3 = await client.put(f"/api/sops/{sop['id']}", json={"proposito": "x"}, headers=h)
    assert [d["id"] for d in r3.json()["departamentos_afectados"]] == [d1]
    # enviar lista vacía sí lo vacía
    r4 = await client.put(
        f"/api/sops/{sop['id']}", json={"departamentos_afectados_ids": []}, headers=h
    )
    assert r4.json()["departamentos_afectados"] == []


async def test_vista_por_departamento_etiqueta_relacion(client):
    """La vista por Departamento devuelve tanto los SOPs propios como los que
    afectan a ese departamento, cada uno etiquetado con su relación (§ pedido owner)."""
    h = await _headers(client)
    d1, d2 = await _dos_departamentos(client, h)
    propio = (
        await client.post(
            "/api/sops",
            json={"area_codigo": "GOV", "nombre": "Propio de d1", "departamento_id": d1},
            headers=h,
        )
    ).json()
    afecta = (
        await client.post(
            "/api/sops",
            json={
                "area_codigo": "GOV", "nombre": "Afecta a d1",
                "departamento_id": d2, "departamentos_afectados_ids": [d1],
            },
            headers=h,
        )
    ).json()

    r = await client.get(f"/api/sops?departamento_relacionado_id={d1}&limit=200", headers=h)
    assert r.status_code == 200
    por_id = {i["id"]: i["relacion_departamento"] for i in r.json()["items"]}
    assert por_id[propio["id"]] == "propio"
    assert por_id[afecta["id"]] == "afecta"
    # la vista por área no etiqueta relación (None)
    r2 = await client.get("/api/sops?area=GOV&limit=200", headers=h)
    assert all(i["relacion_departamento"] is None for i in r2.json()["items"])
