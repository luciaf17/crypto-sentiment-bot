"""Add backtest_runs table

Revision ID: b12f9a8c3d4e
Revises: e3aecd7416dd
Create Date: 2026-02-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b12f9a8c3d4e"
down_revision: Union[str, None] = "e3aecd7416dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "backtest_runs",
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("parameters", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("metrics", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("trades", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("equity_curve", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "data_points",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'completed'"),
        ),
        sa.Column("error_reason", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("backtest_runs")
