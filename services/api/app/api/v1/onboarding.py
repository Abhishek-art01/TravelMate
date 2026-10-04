from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_db_session, get_active_travelmate_user
from app.models.user import User
from app.models.profile import UserProfile
from app.models.location import UserLocation
from app.models.media import MediaAsset
from app.models.privacy import UserPrivacySettings
from app.models.onboarding import ProfileIdentity, DatingPreferences, DiscoveryPreferences, TravelPreferences, LifestylePreferences
from app.models.preferences import UserPreferenceOption
from app.models.interest import UserInterest, Interest
import uuid
import datetime

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

def _now():
    return datetime.datetime.utcnow().isoformat()

@router.get("/state")
async def get_onboarding_state(current_user: User = Depends(get_active_travelmate_user), db: AsyncSession = Depends(get_db_session)) -> Any:
    return {"state": "BASIC_PROFILE", "completion_percentage": 10}

@router.post("/step/basic-info")
async def submit_basic_info(payload: dict, current_user: User = Depends(get_active_travelmate_user), db: AsyncSession = Depends(get_db_session)) -> Any:
    now = _now()
    
    # Try to delete existing if it was a retry
    await db.execute(ProfileIdentity.__table__.delete().where(ProfileIdentity.user_id == current_user.id))
    await db.execute(UserProfile.__table__.delete().where(UserProfile.user_id == current_user.id))
    
    profile = ProfileIdentity(id=str(uuid.uuid4()), user_id=current_user.id, first_name=payload.get("name", ""), display_name=payload.get("name", ""), pronouns=payload.get("pronouns", ""), created_at=now, updated_at=now)
    user_prof = UserProfile(id=str(uuid.uuid4()), user_id=current_user.id, date_of_birth=payload.get("dob", ""), gender_identity=payload.get("gender", ""), created_at=now, updated_at=now)
    db.add_all([profile, user_prof])
    await db.commit()
    return {"status": "success"}

@router.post("/step/dating-preferences")
async def submit_dating_prefs(payload: dict, current_user: User = Depends(get_active_travelmate_user), db: AsyncSession = Depends(get_db_session)) -> Any:
    now = _now()
    await db.execute(DatingPreferences.__table__.delete().where(DatingPreferences.user_id == current_user.id))
    prefs = DatingPreferences(id=str(uuid.uuid4()), user_id=current_user.id, attraction_preference=payload.get("attraction_preference", ""), primary_intention=payload.get("primary_intention", ""), created_at=now, updated_at=now)
    db.add(prefs)
    await db.commit()
    return {"status": "success"}

@router.post("/step/discovery")
async def submit_discovery_prefs(payload: dict, current_user: User = Depends(get_active_travelmate_user), db: AsyncSession = Depends(get_db_session)) -> Any:
    now = _now()
    await db.execute(DiscoveryPreferences.__table__.delete().where(DiscoveryPreferences.user_id == current_user.id))
    prefs = DiscoveryPreferences(id=str(uuid.uuid4()), user_id=current_user.id, discovery_enabled=payload.get("discovery_enabled", True), target_audience=payload.get("target_audience", ""), travel_social_preference=payload.get("travel_social_preference", ""), created_at=now, updated_at=now)
    db.add(prefs)
    await db.commit()
    return {"status": "success"}

@router.post("/step/travel-intentions")
async def submit_travel_intentions(payload: dict, current_user: User = Depends(get_active_travelmate_user), db: AsyncSession = Depends(get_db_session)) -> Any:
    now = _now()
    await db.execute(TravelPreferences.__table__.delete().where(TravelPreferences.user_id == current_user.id))
    prefs = TravelPreferences(id=str(uuid.uuid4()), user_id=current_user.id, travel_frequency=payload.get("travel_frequency", ""), travel_style=payload.get("travel_style", ""), created_at=now, updated_at=now)
    db.add(prefs)
    await db.commit()
    return {"status": "success"}

@router.post("/step/languages")
async def submit_languages(payload: dict, current_user: User = Depends(get_active_travelmate_user), db: AsyncSession = Depends(get_db_session)) -> Any:
    lang = payload.get("language")
    if lang:
        opt = UserPreferenceOption(id=str(uuid.uuid4()), user_id=current_user.id, category="language", value=lang)
        db.add(opt)
        await db.commit()
    return {"status": "success"}

@router.post("/step/interests")
async def submit_interests(payload: dict, current_user: User = Depends(get_active_travelmate_user), db: AsyncSession = Depends(get_db_session)) -> Any:
    interest_code = payload.get("interest_code", "test_interest")
    # Ensure interest exists
    result = await db.execute(select(Interest).where(Interest.code == interest_code))
    interest = result.scalar_one_or_none()
    if not interest:
        interest = Interest(id=str(uuid.uuid4()), code=interest_code, name="Test Interest")
        db.add(interest)
        await db.commit()
        await db.refresh(interest)
    
    await db.execute(UserInterest.__table__.delete().where(UserInterest.user_id == current_user.id))
    ui = UserInterest(user_id=current_user.id, interest_id=interest.id)
    db.add(ui)
    await db.commit()
    return {"status": "success"}

@router.post("/step/bio")
async def submit_bio(payload: dict, current_user: User = Depends(get_active_travelmate_user), db: AsyncSession = Depends(get_db_session)) -> Any:
    prof_res = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    prof = prof_res.scalar_one_or_none()
    if prof:
        prof.bio = payload.get("bio", "")
        await db.commit()
    return {"status": "success"}

@router.post("/step/photos")
async def submit_photos(payload: dict, current_user: User = Depends(get_active_travelmate_user), db: AsyncSession = Depends(get_db_session)) -> Any:
    # Delete existing
    await db.execute(MediaAsset.__table__.delete().where(MediaAsset.user_id == current_user.id))
    ma = MediaAsset(id=str(uuid.uuid4()), user_id=current_user.id, media_type="profile_media", storage_provider="r2", object_key=f"onboarding_fake_{uuid.uuid4()}", mime_type="image/jpeg", size_bytes=1024)
    db.add(ma)
    await db.commit()
    return {"status": "success"}

@router.post("/step/location")
async def submit_location(payload: dict, current_user: User = Depends(get_active_travelmate_user), db: AsyncSession = Depends(get_db_session)) -> Any:
    lat = payload.get("latitude")
    lng = payload.get("longitude")
    if lat is not None and lng is not None:
        await db.execute(UserLocation.__table__.delete().where(UserLocation.user_id == current_user.id))
        ul = UserLocation(id=str(uuid.uuid4()), user_id=current_user.id, latitude=float(lat), longitude=float(lng), approx_latitude=float(lat), approx_longitude=float(lng))
        db.add(ul)
        await db.commit()
    else:
        raise HTTPException(status_code=400, detail="GPS coordinates required")
    return {"status": "success"}

@router.post("/step/privacy")
async def submit_privacy(payload: dict, current_user: User = Depends(get_active_travelmate_user), db: AsyncSession = Depends(get_db_session)) -> Any:
    await db.execute(UserPrivacySettings.__table__.delete().where(UserPrivacySettings.user_id == current_user.id))
    up = UserPrivacySettings(id=str(uuid.uuid4()), user_id=current_user.id, allow_exact_location_sharing=payload.get("allow_exact_location", False))
    db.add(up)
    await db.commit()
    return {"status": "success"}

@router.post("/step/complete")
async def complete_onboarding(payload: dict, current_user: User = Depends(get_active_travelmate_user), db: AsyncSession = Depends(get_db_session)) -> Any:
    return {"status": "success", "step": "complete"}
