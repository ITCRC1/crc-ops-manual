"""Numeración atómica de SOPs por área (§7.2).

El siguiente número se toma bajo bloqueo transaccional (SELECT ... FOR UPDATE) sobre
el contador del área, de modo que dos creaciones concurrentes nunca obtengan el mismo
número. Los números de SOPs eliminados NO se reutilizan (el contador solo avanza).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalogos import (
    Area,
    ContadorArea,
    ContadorDescriptor,
    ContadorLocal,
    Propiedad,
)
from app.models.puesto import DescriptorPuestoMaster


async def siguiente_codigo_area(db: AsyncSession, area: Area) -> tuple[int, str]:
    cont = (
        await db.execute(
            select(ContadorArea).where(ContadorArea.area_id == area.id).with_for_update()
        )
    ).scalar_one_or_none()
    if cont is None:
        cont = ContadorArea(area_id=area.id, ultimo_numero=0)
        db.add(cont)
        await db.flush()
    cont.ultimo_numero += 1
    numero = cont.ultimo_numero
    return numero, f"{area.codigo}-{numero:04d}"


async def siguiente_codigo_local(db: AsyncSession, propiedad: Propiedad) -> tuple[int, str]:
    """Código local por propiedad (§7.10), ej. CWL-LOC-0001."""
    cont = (
        await db.execute(
            select(ContadorLocal)
            .where(ContadorLocal.propiedad_id == propiedad.id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if cont is None:
        cont = ContadorLocal(propiedad_id=propiedad.id, ultimo_numero=0)
        db.add(cont)
        await db.flush()
    cont.ultimo_numero += 1
    numero = cont.ultimo_numero
    return numero, f"{propiedad.codigo}-LOC-{numero:04d}"


async def siguiente_codigo_descriptor(db: AsyncSession) -> tuple[int, str]:
    """Código global de descriptor de puesto (JD-###, §7.2).

    Bloquea la fila única del contador y la reconcilia con el mayor JD-### existente:
    los descriptores sembrados por la ingesta NO pasan por el contador, así que sin la
    reconciliación el primer alta por API colisionaría. Los números no se reutilizan.
    """
    cont = (
        await db.execute(select(ContadorDescriptor).with_for_update().limit(1))
    ).scalar_one_or_none()
    if cont is None:  # defensivo: la migración siembra la fila
        cont = ContadorDescriptor(ultimo_numero=0)
        db.add(cont)
        await db.flush()

    codigos = (
        await db.execute(
            select(DescriptorPuestoMaster.codigo).where(
                DescriptorPuestoMaster.codigo.like("JD-%")
            )
        )
    ).scalars()
    max_existente = 0
    for c in codigos:
        try:
            max_existente = max(max_existente, int(c.split("-")[1]))
        except (IndexError, ValueError):
            continue

    numero = max(cont.ultimo_numero, max_existente) + 1
    cont.ultimo_numero = numero
    return numero, f"JD-{numero:03d}"
