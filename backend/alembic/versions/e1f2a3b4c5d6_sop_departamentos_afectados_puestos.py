"""sop: departamentos afectados + puestos responsables (Etapa 5)

Revision ID: e1f2a3b4c5d6
Revises: d5e6f7a8b9c0
Create Date: 2026-07-05 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sop_master_departamentos_afectados',
        sa.Column('sop_master_id', sa.UUID(), nullable=False),
        sa.Column('departamento_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['departamento_id'], ['departamentos.id']),
        sa.ForeignKeyConstraint(['sop_master_id'], ['sop_master.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sop_master_id', 'departamento_id', name='uq_sop_depto_afectado'),
    )
    op.create_index(
        op.f('ix_sop_master_departamentos_afectados_sop_master_id'),
        'sop_master_departamentos_afectados', ['sop_master_id'], unique=False,
    )
    op.create_index(
        op.f('ix_sop_master_departamentos_afectados_departamento_id'),
        'sop_master_departamentos_afectados', ['departamento_id'], unique=False,
    )

    op.create_table(
        'sop_master_puestos_responsables',
        sa.Column('sop_master_id', sa.UUID(), nullable=False),
        sa.Column('descriptor_puesto_master_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['descriptor_puesto_master_id'], ['descriptor_puesto_master.id']),
        sa.ForeignKeyConstraint(['sop_master_id'], ['sop_master.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'sop_master_id', 'descriptor_puesto_master_id', name='uq_sop_puesto_responsable'
        ),
    )
    op.create_index(
        op.f('ix_sop_master_puestos_responsables_sop_master_id'),
        'sop_master_puestos_responsables', ['sop_master_id'], unique=False,
    )
    op.create_index(
        op.f('ix_sop_master_puestos_responsables_descriptor_puesto_master_id'),
        'sop_master_puestos_responsables', ['descriptor_puesto_master_id'], unique=False,
    )


def downgrade() -> None:
    op.drop_table('sop_master_puestos_responsables')
    op.drop_table('sop_master_departamentos_afectados')
