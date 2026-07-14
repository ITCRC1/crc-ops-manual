"""Pruebas del motor de asignación por propiedad (E4.4): adoptar/adaptar/local,
merge de overrides, solo-firmado-asignable, retiro y sincronización."""

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


async def _crear_master(client, h, nombre, firmar=True):
    sop = (await client.post(
        "/api/sops", json={"area_codigo": "GOV", "nombre": nombre, "proposito": "base"}, headers=h
    )).json()
    if firmar:
        from sqlalchemy import select

        from app.core.db import AsyncSessionLocal
        from app.models.base import EstadoDocumento
        from app.models.sop import SopMaster

        async with AsyncSessionLocal() as db:
            m = (await db.execute(select(SopMaster).where(SopMaster.id == sop["id"]))).scalar_one()
            m.estado = EstadoDocumento.firmado
            await db.commit()
    return sop


async def test_adoptar_solo_firmado(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    # master en borrador NO es asignable (§7.4)
    borrador = await _crear_master(client, h, "Master borrador", firmar=False)
    r = await client.post(f"/api/propiedades/{cwl}/asignaciones",
                          json={"modo": "adoptado", "sop_master_id": borrador["id"]}, headers=h)
    assert r.status_code == 409, r.text
    # master firmado SÍ, y queda vigente heredando la firma
    firmado = await _crear_master(client, h, "Master firmado adoptar")
    r2 = await client.post(f"/api/propiedades/{cwl}/asignaciones",
                           json={"modo": "adoptado", "sop_master_id": firmado["id"]}, headers=h)
    assert r2.status_code == 201, r2.text
    d = r2.json()
    assert d["estado"] == "vigente" and d["modo"] == "adoptado" and d["version_fijada"] == 1


async def test_adaptar_merge_de_overrides(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    m = await _crear_master(client, h, "Master a adaptar")
    r = await client.post(f"/api/propiedades/{cwl}/asignaciones",
                          json={"modo": "adaptado", "sop_master_id": m["id"],
                                "overrides": {"proposito": "Propósito local CWL"}}, headers=h)
    assert r.status_code == 201, r.text
    ps = r.json()
    assert ps["estado"] == "borrador"  # adaptado requiere firma local
    det = (await client.get(f"/api/propiedad-sops/{ps['id']}", headers=h)).json()
    # el contenido efectivo = merge(master, overrides)
    assert det["contenido_efectivo"]["proposito"] == "Propósito local CWL"
    assert det["contenido_efectivo"]["nombre"] == "Master a adaptar"  # heredado del master


async def test_local_genera_codigo(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    r = await client.post(f"/api/propiedades/{cwl}/asignaciones",
                          json={"modo": "local",
                                "campos_locales": {"nombre": "SOP local CWL", "proposito": "x"}},
                          headers=h)
    assert r.status_code == 201, r.text
    ps = r.json()
    assert ps["sop_master_id"] is None
    assert ps["codigo_local"] and "-LOC-" in ps["codigo_local"]
    det = (await client.get(f"/api/propiedad-sops/{ps['id']}", headers=h)).json()
    assert det["contenido_efectivo"]["nombre"] == "SOP local CWL"


async def test_retiro_marca_asignaciones(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    m = await _crear_master(client, h, "Master a retirar")
    ps = (await client.post(f"/api/propiedades/{cwl}/asignaciones",
                            json={"modo": "adoptado", "sop_master_id": m["id"]}, headers=h)).json()
    # archivar el master (firmado → archivado) marca master_retirado en la asignación (§7.12)
    assert (await client.post(f"/api/sops/{m['id']}/archivar", headers=h)).status_code == 204
    det = (await client.get(f"/api/propiedad-sops/{ps['id']}", headers=h)).json()
    assert det["master_retirado"] is True
    assert det["estado"] == "vigente"  # sigue vigente pero marcada


async def test_sincronizar_actualiza_version(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    m = await _crear_master(client, h, "Master a sincronizar")
    ps = (await client.post(f"/api/propiedades/{cwl}/asignaciones",
                            json={"modo": "adoptado", "sop_master_id": m["id"]}, headers=h)).json()
    # simular versión nueva del master + bandera pendiente
    from sqlalchemy import select

    from app.core.db import AsyncSessionLocal
    from app.models.propiedad import PropiedadSop
    from app.models.sop import SopMaster

    async with AsyncSessionLocal() as db:
        mm = (await db.execute(select(SopMaster).where(SopMaster.id == m["id"]))).scalar_one()
        mm.version_actual = 3
        pp = (await db.execute(select(PropiedadSop).where(PropiedadSop.id == ps["id"]))).scalar_one()
        pp.requiere_actualizacion = True
        await db.commit()
    r = await client.post(f"/api/propiedad-sops/{ps['id']}/actualizar", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["version_fijada"] == 3 and r.json()["requiere_actualizacion"] is False


async def test_sugerencias_por_sistemas(client):
    h = await _headers(client)
    cwl = await _cwl_id()
    r = await client.get(f"/api/propiedades/{cwl}/sugerencias", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


async def test_adaptar_desde_adoptado_y_override_por_seccion(client):
    """Adoptar → adaptar (convierte) → override de UNA sección: lo local pisa esa sección
    y el resto sigue heredando del master (versión local del hotel, §7.9)."""
    h = await _headers(client)
    cwl = await _cwl_id()
    m = await _crear_master(client, h, "Master para adaptar por seccion")
    ps = (await client.post(f"/api/propiedades/{cwl}/asignaciones",
                            json={"modo": "adoptado", "sop_master_id": m["id"]}, headers=h)).json()
    assert ps["modo"] == "adoptado" and ps["estado"] == "vigente"
    # adaptar convierte a adaptado + borrador y expone el contenido del master
    r = await client.post(f"/api/propiedad-sops/{ps['id']}/adaptar", headers=h)
    assert r.status_code == 200, r.text
    det = r.json()
    assert det["modo"] == "adaptado" and det["estado"] == "borrador"
    assert det["contenido_master"]["nombre"] == "Master para adaptar por seccion"
    # override de una sola sección
    r2 = await client.put(f"/api/propiedad-sops/{ps['id']}/overrides",
                          json={"overrides": {"proposito": "Propósito local del hotel"}}, headers=h)
    assert r2.status_code == 200, r2.text
    d2 = r2.json()
    assert d2["overrides"]["proposito"] == "Propósito local del hotel"
    assert d2["contenido_efectivo"]["proposito"] == "Propósito local del hotel"  # local pisa
    assert d2["contenido_efectivo"]["nombre"] == "Master para adaptar por seccion"  # resto hereda
    # no se puede adaptar dos veces
    assert (await client.post(f"/api/propiedad-sops/{ps['id']}/adaptar", headers=h)).status_code == 409
