"""Similitud de texto determinística para el laboratorio de intake.

Rankea SOPs existentes por parecido a un procedimiento nuevo, combinando la similitud
del NOMBRE (SequenceMatcher, muy señal) con el solape de vocabulario del CONTENIDO
(índice de Jaccard sobre tokens). Sin IA ni dependencias externas.
"""

import re
import unicodedata
from difflib import SequenceMatcher

_PESO_NOMBRE = 0.6
_PESO_CONTENIDO = 0.4


def _norm(s: str | None) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def _tokens(s: str | None) -> set[str]:
    return {t for t in _norm(s).split() if len(t) > 3}


def puntaje(nombre_a: str, texto_a: str, nombre_b: str, texto_b: str) -> float:
    """Puntaje de similitud 0..1 entre dos procedimientos (nombre + contenido)."""
    nr = SequenceMatcher(None, _norm(nombre_a), _norm(nombre_b)).ratio()
    ta, tb = _tokens(texto_a), _tokens(texto_b)
    jac = len(ta & tb) / len(ta | tb) if (ta or tb) else 0.0
    return round(_PESO_NOMBRE * nr + _PESO_CONTENIDO * jac, 4)
