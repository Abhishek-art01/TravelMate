from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.services.location_privacy import haversine_distance_km
from app.services.travel_dates import is_date_overlap


# Centralized matching score weights
WEIGHT_DESTINATION_MATCH = 30
WEIGHT_COUNTRY_MATCH = 15
WEIGHT_DATE_OVERLAP_STRONG = 20  # >= 3 days overlap
WEIGHT_DATE_OVERLAP_PARTIAL = 15  # 1-2 days overlap
WEIGHT_INTENT_MATCH = 15
WEIGHT_INTEREST_PER_ITEM = 3
WEIGHT_INTEREST_MAX = 15
WEIGHT_LANGUAGE_PER_ITEM = 5
WEIGHT_LANGUAGE_MAX = 10
WEIGHT_PREFERENCE_MATCH = 5
WEIGHT_COMPLETENESS_MAX = 5


@dataclass
class MatchResult:
    score: int
    reasons: list[str] = field(default_factory=list)
    approx_distance_km: float | None = None


@dataclass
class ViewerContext:
    user_id: str
    gender_identity: str | None = None
    age: int = 18
    trip_destinations: set[str] = field(default_factory=set)  # destination_ids
    trip_countries: set[str] = field(default_factory=set)  # country_codes
    trip_dates: list[tuple[date, date]] = field(default_factory=list)  # (start_date, end_date)
    trip_intents: set[str] = field(default_factory=set)
    travel_intentions: set[str] = field(default_factory=set)
    interests: set[str] = field(default_factory=set)
    languages: set[str] = field(default_factory=set)
    dating_intentions: set[str] = field(default_factory=set)
    discovery_preferences: set[str] = field(default_factory=set)
    approx_lat: float | None = None
    approx_lon: float | None = None


@dataclass
class CandidateContext:
    user_id: str
    display_name: str
    age: int
    gender_identity: str | None = None
    profile_completion: int = 0
    trip_destinations: set[str] = field(default_factory=set)  # destination_ids
    trip_destination_names: dict[str, str] = field(default_factory=dict)  # dest_id -> name
    trip_countries: set[str] = field(default_factory=set)  # country_codes
    trip_dates: list[tuple[date, date]] = field(default_factory=list)  # (start_date, end_date)
    trip_intents: set[str] = field(default_factory=set)
    companion_preferences: set[str] = field(default_factory=set)
    travel_intentions: set[str] = field(default_factory=set)
    interests: set[str] = field(default_factory=set)
    languages: set[str] = field(default_factory=set)
    dating_intentions: set[str] = field(default_factory=set)
    discovery_preferences: set[str] = field(default_factory=set)
    approx_lat: float | None = None
    approx_lon: float | None = None


def compute_match_score(viewer: ViewerContext, candidate: CandidateContext) -> MatchResult:
    """
    Compute a deterministic, explainable match score between 0 and 100
    based on travel overlap, shared intent, interests, and preferences.
    """
    total_score = 0
    reasons: list[str] = []

    # 1. Destination compatibility (up to 30 pts)
    shared_destinations = viewer.trip_destinations.intersection(candidate.trip_destinations)
    if shared_destinations:
        total_score += WEIGHT_DESTINATION_MATCH
        first_dest_id = next(iter(shared_destinations))
        dest_name = candidate.trip_destination_names.get(first_dest_id, "the same destination")
        reasons.append(f"Traveling to {dest_name}")
    else:
        shared_countries = viewer.trip_countries.intersection(candidate.trip_countries)
        if shared_countries:
            total_score += WEIGHT_COUNTRY_MATCH
            reasons.append(f"Traveling to the same country ({next(iter(shared_countries))})")

    # 2. Date overlap compatibility (up to 20 pts)
    max_overlap_days = 0
    for v_start, v_end in viewer.trip_dates:
        for c_start, c_end in candidate.trip_dates:
            if is_date_overlap(v_start, v_end, c_start, c_end):
                overlap_start = max(v_start, c_start)
                overlap_end = min(v_end, c_end)
                overlap_days = (overlap_end - overlap_start).days + 1
                if overlap_days > max_overlap_days:
                    max_overlap_days = overlap_days

    if max_overlap_days >= 3:
        total_score += WEIGHT_DATE_OVERLAP_STRONG
        reasons.append(f"Travel dates overlap by {max_overlap_days} days")
    elif max_overlap_days >= 1:
        total_score += WEIGHT_DATE_OVERLAP_PARTIAL
        reasons.append(f"Travel dates overlap by {max_overlap_days} day{'s' if max_overlap_days > 1 else ''}")

    # 3. Travel intent overlap (up to 15 pts)
    all_viewer_intents = viewer.trip_intents.union(viewer.travel_intentions)
    all_candidate_intents = candidate.trip_intents.union(candidate.travel_intentions)
    shared_intents = all_viewer_intents.intersection(all_candidate_intents)
    if shared_intents:
        total_score += WEIGHT_INTENT_MATCH
        intent_display = next(iter(shared_intents)).replace("_", " ").title()
        reasons.append(f"Similar travel intent: {intent_display}")

    # 4. Shared interests (up to 15 pts)
    shared_interests = viewer.interests.intersection(candidate.interests)
    if shared_interests:
        interest_pts = min(WEIGHT_INTEREST_MAX, len(shared_interests) * WEIGHT_INTEREST_PER_ITEM)
        total_score += interest_pts
        interest_sample = list(shared_interests)[:3]
        sample_str = ", ".join(s.replace("_", " ").title() for s in interest_sample)
        if len(shared_interests) > 3:
            reasons.append(f"{len(shared_interests)} shared interests including {sample_str}")
        else:
            reasons.append(f"Shared interests: {sample_str}")

    # 5. Language compatibility (up to 10 pts)
    shared_languages = viewer.languages.intersection(candidate.languages)
    if shared_languages:
        lang_pts = min(WEIGHT_LANGUAGE_MAX, len(shared_languages) * WEIGHT_LANGUAGE_PER_ITEM)
        total_score += lang_pts
        reasons.append(f"Shared language: {', '.join(s.upper() for s in list(shared_languages)[:2])}")

    # 6. Companion / Dating preference compatibility (up to 5 pts)
    if "open_to_companion" in candidate.companion_preferences:
        total_score += WEIGHT_PREFERENCE_MATCH
        reasons.append("Open to travel companion")
    elif viewer.dating_intentions and candidate.dating_intentions:
        shared_dating = viewer.dating_intentions.intersection(candidate.dating_intentions)
        if shared_dating:
            total_score += WEIGHT_PREFERENCE_MATCH
            reasons.append("Compatible dating intention")

    # 7. Profile completeness (up to 5 pts)
    completeness_pts = min(WEIGHT_COMPLETENESS_MAX, round(candidate.profile_completion * 0.05))
    total_score += completeness_pts

    # Distance calculation (for display / proximity context, never affects eligibility negatively)
    approx_distance: float | None = None
    if (
        viewer.approx_lat is not None
        and viewer.approx_lon is not None
        and candidate.approx_lat is not None
        and candidate.approx_lon is not None
    ):
        dist = haversine_distance_km(
            viewer.approx_lat, viewer.approx_lon, candidate.approx_lat, candidate.approx_lon
        )
        approx_distance = round(dist, 1)
        if approx_distance <= 50.0 and not shared_destinations:
            reasons.append(f"Nearby (~{round(approx_distance)} km)")

    final_score = max(0, min(100, total_score))
    return MatchResult(score=final_score, reasons=reasons, approx_distance_km=approx_distance)
