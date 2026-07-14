"""descriptores: categoria del puesto (director/gerente/supervisor/linea)

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-05 22:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('descriptor_puesto_master', sa.Column('categoria', sa.String(length=30), nullable=True))
    op.create_index(
        op.f('ix_descriptor_puesto_master_categoria'),
        'descriptor_puesto_master', ['categoria'], unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_descriptor_puesto_master_categoria'), table_name='descriptor_puesto_master'
    )
    op.drop_column('descriptor_puesto_master', 'categoria')
