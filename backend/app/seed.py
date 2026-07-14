"""Seed de Etapa 2: catálogos, configuración, usuarios y marco institucional (§10.8, E2).

Idempotente: se puede correr varias veces sin duplicar.

Uso:
    python -m app.seed
"""

import asyncio
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.core.seguridad import hash_password
from app.models import (
    Area,
    Configuracion,
    Departamento,
    Division,
    MarcoInstitucional,
    Propiedad,
    RolUsuarioAsignado,
    Sistema,
    Usuario,
)
from app.models.base import RolUsuario

SEED_SOURCE = Path(__file__).resolve().parents[1].parent / "seed" / "source"
MANUAL_DOCX = SEED_SOURCE / "Manual_Sop___Hotel_Corcovado_FINAL_con_manifiesto.docx"

WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# --- Datos de catálogo ---

PROPIEDADES = [
    ("CWL", "Corcovado Wilderness Lodge", "Corcovado Wilderness Lodge S.A."),
    ("AMA", "Amarena", "Amarena S.A."),
    ("OXI", "Oxigen", "Oxigen S.A."),
    ("OJO", "Ojochal Garden Villas", "Ojochal Garden Villas S.A."),
]

# Prefijos y nombres del índice curado de 74 (columna "Área" del Excel = taxonomía del master).
AREAS = [
    ("FIN", "Finanzas"),
    ("GE", "Guest Experience"),
    ("SM", "Sales & Marketing"),
    ("KIT", "Cocina"),
    ("FBS", "F&B"),
    ("HR", "RRHH"),
    ("IT", "IT"),
    ("CT", "Caja & Tesorería"),
    ("GOV", "Gobierno"),
    ("CR", "Crisis"),
    ("MANT", "Mantenimiento"),
]

SISTEMAS = [
    ("OPERA", "OPERA Cloud", "PMS"),
    ("SIMPHONY", "Simphony", "POS"),
    ("SKILLS4IT", "Skills4IT", "POS"),
    ("SITEMINDER", "SiteMinder", "channel manager / tarifas"),
    ("SYNXIS", "SynXis Central Reservation System", "CRS / central de reservas"),
    ("HUBSPOT", "HubSpot", "CRM"),
    ("INTEGRITY", "Integrity", "back office / contable"),
    ("QUICKBOOKS", "QuickBooks", "contable"),
    ("INVENTORY", "Inventory Management", "inventario"),
    ("STARLINK", "Starlink", "conectividad"),
    ("SOLAR", "Paneles solares", "energía"),
    ("GENERADOR", "Generadores", "energía"),
    ("MARITIMO", "Operación marítima (botes)", "transporte"),
]

# Departamentos estándar (propiedad_propietaria_id NULL = estándar del grupo).
DEPARTAMENTOS = [
    ("REC", "Recepción"),
    ("HK", "Ama de Llaves"),
    ("FB", "Alimentos y Bebidas"),
    ("KIT", "Cocina"),
    ("MANT", "Mantenimiento"),
    ("FIN", "Finanzas y Contabilidad"),
    ("SM", "Ventas y Mercadeo"),
    ("HR", "Recursos Humanos"),
    ("IT", "Tecnología de Información"),
    ("GG", "Gerencia General"),
    ("SEG", "Seguridad"),
    ("RES", "Reservas"),
    ("TOURS", "Experiencias y Tours"),
    # Departamentos por particularidad de la propiedad (mapeo de posiciones USALI, 2026-07-05)
    ("SPA", "Spa"),
    ("LAV", "Lavandería"),
    ("TRA", "Transporte"),
    ("CEM", "Comedor de Empleados"),
    ("CONC", "Concierge"),
    ("CMP", "Compras"),
    # Sub-departamentos de Mercadeo y Ventas
    ("REV", "Revenue"),
    ("MKD", "Mercadeo Digital"),
    ("CVE", "Coordinación de Ventas"),
    # Departamentos de las subdivisiones de Recursos Humanos
    ("PLA", "Planilla"),
    ("EYD", "Entrenamiento y Desarrollo"),
    ("CTR", "Contratación"),
    # Utilities dentro de Mantenimiento; Bodegas y Área de Recibo dentro de Finanzas (junto a Compras)
    ("UTL", "Utilities"),
    ("BOD", "Bodegas"),
    ("RCB", "Área de Recibo"),
    # Departamentos de negocio propios (uno por su división)
    ("CLM", "Club Madresal"),
    ("ARE", "Área Recreativa"),
]

# Divisiones funcionales del organigrama. (codigo, nombre, parent_codigo|None, orden)
# Las subdivisiones de Operaciones tienen parent = "OPS".
DIVISIONES = [
    ("OPS", "División de Operaciones", None, 1),
    ("DMV", "División de Mercadeo y Ventas", None, 2),
    ("DFIN", "División de Finanzas", None, 3),
    ("DRH", "División de Recursos Humanos", None, 4),
    # Divisiones de negocio propias de la propiedad (línea máxima)
    ("DCM", "División Club Madresal", None, 5),
    ("DAR", "División Área Recreativa", None, 6),
    # Subdivisiones dentro de Operaciones
    ("SD-HAB", "Habitaciones", "OPS", 1),
    ("SD-AYB", "Alimentos y Bebidas", "OPS", 2),
    ("SD-MNT", "Mantenimiento", "OPS", 3),
    # Subdivisiones dentro de Recursos Humanos
    ("SD-PLA", "Planilla", "DRH", 1),
    ("SD-EYD", "Entrenamiento y Desarrollo", "DRH", 2),
    ("SD-CTR", "Contratación", "DRH", 3),
    # Subdivisión dentro de Finanzas: Compras (con Bodegas y Área de Recibo)
    ("SD-CMP", "Compras", "DFIN", 1),
]

# Departamento (código) -> división/subdivisión (código) a la que pertenece.
# Gerencia General (GG) queda sin división: es el ápice del organigrama.
DEPTO_DIVISION = {
    # Operaciones · Habitaciones
    "REC": "SD-HAB", "CONC": "SD-HAB", "HK": "SD-HAB",
    # Operaciones · Alimentos y Bebidas (Comedor de Empleados va acá)
    "FB": "SD-AYB", "KIT": "SD-AYB", "CEM": "SD-AYB",
    # Operaciones · Mantenimiento (incluye Utilities)
    "MANT": "SD-MNT", "UTL": "SD-MNT",
    # Operaciones · directos (Lavandería y Transporte directos, sin subdivisión)
    "SPA": "OPS", "TOURS": "OPS", "LAV": "OPS", "TRA": "OPS",
    # Mercadeo y Ventas (dirección + sub-departamentos)
    "SM": "DMV", "RES": "DMV", "REV": "DMV", "MKD": "DMV", "CVE": "DMV",
    # Finanzas: directos (Finanzas y Contabilidad, TI, Seguridad) + subdivisión Compras
    "FIN": "DFIN", "IT": "DFIN", "SEG": "DFIN",
    # Subdivisión Compras: el propio departamento de Compras + Bodegas + Área de Recibo
    "CMP": "SD-CMP", "BOD": "SD-CMP", "RCB": "SD-CMP",
    # Recursos Humanos (dirección + subdivisiones)
    "HR": "DRH", "PLA": "SD-PLA", "EYD": "SD-EYD", "CTR": "SD-CTR",
    # Divisiones de negocio propias (un departamento por división)
    "CLM": "DCM", "ARE": "DAR",
}

CONFIGURACION = [
    (
        "nivel_minimo_firmante",
        "3",
        "int",
        "Nivel jerárquico mínimo elegible como firmante (B1).",
        True,
    ),
]

ADMIN_EMAIL = "Finance@thecostaricacollection.com"
ADMIN_PASSWORD = "CambiarCRC2026!"  # provisional — cambiar tras el primer ingreso


def _parrafos_docx(path: Path) -> list[str]:
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("word/document.xml"))
    out = []
    for para in root.iter(WORD_NS + "p"):
        txt = "".join(t.text or "" for t in para.iter(WORD_NS + "t")).strip()
        if txt:
            out.append(txt)
    return out


def extraer_marco_institucional() -> dict:
    """Extrae la Sección 0 (marco institucional) del manual, fiel a la fuente."""
    if not MANUAL_DOCX.exists():
        return {}
    p = _parrafos_docx(MANUAL_DOCX)

    def bloque(desde_contiene: str, hasta_contiene: str) -> list[str]:
        ini = next((i for i, t in enumerate(p) if desde_contiene in t), None)
        fin = next((i for i, t in enumerate(p) if hasta_contiene in t), None)
        if ini is None or fin is None:
            return []
        return p[ini + 1 : fin]

    # Los bloques de listas traen una frase introductoria que termina en ":"; se descarta.
    def sin_intro(items: list[str]) -> list[str]:
        return [t for t in items if not t.rstrip().endswith(":")]

    valores = sin_intro(bloque("0.2.1 Valores", "0.2.2 Visi"))
    objetivos = sin_intro(bloque("0.2.4 Objetivos", "0.2.5 Declaraci"))
    manifiesto = bloque("0.3 Culture", "0.4 Relaci")

    def uno(contiene: str) -> str | None:
        idx = next((i for i, t in enumerate(p) if contiene in t), None)
        return p[idx + 1] if idx is not None and idx + 1 < len(p) else None

    return {
        "vision": uno("0.2.2 Visi"),
        "mision": uno("0.2.3 Misi"),
        "valores": valores,
        "objetivos_estrategicos": objetivos,
        "declaracion_valor": uno("0.2.5 Declaraci"),
        "manifiesto": "\n\n".join(manifiesto) if manifiesto else None,
    }


async def _primero(db, stmt):
    return (await db.execute(stmt)).scalar_one_or_none()


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # Configuración
        for clave, valor, tipo, desc, editable in CONFIGURACION:
            if not await _primero(db, select(Configuracion).where(Configuracion.clave == clave)):
                db.add(
                    Configuracion(
                        clave=clave, valor=valor, tipo=tipo, descripcion=desc, editable=editable
                    )
                )

        # Propiedades
        for codigo, nombre, razon in PROPIEDADES:
            if not await _primero(db, select(Propiedad).where(Propiedad.codigo == codigo)):
                db.add(Propiedad(codigo=codigo, nombre=nombre, razon_social=razon))

        # Áreas (sincroniza el nombre si cambió — taxonomía del master)
        for codigo, nombre in AREAS:
            area = await _primero(db, select(Area).where(Area.codigo == codigo))
            if not area:
                db.add(Area(codigo=codigo, nombre=nombre))
            elif area.nombre != nombre:
                area.nombre = nombre

        # Sistemas (sincroniza nombre/categoría; el catálogo refleja el stack real de CRC)
        for codigo, nombre, categoria in SISTEMAS:
            s = await _primero(db, select(Sistema).where(Sistema.codigo == codigo))
            if not s:
                db.add(Sistema(codigo=codigo, nombre=nombre, categoria=categoria))
            else:
                s.nombre, s.categoria = nombre, categoria

        # Departamentos estándar
        for codigo, nombre in DEPARTAMENTOS:
            existe = await _primero(
                db,
                select(Departamento).where(
                    Departamento.codigo == codigo,
                    Departamento.propiedad_propietaria_id.is_(None),
                ),
            )
            if not existe:
                db.add(Departamento(codigo=codigo, nombre=nombre, propiedad_propietaria_id=None))

        # Divisiones (dos pasadas: primero las raíz, luego resolver parent y sincronizar nombre).
        for codigo, nombre, _parent, orden in DIVISIONES:
            div = await _primero(db, select(Division).where(Division.codigo == codigo))
            if not div:
                db.add(Division(codigo=codigo, nombre=nombre, orden=orden))
            else:
                div.nombre, div.orden = nombre, orden
        await db.flush()
        divs = {d.codigo: d for d in (await db.execute(select(Division))).scalars()}
        for codigo, _nombre, parent, _orden in DIVISIONES:
            div = divs.get(codigo)
            padre = divs.get(parent) if parent else None
            if div and div.parent_id != (padre.id if padre else None):
                div.parent_id = padre.id if padre else None

        # Asignar cada departamento estándar a su división/subdivisión.
        for dcod, divcod in DEPTO_DIVISION.items():
            depto = await _primero(
                db,
                select(Departamento).where(
                    Departamento.codigo == dcod,
                    Departamento.propiedad_propietaria_id.is_(None),
                ),
            )
            destino = divs.get(divcod)
            if depto and destino and depto.division_id != destino.id:
                depto.division_id = destino.id

        # Marco institucional (desde Sección 0 del manual)
        marco = select(MarcoInstitucional).where(MarcoInstitucional.activo.is_(True))
        if not await _primero(db, marco):
            m = extraer_marco_institucional()
            db.add(
                MarcoInstitucional(
                    vision=m.get("vision"),
                    mision=m.get("mision"),
                    objetivos_estrategicos=m.get("objetivos_estrategicos") or [],
                    valores=m.get("valores") or [],
                    declaracion_valor=m.get("declaracion_valor"),
                    manifiesto=m.get("manifiesto"),
                    version=1,
                    activo=True,
                )
            )

        # Usuario administrador inicial (super_admin, alcance corporativo)
        admin = await _primero(db, select(Usuario).where(Usuario.email == ADMIN_EMAIL))
        if not admin:
            admin = Usuario(
                nombre="Administrador CRC",
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                nivel_jerarquico=1,
                activo=True,
            )
            db.add(admin)
            await db.flush()
            db.add(
                RolUsuarioAsignado(
                    usuario_id=admin.id, rol=RolUsuario.super_admin, propiedad_id=None
                )
            )

        await db.commit()

    print("Seed completado.")
    print(f"  Admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}  (cambiar tras el primer ingreso)")


if __name__ == "__main__":
    asyncio.run(seed())
