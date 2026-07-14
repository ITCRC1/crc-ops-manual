"""Seed de usuarios del equipo (PLACEHOLDERS provisionales).

Nombres y correos provisionales aportados por el owner; se actualizarán luego (nombre
completo, correo real, nivel y rol definitivos). Idempotente por email.

Valores por defecto:
- contraseña temporal compartida (cambiar tras el primer ingreso),
- nivel_jerarquico = 3 (jefatura/gerencia) ⇒ TODOS elegibles como firmantes (decisión del
  owner 2026-07-05: habilitar a todo el equipo para firmar; el nivel real de cada uno se
  ajusta luego desde /usuarios),
- rol = lector (firmar no requiere rol, solo nivel <= nivel_minimo_firmante (3) + ser
  firmante designado).

Idempotente: salta a los usuarios existentes (no pisa cambios manuales hechos en /usuarios).

Uso:
    python -m app.seed_usuarios
"""

import asyncio

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.core.seguridad import hash_password
from app.models.base import RolUsuario
from app.models.usuarios import RolUsuarioAsignado, Usuario

PASSWORD_TEMP = "CambiarCRC2026!"

# Usuarios con status de administrador (super_admin, nivel 1) — respaldo del admin
# corporativo (decisión del owner 2026-07-05). El resto: nivel 3 (firmante) + lector.
ADMIN_EMAILS = {"ronald@example.com"}

# (nombre_provisional, email_placeholder)
USUARIOS = [
    ("Ronald", "ronald@example.com"),
    ("Luz Marina", "luz.marina@example.com"),
    ("Berny", "berny@example.com"),
    ("Roberto", "roberto@example.com"),
    ("Isaac Quiros", "isaac.quiros@example.com"),
    ("Karina", "karina@example.com"),
    ("Luis", "luis@example.com"),
    ("Edward", "edward@example.com"),
    ("Alex", "alex@example.com"),
    ("Ivan", "ivan@example.com"),
    ("Andrey", "andrey@example.com"),
]


async def seed() -> None:
    creados = 0
    async with AsyncSessionLocal() as db:
        for nombre, email in USUARIOS:
            existe = (
                await db.execute(select(Usuario).where(Usuario.email == email))
            ).scalar_one_or_none()
            if existe:
                continue
            es_admin = email in ADMIN_EMAILS
            u = Usuario(
                nombre=nombre,
                email=email,
                password_hash=hash_password(PASSWORD_TEMP),
                nivel_jerarquico=1 if es_admin else 3,  # admin=1; resto=3 (elegible firmante)
                activo=True,
            )
            db.add(u)
            await db.flush()
            rol = RolUsuario.super_admin if es_admin else RolUsuario.lector
            db.add(RolUsuarioAsignado(usuario_id=u.id, rol=rol, propiedad_id=None))
            creados += 1
        await db.commit()
    print(f"Usuarios del equipo creados: {creados} de {len(USUARIOS)} (idempotente).")


if __name__ == "__main__":
    asyncio.run(seed())
