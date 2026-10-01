"""Persist profile, preferences, privacy, interests, and media metadata

Revision ID: 20261001_000002
Revises: 20260930_000001
Create Date: 2026-10-01 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261001_000002"
down_revision = "20260930_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.alter_column("profiles", "display_name", existing_type=sa.String(length=80), nullable=True)
    op.alter_column("profiles", "profile_visibility", existing_type=sa.String(length=32), server_default="hidden")
    op.add_column("profiles", sa.Column("gender_identity", sa.String(length=80), nullable=True))
    op.add_column("profiles", sa.Column("discovery_visibility", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_unique_constraint("uq_profiles_user_id", "profiles", ["user_id"])
    op.create_check_constraint("ck_profiles_completion_range", "profiles", "profile_completion >= 0 AND profile_completion <= 100")
    op.create_check_constraint(
        "ck_profiles_visibility",
        "profiles",
        "profile_visibility IN ('public', 'discoverable', 'limited', 'hidden', 'private')",
    )
    op.create_unique_constraint("uq_user_accounts_provider_subject", "user_accounts", ["provider", "provider_subject"])

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("minimum_age", sa.Integer(), server_default="18", nullable=False),
        sa.Column("maximum_age", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("minimum_age >= 18 AND minimum_age <= 100", name="ck_user_preferences_minimum_age"),
        sa.CheckConstraint("maximum_age IS NULL OR (maximum_age >= minimum_age AND maximum_age <= 100)", name="ck_user_preferences_maximum_age"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_preferences_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_preferences_user_id"),
    )

    op.create_table(
        "user_preference_options",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("value", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "category IN ('dating_intention', 'dating_preference', 'discovery_preference', 'travel_intention', 'language')",
            name="ck_user_preference_options_category",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_preference_options_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "category", "value", name="uq_user_preference_options_value"),
    )
    op.create_index("ix_user_preference_options_user_category", "user_preference_options", ["user_id", "category"])

    op.create_table(
        "interests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_interests_code"),
    )
    interests = sa.table(
        "interests",
        sa.column("id", sa.String(length=36)),
        sa.column("code", sa.String(length=64)),
        sa.column("name", sa.String(length=100)),
        sa.column("active", sa.Boolean()),
    )
    op.bulk_insert(interests, [
        {"id": "a6406da9-8844-42f1-8c1c-7b9e1a000001", "code": "food_walks", "name": "Food walks", "active": True},
        {"id": "a6406da9-8844-42f1-8c1c-7b9e1a000002", "code": "hiking", "name": "Hiking", "active": True},
        {"id": "a6406da9-8844-42f1-8c1c-7b9e1a000003", "code": "photography", "name": "Photography", "active": True},
        {"id": "a6406da9-8844-42f1-8c1c-7b9e1a000004", "code": "heritage", "name": "Heritage", "active": True},
        {"id": "a6406da9-8844-42f1-8c1c-7b9e1a000005", "code": "art_design", "name": "Art and design", "active": True},
        {"id": "a6406da9-8844-42f1-8c1c-7b9e1a000006", "code": "live_music", "name": "Live music", "active": True},
        {"id": "a6406da9-8844-42f1-8c1c-7b9e1a000007", "code": "beaches", "name": "Beaches", "active": True},
        {"id": "a6406da9-8844-42f1-8c1c-7b9e1a000008", "code": "local_culture", "name": "Local culture", "active": True},
    ])
    op.create_table(
        "interest_translations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("interest_id", sa.String(length=36), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=False),
        sa.Column("localized_name", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["interest_id"], ["interests.id"], name="fk_interest_translations_interest_id_interests", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("interest_id", "language_code", name="uq_interest_translations_locale"),
    )
    op.create_table(
        "user_interests",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("interest_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["interest_id"], ["interests.id"], name="fk_user_interests_interest_id_interests", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_interests_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "interest_id"),
    )

    op.create_table(
        "user_privacy_settings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("location_precision", sa.String(length=24), server_default="approximate", nullable=False),
        sa.Column("allow_exact_location_sharing", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("personalization_enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("communications_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("location_precision IN ('hidden', 'approximate', 'destination')", name="ck_user_privacy_location_precision"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_privacy_settings_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_privacy_settings_user_id"),
    )

    op.create_table(
        "media_assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("media_type", sa.String(length=32), nullable=False),
        sa.Column("storage_provider", sa.String(length=32), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("processing_status", sa.String(length=24), server_default="pending", nullable=False),
        sa.Column("moderation_status", sa.String(length=24), server_default="pending_review", nullable=False),
        sa.Column("visibility", sa.String(length=24), server_default="private", nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("media_type IN ('profile_media', 'chat_media', 'verification_media')", name="ck_media_assets_type"),
        sa.CheckConstraint("storage_provider IN ('r2', 'cloudinary')", name="ck_media_assets_provider"),
        sa.CheckConstraint("processing_status IN ('pending', 'uploading', 'processing', 'ready', 'failed', 'deleted')", name="ck_media_assets_processing_status"),
        sa.CheckConstraint("moderation_status IN ('pending_review', 'approved', 'rejected', 'requires_review')", name="ck_media_assets_moderation_status"),
        sa.CheckConstraint("visibility IN ('public', 'profile_only', 'private')", name="ck_media_assets_visibility"),
        sa.CheckConstraint("size_bytes > 0", name="ck_media_assets_size_positive"),
        sa.CheckConstraint("sort_order >= 0", name="ck_media_assets_sort_order"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_media_assets_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key", name="uq_media_assets_object_key"),
    )
    op.create_index("ix_media_assets_user_type_status", "media_assets", ["user_id", "media_type", "processing_status"])


def downgrade() -> None:
    op.drop_index("ix_media_assets_user_type_status", table_name="media_assets")
    op.drop_table("media_assets")
    op.drop_table("user_privacy_settings")
    op.drop_table("user_interests")
    op.drop_table("interest_translations")
    op.drop_table("interests")
    op.drop_index("ix_user_preference_options_user_category", table_name="user_preference_options")
    op.drop_table("user_preference_options")
    op.drop_table("user_preferences")
    op.drop_constraint("uq_user_accounts_provider_subject", "user_accounts", type_="unique")
    op.drop_constraint("ck_profiles_visibility", "profiles", type_="check")
    op.drop_constraint("ck_profiles_completion_range", "profiles", type_="check")
    op.drop_constraint("uq_profiles_user_id", "profiles", type_="unique")
    op.drop_column("profiles", "discovery_visibility")
    op.drop_column("profiles", "gender_identity")
    op.alter_column("profiles", "profile_visibility", existing_type=sa.String(length=32), server_default="private")
    op.execute("UPDATE profiles SET display_name = '' WHERE display_name IS NULL")
    op.alter_column("profiles", "display_name", existing_type=sa.String(length=80), nullable=False)
