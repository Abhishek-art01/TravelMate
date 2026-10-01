"""Trips, destinations, postgis geospatial foundation, and user locations

Revision ID: 20261001_000004
Revises: 20261001_000003
Create Date: 2026-10-01 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261001_000004"
down_revision = "20261001_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    geom_type = sa.text("geography(Point, 4326)") if is_postgres else sa.String(length=64)

    # 1. Create destinations
    op.create_table(
        "destinations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("country", sa.String(length=80), nullable=False),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("region", sa.String(length=80), nullable=False),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("location_geom", geom_type, nullable=True),
        sa.Column("timezone", sa.String(length=40), server_default="UTC", nullable=False),
        sa.Column("category", sa.String(length=40), server_default="general", nullable=False),
        sa.Column("status", sa.String(length=24), server_default="active", nullable=False),
        sa.Column("external_provider", sa.String(length=40), nullable=True),
        sa.Column("external_place_id", sa.String(length=120), nullable=True),
        sa.Column("geonames_id", sa.String(length=40), nullable=True),
        sa.Column("osm_id", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'draft', 'archived')", name="ck_destinations_status"),
        sa.CheckConstraint("latitude >= -90.0 AND latitude <= 90.0", name="ck_destinations_latitude"),
        sa.CheckConstraint("longitude >= -180.0 AND longitude <= 180.0", name="ck_destinations_longitude"),
    )
    op.create_index("idx_destinations_slug", "destinations", ["slug"], unique=True)
    op.create_index("idx_destinations_country_region", "destinations", ["country_code", "region"])
    op.create_index("idx_destinations_coordinates", "destinations", ["latitude", "longitude"])
    if is_postgres:
        op.execute("CREATE INDEX idx_destinations_location_geom ON destinations USING GIST (location_geom)")

    # 2. Create destination_aliases
    op.create_table(
        "destination_aliases",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("destination_id", sa.String(length=36), sa.ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(length=120), nullable=False),
        sa.Column("locale", sa.String(length=10), server_default="en", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("destination_id", "alias", name="uq_destination_aliases_dest_alias"),
    )
    op.create_index("idx_destination_aliases_dest_id", "destination_aliases", ["destination_id"])
    op.create_index("idx_destination_aliases_search", "destination_aliases", ["alias"])

    # 3. Create user_locations
    op.create_table(
        "user_locations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("approx_latitude", sa.Float(), nullable=False),
        sa.Column("approx_longitude", sa.Float(), nullable=False),
        sa.Column("location_geom", geom_type, nullable=True),
        sa.Column("precision", sa.String(length=24), server_default="approximate", nullable=False),
        sa.Column("sharing_mode", sa.String(length=24), server_default="approximate", nullable=False),
        sa.Column("source", sa.String(length=32), server_default="manual", nullable=False),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("region", sa.String(length=80), nullable=True),
        sa.Column("country_code", sa.String(length=3), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", name="uq_user_locations_user_id"),
        sa.CheckConstraint(
            "precision IN ('exact', 'approximate', 'city', 'destination', 'region')",
            name="ck_user_locations_precision",
        ),
        sa.CheckConstraint(
            "sharing_mode IN ('private', 'approximate', 'explicit_share')",
            name="ck_user_locations_sharing_mode",
        ),
    )
    op.create_index("idx_user_locations_user_id", "user_locations", ["user_id"])
    op.create_index("idx_user_locations_approx_coords", "user_locations", ["approx_latitude", "approx_longitude"])
    if is_postgres:
        op.execute("CREATE INDEX idx_user_locations_location_geom ON user_locations USING GIST (location_geom)")

    # 4. Create trips
    op.create_table(
        "trips",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("destination_id", sa.String(length=36), sa.ForeignKey("destinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=24), server_default="planned", nullable=False),
        sa.Column("visibility", sa.String(length=24), server_default="discoverable", nullable=False),
        sa.Column("companion_preference", sa.String(length=32), server_default="open_to_companion", nullable=False),
        sa.Column("party_size", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("start_date <= end_date", name="ck_trips_start_end_dates"),
        sa.CheckConstraint(
            "status IN ('draft', 'planned', 'active', 'completed', 'cancelled', 'archived')",
            name="ck_trips_status",
        ),
        sa.CheckConstraint(
            "visibility IN ('private', 'matches_only', 'discoverable', 'public')",
            name="ck_trips_visibility",
        ),
        sa.CheckConstraint(
            "companion_preference IN ('travelling_alone', 'open_to_companion', 'travelling_with_group')",
            name="ck_trips_companion_preference",
        ),
        sa.CheckConstraint("party_size >= 1 AND party_size <= 50", name="ck_trips_party_size"),
    )
    op.create_index("idx_trips_user_id", "trips", ["user_id"])
    op.create_index("idx_trips_destination_id", "trips", ["destination_id"])
    op.create_index("idx_trips_dates", "trips", ["start_date", "end_date"])
    op.create_index("idx_trips_destination_dates", "trips", ["destination_id", "start_date", "end_date"])
    op.create_index("idx_trips_visibility_status", "trips", ["visibility", "status"])

    # 5. Create trip_intents
    op.create_table(
        "trip_intents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("trip_id", sa.String(length=36), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("intent", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("trip_id", "intent", name="uq_trip_intents_trip_intent"),
        sa.CheckConstraint(
            "intent IN ('dating_romantic', 'serious_relationship', 'casual_dating', 'travel_companion', 'friends_social', 'local_guide', 'activity_partner')",
            name="ck_trip_intents_intent",
        ),
    )
    op.create_index("idx_trip_intents_trip_id", "trip_intents", ["trip_id"])


def downgrade() -> None:
    op.drop_table("trip_intents")
    op.drop_table("trips")
    op.drop_table("user_locations")
    op.drop_table("destination_aliases")
    op.drop_table("destinations")
