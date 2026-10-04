import React, { useState, useEffect } from 'react';
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
