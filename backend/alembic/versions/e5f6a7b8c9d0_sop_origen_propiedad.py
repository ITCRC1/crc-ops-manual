"""sop_master: origen_propiedad (marca interna de despliegue por propiedad)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-05 23:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sop_master', sa.Column('origen_propiedad', sa.String(length=20), nullable=True))
    op.create_index(
        op.f('ix_sop_master_origen_propiedad'), 'sop_master', ['origen_propiedad'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_sop_master_origen_propiedad'), table_name='sop_master')
    op.drop_column('sop_master', 'origen_propiedad')
