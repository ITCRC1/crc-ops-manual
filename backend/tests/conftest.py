"""Fixtures de test. Cliente HTTP async sobre la app ASGI, compartiendo un solo
event loop de sesión para evitar conflictos de conexiones asyncpg entre loops."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.rate_limit import _intentos
from app.main import app


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    """El limitador de login/firma es estado en memoria del proceso; sin reset se
    acumula entre tests y el suite completo supera el umbral (10/5min) según el orden.
    Se limpia antes y después de cada test para aislar el rate limiting."""
    _intentos.clear()
    yield
    _intentos.clear()


@pytest_asyncio.fixture(loop_scope="session")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
