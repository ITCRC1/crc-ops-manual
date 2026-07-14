"""descriptor_puesto_master.smart — capa JD SMART (estándar JD SMART, ~30 secciones + crosswalk a SOPs)

Columna JSONB aditiva y nullable: NULL = JD aún sin reformatear (el frontend cae al
formato base). No destruye ni migra datos existentes. Paralelo a `sop_master.smart`.

Revision ID: b5c6d7e8f9a0
Revises: a4b5c6d7e8f9
Create Date: 2026-07-10
"""

from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b5c6d7e8f9a0"
down_revision: Union[str, None] = "a4b5c6d7e8f9"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        "descriptor_puesto_master",
        sa.Column("smart", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("descriptor_puesto_master", "smart")
