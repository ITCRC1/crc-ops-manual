"""capacitacion: manuales de training por departamento + secciones

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-07-05 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'training_manual',
        sa.Column('departamento_id', sa.UUID(), nullable=True),
        sa.Column('titulo', sa.String(length=300), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('creado_por', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('eliminado_en', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['departamento_id'], ['departamentos.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_training_manual_departamento_id'), 'training_manual', ['departamento_id'], unique=False
    )

    op.create_table(
        'training_seccion',
        sa.Column('training_manual_id', sa.UUID(), nullable=False),
        sa.Column('titulo', sa.String(length=300), nullable=False),
        sa.Column('contenido', sa.Text(), nullable=True),
        sa.Column('orden', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('eliminado_en', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['training_manual_id'], ['training_manual.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_training_seccion_training_manual_id'),
        'training_seccion', ['training_manual_id'], unique=False,
    )


def downgrade() -> None:
    op.drop_table('training_seccion')
    op.drop_table('training_manual')
