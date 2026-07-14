"""propiedad_training_manual: adopción/adaptación de manuales por propiedad (Etapa C)

Revision ID: a9b0c1d2e3f4
Revises: f8a9b0c1d2e3
Create Date: 2026-07-11 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a9b0c1d2e3f4'
down_revision: Union[str, None] = 'f8a9b0c1d2e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    estado_asignacion = postgresql.ENUM(
        'borrador', 'en_revision', 'en_firma', 'vigente', 'rechazado', 'archivado',
        name='estado_asignacion', create_type=False,
    )
    modo_asignacion = postgresql.ENUM(
        'adoptado', 'adaptado', 'local', 'no_aplica',
        name='modo_asignacion', create_type=False,
    )
    op.create_table(
        'propiedad_training_manual',
        sa.Column('propiedad_id', sa.UUID(), nullable=False),
        sa.Column('training_manual_id', sa.UUID(), nullable=True),
        sa.Column('modo', modo_asignacion, nullable=False),
        sa.Column('smart_overrides', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('titulo_local', sa.String(length=300), nullable=True),
        sa.Column('estado', estado_asignacion, nullable=False, server_default='borrador'),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('eliminado_en', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['propiedad_id'], ['propiedades.id']),
        sa.ForeignKeyConstraint(['training_manual_id'], ['training_manual.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('propiedad_id', 'training_manual_id', name='uq_propiedad_training_manual'),
    )
    op.create_index(op.f('ix_propiedad_training_manual_propiedad_id'), 'propiedad_training_manual', ['propiedad_id'], unique=False)
    op.create_index(op.f('ix_propiedad_training_manual_training_manual_id'), 'propiedad_training_manual', ['training_manual_id'], unique=False)
    op.create_index(op.f('ix_propiedad_training_manual_estado'), 'propiedad_training_manual', ['estado'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_propiedad_training_manual_estado'), table_name='propiedad_training_manual')
    op.drop_index(op.f('ix_propiedad_training_manual_training_manual_id'), table_name='propiedad_training_manual')
    op.drop_index(op.f('ix_propiedad_training_manual_propiedad_id'), table_name='propiedad_training_manual')
    op.drop_table('propiedad_training_manual')
