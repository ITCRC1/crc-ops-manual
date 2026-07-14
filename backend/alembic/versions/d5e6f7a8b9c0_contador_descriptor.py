"""contador global de descriptores (Etapa 4.5)

Revision ID: d5e6f7a8b9c0
Revises: a042cced3322
Create Date: 2026-07-04 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, None] = 'a042cced3322'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'contador_descriptor',
        sa.Column('ultimo_numero', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    # Fila única inicial: la secuencia global de descriptores (§7.2). El servicio la
    # reconcilia con el mayor JD-### existente al asignar el siguiente código.
    op.execute("INSERT INTO contador_descriptor (id, ultimo_numero) VALUES (gen_random_uuid(), 0)")


def downgrade() -> None:
    op.drop_table('contador_descriptor')
