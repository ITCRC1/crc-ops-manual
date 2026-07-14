from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_salud_ok():
    respuesta = client.get("/api/salud")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "ok"
