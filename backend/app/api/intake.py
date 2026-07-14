"""Laboratorio de intake (§ backlog C): metés un procedimiento (pegado o archivo),
el sistema lo triagea contra los SOPs existentes por similitud de texto y dice si es
un posible duplicado (para mejorar el existente) o algo nuevo (para crearlo como SOP
borrador con `POST /api/sops`). Determinístico, sin IA.
"""

import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UsuarioActual, require_rol
from app.core.db import get_db
from app.models.base import RolUsuario
from app.models.catalogos import Area
from app.models.sop import SopMaster
from app.schemas.intake import ExtraerOut, IntakeAnalizar, SimilarOut, TriageOut
from app.services import similitud

router = APIRouter(prefix="/api/intake", tags=["intake"])

editor = require_rol(RolUsuario.editor_corporativo, RolUsuario.super_admin)

UMBRAL = 0.45  # >= ⇒ posible duplicado
TOP_N = 5


def _texto_sop(s: SopMaster) -> str:
    partes: list[str] = [s.nombre, s.proposito, s.evaluacion_riesgos, s.controles_existentes,
                         s.responsables, s.evidencia]
    if isinstance(s.procedimiento, dict):
        p = s.procedimiento
        lst = p.get("secciones") or p.get("pasos") or p.get("contenido")
        if isinstance(lst, list):
            partes.append(" ".join(str(x) for x in lst))
    return " ".join(p for p in partes if p)


@router.post("/analizar", response_model=TriageOut)
async def analizar(
    datos: IntakeAnalizar,
    db: AsyncSession = Depends(get_db),
    _: UsuarioActual = Depends(editor),
) -> TriageOut:
    sops = list(
        (await db.execute(select(SopMaster).where(SopMaster.eliminado_en.is_(None)))).scalars()
    )
    areas = {a.id: a.codigo for a in (await db.execute(select(Area))).scalars()}
    rank = [
        (similitud.puntaje(datos.nombre, datos.texto, s.nombre, _texto_sop(s)), s) for s in sops
    ]
    rank.sort(key=lambda x: x[0], reverse=True)
    top = rank[:TOP_N]
    verdict = "posible_duplicado" if top and top[0][0] >= UMBRAL else "nuevo"
    return TriageOut(
        verdict=verdict,
        umbral=UMBRAL,
        similares=[
            SimilarOut(
                id=s.id, codigo=s.codigo, nombre=s.nombre,
                area_codigo=areas.get(s.area_id, "?"), estado=s.estado.value, score=sc,
            )
            for sc, s in top
        ],
    )


@router.post("/extraer", response_model=ExtraerOut)
async def extraer(
    archivo: UploadFile = File(...),
    _: UsuarioActual = Depends(editor),
) -> ExtraerOut:
    """Extrae texto de un .docx o .txt para precargar el analizador."""
    nombre_archivo = archivo.filename or "documento"
    data = await archivo.read()
    bajo = nombre_archivo.lower()
    if bajo.endswith(".docx"):
        import docx

        doc = docx.Document(io.BytesIO(data))
        texto = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    elif bajo.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        texto = "\n".join((pag.extract_text() or "") for pag in reader.pages).strip()
        if not texto:
            raise HTTPException(
                status_code=422,
                detail="No se pudo extraer texto del PDF (¿es escaneado/imagen? no hay OCR).",
            )
    elif bajo.endswith(".txt"):
        texto = data.decode("utf-8", errors="replace")
    else:
        raise HTTPException(status_code=415, detail="Formato no soportado; usá .docx, .pdf o .txt.")
    primera = next((ln.strip() for ln in texto.splitlines() if ln.strip()), "")
    nombre = (primera[:200] if primera else nombre_archivo.rsplit(".", 1)[0]).strip()
    return ExtraerOut(nombre=nombre, texto=texto)
