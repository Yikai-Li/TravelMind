import { useState } from 'react';
import styles from '../styles/PlanningForm.module.css';

export default function PlanningForm({ onPlanGenerated, onError, loading, setLoading }) {
  const [planMode, setPlanMode] = useState('discover'); // 'discover' or 'custom'
  const [userLocation, setUserLocation] = useState(null); // Store GPS location
  const [locationDetected, setLocationDetected] = useState(false);
  const [formData, setFormData] = useState({
    start_date: '',
    end_date: '',
    departure_city: '',
    budget_range: '',
    budget_custom: '',
    travel_style: 'cultural',
    interests: '',
    pace: 'moderate',
    group_type: 'solo',
    detail_level: 'high_level',
    // Custom mode fields
    specific_destination: '',
    existing_plan: '',
    plan_action: 'enhance'
  });

  // Function to get user's location
  const requestLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation({ lat: latitude, lon: longitude });
          
          // Reverse geocode to get city name
          try {
            const response = await fetch(
              `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`
            );
            const data = await response.json();
            const city = data.address.city || data.address.town || data.address.village || data.address.county;
            const state = data.address.state;
            const cityName = state ? `${city}, ${state}` : city;
            
            setFormData(prev => ({ ...prev, departure_city: cityName }));
            setLocationDetected(true);
          } catch (error) {
            console.error('Geocoding error:', error);
          }
        },
        (error) => {
          onError('Location access denied or unavailable');
        }
      );
    } else {
      onError('Geolocation is not supported by your browser');
    }
  };

  const budgetRanges = {
    '$': { label: '$ Budget', value: 1500, description: 'Up to $1,500' },
    '$$': { label: '$$ Moderate', value: 3500, description: '$1,500 - $3,500' },
    '$$$': { label: '$$$ Comfortable', value: 6000, description: '$3,500 - $6,000' },
    '$$$$': { label: '$$$$ Luxury', value: 10000, description: '$6,000+' }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      let budget = formData.budget_custom ? parseFloat(formData.budget_custom) : 
                   formData.budget_range ? budgetRanges[formData.budget_range].value : undefined;

      let dates = '';
      if (formData.start_date && formData.end_date) {
        dates = `${formData.start_date} to ${formData.end_date}`;
      }

      const submitData = {
        dates: dates || undefined,
        departure_city: formData.departure_city || undefined,
        budget: budget,
        travel_style: formData.travel_style,
        travel_range: formData.travel_range || undefined,
        interests: formData.interests ? formData.interests.split(',').map(i => i.trim()) : [],
        pace: formData.pace,
        group_type: formData.group_type,
        detail_level: formData.detail_level
      };

      // Add custom mode specific fields
      if (planMode === 'custom') {
        submitData.specific_destination = formData.specific_destination;
        submitData.existing_plan = formData.existing_plan;
        submitData.plan_action = formData.plan_action;
      }

      // Remove undefined fields
      Object.keys(submitData).forEach(key => {
        if (submitData[key] === undefined || submitData[key] === '') {
          delete submitData[key];
        }
      });

      const response = await fetch(`${process.env.API_BASE_URL}/api/plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData),
      });

      const data = await response.json();

      if (data.status === 'success') {
        onPlanGenerated(data);
      } else {
        onError(data.error || 'Failed to generate plan');
      }
    } catch (error) {
      onError(error.message || 'Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      {/* Mode Toggle */}
      <div className={styles.modeToggle}>
        <button
          type="button"
          className={planMode === 'discover' ? styles.modeActive : styles.modeInactive}
          onClick={() => setPlanMode('discover')}
        >
          🔍 Discover Destinations
        </button>
        <button
          type="button"
          className={planMode === 'custom' ? styles.modeActive : styles.modeInactive}
          onClick={() => setPlanMode('custom')}
        >
          📝 I Have a Plan
        </button>
      </div>

      <div className={styles.compactSection}>
        <h2>{planMode === 'discover' ? 'Plan Your Trip' : 'Enhance Your Plan'}</h2>
        
        {planMode === 'discover' ? (
          <>
            {/* Original Discover Mode */}
            <div className={styles.row}>
              <div className={styles.formGroup}>
                <label>Travel Dates</label>
                <div className={styles.dateInputs}>
                  <input
                    type="date"
                    name="start_date"
                    value={formData.start_date}
                    onChange={handleChange}
                    placeholder="Start"
                  />
                  <span className={styles.dateSeparator}>to</span>
                  <input
                    type="date"
                    name="end_date"
                    value={formData.end_date}
                    onChange={handleChange}
                    placeholder="End"
                  />
                </div>
              </div>

              <div className={styles.formGroup}>
                <label>Budget</label>
                <div className={styles.budgetSelector}>
                  <select
                    name="budget_range"
                    value={formData.budget_range}
                    onChange={handleChange}
                  >
                    <option value="">Select Range</option>
                    {Object.entries(budgetRanges).map(([key, val]) => (
                      <option key={key} value={key}>{val.label}</option>
                    ))}
                    <option value="custom">Custom Amount</option>
                  </select>
                  {(formData.budget_range === 'custom' || formData.budget_custom) && (
                    <input
                      type="number"
                      name="budget_custom"
                      value={formData.budget_custom}
                      onChange={handleChange}
                      placeholder="Enter amount"
                      min="0"
                      className={styles.customBudget}
                    />
                  )}
                </div>
              </div>
            </div>

            <div className={styles.row}>
              <div className={styles.formGroup}>
                <label>Travel Style</label>
                <select name="travel_style" value={formData.travel_style} onChange={handleChange}>
                  <option value="adventure">🏔️ Adventure</option>
                  <option value="relaxation">🏖️ Relaxation</option>
                  <option value="cultural">🎭 Cultural</option>
                  <option value="romantic">❤️ Romantic</option>
                  <option value="foodie">🍜 Foodie</option>
                  <option value="nature">🌲 Nature & Wildlife</option>
                  <option value="urban">🏙️ Urban Explorer</option>
                  <option value="wellness">🧘 Wellness & Spa</option>
                </select>
              </div>

              <div className={styles.formGroup}>
                <label>Travel Range</label>
                <select name="travel_range" value={formData.travel_range || ''} onChange={handleChange}>
                  <option value="">Any Distance</option>
                  <option value="local">🚗 Local (Same Region)</option>
                  <option value="domestic">✈️ Domestic</option>
                  <option value="regional">🌎 Regional (Nearby Countries)</option>
                  <option value="international">🌍 International</option>
                </select>
              </div>

              <div className={styles.formGroup}>
                <label>Pace</label>
                <select name="pace" value={formData.pace} onChange={handleChange}>
                  <option value="relaxed">😌 Relaxed</option>
                  <option value="moderate">🚶 Moderate</option>
                  <option value="packed">🏃 Packed</option>
                </select>
              </div>

              <div className={styles.formGroup}>
                <label>Group</label>
                <select name="group_type" value={formData.group_type} onChange={handleChange}>
                  <option value="solo">Solo</option>
                  <option value="couple">Couple</option>
                  <option value="family">Family</option>
                  <option value="friends">Friends</option>
                </select>
              </div>
            </div>

            <div className={styles.row}>
              <div className={styles.formGroup}>
                <label>From</label>
                <div className={styles.locationInput}>
                  <input
                    type="text"
                    name="departure_city"
                    value={formData.departure_city}
                    onChange={handleChange}
                    placeholder="Departure city"
                  />
                  <button
                    type="button"
                    onClick={requestLocation}
                    className={styles.locationButton}
                    title="Use my current location"
                  >
                    {locationDetected ? '✓ 📍' : '📍'}
                  </button>
                </div>
                {locationDetected && (
                  <small className={styles.locationHint}>✓ Location detected</small>
                )}
              </div>

              <div className={styles.formGroup} style={{flex: 2}}>
                <label>Interests</label>
                <input
                  type="text"
                  name="interests"
                  value={formData.interests}
                  onChange={handleChange}
                  placeholder="hiking, food, museums, beaches..."
                />
              </div>
            </div>

            <div className={styles.row}>
              <div className={styles.formGroup} style={{flex: 1}}>
                <label>Detail Level</label>
                <select name="detail_level" value={formData.detail_level} onChange={handleChange}>
                  <option value="high_level">⚡ Quick - Destination Ideas (~20s)</option>
                  <option value="medium">📋 Medium - Daily Outline (~60s)</option>
                  <option value="full">📖 Detailed - Full Itinerary (~90s)</option>
                </select>
              </div>
            </div>
          </>
        ) : (
          <>
            {/* Custom Plan Mode */}
            <div className={styles.row}>
              <div className={styles.formGroup}>
                <label>Destination *</label>
                <input
                  type="text"
                  name="specific_destination"
                  value={formData.specific_destination}
                  onChange={handleChange}
                  placeholder="e.g., Paris, France"
                  required
                />
              </div>

              <div className={styles.formGroup}>
                <label>Travel Dates</label>
                <div className={styles.dateInputs}>
                  <input
                    type="date"
                    name="start_date"
                    value={formData.start_date}
                    onChange={handleChange}
                  />
                  <span className={styles.dateSeparator}>to</span>
                  <input
                    type="date"
                    name="end_date"
                    value={formData.end_date}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </div>

            <div className={styles.row}>
              <div className={styles.formGroup} style={{flex: 1}}>
                <label>Your Existing Plan / Outline</label>
                <textarea
                  name="existing_plan"
                  value={formData.existing_plan}
                  onChange={handleChange}
                  placeholder="Paste your existing itinerary, outline, or rough ideas here...&#10;&#10;Example:&#10;Day 1: Arrive, check in hotel&#10;Day 2: Visit Eiffel Tower&#10;Day 3: Louvre Museum&#10;..."
                  rows="8"
                  className={styles.planTextarea}
                />
              </div>
            </div>

            <div className={styles.row}>
              <div className={styles.formGroup}>
                <label>What would you like us to do?</label>
                <select name="plan_action" value={formData.plan_action} onChange={handleChange}>
                  <option value="enhance">✨ Enhance with details (timing, costs, tips)</option>
                  <option value="modify">🔧 Modify and improve</option>
                  <option value="fill_gaps">📝 Fill in the gaps</option>
                  <option value="optimize">⚡ Optimize routing and timing</option>
                </select>
              </div>

              <div className={styles.formGroup}>
                <label>Pace</label>
                <select name="pace" value={formData.pace} onChange={handleChange}>
                  <option value="relaxed">😌 Relaxed</option>
                  <option value="moderate">🚶 Moderate</option>
                  <option value="packed">🏃 Packed</option>
                </select>
              </div>
            </div>
          </>
        )}
      </div>

      <button type="submit" className={styles.submitButton} disabled={loading}>
        {loading ? '✨ Processing...' : planMode === 'discover' ? '✨ Generate Travel Plan' : '✨ Enhance My Plan'}
      </button>

      <p className={styles.hint}>
        💡 {planMode === 'discover' 
          ? 'All fields are optional - provide as much or as little as you want!' 
          : 'Paste your rough plans and we\'ll enhance them with AI-powered details!'}
      </p>
    </form>
  );
}
