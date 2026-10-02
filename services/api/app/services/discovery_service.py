from __future__ import annotations

import base64
import uuid
from datetime import UTC, date, datetime
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.block import UserBlock
from app.models.destination import Destination
from app.models.discovery import DiscoveryInteraction
from app.models.interest import Interest, UserInterest
from app.models.location import UserLocation
from app.models.media import MediaAsset
from app.models.preferences import UserPreferenceOption, UserPreferences
from app.models.privacy import UserPrivacySettings
from app.models.profile import UserProfile
from app.models.report import UserReport
from app.models.trip import Trip, TripIntent
from app.models.user import User
from app.schemas.discovery import (
    AdminReportListResponse,
    AdminReportRead,
    AdminReportUpdate,
    DiscoveryCandidateRead,
    DiscoveryInteractionRead,
    DiscoveryListResponse,
    DiscoveryTripRead,
    REPORT_REASONS,
    UserBlockListResponse,
    UserBlockRead,
    UserReportRead,
)
from app.schemas.profile import calculate_age
from app.services.matching_engine import (
    CandidateContext,
    ViewerContext,
    compute_match_score,
)
from app.services.media_storage import StorageUnavailable
from app.services.r2_storage import R2Storage
from app.services.travel_dates import is_date_overlap, validate_date_range


def encode_cursor(score: int, user_id: str) -> str:
    payload = f"{score}:{user_id}".encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")


def decode_cursor(cursor_str: str) -> tuple[int, str]:
    try:
        raw = base64.urlsafe_b64decode(cursor_str.encode("utf-8")).decode("utf-8")
        parts = raw.split(":", 1)
        if len(parts) != 2:
            raise ValueError("Malformed cursor structure")
        return int(parts[0]), parts[1]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_CURSOR", "message": "Invalid pagination cursor."}},
        ) from exc


class DiscoveryService:
    @staticmethod
    async def get_candidates(
        db: AsyncSession,
        viewer_id: str,
        *,
        destination_id: str | None = None,
        country_code: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        intent: str | None = None,
        interests: list[str] | None = None,
        languages: list[str] | None = None,
        gender: str | None = None,
        min_age: int | None = None,
        max_age: int | None = None,
        cursor: str | None = None,
        limit: int = 20,
    ) -> DiscoveryListResponse:
        # Bounded page size
        limit = max(1, min(limit, 50))

        if start_date and end_date:
            validate_date_range(start_date, end_date)

        # 1. Fetch viewer data (profile, preferences, trips, location)
        viewer_profile_res = await db.execute(select(UserProfile).where(UserProfile.user_id == viewer_id))
        viewer_profile = viewer_profile_res.scalar_one_or_none()
        if not viewer_profile or not viewer_profile.date_of_birth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "PROFILE_INCOMPLETE", "message": "Viewer profile must be completed for discovery."}},
            )

        viewer_age = calculate_age(date.fromisoformat(viewer_profile.date_of_birth))

        # Viewer preferences
        viewer_pref_res = await db.execute(select(UserPreferences).where(UserPreferences.user_id == viewer_id))
        viewer_pref = viewer_pref_res.scalar_one_or_none()
        viewer_min_age = viewer_pref.minimum_age if viewer_pref else 18
        viewer_max_age = viewer_pref.maximum_age if viewer_pref else None

        # Viewer preference options
        viewer_opts_res = await db.execute(
            select(UserPreferenceOption).where(UserPreferenceOption.user_id == viewer_id)
        )
        viewer_opts = list(viewer_opts_res.scalars().all())
        viewer_travel_intentions = {o.value for o in viewer_opts if o.category == "travel_intention"}
        viewer_dating_intentions = {o.value for o in viewer_opts if o.category == "dating_intention"}
        viewer_discovery_prefs = {o.value for o in viewer_opts if o.category == "discovery_preference"}
        viewer_languages = {o.value for o in viewer_opts if o.category == "language"}

        # Viewer interests
        viewer_interests_res = await db.execute(
            select(Interest.code)
            .join(UserInterest, UserInterest.interest_id == Interest.id)
            .where(UserInterest.user_id == viewer_id)
        )
        viewer_interests = set(viewer_interests_res.scalars().all())

        # Viewer trips (planned or active)
        viewer_trips_res = await db.execute(
            select(Trip)
            .options(selectinload(Trip.intents), selectinload(Trip.destination))
            .where(
                Trip.user_id == viewer_id,
                Trip.status.in_(["planned", "active"]),
            )
        )
        viewer_trips = list(viewer_trips_res.scalars().all())
        viewer_trip_destinations = {t.destination_id for t in viewer_trips}
        viewer_trip_countries = {t.destination.country_code for t in viewer_trips if t.destination}
        viewer_trip_dates = [(t.start_date, t.end_date) for t in viewer_trips]
        viewer_trip_intents = {i.intent for t in viewer_trips for i in t.intents}

        # Viewer location
        viewer_loc_res = await db.execute(select(UserLocation).where(UserLocation.user_id == viewer_id))
        viewer_loc = viewer_loc_res.scalar_one_or_none()
        viewer_lat = viewer_loc.approx_latitude if viewer_loc else None
        viewer_lon = viewer_loc.approx_longitude if viewer_loc else None

        viewer_context = ViewerContext(
            user_id=viewer_id,
            gender_identity=viewer_profile.gender_identity,
            age=viewer_age,
            trip_destinations=viewer_trip_destinations,
            trip_countries=viewer_trip_countries,
            trip_dates=viewer_trip_dates,
            trip_intents=viewer_trip_intents,
            travel_intentions=viewer_travel_intentions,
            interests=viewer_interests,
            languages=viewer_languages,
            dating_intentions=viewer_dating_intentions,
            discovery_preferences=viewer_discovery_prefs,
            approx_lat=viewer_lat,
            approx_lon=viewer_lon,
        )

        # 2. Build candidate eligibility query with hard filters
        today = datetime.now(UTC).date()
        cutoff_18 = today.replace(year=today.year - 18).isoformat()

        # Bidirectional blocks subqueries
        blocked_by_me = select(UserBlock.blocked_id).where(UserBlock.blocker_id == viewer_id)
        blocked_me = select(UserBlock.blocker_id).where(UserBlock.blocked_id == viewer_id)
        # Already interacted subquery
        interacted_with = select(DiscoveryInteraction.target_user_id).where(DiscoveryInteraction.user_id == viewer_id)

        stmt = (
            select(UserProfile.user_id)
            .join(User, User.id == UserProfile.user_id)
            .where(
                UserProfile.user_id != viewer_id,
                User.account_status == "active",
                User.deleted_at.is_(None),
                UserProfile.profile_visibility.in_(["public", "discoverable"]),
                UserProfile.discovery_visibility.is_(True),
                UserProfile.date_of_birth.is_not(None),
                UserProfile.date_of_birth <= cutoff_18,
                UserProfile.user_id.not_in(blocked_by_me),
                UserProfile.user_id.not_in(blocked_me),
                UserProfile.user_id.not_in(interacted_with),
            )
        )

        # Age filters from viewer preferences
        if viewer_min_age and viewer_min_age > 18:
            cutoff_viewer_min = today.replace(year=today.year - viewer_min_age).isoformat()
            stmt = stmt.where(UserProfile.date_of_birth <= cutoff_viewer_min)
        if viewer_max_age:
            cutoff_viewer_max = today.replace(year=today.year - viewer_max_age - 1).isoformat()
            stmt = stmt.where(UserProfile.date_of_birth > cutoff_viewer_max)

        # Filter query params
        if min_age and min_age > 18:
            cutoff_param_min = today.replace(year=today.year - min_age).isoformat()
            stmt = stmt.where(UserProfile.date_of_birth <= cutoff_param_min)
        if max_age:
            cutoff_param_max = today.replace(year=today.year - max_age - 1).isoformat()
            stmt = stmt.where(UserProfile.date_of_birth > cutoff_param_max)

        if gender:
            stmt = stmt.where(UserProfile.gender_identity == gender)

        if destination_id:
            trip_subq = select(Trip.user_id).where(
                Trip.destination_id == destination_id,
                Trip.status.in_(["planned", "active"]),
                Trip.visibility.in_(["discoverable", "public"]),
            )
            stmt = stmt.where(UserProfile.user_id.in_(trip_subq))

        if country_code:
            trip_country_subq = (
                select(Trip.user_id)
                .join(Destination, Destination.id == Trip.destination_id)
                .where(
                    Destination.country_code == country_code.upper(),
                    Trip.status.in_(["planned", "active"]),
                    Trip.visibility.in_(["discoverable", "public"]),
                )
            )
            stmt = stmt.where(UserProfile.user_id.in_(trip_country_subq))

        if start_date and end_date:
            date_subq = select(Trip.user_id).where(
                Trip.status.in_(["planned", "active"]),
                Trip.visibility.in_(["discoverable", "public"]),
                Trip.start_date <= end_date,
                Trip.end_date >= start_date,
            )
            stmt = stmt.where(UserProfile.user_id.in_(date_subq))

        if intent:
            clean_intent = intent.strip().lower()
            intent_subq = (
                select(Trip.user_id)
                .join(TripIntent, TripIntent.trip_id == Trip.id)
                .where(
                    Trip.status.in_(["planned", "active"]),
                    Trip.visibility.in_(["discoverable", "public"]),
                    TripIntent.intent == clean_intent,
                )
            )
            pref_intent_subq = select(UserPreferenceOption.user_id).where(
                UserPreferenceOption.category == "travel_intention",
                UserPreferenceOption.value == clean_intent,
            )
            stmt = stmt.where(or_(UserProfile.user_id.in_(intent_subq), UserProfile.user_id.in_(pref_intent_subq)))

        eligible_ids_res = await db.execute(stmt)
        candidate_ids = list(eligible_ids_res.scalars().all())
        if not candidate_ids:
            return DiscoveryListResponse(items=[], next_cursor=None, total=0)

        # 3. Batch load candidate details for scoring
        # Load Profiles & Users
        profiles_res = await db.execute(
            select(UserProfile, User.is_verified)
            .join(User, User.id == UserProfile.user_id)
            .where(UserProfile.user_id.in_(candidate_ids))
        )
        profile_rows = profiles_res.all()
        profiles_map = {row[0].user_id: (row[0], row[1]) for row in profile_rows}

        # Load Preferences
        prefs_res = await db.execute(select(UserPreferences).where(UserPreferences.user_id.in_(candidate_ids)))
        prefs_map = {p.user_id: p for p in prefs_res.scalars().all()}

        # Load Preference Options
        options_res = await db.execute(
            select(UserPreferenceOption).where(UserPreferenceOption.user_id.in_(candidate_ids))
        )
        options_by_user: dict[str, list[UserPreferenceOption]] = {uid: [] for uid in candidate_ids}
        for opt in options_res.scalars().all():
            options_by_user[opt.user_id].append(opt)

        # Load Interests
        interests_res = await db.execute(
            select(UserInterest.user_id, Interest.code)
            .join(Interest, Interest.id == UserInterest.interest_id)
            .where(UserInterest.user_id.in_(candidate_ids))
        )
        interests_by_user: dict[str, set[str]] = {uid: set() for uid in candidate_ids}
        for uid, code in interests_res.all():
            interests_by_user[uid].add(code)

        # Load Privacy Settings
        privacy_res = await db.execute(
            select(UserPrivacySettings).where(UserPrivacySettings.user_id.in_(candidate_ids))
        )
        privacy_map = {p.user_id: p for p in privacy_res.scalars().all()}

        # Load Locations
        locs_res = await db.execute(select(UserLocation).where(UserLocation.user_id.in_(candidate_ids)))
        locs_map = {l.user_id: l for l in locs_res.scalars().all()}

        # Load Trips (public & discoverable only!)
        trips_res = await db.execute(
            select(Trip)
            .options(selectinload(Trip.destination), selectinload(Trip.intents))
            .where(
                Trip.user_id.in_(candidate_ids),
                Trip.status.in_(["planned", "active"]),
                Trip.visibility.in_(["discoverable", "public"]),
            )
        )
        trips_by_user: dict[str, list[Trip]] = {uid: [] for uid in candidate_ids}
        for t in trips_res.scalars().all():
            trips_by_user[t.user_id].append(t)

        # Load profile photos (approved, ready, profile_media)
        media_res = await db.execute(
            select(MediaAsset)
            .where(
                MediaAsset.user_id.in_(candidate_ids),
                MediaAsset.media_type == "profile_media",
                MediaAsset.processing_status == "ready",
                MediaAsset.moderation_status == "approved",
                MediaAsset.visibility.in_(["public", "profile_only"]),
                MediaAsset.deleted_at.is_(None),
            )
            .order_by(MediaAsset.sort_order.asc(), MediaAsset.created_at.asc())
        )
        photo_keys: dict[str, str] = {}
        for m in media_res.scalars().all():
            if m.user_id not in photo_keys:
                photo_keys[m.user_id] = m.object_key

        storage: R2Storage | None = None
        try:
            storage = R2Storage()
        except StorageUnavailable:
            storage = None

        photo_urls: dict[str, str | None] = {}
        for uid, key in photo_keys.items():
            if storage:
                try:
                    photo_urls[uid] = await storage.create_download_url(key, 3600)
                except Exception:
                    photo_urls[uid] = None
            else:
                photo_urls[uid] = None

        # 4. Filter by candidate preferences & compute scores
        scored_candidates: list[DiscoveryCandidateRead] = []

        for cid in candidate_ids:
            if cid not in profiles_map:
                continue
            cand_profile, cand_verified = profiles_map[cid]
            if not cand_profile.date_of_birth:
                continue
            cand_age = calculate_age(date.fromisoformat(cand_profile.date_of_birth))

            # Candidate's age preference check on viewer
            cand_pref = prefs_map.get(cid)
            if cand_pref:
                if viewer_age < cand_pref.minimum_age:
                    continue
                if cand_pref.maximum_age is not None and viewer_age > cand_pref.maximum_age:
                    continue

            cand_opts = options_by_user.get(cid, [])
            cand_travel_intentions = {o.value for o in cand_opts if o.category == "travel_intention"}
            cand_dating_intentions = {o.value for o in cand_opts if o.category == "dating_intention"}
            cand_discovery_prefs = {o.value for o in cand_opts if o.category == "discovery_preference"}
            cand_languages = {o.value for o in cand_opts if o.category == "language"}
            cand_interests = interests_by_user.get(cid, set())

            # Optional interests filter
            if interests:
                required_interests = set(interests)
                if not required_interests.intersection(cand_interests):
                    continue

            # Optional languages filter
            if languages:
                required_languages = set(languages)
                if not required_languages.intersection(cand_languages):
                    continue

            cand_trips = trips_by_user.get(cid, [])
            cand_dest_ids = {t.destination_id for t in cand_trips}
            cand_dest_names = {t.destination_id: t.destination.name for t in cand_trips if t.destination}
            cand_countries = {t.destination.country_code for t in cand_trips if t.destination}
            cand_dates = [(t.start_date, t.end_date) for t in cand_trips]
            cand_intents = {i.intent for t in cand_trips for i in t.intents}
            cand_companions = {t.companion_preference for t in cand_trips}

            # Location privacy
            cand_privacy = privacy_map.get(cid)
            cand_loc = locs_map.get(cid)
            cand_lat = cand_loc.approx_latitude if cand_loc else None
            cand_lon = cand_loc.approx_longitude if cand_loc else None

            cand_context = CandidateContext(
                user_id=cid,
                display_name=cand_profile.display_name or "Traveler",
                age=cand_age,
                gender_identity=cand_profile.gender_identity,
                profile_completion=cand_profile.profile_completion,
                trip_destinations=cand_dest_ids,
                trip_destination_names=cand_dest_names,
                trip_countries=cand_countries,
                trip_dates=cand_dates,
                trip_intents=cand_intents,
                companion_preferences=cand_companions,
                travel_intentions=cand_travel_intentions,
                interests=cand_interests,
                languages=cand_languages,
                dating_intentions=cand_dating_intentions,
                discovery_preferences=cand_discovery_prefs,
                approx_lat=cand_lat,
                approx_lon=cand_lon,
            )

            match_result = compute_match_score(viewer_context, cand_context)

            # Build safe read model respecting location precision
            loc_precision = cand_privacy.location_precision if cand_privacy else "approximate"
            show_approx_coords = loc_precision == "approximate" and cand_lat is not None

            read_trips = [
                DiscoveryTripRead(
                    id=t.id,
                    destination_id=t.destination_id,
                    destination_name=t.destination.name if t.destination else "Unknown",
                    city=t.destination.city if t.destination else None,
                    region=t.destination.region if t.destination else None,
                    country=t.destination.country if t.destination else "Unknown",
                    country_code=t.destination.country_code if t.destination else "XX",
                    start_date=t.start_date,
                    end_date=t.end_date,
                    companion_preference=t.companion_preference,
                    party_size=t.party_size,
                    intents=[i.intent for i in t.intents],
                )
                for t in cand_trips
            ]

            candidate_read = DiscoveryCandidateRead(
                id=cid,
                display_name=cand_profile.display_name or "Traveler",
                age=cand_age,
                bio=cand_profile.bio,
                gender_identity=cand_profile.gender_identity,
                is_verified=cand_verified,
                photo_url=photo_urls.get(cid),
                approx_city=cand_loc.city if loc_precision != "hidden" and cand_loc else None,
                approx_country=cand_loc.country_code if loc_precision != "hidden" and cand_loc else None,
                approx_latitude=cand_lat if show_approx_coords else None,
                approx_longitude=cand_lon if show_approx_coords else None,
                approx_distance_km=match_result.approx_distance_km if show_approx_coords else None,
                trips=read_trips,
                travel_intentions=sorted(cand_travel_intentions),
                interests=sorted(cand_interests),
                languages=sorted(cand_languages),
                match_score=match_result.score,
                match_reasons=match_result.reasons,
            )
            scored_candidates.append(candidate_read)

        # 5. Deterministic sorting: match_score DESC, id ASC
        scored_candidates.sort(key=lambda c: (-c.match_score, c.id))
        total_eligible = len(scored_candidates)

        # 6. Cursor pagination
        if cursor:
            cursor_score, cursor_id = decode_cursor(cursor)
            scored_candidates = [
                c
                for c in scored_candidates
                if (c.match_score < cursor_score) or (c.match_score == cursor_score and c.id > cursor_id)
            ]

        # Slice limit
        paged_items = scored_candidates[:limit]
        next_cursor = None
        if len(scored_candidates) > limit:
            last_item = paged_items[-1]
            next_cursor = encode_cursor(last_item.match_score, last_item.id)

        return DiscoveryListResponse(
            items=paged_items,
            next_cursor=next_cursor,
            total=total_eligible,
        )

    @staticmethod
    async def get_candidate_detail(
        db: AsyncSession,
        viewer_id: str,
        candidate_id: str,
    ) -> DiscoveryCandidateRead:
        if viewer_id == candidate_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "CANDIDATE_NOT_FOUND", "message": "Candidate not found."}},
            )

        # Check bidirectional block
        block_check = await db.execute(
            select(UserBlock).where(
                or_(
                    (UserBlock.blocker_id == viewer_id) & (UserBlock.blocked_id == candidate_id),
                    (UserBlock.blocker_id == candidate_id) & (UserBlock.blocked_id == viewer_id),
                )
            )
        )
        if block_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "CANDIDATE_NOT_FOUND", "message": "Candidate not found."}},
            )

        # Fetch candidate User and Profile
        user_res = await db.execute(
            select(UserProfile, User.is_verified, User.account_status, User.deleted_at)
            .join(User, User.id == UserProfile.user_id)
            .where(UserProfile.user_id == candidate_id)
        )
        row = user_res.first()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "CANDIDATE_NOT_FOUND", "message": "Candidate not found."}},
            )
        cand_profile, cand_verified, cand_status, cand_deleted = row
        if (
            cand_status != "active"
            or cand_deleted is not None
            or cand_profile.profile_visibility not in ("public", "discoverable")
            or not cand_profile.discovery_visibility
            or not cand_profile.date_of_birth
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "CANDIDATE_NOT_FOUND", "message": "Candidate not found."}},
            )

        cand_age = calculate_age(date.fromisoformat(cand_profile.date_of_birth))
        if cand_age < 18:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "CANDIDATE_NOT_FOUND", "message": "Candidate not found."}},
            )

        # Compute match score between viewer and this candidate
        list_res = await DiscoveryService.get_candidates(
            db,
            viewer_id,
            limit=50,
        )
        for item in list_res.items:
            if item.id == candidate_id:
                return item

        # If candidate wasn't in top page, compute directly
        # Fetch candidate options, interests, trips, privacy, loc
        opts_res = await db.execute(
            select(UserPreferenceOption).where(UserPreferenceOption.user_id == candidate_id)
        )
        cand_opts = list(opts_res.scalars().all())
        cand_travel_intentions = {o.value for o in cand_opts if o.category == "travel_intention"}
        cand_dating_intentions = {o.value for o in cand_opts if o.category == "dating_intention"}
        cand_discovery_prefs = {o.value for o in cand_opts if o.category == "discovery_preference"}
        cand_languages = {o.value for o in cand_opts if o.category == "language"}

        interests_res = await db.execute(
            select(Interest.code)
            .join(UserInterest, UserInterest.interest_id == Interest.id)
            .where(UserInterest.user_id == candidate_id)
        )
        cand_interests = set(interests_res.scalars().all())

        trips_res = await db.execute(
            select(Trip)
            .options(selectinload(Trip.destination), selectinload(Trip.intents))
            .where(
                Trip.user_id == candidate_id,
                Trip.status.in_(["planned", "active"]),
                Trip.visibility.in_(["discoverable", "public"]),
            )
        )
        cand_trips = list(trips_res.scalars().all())

        privacy_res = await db.execute(
            select(UserPrivacySettings).where(UserPrivacySettings.user_id == candidate_id)
        )
        cand_privacy = privacy_res.scalar_one_or_none()
        locs_res = await db.execute(select(UserLocation).where(UserLocation.user_id == candidate_id))
        cand_loc = locs_res.scalar_one_or_none()
        cand_lat = cand_loc.approx_latitude if cand_loc else None
        cand_lon = cand_loc.approx_longitude if cand_loc else None

        # Photo
        media_res = await db.execute(
            select(MediaAsset)
            .where(
                MediaAsset.user_id == candidate_id,
                MediaAsset.media_type == "profile_media",
                MediaAsset.processing_status == "ready",
                MediaAsset.moderation_status == "approved",
                MediaAsset.visibility.in_(["public", "profile_only"]),
                MediaAsset.deleted_at.is_(None),
            )
            .order_by(MediaAsset.sort_order.asc(), MediaAsset.created_at.asc())
        )
        first_asset = media_res.scalar_one_or_none()
        photo_url: str | None = None
        if first_asset:
            try:
                storage = R2Storage()
                photo_url = await storage.create_download_url(first_asset.object_key, 3600)
            except Exception:
                photo_url = None

        loc_precision = cand_privacy.location_precision if cand_privacy else "approximate"
        show_approx_coords = loc_precision == "approximate" and cand_lat is not None

        read_trips = [
            DiscoveryTripRead(
                id=t.id,
                destination_id=t.destination_id,
                destination_name=t.destination.name if t.destination else "Unknown",
                city=t.destination.city if t.destination else None,
                region=t.destination.region if t.destination else None,
                country=t.destination.country if t.destination else "Unknown",
                country_code=t.destination.country_code if t.destination else "XX",
                start_date=t.start_date,
                end_date=t.end_date,
                companion_preference=t.companion_preference,
                party_size=t.party_size,
                intents=[i.intent for i in t.intents],
            )
            for t in cand_trips
        ]

        return DiscoveryCandidateRead(
            id=candidate_id,
            display_name=cand_profile.display_name or "Traveler",
            age=cand_age,
            bio=cand_profile.bio,
            gender_identity=cand_profile.gender_identity,
            is_verified=cand_verified,
            photo_url=photo_url,
            approx_city=cand_loc.city if loc_precision != "hidden" and cand_loc else None,
            approx_country=cand_loc.country_code if loc_precision != "hidden" and cand_loc else None,
            approx_latitude=cand_lat if show_approx_coords else None,
            approx_longitude=cand_lon if show_approx_coords else None,
            approx_distance_km=None,
            trips=read_trips,
            travel_intentions=sorted(cand_travel_intentions),
            interests=sorted(cand_interests),
            languages=sorted(cand_languages),
            match_score=50,
            match_reasons=["Public travel profile"],
        )

    @staticmethod
    async def record_interaction(
        db: AsyncSession,
        user_id: str,
        target_user_id: str,
        interaction_type: str,
    ) -> DiscoveryInteractionRead:
        if user_id == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "CANNOT_INTERACT_WITH_SELF", "message": "Cannot interact with yourself."}},
            )

        # Check bidirectional block
        block_check = await db.execute(
            select(UserBlock).where(
                or_(
                    (UserBlock.blocker_id == user_id) & (UserBlock.blocked_id == target_user_id),
                    (UserBlock.blocker_id == target_user_id) & (UserBlock.blocked_id == user_id),
                )
            )
        )
        if block_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found."}},
            )

        # Target user must exist and be active
        target_user = await db.get(User, target_user_id)
        if not target_user or target_user.account_status != "active" or target_user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found."}},
            )

        # Check if interaction already exists
        existing_res = await db.execute(
            select(DiscoveryInteraction).where(
                DiscoveryInteraction.user_id == user_id,
                DiscoveryInteraction.target_user_id == target_user_id,
            )
        )
        existing = existing_res.scalar_one_or_none()
        if existing:
            if existing.interaction_type != interaction_type:
                existing.interaction_type = interaction_type
                await db.flush()
            is_match = False
            if existing.interaction_type == "like":
                reverse_res = await db.execute(
                    select(DiscoveryInteraction).where(
                        DiscoveryInteraction.user_id == target_user_id,
                        DiscoveryInteraction.target_user_id == user_id,
                        DiscoveryInteraction.interaction_type == "like",
                    )
                )
                is_match = reverse_res.scalar_one_or_none() is not None
            return DiscoveryInteractionRead(
                id=existing.id,
                user_id=existing.user_id,
                target_user_id=existing.target_user_id,
                interaction_type=existing.interaction_type,
                is_match=is_match,
                created_at=existing.created_at,
            )

        # Mutual like detection
        is_match = False
        if interaction_type == "like":
            reverse_res = await db.execute(
                select(DiscoveryInteraction).where(
                    DiscoveryInteraction.user_id == target_user_id,
                    DiscoveryInteraction.target_user_id == user_id,
                    DiscoveryInteraction.interaction_type == "like",
                )
            )
            is_match = reverse_res.scalar_one_or_none() is not None

        interaction_id = str(uuid.uuid4())
        interaction = DiscoveryInteraction(
            id=interaction_id,
            user_id=user_id,
            target_user_id=target_user_id,
            interaction_type=interaction_type,
        )
        db.add(interaction)
        await db.flush()

        return DiscoveryInteractionRead(
            id=interaction.id,
            user_id=interaction.user_id,
            target_user_id=interaction.target_user_id,
            interaction_type=interaction.interaction_type,
            is_match=is_match,
            created_at=interaction.created_at,
        )

    # --- Block Management ---
    @staticmethod
    async def block_user(
        db: AsyncSession,
        blocker_id: str,
        blocked_id: str,
        reason: str | None = None,
    ) -> UserBlockRead:
        if blocker_id == blocked_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "CANNOT_BLOCK_SELF", "message": "You cannot block yourself."}},
            )

        target_user = await db.get(User, blocked_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found."}},
            )

        # Idempotent: check existing
        existing_res = await db.execute(
            select(UserBlock).where(
                UserBlock.blocker_id == blocker_id,
                UserBlock.blocked_id == blocked_id,
            )
        )
        existing = existing_res.scalar_one_or_none()
        if existing:
            return UserBlockRead.model_validate(existing)

        block = UserBlock(
            id=str(uuid.uuid4()),
            blocker_id=blocker_id,
            blocked_id=blocked_id,
            reason=reason,
        )
        db.add(block)
        await db.flush()
        return UserBlockRead.model_validate(block)

    @staticmethod
    async def unblock_user(
        db: AsyncSession,
        blocker_id: str,
        blocked_id: str,
    ) -> None:
        stmt = delete(UserBlock).where(
            UserBlock.blocker_id == blocker_id,
            UserBlock.blocked_id == blocked_id,
        )
        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "BLOCK_NOT_FOUND", "message": "Block record not found."}},
            )
        await db.flush()

    @staticmethod
    async def list_blocks(
        db: AsyncSession,
        blocker_id: str,
    ) -> UserBlockListResponse:
        stmt = (
            select(UserBlock)
            .where(UserBlock.blocker_id == blocker_id)
            .order_by(UserBlock.created_at.desc())
        )
        result = await db.execute(stmt)
        blocks = list(result.scalars().all())
        return UserBlockListResponse(
            items=[UserBlockRead.model_validate(b) for b in blocks],
            total=len(blocks),
        )

    # --- Report Management ---
    @staticmethod
    async def create_report(
        db: AsyncSession,
        reporter_id: str,
        reported_id: str,
        reason: REPORT_REASONS,
        details: str | None = None,
    ) -> UserReportRead:
        if reporter_id == reported_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "CANNOT_REPORT_SELF", "message": "You cannot report yourself."}},
            )

        reported_user = await db.get(User, reported_id)
        if not reported_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "USER_NOT_FOUND", "message": "Reported user not found."}},
            )

        report = UserReport(
            id=str(uuid.uuid4()),
            reporter_id=reporter_id,
            reported_id=reported_id,
            reason=reason,
            details=details,
            status="pending",
        )
        db.add(report)
        await db.flush()
        return UserReportRead.model_validate(report)

    @staticmethod
    async def list_admin_reports(
        db: AsyncSession,
        status_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AdminReportListResponse:
        stmt = select(UserReport).order_by(UserReport.created_at.desc())
        count_stmt = select(func.count(UserReport.id))

        if status_filter:
            stmt = stmt.where(UserReport.status == status_filter)
            count_stmt = count_stmt.where(UserReport.status == status_filter)

        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = stmt.limit(limit).offset(offset)
        result = await db.execute(stmt)
        reports = list(result.scalars().all())

        return AdminReportListResponse(
            items=[AdminReportRead.model_validate(r) for r in reports],
            total=total,
        )

    @staticmethod
    async def update_admin_report(
        db: AsyncSession,
        report_id: str,
        reviewed_by_id: str,
        update_data: AdminReportUpdate,
    ) -> AdminReportRead:
        report = await db.get(UserReport, report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "REPORT_NOT_FOUND", "message": "Report not found."}},
            )

        report.status = update_data.status
        report.reviewed_by_id = reviewed_by_id
        if update_data.resolution_notes is not None:
            report.resolution_notes = update_data.resolution_notes
        report.updated_at = datetime.now(UTC)

        await db.flush()
        return AdminReportRead.model_validate(report)
