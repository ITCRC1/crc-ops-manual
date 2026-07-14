"""Máquina de estados del documento master (§11, B4)."""

from app.models.base import EstadoDocumento as E

# Transiciones permitidas. `en_firma -> firmado` es automática (al completar firmas).
TRANSICIONES: dict[E, set[E]] = {
    E.borrador: {E.en_revision},
    E.en_revision: {E.en_firma, E.borrador},
    E.en_firma: {E.firmado, E.rechazado},
    E.rechazado: {E.en_revision},
    E.firmado: {E.archivado},
    E.archivado: set(),
}


def puede_transicionar(actual: E, nuevo: E) -> bool:
    return nuevo in TRANSICIONES.get(actual, set())
