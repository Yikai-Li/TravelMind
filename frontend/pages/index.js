import { useState } from 'react';
import Head from 'next/head';
import styles from '../styles/Home.module.css';
import PlanningForm from '../components/PlanningForm';
import ItineraryView from '../components/ItineraryView';
import DestinationsList from '../components/DestinationsList';
import LoadingScreen from '../components/LoadingScreen';

export default function Home() {
  const [planData, setPlanData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingDetailLevel, setLoadingDetailLevel] = useState('medium');
  const [error, setError] = useState(null);
  const [selectedDestination, setSelectedDestination] = useState(null);
  const [userConstraints, setUserConstraints] = useState(null);
  const [rejectedDestinations, setRejectedDestinations] = useState([]);
  const [showAlternativesModal, setShowAlternativesModal] = useState(false);
  const [lastRecommendations, setLastRecommendations] = useState(null); // Store last recommendations page
  const [savedFormData, setSavedFormData] = useState(null); // Store form inputs for back navigation
  const [alternativesInput, setAlternativesInput] = useState({
    additionalNotes: '',
    budget_range: '',
    pace: '',
    travel_range: ''
  });

  const handlePlanGenerated = (data) => {
    // If this is a high_level (recommendations) result, save it
    if (data.level === 'high_level') {
      setLastRecommendations(data);
    }
    setPlanData(data);
    setError(null);
  };

  const handleError = (err) => {
    setError(err);
    setLoading(false);
  };

  const handleRefine = async (refinements) => {
    if (!planData?.plan_id) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${process.env.API_BASE_URL}/api/refine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan_id: planData.plan_id,
          refinements
        })
      });
      
      const data = await response.json();
      if (data.status === 'success') {
        setPlanData(data);
      } else {
        setError(data.error || 'Failed to refine plan');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAlternatives = () => {
    // Show modal to let user optionally adjust constraints
    setShowAlternativesModal(true);
  };

  const handleGetAlternatives = async () => {
    setShowAlternativesModal(false);
    
    setLoading(true);
    setLoadingDetailLevel('high_level');
    
    try {
      // Add current destination to rejected list
      if (planData.destination) {
        const currentDest = `${planData.destination.name}, ${planData.destination.country}`;
        setRejectedDestinations(prev => [...prev, currentDest]);
      }
      
      // Merge original constraints with any updates
      const originalConstraints = planData.parsed_constraints?.constraints || {};
      const updatedConstraints = {
        ...originalConstraints,
        rejected_destinations: [...rejectedDestinations, `${planData.destination?.name}, ${planData.destination?.country}`],
        additional_notes: alternativesInput.additionalNotes || undefined,
        specific_destination: undefined // REMOVE specific_destination to get 5 recommendations
      };
      
      // Apply any refinements
      const budgetRanges = { '$': 1500, '$$': 3500, '$$$': 6000, '$$$$': 10000 };
      if (alternativesInput.budget_range === 'custom' && alternativesInput.budget_custom) {
        updatedConstraints.budget = parseFloat(alternativesInput.budget_custom);
      } else if (alternativesInput.budget_range) {
        updatedConstraints.budget = budgetRanges[alternativesInput.budget_range];
      }
      if (alternativesInput.pace) updatedConstraints.pace = alternativesInput.pace;
      if (alternativesInput.travel_range) updatedConstraints.travel_range = alternativesInput.travel_range;
      
      // Clean up undefined
      Object.keys(updatedConstraints).forEach(key => {
        if (updatedConstraints[key] === undefined) delete updatedConstraints[key];
      });
      
      // Request new recommendations
      const response = await fetch(`${process.env.API_BASE_URL}/api/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...updatedConstraints,
          detail_level: 'high_level'
        })
      });
      
      const data = await response.json();
      if (data.status === 'success') {
        setPlanData(data);
        // Reset alternatives input
        setAlternativesInput({ additionalNotes: '', budget_range: '', pace: '', travel_range: '' });
      } else {
        setError(data.error || 'Failed to get alternatives');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const goBack = () => {
    // Smart back navigation:
    // From itinerary (medium/full) → Go to last recommendations
    // From recommendations → Go to form with saved inputs
    
    if (planData.level === 'medium' || planData.level === 'full') {
      // From itinerary back to recommendations
      if (lastRecommendations) {
        setPlanData(lastRecommendations);
      }
    } else if (planData.level === 'high_level') {
      // From recommendations back to form
      setPlanData(null);
      // Form data will be preserved in PlanningForm component
    }
  };

  const resetPlan = () => {
    setPlanData(null);
    setError(null);
  };

  return (
    <div className={styles.container}>
      <Head>
        <title>TravelMind - AI Travel Planning</title>
        <meta name="description" content="AI-powered travel planning application" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.title}>
            🌍 TravelMind
          </h1>
          <p className={styles.subtitle}>
            AI-Powered Travel Planning with Progressive Refinement
          </p>
        </div>

        {error && (
          <div className={styles.error}>
            <strong>Error:</strong> {error}
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

        {loading ? (
          <LoadingScreen detailLevel={loadingDetailLevel} />
        ) : !planData ? (
          <PlanningForm
            onPlanGenerated={handlePlanGenerated}
            onError={handleError}
            loading={loading}
            setLoading={(val) => {
              setLoading(val);
              // Store detail level for loading screen
              if (val && typeof window !== 'undefined') {
                const formDetailLevel = document.querySelector('[name="detail_level"]')?.value || 'medium';
                setLoadingDetailLevel(formDetailLevel);
              }
            }}
          />
        ) : (
          <div className={styles.results}>
            {planData.level === 'high_level' ? (
              <DestinationsList
                data={planData}
                onSelectDestination={async (dest) => {
                  setLoading(true);
                  setLoadingDetailLevel('medium');
                  try {
                    // Generate itinerary for THE SPECIFIC destination selected
                    const constraints = planData.parsed_constraints?.constraints || {};
                    const response = await fetch(`${process.env.API_BASE_URL}/api/plan`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        ...constraints,
                        specific_destination: `${dest.name}, ${dest.country}`,
                        detail_level: 'medium'
                      })
                    });
                    
                    const data = await response.json();
                    if (data.status === 'success') {
                      setPlanData(data);
                    } else {
                      setError(data.error || 'Failed to generate itinerary');
                    }
                  } catch (err) {
                    setError(err.message);
                  } finally {
                    setLoading(false);
                  }
                }}
                onRefine={handleRefine}
              />
            ) : (
              <ItineraryView
                data={planData}
                onRefine={handleRefine}
                onAlternatives={handleAlternatives}
                loading={loading}
              />
            )}
            
            <div className={styles.actions}>
              {planData && (
                <button onClick={goBack} className={styles.backButton}>
                  {planData.level === 'high_level' 
                    ? '← Back to Search Form' 
                    : '← Back to Recommendations'}
                </button>
              )}
              <button onClick={resetPlan} className={styles.secondaryButton}>
                Start New Plan
              </button>
            </div>
          </div>
        )}

        {/* Alternatives Modal */}
        {showAlternativesModal && (
          <div className={styles.modal}>
            <div className={styles.modalContent}>
              <h3>🔄 Get Alternative Destinations</h3>
              <p>We'll remember you weren't interested in <strong>{planData.destination?.name}</strong> and suggest new options.</p>
              
              {rejectedDestinations.length > 0 && (
                <div className={styles.rejectedList}>
                  <strong>Previously rejected:</strong> {rejectedDestinations.join(', ')}
                </div>
              )}
              
              <div className={styles.modalForm}>
                <div className={styles.formGroup}>
                  <label>Any additional preferences or changes?</label>
                  <textarea
                    value={alternativesInput.additionalNotes}
                    onChange={(e) => setAlternativesInput({...alternativesInput, additionalNotes: e.target.value})}
                    placeholder="e.g., 'prefer somewhere warmer', 'want more beach options', 'need cheaper alternatives'..."
                    rows="3"
                  />
                </div>
                
                <div className={styles.modalRow}>
                  <div className={styles.formGroup}>
                    <label>New Budget (optional):</label>
                    <select
                      value={alternativesInput.budget_range}
                      onChange={(e) => setAlternativesInput({...alternativesInput, budget_range: e.target.value})}
                    >
                      <option value="">Keep current</option>
                      <option value="$">$ Budget</option>
                      <option value="$$">$$ Moderate</option>
                      <option value="$$$">$$$ Comfortable</option>
                      <option value="$$$$">$$$$ Luxury</option>
                      <option value="custom">Custom Amount</option>
                    </select>
                    {alternativesInput.budget_range === 'custom' && (
                      <input
                        type="number"
                        value={alternativesInput.budget_custom || ''}
                        onChange={(e) => setAlternativesInput({...alternativesInput, budget_custom: e.target.value})}
                        placeholder="Enter amount"
                        style={{marginTop: '0.5rem'}}
                      />
                    )}
                  </div>
                  
                  <div className={styles.formGroup}>
                    <label>New Pace (optional):</label>
                    <select
                      value={alternativesInput.pace}
                      onChange={(e) => setAlternativesInput({...alternativesInput, pace: e.target.value})}
                    >
                      <option value="">Keep current</option>
                      <option value="relaxed">😌 Relaxed</option>
                      <option value="moderate">🚶 Moderate</option>
                      <option value="packed">🏃 Packed</option>
                    </select>
                  </div>
                  
                  <div className={styles.formGroup}>
                    <label>New Range (optional):</label>
                    <select
                      value={alternativesInput.travel_range}
                      onChange={(e) => setAlternativesInput({...alternativesInput, travel_range: e.target.value})}
                    >
                      <option value="">Keep current</option>
                      <option value="local">🚗 Local</option>
                      <option value="domestic">✈️ Domestic</option>
                      <option value="regional">🌎 Regional</option>
                      <option value="international">🌍 International</option>
                    </select>
                  </div>
                </div>
                
                <div className={styles.modalActions}>
                  <button onClick={handleGetAlternatives} className={styles.primaryButton}>
                    ✨ Get 5 New Destinations
                  </button>
                  <button onClick={() => setShowAlternativesModal(false)} className={styles.secondaryButton}>
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className={styles.features}>
          <div className={styles.feature}>
            <h3>🎯 Flexible Input</h3>
            <p>Start with minimal info or provide detailed constraints</p>
          </div>
          <div className={styles.feature}>
            <h3>🤖 AI Agents</h3>
            <p>Multiple specialized agents work together</p>
          </div>
          <div className={styles.feature}>
            <h3>🔄 Interactive Refinement</h3>
            <p>Adjust and regenerate plans easily</p>
          </div>
          <div className={styles.feature}>
            <h3>📊 Transparency</h3>
            <p>See reasoning and assumptions clearly</p>
          </div>
        </div>
      </main>

      <footer className={styles.footer}>
        <p>TravelMind Demo - AI-Powered Travel Planning</p>
      </footer>
    </div>
  );
}
