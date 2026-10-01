"""Identity verification infrastructure and secure verification media

Revision ID: 20261001_000003
Revises: 20261001_000002
Create Date: 2026-10-01 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261001_000003"
down_revision = "20261001_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Alter verification_records
    op.add_column("verification_records", sa.Column("verification_type", sa.String(length=32), nullable=True))
    op.add_column("verification_records", sa.Column("provider_reference", sa.String(length=255), nullable=True))
    op.add_column("verification_records", sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("verification_records", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("verification_records", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("verification_records", sa.Column("reviewed_by", sa.String(length=36), nullable=True))
    op.add_column("verification_records", sa.Column("review_decision_reason", sa.Text(), nullable=True))
    op.add_column("verification_records", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_verification_records_reviewed_by_users",
        "verification_records",
        "users",
        ["reviewed_by"],
        ["id"],
    )
    op.create_index("ix_verification_records_user_id", "verification_records", ["user_id"])
    op.create_index("ix_verification_records_status_category", "verification_records", ["status", "category"])

    # 2. verification_attempts
    op.create_table(
        "verification_attempts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("verification_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("provider_session_id", sa.String(length=255), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["verification_id"],
            ["verification_records.id"],
            name="fk_verification_attempts_verification_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_verification_attempts_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_attempts_verification_id", "verification_attempts", ["verification_id"])
    op.create_index("ix_verification_attempts_user_id", "verification_attempts", ["user_id"])

    # 3. verification_media
    op.create_table(
        "verification_media",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("verification_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("media_type", sa.String(length=32), nullable=False),
        sa.Column("storage_provider", sa.String(length=32), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retention_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "media_type IN ('selfie', 'document_front', 'document_back', 'video')",
            name="ck_verification_media_type",
        ),
        sa.CheckConstraint(
            "storage_provider IN ('r2', 'private_s3', 'mock')",
            name="ck_verification_media_provider",
        ),
        sa.CheckConstraint("size_bytes > 0", name="ck_verification_media_size_positive"),
        sa.ForeignKeyConstraint(
            ["verification_id"],
            ["verification_records.id"],
            name="fk_verification_media_verification_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_verification_media_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key", name="uq_verification_media_object_key"),
    )
    op.create_index("ix_verification_media_verification_id", "verification_media", ["verification_id"])
    op.create_index("ix_verification_media_user_id", "verification_media", ["user_id"])

    # 4. verification_events
    op.create_table(
        "verification_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("verification_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_type", sa.String(length=32), server_default="user", nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["verification_id"],
            ["verification_records.id"],
            name="fk_verification_events_verification_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_verification_events_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_events_verification_id", "verification_events", ["verification_id"])
    op.create_index("ix_verification_events_user_id", "verification_events", ["user_id"])
    op.create_index("ix_verification_events_event_type", "verification_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_verification_events_event_type", table_name="verification_events")
    op.drop_index("ix_verification_events_user_id", table_name="verification_events")
    op.drop_index("ix_verification_events_verification_id", table_name="verification_events")
    op.drop_table("verification_events")

    op.drop_index("ix_verification_media_user_id", table_name="verification_media")
    op.drop_index("ix_verification_media_verification_id", table_name="verification_media")
    op.drop_table("verification_media")

    op.drop_index("ix_verification_attempts_user_id", table_name="verification_attempts")
    op.drop_index("ix_verification_attempts_verification_id", table_name="verification_attempts")
    op.drop_table("verification_attempts")

    op.drop_index("ix_verification_records_status_category", table_name="verification_records")
    op.drop_index("ix_verification_records_user_id", table_name="verification_records")
    op.drop_constraint("fk_verification_records_reviewed_by_users", "verification_records", type_="foreignkey")
    op.drop_column("verification_records", "expires_at")
    op.drop_column("verification_records", "review_decision_reason")
    op.drop_column("verification_records", "reviewed_by")
    op.drop_column("verification_records", "reviewed_at")
    op.drop_column("verification_records", "submitted_at")
    op.drop_column("verification_records", "attempt_number")
    op.drop_column("verification_records", "provider_reference")
    op.drop_column("verification_records", "verification_type")
