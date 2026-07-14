"""propiedad_puesto_ocupante: titulares (personas) de un puesto por propiedad

Revision ID: f3a4b5c6d7e8
Revises: e5f6a7b8c9d0
Create Date: 2026-07-05 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'f3a4b5c6d7e8'
down_revision: str | None = 'e5f6a7b8c9d0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'propiedad_puesto_ocupante',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('propiedad_puesto_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('es_principal', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('nota', sa.String(length=300), nullable=True),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['propiedad_puesto_id'], ['propiedad_puesto.id']),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('propiedad_puesto_id', 'usuario_id', name='uq_puesto_ocupante'),
    )
    op.create_index(
        op.f('ix_propiedad_puesto_ocupante_propiedad_puesto_id'),
        'propiedad_puesto_ocupante', ['propiedad_puesto_id'], unique=False,
    )
    op.create_index(
        op.f('ix_propiedad_puesto_ocupante_usuario_id'),
        'propiedad_puesto_ocupante', ['usuario_id'], unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_propiedad_puesto_ocupante_usuario_id'), table_name='propiedad_puesto_ocupante'
    )
    op.drop_index(
        op.f('ix_propiedad_puesto_ocupante_propiedad_puesto_id'),
        table_name='propiedad_puesto_ocupante',
    )
    op.drop_table('propiedad_puesto_ocupante')
