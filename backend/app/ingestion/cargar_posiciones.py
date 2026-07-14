"""Carga de posiciones/descriptores por particularidad de la propiedad (mapeo USALI).

Fuente: Positions_Mapping_OutputX.xlsx (todas las ocupaciones del hotel según USALI +
extras). Los descriptores ya existentes (JD-001..027) NO se duplican; acá se agregan las
posiciones de línea/supervisión que faltaban, con descriptor completo según el estándar de
9 campos. El contenido (propósito, responsabilidades, KPIs, requisitos) vive en
seed/ingesta/posiciones_contenido.json (redactado con criterio de industria hotelera CR,
contenido propio de CRC). Numeración JD-### atómica; reporta_a resuelto en dos pasadas
(códigos JD existentes o claves locales de este mismo lote). Idempotente por título+depto.

También reubica descriptores existentes a los departamentos nuevos:
  - JD-021 Supervisor de Concierge  -> CONC (Concierge)
  - JD-027 Coordinador de Compras    -> CMP  (Compras)

Uso:  python -m app.ingestion.cargar_posiciones
"""

import asyncio
import json
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select, update

from app.core.db import AsyncSessionLocal
from app.models import Departamento, DescriptorPuestoMaster, DescriptorPuestoVersion, Usuario
from app.models.base import EstadoDocumento
from app.services.numeracion import siguiente_codigo_descriptor

RAIZ = Path(__file__).resolve().parents[3]
CONTENIDO = RAIZ / "seed" / "ingesta" / "posiciones_contenido.json"
ADMIN_EMAIL = "Finance@thecostaricacollection.com"

# Estructura: (clave_local, titulo, depto_codigo, nivel_jerarquico, reporta_a)
# reporta_a = código JD existente ("JD-009") o clave_local de este lote.
POSICIONES = [
    # Dirección de operaciones en sitio (sin departamento: supervisa toda la operación)
    ("GRES", "Gerente Residente", None, 2, "JD-004"),
    # Recepción / Front Desk
    ("REC-2", "Gerente en Sitio", "REC", 2, "JD-004"),
    ("REC-3", "Asistente de Gerencia en Sitio", "REC", 3, "REC-2"),
    ("REC-1", "Agente de Recepción", "REC", 4, "JD-009"),
    # Concierge
    ("CONC-1", "Agente de Concierge", "CONC", 4, "JD-021"),
    ("CONC-2", "Agente de Experiencia de Clientes", "CONC", 4, "JD-021"),
    ("CONC-3", "Botones", "CONC", 4, "JD-021"),
    # Ama de Llaves / Lavandería
    ("HK-1", "Camarero(a) / Room Attendant", "HK", 4, "JD-010"),
    ("HK-2", "Asistente de Pasillo (Houseperson)", "HK", 4, "JD-010"),
    ("HK-3", "Encargado de Áreas Públicas", "HK", 4, "JD-010"),
    ("LAV-1", "Ayudante de Lavandería", "LAV", 4, "JD-010"),
    # Cocina / Comedor de Empleados
    ("KIT-1", "Cocinero A - Supervisor", "KIT", 3, "JD-020"),
    ("KIT-2", "Cocinero A", "KIT", 4, "KIT-1"),
    ("KIT-3", "Cocinero B", "KIT", 4, "KIT-1"),
    ("KIT-4", "Panadero", "KIT", 4, "KIT-1"),
    ("KIT-5", "Steward", "KIT", 4, "JD-020"),
    ("CEM-1", "Cocinero B - Comedor de Empleados", "CEM", 4, "JD-020"),
    # Alimentos y Bebidas / Restaurante
    ("FB-1", "Capitán de Saloneros", "FB", 3, "JD-011"),
    ("FB-2", "Bartender", "FB", 4, "FB-1"),
    # Mantenimiento / Transporte
    ("MANT-1", "Ayudante de Construcción", "MANT", 4, "JD-022"),
    ("MANT-2", "Jardinero", "MANT", 4, "JD-022"),
    ("MANT-3", "Mecánico", "MANT", 4, "JD-022"),
    ("MANT-4", "Operador de Campo", "MANT", 4, "JD-022"),
    ("MANT-5", "Operador de Habitaciones y Áreas Públicas", "MANT", 4, "JD-022"),
    ("MANT-6", "Operador de Salas y Áreas Públicas", "MANT", 4, "JD-022"),
    ("MANT-7", "Piscinero", "MANT", 4, "JD-022"),
    ("TRA-1", "Chofer", "TRA", 4, "JD-007"),
    # Reservas / Ventas / Finanzas
    ("RES-1", "Agente de Reservas", "RES", 4, "JD-013"),
    ("SM-1", "Agente de Ventas", "CVE", 4, "JD-005"),
    ("FIN-1", "Ejecutivo Contable", "FIN", 4, "JD-025"),
    # Seguridad
    ("SEG-1", "Supervisor de Oficiales de Seguridad", "SEG", 3, "JD-007"),
    ("SEG-2", "Oficial de Seguridad", "SEG", 4, "SEG-1"),
    # Spa
    ("SPA-1", "Supervisor(a) de Spa", "SPA", 3, "JD-007"),
    ("SPA-2", "Terapeuta de Spa", "SPA", 4, "SPA-1"),
    # Experiencias y Tours
    ("TOURS-1", "Capitán de Barco", "TOURS", 3, "JD-023"),
    ("TOURS-2", "Buceador (Divemaster)", "TOURS", 4, "JD-023"),
    ("TOURS-3", "Guía de Aventura", "TOURS", 4, "JD-023"),
    ("TOURS-4", "Guía Naturalista", "TOURS", 4, "JD-023"),
    # Recursos Humanos (jefatura de división + subdivisiones)
    ("HR-1", "Gerente de Recursos Humanos", "HR", 2, "JD-001"),
    ("PLA-1", "Encargado de Planilla", "PLA", 3, "HR-1"),
    ("EYD-1", "Coordinador de Entrenamiento y Desarrollo", "EYD", 3, "HR-1"),
    ("CTR-1", "Coordinador de Reclutamiento y Selección", "CTR", 3, "HR-1"),
    # Compras / Bodegas / Área de Recibo (dependen del Coordinador de Compras JD-027)
    ("CMP-2", "Asistente de Compras", "CMP", 4, "JD-027"),
    ("BOD-1", "Encargado de Bodega", "BOD", 3, "JD-027"),
    ("BOD-2", "Bodeguero / Auxiliar de Bodega", "BOD", 4, "BOD-1"),
    ("RCB-1", "Encargado de Recibo de Mercadería", "RCB", 3, "JD-027"),
    # Utilities (dentro de Mantenimiento)
    ("UTL-1", "Encargado de Utilities", "UTL", 3, "JD-022"),
    # División Club Madresal (manager + línea)
    ("CLM-1", "Gerente de Club Madresal", "CLM", 3, "JD-001"),
    ("CLM-2", "Host de Club Madresal", "CLM", 4, "CLM-1"),
    ("CLM-3", "Miscelánea de Club Madresal", "CLM", 4, "CLM-1"),
    ("CLM-4", "Encargado de Playa", "CLM", 4, "CLM-1"),
    # División Área Recreativa (manager + línea)
    ("ARE-1", "Gerente de Área Recreativa", "ARE", 3, "JD-001"),
    ("ARE-2", "Salvavidas", "ARE", 4, "ARE-1"),
    ("ARE-3", "Auxiliar de Gimnasio y Áreas Recreativas", "ARE", 4, "ARE-1"),
    # Recepción — puestos sueltos de Amarena
    ("REC-4", "Auditor Nocturno", "REC", 4, "JD-009"),
    ("REC-5", "Asistente Administrativo", "REC", 4, "JD-009"),
    ("REC-6", "Runner de Hotel", "REC", 4, "JD-009"),
    # Refuerzo de departamentos con un solo puesto (línea/apoyo)
    ("RCB-2", "Auxiliar de Recibo de Mercadería", "RCB", 4, "RCB-1"),
    ("PLA-2", "Auxiliar de Planilla", "PLA", 4, "PLA-1"),
    ("CTR-2", "Analista de Reclutamiento y Selección", "CTR", 4, "CTR-1"),
    ("HR-2", "Generalista de Recursos Humanos", "HR", 4, "HR-1"),
    ("EYD-2", "Facilitador de Capacitación", "EYD", 4, "EYD-1"),
    ("LAV-2", "Encargado de Lavandería", "LAV", 3, "JD-010"),
    ("TRA-2", "Coordinador de Transporte", "TRA", 3, "JD-007"),
    ("CEM-2", "Encargado de Comedor de Empleados", "CEM", 3, "JD-020"),
    ("UTL-2", "Operador de Utilities", "UTL", 4, "UTL-1"),
    ("CVE-2", "Coordinador de Ventas y Grupos", "CVE", 3, "JD-005"),
    ("MKD-2", "Community Manager", "MKD", 4, "JD-015"),
    ("REV-2", "Analista de Revenue", "REV", 4, "JD-014"),
    ("SM-2", "Asistente de Ventas y Mercadeo", "SM", 4, "JD-005"),
    ("IT-2", "Soporte Técnico de TI", "IT", 4, "JD-019"),
]

# Reubicación de descriptores existentes a los departamentos nuevos.
REUBICAR = {
    "JD-021": "CONC",   # Supervisor de Concierge
    "JD-027": "CMP",    # Coordinador de Compras
    "JD-014": "REV",    # Coordinador de Revenue Management
    "JD-015": "MKD",    # Coordinador de Marketing Digital
    "JD-010": "HK",     # Supervisor(a) de Housekeeping -> Ama de Llaves
    "JD-023": "TOURS",  # Supervisor de Capitanes -> Experiencias y Tours
}

# Puestos (por código) que deben reportar al Gerente Residente (clave local "GRES"):
# el Gerente Residente supervisa toda la operación por debajo del Director de Operaciones.
REPORTAN_A_GERENTE_RESIDENTE = ("JD-007", "JD-016")

# Duplicados a unificar: (identificador a eliminar, código superviviente). El
# identificador puede ser un código "JD-###" o "titulo:<Título exacto>". Los
# subordinados del eliminado se re-cuelgan del superviviente antes del soft-delete.
DEDUP_PUESTOS = [
    ("JD-016", "JD-007"),                    # Gerente de Operaciones (duplicado)
    ("JD-017", "JD-008"),                    # Asistente de Operaciones (duplicado)
    ("titulo:Gerente en Sitio", "JD-028"),   # Gerente en Sitio ≈ Gerente Residente
]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


async def _uno(db, stmt):
    return (await db.execute(stmt)).scalars().first()


async def cargar() -> None:
    contenido = {c["clave_local"]: c for c in json.loads(CONTENIDO.read_text(encoding="utf-8"))}

    async with AsyncSessionLocal() as db:
        admin = await _uno(db, select(Usuario).where(Usuario.email == ADMIN_EMAIL))
        deptos = {d.codigo: d for d in (await db.execute(
            select(Departamento).where(Departamento.propiedad_propietaria_id.is_(None))
        )).scalars()}

        # Índice por título normalizado (para no duplicar si ya existe uno equivalente).
        existentes = list((await db.execute(select(DescriptorPuestoMaster))).scalars())
        por_titulo = {_norm(x.titulo): x for x in existentes}

        clave_a_desc: dict[str, DescriptorPuestoMaster] = {}
        creados = 0
        for clave, titulo, dcod, nivel, _ra in POSICIONES:
            ya = por_titulo.get(_norm(titulo))
            if ya:
                clave_a_desc[clave] = ya
                # Reafirma el departamento declarado (permite re-mapear en re-corridas);
                # dcod None = puesto sin departamento (liderazgo transversal).
                if dcod is None:
                    nuevo_dep_id = None
                elif dcod in deptos:
                    nuevo_dep_id = deptos[dcod].id
                else:
                    nuevo_dep_id = ya.departamento_id  # dcod desconocido: no tocar
                if ya.departamento_id != nuevo_dep_id:
                    ya.departamento_id = nuevo_dep_id
                continue
            _num, codigo = await siguiente_codigo_descriptor(db)
            cont = contenido.get(clave, {})
            d = DescriptorPuestoMaster(
                codigo=codigo, titulo=titulo,
                departamento_id=deptos[dcod].id if dcod in deptos else None,
                nivel_jerarquico=nivel,
                proposito=cont.get("proposito"),
                responsabilidades=cont.get("responsabilidades", []),
                nivel_autoridad=cont.get("nivel_autoridad"),
                kpis=cont.get("kpis", []),
                requisitos=cont.get("requisitos"),
                estado=EstadoDocumento.borrador, version_actual=1,
            )
            db.add(d)
            await db.flush()
            clave_a_desc[clave] = d
            por_titulo[_norm(titulo)] = d
            db.add(DescriptorPuestoVersion(
                descriptor_puesto_master_id=d.id, version=1,
                snapshot={"codigo": d.codigo, "titulo": d.titulo, "nivel_jerarquico": nivel,
                          "origen": "posición USALI/propiedad (contenido propio CRC)",
                          "responsabilidades": d.responsabilidades, "kpis": d.kpis},
                nota_cambio="Carga inicial (posición mapeada desde USALI + particularidades).",
                estado_en_version="borrador", creado_por=admin.id if admin else None,
            ))
            creados += 1

        # Segunda pasada: resolver reporta_a (código JD existente o clave local del lote).
        resueltos = 0
        for clave, _t, _d, _n, ra in POSICIONES:
            d = clave_a_desc.get(clave)
            if not d:
                continue
            destino = None
            if ra in clave_a_desc:
                destino = clave_a_desc[ra]
            elif ra.startswith("JD-"):
                destino = await _uno(db, select(DescriptorPuestoMaster).where(
                    DescriptorPuestoMaster.codigo == ra))
            if destino and d.reporta_a_id != destino.id and destino.id != d.id:
                d.reporta_a_id = destino.id
                resueltos += 1

        # Reubicación de descriptores existentes a departamentos nuevos.
        reubicados = 0
        for cod, dcod in REUBICAR.items():
            d = await _uno(db, select(DescriptorPuestoMaster).where(
                DescriptorPuestoMaster.codigo == cod))
            if d and dcod in deptos and d.departamento_id != deptos[dcod].id:
                d.departamento_id = deptos[dcod].id
                reubicados += 1

        # Los Gerentes de Operaciones reportan al Gerente Residente (que a su vez cuelga
        # del Director de Operaciones), de modo que toda la operación queda bajo él.
        corregidos = 0
        gres = clave_a_desc.get("GRES")
        if gres:
            for cod in REPORTAN_A_GERENTE_RESIDENTE:
                d = await _uno(db, select(DescriptorPuestoMaster).where(
                    DescriptorPuestoMaster.codigo == cod))
                if d and d.id != gres.id and d.reporta_a_id != gres.id:
                    d.reporta_a_id = gres.id
                    corregidos += 1

        # Unificación de duplicados: re-cuelga subordinados al superviviente y soft-delete.
        eliminados = 0
        for ident, keep_cod in DEDUP_PUESTOS:
            if ident.startswith("titulo:"):
                elim = await _uno(db, select(DescriptorPuestoMaster).where(
                    DescriptorPuestoMaster.titulo == ident.split(":", 1)[1]))
            else:
                elim = await _uno(db, select(DescriptorPuestoMaster).where(
                    DescriptorPuestoMaster.codigo == ident))
            keep = await _uno(db, select(DescriptorPuestoMaster).where(
                DescriptorPuestoMaster.codigo == keep_cod))
            if not elim or elim.eliminado_en is not None or not keep or keep.id == elim.id:
                continue
            await db.execute(
                update(DescriptorPuestoMaster)
                .where(DescriptorPuestoMaster.reporta_a_id == elim.id)
                .values(reporta_a_id=keep.id)
            )
            elim.eliminado_en = datetime.now(UTC)
            eliminados += 1

        await db.commit()
    print(f"Posiciones: creadas {creados} | reporta_a resueltos {resueltos} | "
          f"reubicados {reubicados} | jerarquía corregida {corregidos} | "
          f"duplicados eliminados {eliminados}")


if __name__ == "__main__":
    asyncio.run(cargar())
