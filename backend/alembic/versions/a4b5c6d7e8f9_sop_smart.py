"""sop_master.smart — capa SMART (estándar SOP SMART, 18 secciones + apéndices A–F)

Columna JSONB aditiva y nullable: NULL = SOP aún sin reformatear (el frontend cae al
formato de 9 campos). No destruye ni migra datos existentes.

Revision ID: a4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-07-09
"""

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a4b5c6d7e8f9"
down_revision: Union[str, None] = "f3a4b5c6d7e8"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        "sop_master",
        sa.Column("smart", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sop_master", "smart")
