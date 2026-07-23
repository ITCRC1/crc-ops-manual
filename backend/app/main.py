from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auditoria,
    auth,
    busqueda,
    catalogos,
    descriptores,
    firma,
    intake,
    organigrama,
    programacion,
    propiedad_armador,
    propiedad_sops,
    propiedad_training,
    sops,
    training,
    usuarios,
)
from app.core.config import get_settings
from app.sso_guard import SsoGuardMiddleware

settings = get_settings()

app = FastAPI(title=settings.app_name)

# Guardia SSO corporativo: exige la cookie `crc_sso` en toda ruta salvo PUBLIC_PREFIXES.
# Se registra ANTES del CORS a propósito: en Starlette el último add_middleware queda como el
# más externo, así que CORS debe ir después para envolver al guardia y responder los preflight
# OPTIONS (que llegan sin cookie); si no, el guardia los cortaría con 401 y el navegador
# bloquearía toda llamada del frontend.
app.add_middleware(SsoGuardMiddleware)

# CORS allowlist explícita al origen del frontend (nunca "*", §14).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sops.router)
app.include_router(firma.router)
app.include_router(propiedad_sops.router)
app.include_router(propiedad_armador.router)
app.include_router(propiedad_training.router)
app.include_router(descriptores.router)
app.include_router(organigrama.router)
app.include_router(busqueda.router)
app.include_router(auditoria.router)
app.include_router(catalogos.router)
app.include_router(usuarios.router)
app.include_router(training.router)
app.include_router(programacion.router)
app.include_router(intake.router)


@app.get("/api/salud")
def salud() -> dict[str, str]:
    return {"estado": "ok", "entorno": settings.entorno}
