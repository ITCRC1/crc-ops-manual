"""programacion: actividades programadas por SOP (calendario consolidado)

Revision ID: a1b2c3d4e5f6
Revises: f2a3b4c5d6e7
Create Date: 2026-07-05 15:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tipo_recurrencia = postgresql.ENUM(
        'unica', 'diaria', 'semanal', 'mensual', 'anual',
        name='tipo_recurrencia',
        create_type=False,
    )
    tipo_recurrencia.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'programacion_sop',
        sa.Column('sop_master_id', sa.UUID(), nullable=False),
        sa.Column('titulo', sa.String(length=300), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('tipo_recurrencia', tipo_recurrencia, nullable=False),
        sa.Column('fecha', sa.Date(), nullable=True),
        sa.Column('hora', sa.Time(), nullable=True),
        sa.Column('dia_semana', sa.Integer(), nullable=True),
        sa.Column('dia_mes', sa.Integer(), nullable=True),
        sa.Column('mes', sa.Integer(), nullable=True),
        sa.Column('fecha_inicio', sa.Date(), nullable=True),
        sa.Column('fecha_fin', sa.Date(), nullable=True),
        sa.Column('responsable_puesto_id', sa.UUID(), nullable=True),
        sa.Column('responsable_texto', sa.String(length=300), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('orden', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('eliminado_en', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['sop_master_id'], ['sop_master.id']),
        sa.ForeignKeyConstraint(['responsable_puesto_id'], ['descriptor_puesto_master.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_programacion_sop_sop_master_id'),
        'programacion_sop', ['sop_master_id'], unique=False,
    )
    op.create_index(
        op.f('ix_programacion_sop_responsable_puesto_id'),
        'programacion_sop', ['responsable_puesto_id'], unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_programacion_sop_responsable_puesto_id'), table_name='programacion_sop')
    op.drop_index(op.f('ix_programacion_sop_sop_master_id'), table_name='programacion_sop')
    op.drop_table('programacion_sop')
    postgresql.ENUM(name='tipo_recurrencia').drop(op.get_bind(), checkfirst=True)
