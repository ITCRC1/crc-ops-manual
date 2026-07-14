"""programacion: fecha de ejecución como ancla + quincenal/trimestral

Simplifica el modelo: la 'fecha de ejecución' (columna `fecha`, ahora obligatoria)
es el ancla desde la que se deriva la cadencia, por lo que se eliminan las columnas
`dia_semana`/`dia_mes`/`mes`/`fecha_inicio`. Agrega las cadencias 'quincenal' y
'trimestral' al enum tipo_recurrencia. La tabla está vacía → sin migración de datos.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-05 19:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PG 12+: ADD VALUE puede correr en transacción si el valor no se usa en la misma.
    op.execute("ALTER TYPE tipo_recurrencia ADD VALUE IF NOT EXISTS 'quincenal'")
    op.execute("ALTER TYPE tipo_recurrencia ADD VALUE IF NOT EXISTS 'trimestral'")

    # Backfill: la fecha de ejecución (ancla) toma la antigua fecha_inicio; si tampoco
    # existía, cae a hoy. Deja todas las filas con `fecha` no nula antes del NOT NULL.
    op.execute(
        "UPDATE programacion_sop SET fecha = COALESCE(fecha, fecha_inicio, CURRENT_DATE) "
        "WHERE fecha IS NULL"
    )
    # `fecha` pasa a ser obligatoria (ancla).
    op.alter_column('programacion_sop', 'fecha', existing_type=sa.Date(), nullable=False)
    op.drop_column('programacion_sop', 'dia_semana')
    op.drop_column('programacion_sop', 'dia_mes')
    op.drop_column('programacion_sop', 'mes')
    op.drop_column('programacion_sop', 'fecha_inicio')


def downgrade() -> None:
    op.add_column('programacion_sop', sa.Column('fecha_inicio', sa.Date(), nullable=True))
    op.add_column('programacion_sop', sa.Column('mes', sa.Integer(), nullable=True))
    op.add_column('programacion_sop', sa.Column('dia_mes', sa.Integer(), nullable=True))
    op.add_column('programacion_sop', sa.Column('dia_semana', sa.Integer(), nullable=True))
    op.alter_column('programacion_sop', 'fecha', existing_type=sa.Date(), nullable=True)
    # Los valores 'quincenal'/'trimestral' quedan en el enum (PG no soporta quitarlos).
