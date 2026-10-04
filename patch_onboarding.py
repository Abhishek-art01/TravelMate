import os

onboarding_py = """from fastapi import APIRouter, Depends, HTTPException, status
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
"""

with open("services/api/app/api/v1/onboarding.py", "w") as f:
    f.write(onboarding_py)

onboarding_tsx = """import React, { useState, useEffect } from 'react';
import { getSessionSnapshot } from '../../services/auth/auth';

export const OnboardingPage: React.FC = () => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<any>({});
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    getSessionSnapshot().then(({ session }) => {
      if (session) {
        setToken(session.access_token);
      }
    });
  }, []);

  const apiCall = async (endpoint: string, body: any) => {
    if (!token) return;
    const res = await fetch(`/api/v1/onboarding/step/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error('API failed');
  };

  const handleNext = async () => {
    try {
      if (step === 1) {
        // Welcome, do nothing
      } else if (step === 2) {
        await apiCall('basic-info', formData);
      } else if (step === 3) {
        await apiCall('dating-preferences', formData);
      } else if (step === 4) {
        await apiCall('discovery', formData);
      } else if (step === 5) {
        await apiCall('travel-intentions', formData);
      } else if (step === 6) {
        await apiCall('languages', formData);
      } else if (step === 7) {
        await apiCall('interests', formData);
      } else if (step === 8) {
        await apiCall('bio', formData);
      } else if (step === 9) {
        await apiCall('photos', formData);
      } else if (step === 10) {
        // location and complete
        if (!formData.latitude || !formData.longitude) {
           alert("Please wait for GPS location");
           return;
        }
        await apiCall('location', formData);
        await apiCall('privacy', formData);
        await apiCall('complete', formData);
        alert('Onboarding Complete!');
        return;
      }
      setStep(step + 1);
    } catch (e) {
      console.error(e);
      alert('Error saving data');
    }
  };

  const requestLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setFormData({ ...formData, latitude: pos.coords.latitude, longitude: pos.coords.longitude });
        },
        (err) => {
          alert('GPS required to complete onboarding');
        }
      );
    }
  };

  return (
    <div className="onboarding-container p-8 max-w-lg mx-auto">
      <h1 className="text-2xl font-bold mb-4">Onboarding Step {step} of 10</h1>
      
      {step === 1 && <div><h2>Welcome to TravelMate</h2></div>}
      {step === 2 && <div>
        <h2>Basic Identity</h2>
        <input type="text" placeholder="Name" onChange={e => setFormData({ ...formData, name: e.target.value })} className="border p-2 w-full mb-2" />
        <input type="text" placeholder="DOB" onChange={e => setFormData({ ...formData, dob: e.target.value })} className="border p-2 w-full mb-2" />
        <input type="text" placeholder="Gender" onChange={e => setFormData({ ...formData, gender: e.target.value })} className="border p-2 w-full mb-2" />
      </div>}
      {step === 3 && <div><h2>Dating Preferences</h2>
         <input type="text" placeholder="Attraction" onChange={e => setFormData({ ...formData, attraction_preference: e.target.value })} className="border p-2 w-full mb-2" />
      </div>}
      {step === 4 && <div><h2>Discovery</h2>
         <input type="text" placeholder="Target Audience" onChange={e => setFormData({ ...formData, target_audience: e.target.value })} className="border p-2 w-full mb-2" />
      </div>}
      {step === 5 && <div><h2>Travel Intentions</h2>
         <input type="text" placeholder="Travel Style" onChange={e => setFormData({ ...formData, travel_style: e.target.value })} className="border p-2 w-full mb-2" />
      </div>}
      {step === 6 && <div><h2>Languages</h2>
         <input type="text" placeholder="Language" onChange={e => setFormData({ ...formData, language: e.target.value })} className="border p-2 w-full mb-2" />
      </div>}
      {step === 7 && <div><h2>Interests</h2>
         <input type="text" placeholder="Interest Code" onChange={e => setFormData({ ...formData, interest_code: e.target.value })} className="border p-2 w-full mb-2" />
      </div>}
      {step === 8 && <div><h2>Bio</h2>
         <textarea placeholder="About you" onChange={e => setFormData({ ...formData, bio: e.target.value })} className="border p-2 w-full mb-2" />
      </div>}
      {step === 9 && <div><h2>Photos</h2>
         <p>Mock photo upload</p>
      </div>}
      {step === 10 && <div><h2>Location & Privacy</h2>
         <button onClick={requestLocation} className="bg-blue-500 text-white p-2 rounded mb-2">Get GPS Location</button>
         {formData.latitude && <p>Location acquired: {formData.latitude}, {formData.longitude}</p>}
      </div>}

      <div className="mt-4 flex gap-4">
        {step > 1 && <button onClick={() => setStep(step - 1)} className="px-4 py-2 bg-gray-200 rounded">Back</button>}
        <button onClick={handleNext} className="px-4 py-2 bg-blue-600 text-white rounded">
          {step === 10 ? 'Complete' : 'Next'}
        </button>
      </div>
    </div>
  );
};

export default OnboardingPage;
"""

with open("apps/web/src/features/onboarding/OnboardingPage.tsx", "w") as f:
    f.write(onboarding_tsx)
