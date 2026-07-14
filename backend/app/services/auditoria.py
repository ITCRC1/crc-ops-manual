"""Helpers de trazabilidad: registro de auditoría transversal y bitácora de controlados
(§7.7, §7.18)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auditoria import BitacoraControl, RegistroAuditoria


def auditar(
    db: AsyncSession,
    usuario_id: uuid.UUID | None,
    entidad: str,
    entidad_id: uuid.UUID | None,
    accion: str,
    detalle: dict | None = None,
    ip: str | None = None,
) -> None:
    db.add(RegistroAuditoria(
        usuario_id=usuario_id, entidad=entidad, entidad_id=entidad_id,
        accion=accion, detalle=detalle, ip=ip,
    ))


def bitacora(
    db: AsyncSession,
    documento_controlado_id: uuid.UUID,
    usuario_id: uuid.UUID | None,
    accion: str,
    detalle: dict | None = None,
) -> None:
    db.add(BitacoraControl(
        documento_controlado_id=documento_controlado_id, usuario_id=usuario_id,
        accion=accion, detalle=detalle,
    ))
