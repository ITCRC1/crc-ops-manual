"""Rate limiting simple en memoria para endpoints sensibles (login, firma) — §14.

Ventana deslizante por (clave). Suficiente para una sola instancia; en despliegue
multi-instancia debería respaldarse con Redis (pendiente documentado).
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

_intentos: dict[str, deque] = defaultdict(deque)


class RateLimiter:
    def __init__(self, max_intentos: int, ventana_seg: int, nombre: str = "acción"):
        self.max = max_intentos
        self.ventana = ventana_seg
        self.nombre = nombre

    async def __call__(self, request: Request) -> None:
        ip = request.client.host if request.client else "desconocida"
        clave = f"{request.url.path}:{ip}"
        ahora = time.monotonic()
        cola = _intentos[clave]
        while cola and ahora - cola[0] > self.ventana:
            cola.popleft()
        if len(cola) >= self.max:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Demasiados intentos de {self.nombre}. Reintentá en unos minutos.",
            )
        cola.append(ahora)


# Login: 10 intentos / 5 min por IP. Firma: 20 / 5 min por IP.
limite_login = RateLimiter(10, 300, "inicio de sesión")
limite_firma = RateLimiter(20, 300, "firma")
