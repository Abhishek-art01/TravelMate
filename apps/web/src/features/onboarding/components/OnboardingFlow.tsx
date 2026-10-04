import React, { useState } from 'react';

const OnboardingFlow = () => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    dob: '',
    gender: '',
  });

  const nextStep = () => setStep(step + 1);
  const prevStep = () => setStep(step - 1);

  const handleSubmit = async () => {
    // Submit to our new onboarding API
    try {
      await fetch('/api/v1/onboarding/step/basic-info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      alert('Onboarding completed successfully!');
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="onboarding-container p-6 max-w-lg mx-auto bg-white rounded-xl shadow-md">
      <h1 className="text-2xl font-bold mb-4">TravelMate Onboarding</h1>
      <div className="step-indicator mb-6">
        Step {step} of 2
      </div>
      
      {step === 1 && (
        <div className="step-1 space-y-4">
          <input
            className="w-full p-2 border rounded"
            placeholder="Name"
            value={formData.name}
            onChange={e => setFormData({...formData, name: e.target.value})}
          />
          <input
            className="w-full p-2 border rounded"
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={e => setFormData({...formData, email: e.target.value})}
          />
          <button className="bg-blue-500 text-white p-2 rounded" onClick={nextStep}>Next</button>
        </div>
      )}

      {step === 2 && (
        <div className="step-2 space-y-4">
          <input
            className="w-full p-2 border rounded"
            type="date"
            placeholder="Date of Birth"
            value={formData.dob}
            onChange={e => setFormData({...formData, dob: e.target.value})}
          />
          <select 
            className="w-full p-2 border rounded"
            value={formData.gender}
            onChange={e => setFormData({...formData, gender: e.target.value})}
          >
            <option value="">Select Gender</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="non-binary">Non-binary</option>
            <option value="other">Other</option>
          </select>
          <div className="flex gap-4">
            <button className="bg-gray-300 p-2 rounded" onClick={prevStep}>Back</button>
            <button className="bg-blue-500 text-white p-2 rounded" onClick={handleSubmit}>Complete</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default OnboardingFlow;
