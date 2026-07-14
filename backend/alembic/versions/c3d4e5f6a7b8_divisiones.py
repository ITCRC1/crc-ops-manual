"""divisiones: nivel organizativo sobre los departamentos (organigrama)

Crea la tabla `divisiones` (auto-referenciada para subdivisiones) y agrega
`departamentos.division_id`.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-05 21:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'divisiones',
        sa.Column('codigo', sa.String(length=20), nullable=False),
        sa.Column('nombre', sa.String(length=200), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('orden', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['divisiones.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo', name='uq_division_codigo'),
    )
    op.create_index(op.f('ix_divisiones_codigo'), 'divisiones', ['codigo'], unique=False)
    op.create_index(op.f('ix_divisiones_parent_id'), 'divisiones', ['parent_id'], unique=False)

    op.add_column('departamentos', sa.Column('division_id', sa.UUID(), nullable=True))
    op.create_index(
        op.f('ix_departamentos_division_id'), 'departamentos', ['division_id'], unique=False
    )
    op.create_foreign_key(
        'fk_departamentos_division', 'departamentos', 'divisiones', ['division_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_departamentos_division', 'departamentos', type_='foreignkey')
    op.drop_index(op.f('ix_departamentos_division_id'), table_name='departamentos')
    op.drop_column('departamentos', 'division_id')
    op.drop_index(op.f('ix_divisiones_parent_id'), table_name='divisiones')
    op.drop_index(op.f('ix_divisiones_codigo'), table_name='divisiones')
    op.drop_table('divisiones')
