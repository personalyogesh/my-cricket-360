"""Organization-scoped schedules and fixtures.

Revision ID: 20261104_0002
Revises: 20261104_0001
Create Date: 2026-11-04
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261104_0002"
down_revision: Union[str, None] = "20261104_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "schedules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("season", sa.String(length=64), nullable=False),
        sa.Column("competition", sa.String(length=128), nullable=False),
        sa.Column("format_code", sa.String(length=32), nullable=False),
        sa.Column("format_name", sa.String(length=128), nullable=False),
        sa.Column("overs", sa.Integer(), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_schedules_org_status", "schedules", ["organization_id", "status"])

    op.create_table(
        "fixtures",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("schedule_id", sa.Uuid(), nullable=True),
        sa.Column("season", sa.String(length=64), nullable=False),
        sa.Column("competition", sa.String(length=128), nullable=False),
        sa.Column("home_team_id", sa.Uuid(), nullable=True),
        sa.Column("away_team_id", sa.Uuid(), nullable=True),
        sa.Column("home_team_name", sa.String(length=255), nullable=False),
        sa.Column("away_team_name", sa.String(length=255), nullable=False),
        sa.Column("venue", sa.String(length=255), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("format_code", sa.String(length=32), nullable=False),
        sa.Column("format_name", sa.String(length=128), nullable=False),
        sa.Column("overs", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["away_team_id"], ["teams.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fixtures_org_starts", "fixtures", ["organization_id", "starts_at"])
    op.create_index("ix_fixtures_org_status", "fixtures", ["organization_id", "status"])
    op.create_index("ix_fixtures_org_format", "fixtures", ["organization_id", "format_code"])


def downgrade() -> None:
    op.drop_index("ix_fixtures_org_format", table_name="fixtures")
    op.drop_index("ix_fixtures_org_status", table_name="fixtures")
    op.drop_index("ix_fixtures_org_starts", table_name="fixtures")
    op.drop_table("fixtures")
    op.drop_index("ix_schedules_org_status", table_name="schedules")
    op.drop_table("schedules")
