"""Colaboración, firma electrónica, máquina de estados y documento controlado
(§6, §7.3-7.7, §11, B1/B4/B5/B6)."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, get_current_user, require_rol
from app.core.config import get_settings
from app.core.db import get_db
from app.core.rate_limit import limite_firma
from app.firma.almacenamiento import guardar_pdf, leer_pdf
from app.firma.pdf import generar_pdf_controlado
from app.models.base import EstadoDocumento, RolUsuario
from app.models.catalogos import Area
from app.models.config import Configuracion
from app.models.propiedad import PropiedadSop
from app.models.sop import (
    ColaboradorSop,
    DocumentoControlado,
    FirmaElectronica,
    FirmanteSop,
    SopMaster,
)
from app.models.usuarios import Usuario
from app.schemas.firma import (
    ColaboradorCrear,
    ColaboradorOut,
    ColaboradoresLote,
    ColaboradoresLoteResultado,
    DocumentoControladoOut,
    FirmanteCrear,
    FirmanteOut,
    FirmarRequest,
    ReasignarRequest,
    RechazarRequest,
)
from app.services.auditoria import auditar, bitacora
from app.services.estados import puede_transicionar

router = APIRouter(prefix="/api/sops", tags=["firma"])
settings = get_settings()

editor = require_rol(RolUsuario.editor_corporativo, RolUsuario.super_admin)


async def _get_sop(db: AsyncSession, sop_id: uuid.UUID) -> SopMaster:
    sop = (await db.execute(select(SopMaster).where(SopMaster.id == sop_id))).scalar_one_or_none()
    if not sop or sop.eliminado_en is not None:
        raise HTTPException(status_code=404, detail="SOP no encontrado")
    return sop


async def _nivel_minimo_firmante(db: AsyncSession) -> int:
    cfg = (
        await db.execute(
            select(Configuracion).where(Configuracion.clave == "nivel_minimo_firmante")
        )
    ).scalar_one_or_none()
    try:
        return int(cfg.valor) if cfg else settings.nivel_minimo_firmante
    except (TypeError, ValueError):
        return settings.nivel_minimo_firmante


async def _transicion(db, sop, nuevo, actual, ip):
    if not puede_transicionar(sop.estado, nuevo):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transición inválida: {sop.estado.value} → {nuevo.value}",
        )
    anterior = sop.estado
    sop.estado = nuevo
    auditar(db, actual.id, "sop_master", sop.id, f"estado:{anterior.value}->{nuevo.value}", ip=ip)


# --- Transiciones (editor del ámbito) ---


@router.post("/{sop_id}/enviar-revision", status_code=204)
async def enviar_revision(
    sop_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
):
    sop = await _get_sop(db, sop_id)
    await _transicion(db, sop, EstadoDocumento.en_revision, actual, request.client.host)
    await db.commit()


@router.post("/{sop_id}/volver-borrador", status_code=204)
async def volver_borrador(
    sop_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
):
    sop = await _get_sop(db, sop_id)
    await _transicion(db, sop, EstadoDocumento.borrador, actual, request.client.host)
    await db.commit()


@router.post("/{sop_id}/retomar-revision", status_code=204)
async def retomar_revision(
    sop_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
):
    """rechazado → en_revision (§11)."""
    sop = await _get_sop(db, sop_id)
    await _transicion(db, sop, EstadoDocumento.en_revision, actual, request.client.host)
    await db.commit()


@router.post("/{sop_id}/enviar-firma", status_code=204)
async def enviar_firma(
    sop_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
):
    sop = await _get_sop(db, sop_id)
    firmantes = list(
        (await db.execute(select(FirmanteSop).where(FirmanteSop.sop_master_id == sop_id))).scalars()
    )
    obligatorios = [f for f in firmantes if f.obligatorio]
    if not obligatorios:
        raise HTTPException(status_code=409, detail="Designá al menos un firmante obligatorio.")
    # Segregación de funciones (§7.3): quien redacta en solitario no puede ser el único firmante.
    if len(obligatorios) == 1 and obligatorios[0].usuario_id == sop.creado_por:
        raise HTTPException(
            status_code=409,
            detail="Segregación de funciones: el único firmante no puede ser el propio autor. "
                   "Designá otro firmante.",
        )
    await _transicion(db, sop, EstadoDocumento.en_firma, actual, request.client.host)
    await db.commit()


@router.post("/{sop_id}/archivar", status_code=204)
async def archivar(
    sop_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db),
    actual: UsuarioActual = Depends(require_rol(RolUsuario.super_admin, RolUsuario.editor_corporativo)),
):
    sop = await _get_sop(db, sop_id)
    await _transicion(db, sop, EstadoDocumento.archivado, actual, request.client.host)
    # Retiro del master (§7.12, B3): las asignaciones quedan vigentes pero marcadas.
    await db.execute(
        update(PropiedadSop)
        .where(PropiedadSop.sop_master_id == sop.id, PropiedadSop.eliminado_en.is_(None))
        .values(master_retirado=True)
    )
    await db.commit()


# --- Firmantes y colaboradores ---


@router.post("/{sop_id}/firmantes", response_model=FirmanteOut, status_code=201)
async def designar_firmante(
    sop_id: uuid.UUID, datos: FirmanteCrear,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
):
    sop = await _get_sop(db, sop_id)
    if sop.estado not in {EstadoDocumento.borrador, EstadoDocumento.en_revision}:
        raise HTTPException(status_code=409, detail="Los firmantes se designan antes de enviar a firma.")
    usuario = (
        await db.execute(select(Usuario).where(Usuario.id == datos.usuario_id))
    ).scalar_one_or_none()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=404, detail="Usuario firmante no encontrado")
    nivel_min = await _nivel_minimo_firmante(db)
    if usuario.nivel_jerarquico > nivel_min:
        raise HTTPException(
            status_code=409,
            detail=f"El firmante debe tener nivel jerárquico ≤ {nivel_min} (B1). "
                   f"Nivel del usuario: {usuario.nivel_jerarquico}.",
        )
    f = FirmanteSop(
        sop_master_id=sop_id, usuario_id=datos.usuario_id,
        orden=datos.orden, obligatorio=datos.obligatorio,
    )
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return FirmanteOut(
        id=f.id, usuario_id=f.usuario_id, orden=f.orden, obligatorio=f.obligatorio, firmado=False
    )


@router.get("/{sop_id}/firmantes", response_model=list[FirmanteOut])
async def listar_firmantes(
    sop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), _: UsuarioActual = Depends(get_current_user),
):
    firmantes = list(
        (await db.execute(
            select(FirmanteSop).where(FirmanteSop.sop_master_id == sop_id).order_by(FirmanteSop.orden)
        )).scalars()
    )
    sop = await _get_sop(db, sop_id)
    firmados = {
        r.usuario_id
        for r in (await db.execute(
            select(FirmaElectronica).where(
                FirmaElectronica.sop_master_id == sop_id,
                FirmaElectronica.version == sop.version_actual,
            )
        )).scalars()
    }
    return [
        FirmanteOut(id=f.id, usuario_id=f.usuario_id, orden=f.orden,
                    obligatorio=f.obligatorio, firmado=f.usuario_id in firmados)
        for f in firmantes
    ]


@router.post("/{sop_id}/firmantes/{firmante_id}/reasignar", response_model=FirmanteOut)
async def reasignar_firmante(
    sop_id: uuid.UUID, firmante_id: uuid.UUID, datos: ReasignarRequest, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
):
    """Reasignar un firmante pendiente (que aún no firmó), §B6. Auditado."""
    sop = await _get_sop(db, sop_id)
    f = (
        await db.execute(
            select(FirmanteSop).where(FirmanteSop.id == firmante_id, FirmanteSop.sop_master_id == sop_id)
        )
    ).scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=404, detail="Firmante no encontrado")
    ya_firmo = (
        await db.execute(
            select(FirmaElectronica).where(
                FirmaElectronica.sop_master_id == sop_id,
                FirmaElectronica.version == sop.version_actual,
                FirmaElectronica.usuario_id == f.usuario_id,
            )
        )
    ).scalar_one_or_none()
    if ya_firmo:
        raise HTTPException(status_code=409, detail="No se puede reasignar un firmante que ya firmó.")
    nuevo = (
        await db.execute(select(Usuario).where(Usuario.id == datos.nuevo_usuario_id))
    ).scalar_one_or_none()
    nivel_min = await _nivel_minimo_firmante(db)
    if not nuevo or not nuevo.activo or nuevo.nivel_jerarquico > nivel_min:
        raise HTTPException(status_code=409, detail="El nuevo firmante no es elegible (nivel/estado).")
    anterior = f.usuario_id
    f.usuario_id = datos.nuevo_usuario_id
    auditar(db, actual.id, "firmante_sop", f.id, "reasignacion",
            {"anterior": str(anterior), "nuevo": str(datos.nuevo_usuario_id)}, request.client.host)
    await db.commit()
    await db.refresh(f)
    return FirmanteOut(id=f.id, usuario_id=f.usuario_id, orden=f.orden,
                       obligatorio=f.obligatorio, firmado=False)


async def _existe_colaborador(
    db: AsyncSession, sop_id: uuid.UUID, usuario_id: uuid.UUID, rol: str
) -> bool:
    fila = (await db.execute(
        select(ColaboradorSop).where(
            ColaboradorSop.sop_master_id == sop_id,
            ColaboradorSop.usuario_id == usuario_id,
            ColaboradorSop.rol_colaboracion == rol,
        )
    )).scalars().first()
    return fila is not None


@router.post("/colaboradores/lote", response_model=ColaboradoresLoteResultado)
async def invitar_colaboradores_lote(
    datos: ColaboradoresLote,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
) -> ColaboradoresLoteResultado:
    """N personas × M SOPs en una llamada. Idempotente.

    Declarada ANTES que `/{sop_id}/colaboradores` no hace falta (distinto largo de ruta),
    pero sí antes que cualquier `/{algo}` de un solo segmento."""
    if not datos.sop_ids or not datos.usuario_ids:
        raise HTTPException(status_code=422, detail="Elegí al menos un SOP y una persona.")
    creados = ya = 0
    for sop_id in datos.sop_ids:
        await _get_sop(db, sop_id)  # 404 si alguno no existe: no se invita a medias
        for usuario_id in datos.usuario_ids:
            if await _existe_colaborador(db, sop_id, usuario_id, datos.rol_colaboracion):
                ya += 1
                continue
            db.add(ColaboradorSop(
                sop_master_id=sop_id, usuario_id=usuario_id,
                rol_colaboracion=datos.rol_colaboracion, estado="invitado",
            ))
            creados += 1
    await db.commit()
    return ColaboradoresLoteResultado(creados=creados, ya_existian=ya)


@router.post("/{sop_id}/colaboradores", status_code=201)
async def invitar_colaborador(
    sop_id: uuid.UUID, datos: ColaboradorCrear,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
):
    """Un colaborador `redactor` puede editar la capa SMART de ESTE SOP (no el master)."""
    await _get_sop(db, sop_id)
    if await _existe_colaborador(db, sop_id, datos.usuario_id, datos.rol_colaboracion):
        return {"ok": True, "ya_existia": True}
    db.add(ColaboradorSop(
        sop_master_id=sop_id, usuario_id=datos.usuario_id,
        rol_colaboracion=datos.rol_colaboracion, seccion_asignada=datos.seccion_asignada,
        estado="invitado",
    ))
    await db.commit()
    return {"ok": True, "ya_existia": False}


@router.get("/{sop_id}/colaboradores", response_model=list[ColaboradorOut])
async def listar_colaboradores(
    sop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(get_current_user),
) -> list[ColaboradorOut]:
    """La lee cualquier autenticado: la ficha necesita saber si el usuario puede editar."""
    await _get_sop(db, sop_id)
    filas = (await db.execute(
        select(ColaboradorSop).where(ColaboradorSop.sop_master_id == sop_id)
    )).scalars().all()
    nombres = {u.id: u.nombre for u in (await db.execute(select(Usuario))).scalars()}
    return [
        ColaboradorOut(
            id=c.id, usuario_id=c.usuario_id, usuario_nombre=nombres.get(c.usuario_id),
            rol_colaboracion=c.rol_colaboracion, seccion_asignada=c.seccion_asignada,
            estado=c.estado,
        )
        for c in filas
    ]


@router.delete("/{sop_id}/colaboradores/{colaborador_id}", status_code=204)
async def revocar_colaborador(
    sop_id: uuid.UUID, colaborador_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(editor),
) -> Response:
    await db.execute(
        delete(ColaboradorSop).where(
            ColaboradorSop.id == colaborador_id, ColaboradorSop.sop_master_id == sop_id
        )
    )
    await db.commit()
    return Response(status_code=204)


# --- Firma electrónica y rechazo ---


@router.post("/{sop_id}/firmar", dependencies=[Depends(limite_firma)])
async def firmar(
    sop_id: uuid.UUID, datos: FirmarRequest, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    sop = await _get_sop(db, sop_id)
    if sop.estado != EstadoDocumento.en_firma:
        raise HTTPException(status_code=409, detail="El documento no está en proceso de firma.")
    firmantes = list(
        (await db.execute(select(FirmanteSop).where(FirmanteSop.sop_master_id == sop_id))).scalars()
    )
    yo = next((f for f in firmantes if f.usuario_id == actual.id), None)
    if not yo:
        raise HTTPException(status_code=403, detail="No sos firmante designado de este documento.")

    firmas = list(
        (await db.execute(
            select(FirmaElectronica).where(
                FirmaElectronica.sop_master_id == sop_id,
                FirmaElectronica.version == sop.version_actual,
            )
        )).scalars()
    )
    if any(fi.usuario_id == actual.id for fi in firmas):
        raise HTTPException(status_code=409, detail="Ya firmaste este documento.")
    # Orden: todos los obligatorios con orden menor deben haber firmado antes (§6.4).
    firmados_ids = {fi.usuario_id for fi in firmas}
    pendientes_antes = [
        f for f in firmantes if f.obligatorio and f.orden < yo.orden and f.usuario_id not in firmados_ids
    ]
    if pendientes_antes:
        raise HTTPException(status_code=409, detail="Aún faltan firmas de orden anterior.")

    db.add(FirmaElectronica(
        sop_master_id=sop_id, version=sop.version_actual, usuario_id=actual.id,
        fecha_hora=datetime.now(UTC), metodo=datos.metodo, ip=request.client.host,
    ))
    await db.flush()

    # ¿Se completaron todas las firmas obligatorias? → firmado automático (§11, B4)
    firmas_ahora = list(
        (await db.execute(
            select(FirmaElectronica).where(
                FirmaElectronica.sop_master_id == sop_id,
                FirmaElectronica.version == sop.version_actual,
            )
        )).scalars()
    )
    ids_firmados = {fi.usuario_id for fi in firmas_ahora}
    completo = all(f.usuario_id in ids_firmados for f in firmantes if f.obligatorio)

    resultado = {"firmado": True, "documento_controlado": False}
    if completo:
        await _emitir_documento_controlado(db, sop, firmantes, firmas_ahora)
        resultado["documento_controlado"] = True
    auditar(db, actual.id, "sop_master", sop.id, "firma", {"metodo": datos.metodo}, request.client.host)
    await db.commit()
    return resultado


async def _emitir_documento_controlado(db, sop, firmantes, firmas):
    """Genera el PDF firmado, su hash, lo archiva y pasa el SOP a 'firmado' (A5)."""
    area = (await db.execute(select(Area).where(Area.id == sop.area_id))).scalar_one()
    usuarios = {
        u.id: u for u in (await db.execute(
            select(Usuario).where(Usuario.id.in_([f.usuario_id for f in firmas]))
        )).scalars()
    }
    firmas_pdf = [
        {
            "firmante": usuarios[f.usuario_id].nombre if f.usuario_id in usuarios else str(f.usuario_id),
            "fecha_hora": f.fecha_hora.strftime("%Y-%m-%d %H:%M"),
            "metodo": f.metodo or "", "ip": f.ip or "",
        }
        for f in firmas
    ]
    sop_dict = {
        "codigo": sop.codigo, "nombre": sop.nombre, "area": area.codigo, "tipo": sop.tipo.value,
        "version": sop.version_actual, "proposito": sop.proposito,
        "evaluacion_riesgos": sop.evaluacion_riesgos, "controles_existentes": sop.controles_existentes,
        "procedimiento": sop.procedimiento, "responsables": sop.responsables,
        "evidencia": sop.evidencia,
        "frecuencia_revision": sop.frecuencia_revision.value if sop.frecuencia_revision else None,
    }
    pdf, hash_pdf = generar_pdf_controlado(sop_dict, firmas_pdf)
    clave = f"{sop.codigo}_v{sop.version_actual}.pdf"
    guardar_pdf(clave, pdf)

    for f in firmas:
        f.hash_pdf = hash_pdf
    sop.estado = EstadoDocumento.firmado
    sop.firmado_en = datetime.now(UTC)
    doc = DocumentoControlado(
        sop_master_id=sop.id, version=sop.version_actual, pdf_storage_key=clave,
        hash_pdf=hash_pdf, fecha_firma=sop.firmado_en, es_vigente=True,
    )
    db.add(doc)
    await db.flush()
    bitacora(db, doc.id, None, "emision", {"hash_pdf": hash_pdf, "clave": clave})
    # Sincronización controlada (§7.11, A1): si es una versión nueva, marcar a las
    # propiedades que adoptaron/adaptaron una versión anterior (nunca automático el update).
    if sop.version_actual > 1:
        await db.execute(
            update(PropiedadSop)
            .where(
                PropiedadSop.sop_master_id == sop.id,
                PropiedadSop.version_fijada < sop.version_actual,
                PropiedadSop.eliminado_en.is_(None),
            )
            .values(requiere_actualizacion=True)
        )


@router.post("/{sop_id}/rechazar", status_code=204, dependencies=[Depends(limite_firma)])
async def rechazar(
    sop_id: uuid.UUID, datos: RechazarRequest, request: Request,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    """Un firmante rechaza con comentario obligatorio (§B5): el documento pasa a
    'rechazado' y se invalidan las firmas parciales de esta versión."""
    if not datos.comentario.strip():
        raise HTTPException(status_code=422, detail="El comentario de rechazo es obligatorio.")
    sop = await _get_sop(db, sop_id)
    if sop.estado != EstadoDocumento.en_firma:
        raise HTTPException(status_code=409, detail="El documento no está en proceso de firma.")
    es_firmante = (
        await db.execute(
            select(FirmanteSop).where(
                FirmanteSop.sop_master_id == sop_id, FirmanteSop.usuario_id == actual.id
            )
        )
    ).scalar_one_or_none()
    if not es_firmante:
        raise HTTPException(status_code=403, detail="No sos firmante designado de este documento.")

    await db.execute(
        delete(FirmaElectronica).where(
            FirmaElectronica.sop_master_id == sop_id,
            FirmaElectronica.version == sop.version_actual,
        )
    )
    sop.estado = EstadoDocumento.rechazado
    auditar(db, actual.id, "sop_master", sop.id, "rechazo",
            {"comentario": datos.comentario, "version": sop.version_actual}, request.client.host)
    await db.commit()


# --- Documento controlado (custodio / lectura) ---


@router.get("/{sop_id}/documento-controlado", response_model=DocumentoControladoOut)
async def obtener_documento_controlado(
    sop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), _: UsuarioActual = Depends(get_current_user),
):
    doc = (
        await db.execute(
            select(DocumentoControlado).where(
                DocumentoControlado.sop_master_id == sop_id, DocumentoControlado.es_vigente.is_(True)
            )
        )
    ).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="No hay documento controlado vigente.")
    return DocumentoControladoOut(
        id=doc.id, sop_master_id=doc.sop_master_id, version=doc.version,
        hash_pdf=doc.hash_pdf, fecha_firma=doc.fecha_firma, es_vigente=doc.es_vigente,
    )


@router.get("/{sop_id}/documento-controlado/descargar")
async def descargar_documento_controlado(
    sop_id: uuid.UUID,
    db: AsyncSession = Depends(get_db), actual: UsuarioActual = Depends(get_current_user),
):
    doc = (
        await db.execute(
            select(DocumentoControlado).where(
                DocumentoControlado.sop_master_id == sop_id, DocumentoControlado.es_vigente.is_(True)
            )
        )
    ).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="No hay documento controlado vigente.")
    contenido = leer_pdf(doc.pdf_storage_key)
    if contenido is None:
        raise HTTPException(status_code=404, detail="Archivo del documento no disponible.")
    bitacora(db, doc.id, actual.id, "descarga")
    await db.commit()
    return Response(
        content=contenido, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{doc.pdf_storage_key}"'},
    )
