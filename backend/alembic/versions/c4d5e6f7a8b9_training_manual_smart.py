"""training_manual.smart — capa Training SMART (#3 de la trilogía: ficha estructurada por training)

Columna JSONB aditiva y nullable: NULL = training aún sin ficha SMART (el frontend cae al
contenido base de secciones). No destruye ni migra datos existentes. Paralelo a
`sop_master.smart` y `descriptor_puesto_master.smart`.

Revision ID: c4d5e6f7a8b9
Revises: b5c6d7e8f9a0
Create Date: 2026-07-11
"""

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b5c6d7e8f9a0"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        "training_manual",
        sa.Column("smart", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("training_manual", "smart")
