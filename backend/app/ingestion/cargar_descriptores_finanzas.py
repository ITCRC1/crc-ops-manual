"""Etapa 3+ — Carga de 3 Descriptores de Puesto de Finanzas (JD-025/026/027).

Adaptados a CRC desde descriptores reales de un hotel CR comparable (contenido propio,
sin datos sensibles ni marca ajena; ver seed/ingesta/jd_finanzas.json). Resuelve reporta_a
por título (incluyendo descriptores existentes y los nuevos) y crea snapshot v1. Idempotente.

Uso:
    python -m app.ingestion.cargar_descriptores_finanzas
"""

import asyncio
import json
import re
import unicodedata
from pathlib import Path

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.ingestion.cargar_sops import _uno
from app.models import Departamento, DescriptorPuestoMaster, DescriptorPuestoVersion, Usuario
from app.models.base import EstadoDocumento

RAIZ = Path(__file__).resolve().parents[3]
ING = RAIZ / "seed" / "ingesta"
ADMIN_EMAIL = "Finance@thecostaricacollection.com"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


async def cargar() -> None:
    jds = json.loads((ING / "jd_finanzas.json").read_text(encoding="utf-8"))["jds"]

    def por_codigo(cod):
        return select(DescriptorPuestoMaster).where(DescriptorPuestoMaster.codigo == cod)

    async with AsyncSessionLocal() as db:
        admin = await _uno(db, select(Usuario).where(Usuario.email == ADMIN_EMAIL))
        fin = await _uno(db, select(Departamento).where(
            Departamento.codigo == "FIN", Departamento.propiedad_propietaria_id.is_(None)))

        creados = 0
        for j in jds:
            d = j["jd"]
            if await _uno(db, por_codigo(j["clave"])):
                continue
            db.add(DescriptorPuestoMaster(
                codigo=j["clave"], titulo=d["titulo"],
                departamento_id=fin.id if fin else None,
                nivel_jerarquico=d["nivel_jerarquico"],
                proposito=d.get("proposito"),
                responsabilidades=d.get("responsabilidades", []),
                nivel_autoridad=d.get("nivel_autoridad"),
                kpis=d.get("kpis", []),
                requisitos=d.get("requisitos"),
                estado=EstadoDocumento.borrador, version_actual=1,
            ))
            creados += 1

        # Resolver reporta_a por título (contra TODOS los descriptores, incl. nuevos)
        todos = list((await db.execute(select(DescriptorPuestoMaster))).scalars())
        por_norm = {}
        for x in todos:
            por_norm.setdefault(_norm(x.titulo), x)
        resueltos = 0
        for j in jds:
            d = await _uno(db, por_codigo(j["clave"]))
            if not d:
                continue
            ra = _norm(j["jd"].get("reporta_a_titulo", ""))
            dest = None
            # match: título del jefe contenido en el texto reporta_a o viceversa
            for norm_t, obj in por_norm.items():
                if norm_t and norm_t != _norm(d.titulo) and (norm_t in ra or ra in norm_t):
                    dest = obj
                    break
            if dest and d.reporta_a_id != dest.id:
                d.reporta_a_id = dest.id
                resueltos += 1
            ver_stmt = select(DescriptorPuestoVersion).where(
                DescriptorPuestoVersion.descriptor_puesto_master_id == d.id)
            if not await _uno(db, ver_stmt):
                db.add(DescriptorPuestoVersion(
                    descriptor_puesto_master_id=d.id, version=1,
                    snapshot={"codigo": d.codigo, "titulo": d.titulo,
                              "origen": "descriptor de finanzas adaptado (fuente real CR)",
                              "nivel_jerarquico": d.nivel_jerarquico,
                              "reporta_a": j["jd"].get("reporta_a_titulo"),
                              "responsabilidades": d.responsabilidades, "kpis": d.kpis},
                    nota_cambio="Carga inicial (descriptor de finanzas adaptado a CRC).",
                    estado_en_version="borrador",
                    creado_por=admin.id if admin else None,
                ))
        await db.commit()
    print(f"Descriptores de finanzas creados: {creados}  | reporta_a resueltos: {resueltos}")


if __name__ == "__main__":
    asyncio.run(cargar())
