"""Discovery, matching, blocks, and reports foundation

Revision ID: 20261002_000005
Revises: 20261001_000004
Create Date: 2026-10-02 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261002_000005"
down_revision = "20261001_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Discovery Interactions
    op.create_table(
        "discovery_interactions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interaction_type", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "target_user_id", name="uq_discovery_interactions_user_target"),
        sa.CheckConstraint("user_id != target_user_id", name="ck_discovery_interactions_not_self"),
        sa.CheckConstraint(
            "interaction_type IN ('like', 'pass', 'super_like', 'save')",
            name="ck_discovery_interactions_type",
        ),
    )
    op.create_index("ix_discovery_interactions_user_id", "discovery_interactions", ["user_id"])
    op.create_index("ix_discovery_interactions_target_user_id", "discovery_interactions", ["target_user_id"])
    op.create_index("idx_discovery_interactions_target_type", "discovery_interactions", ["target_user_id", "interaction_type"])

    # 2. User Blocks
    op.create_table(
        "user_blocks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("blocker_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("blocked_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("blocker_id", "blocked_id", name="uq_user_blocks_blocker_blocked"),
        sa.CheckConstraint("blocker_id != blocked_id", name="ck_user_blocks_not_self"),
    )
    op.create_index("ix_user_blocks_blocker_id", "user_blocks", ["blocker_id"])
    op.create_index("ix_user_blocks_blocked_id", "user_blocks", ["blocked_id"])
    op.create_index("idx_user_blocks_blocked_blocker", "user_blocks", ["blocked_id", "blocker_id"])

    # 3. User Reports
    op.create_table(
        "user_reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("reporter_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reported_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), server_default="pending", nullable=False),
        sa.Column("reviewed_by_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("reporter_id != reported_id", name="ck_user_reports_not_self"),
        sa.CheckConstraint(
            "status IN ('pending', 'under_review', 'actioned', 'dismissed')",
            name="ck_user_reports_status",
        ),
    )
    op.create_index("ix_user_reports_reporter_id", "user_reports", ["reporter_id"])
    op.create_index("ix_user_reports_reported_id", "user_reports", ["reported_id"])
    op.create_index("idx_user_reports_status_created", "user_reports", ["status", "created_at"])


def downgrade() -> None:
    op.drop_table("user_reports")
    op.drop_table("user_blocks")
    op.drop_table("discovery_interactions")
