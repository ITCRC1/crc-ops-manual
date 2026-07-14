"""Auditoría y custodia documental (§8.8, §8.18, §7.7, §7.18, §14).

Solo roles corporativos y el custodio documental consultan la trazabilidad transversal,
el inventario de documentos controlados, su bitácora de accesos/cambios y la
verificación de integridad por hash SHA-256.
"""

import hashlib
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, require_rol
from app.core.db import get_db
from app.firma.almacenamiento import leer_pdf
from app.models.auditoria import BitacoraControl, RegistroAuditoria
from app.models.base import RolUsuario
from app.models.sop import DocumentoControlado, SopMaster
from app.schemas.auditoria import (
    AuditoriaLista,
    BitacoraControlOut,
    DocumentoControladoItem,
    DocumentoControladoLista,
    RegistroAuditoriaOut,
    VerificacionIntegridad,
)
from app.services.auditoria import bitacora

router = APIRouter(tags=["auditoria"])

# Acceso a la traza y a los controlados: corporativo + custodio (§14, §8.18).
auditor = require_rol(
    RolUsuario.super_admin,
    RolUsuario.editor_corporativo,
    RolUsuario.custodio_documental,
)


@router.get("/api/auditoria", response_model=AuditoriaLista)
async def listar_auditoria(
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(auditor),
    entidad: str | None = None,
    entidad_id: uuid.UUID | None = None,
    usuario_id: uuid.UUID | None = None,
    accion: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> AuditoriaLista:
    filtros = []
    if entidad:
        filtros.append(RegistroAuditoria.entidad == entidad)
    if entidad_id:
        filtros.append(RegistroAuditoria.entidad_id == entidad_id)
    if usuario_id:
        filtros.append(RegistroAuditoria.usuario_id == usuario_id)
    if accion:
        filtros.append(RegistroAuditoria.accion.ilike(f"%{accion}%"))
    if desde:
        filtros.append(RegistroAuditoria.creado_en >= desde)
    if hasta:
        filtros.append(RegistroAuditoria.creado_en <= hasta)

    total = (
        await db.execute(select(func.count()).select_from(RegistroAuditoria).where(*filtros))
    ).scalar_one()
    filas = (
        await db.execute(
            select(RegistroAuditoria)
            .where(*filtros)
            .order_by(RegistroAuditoria.creado_en.desc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars()
    items = [
        RegistroAuditoriaOut(
            id=r.id, usuario_id=r.usuario_id, entidad=r.entidad, entidad_id=r.entidad_id,
            accion=r.accion, detalle=r.detalle, ip=r.ip, creado_en=r.creado_en,
        )
        for r in filas
    ]
    return AuditoriaLista(total=total, items=items)


@router.get("/api/documentos-controlados", response_model=DocumentoControladoLista)
async def listar_documentos_controlados(
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(auditor),
    sop_master_id: uuid.UUID | None = None,
    solo_vigentes: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> DocumentoControladoLista:
    filtros = []
    if sop_master_id:
        filtros.append(DocumentoControlado.sop_master_id == sop_master_id)
    if solo_vigentes:
        filtros.append(DocumentoControlado.es_vigente.is_(True))

    total = (
        await db.execute(select(func.count()).select_from(DocumentoControlado).where(*filtros))
    ).scalar_one()
    filas = list(
        (await db.execute(
            select(DocumentoControlado)
            .where(*filtros)
            .order_by(DocumentoControlado.creado_en.desc())
            .limit(limit)
            .offset(offset)
        )).scalars()
    )
    sop_ids = {d.sop_master_id for d in filas}
    sops = {
        s.id: s
        for s in (await db.execute(select(SopMaster).where(SopMaster.id.in_(sop_ids)))).scalars()
    } if sop_ids else {}
    items = [
        DocumentoControladoItem(
            id=d.id, sop_master_id=d.sop_master_id,
            sop_codigo=sops[d.sop_master_id].codigo if d.sop_master_id in sops else None,
            sop_nombre=sops[d.sop_master_id].nombre if d.sop_master_id in sops else None,
            version=d.version, hash_pdf=d.hash_pdf, fecha_firma=d.fecha_firma,
            es_vigente=d.es_vigente, custodio_id=d.custodio_id, creado_en=d.creado_en,
        )
        for d in filas
    ]
    return DocumentoControladoLista(total=total, items=items)


async def _get_doc(db: AsyncSession, doc_id: uuid.UUID) -> DocumentoControlado:
    doc = (
        await db.execute(select(DocumentoControlado).where(DocumentoControlado.id == doc_id))
    ).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento controlado no encontrado")
    return doc


@router.get(
    "/api/documentos-controlados/{doc_id}/bitacora",
    response_model=list[BitacoraControlOut],
)
async def listar_bitacora(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), _: UsuarioActual = Depends(auditor),
) -> list[BitacoraControlOut]:
    await _get_doc(db, doc_id)
    filas = (
        await db.execute(
            select(BitacoraControl)
            .where(BitacoraControl.documento_controlado_id == doc_id)
            .order_by(BitacoraControl.creado_en.desc())
        )
    ).scalars()
    return [
        BitacoraControlOut(
            id=b.id, documento_controlado_id=b.documento_controlado_id, accion=b.accion,
            detalle=b.detalle, usuario_id=b.usuario_id, creado_en=b.creado_en,
        )
        for b in filas
    ]


@router.post(
    "/api/documentos-controlados/{doc_id}/verificar-integridad",
    response_model=VerificacionIntegridad,
)
async def verificar_integridad(
    doc_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(auditor),
) -> VerificacionIntegridad:
    """Recalcula el SHA-256 del PDF archivado y lo compara con el hash registrado al
    firmar (§14). Deja constancia del acceso en la bitácora (§7.7)."""
    doc = await _get_doc(db, doc_id)
    contenido = leer_pdf(doc.pdf_storage_key) if doc.pdf_storage_key else None
    if contenido is None:
        bitacora(db, doc.id, actual.id, "verificacion_integridad",
                 {"resultado": "archivo_no_disponible"})
        await db.commit()
        return VerificacionIntegridad(
            documento_controlado_id=doc.id, integro=False, hash_esperado=doc.hash_pdf,
            hash_actual=None, mensaje="El archivo del documento no está disponible.",
        )
    hash_actual = hashlib.sha256(contenido).hexdigest()
    integro = hash_actual == doc.hash_pdf
    bitacora(db, doc.id, actual.id, "verificacion_integridad",
             {"integro": integro, "hash_actual": hash_actual})
    await db.commit()
    return VerificacionIntegridad(
        documento_controlado_id=doc.id, integro=integro, hash_esperado=doc.hash_pdf,
        hash_actual=hash_actual,
        mensaje="Integridad verificada: el documento no ha sido alterado." if integro
        else "¡Alerta! El hash no coincide: el documento pudo haber sido alterado.",
    )
