import { useState } from 'react';
import styles from '../styles/ItineraryView.module.css';

export default function ItineraryView({ data, onRefine, onAlternatives, loading }) {
  const [showRefineForm, setShowRefineForm] = useState(false);
  const [refinements, setRefinements] = useState({});
  const [enrichedActivities, setEnrichedActivities] = useState({}); // Hash table: "day_activity" -> enriched data
  const [expandedActivities, setExpandedActivities] = useState({}); // Track which activities are expanded
  const [loadingActivities, setLoadingActivities] = useState({}); // Track which activities are being enriched
  const [isEnriching, setIsEnriching] = useState(false);
  const [showDateModal, setShowDateModal] = useState(false);
  const [calendarDates, setCalendarDates] = useState({ start: '', end: '' });
  const [transportationTo, setTransportationTo] = useState(null);
  const [transportationBack, setTransportationBack] = useState(null);

  const enrichSingleActivity = async (dayIdx, actIdx, activity) => {
    const key = `${dayIdx}_${actIdx}`;
    
    // Check if already enriched
    if (enrichedActivities[key]) {
      setExpandedActivities(prev => ({ ...prev, [key]: !prev[key] }));
      return;
    }
    
    // Mark as loading
    setLoadingActivities(prev => ({ ...prev, [key]: true }));
    setExpandedActivities(prev => ({ ...prev, [key]: true }));
    
    try {
      const response = await fetch(`${process.env.API_BASE_URL}/api/enrich-single-activity`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          activity,
          destination: data.destination?.name,
          day_number: data.itinerary[dayIdx].day_number || data.itinerary[dayIdx].day || (dayIdx + 1)
        })
      });
      
      const enriched = await response.json();
      
      console.log('Enrichment response:', enriched);
      
      if (enriched.status === 'success' && enriched.data) {
        setEnrichedActivities(prev => ({ ...prev, [key]: enriched.data }));
      } else {
        console.error('No data in enrichment response:', enriched);
        setEnrichedActivities(prev => ({ ...prev, [key]: { 
          description: 'Enrichment data not available for this activity',
          tips: ['Please try enriching again or contact support']
        }}));
      }
    } catch (err) {
      console.error('Enrichment error:', err);
    } finally {
      setLoadingActivities(prev => ({ ...prev, [key]: false }));
    }
  };

  const handleProgressiveEnrichment = async () => {
    setIsEnriching(true);
    
    try {
      const eventSource = new EventSource(
        `${process.env.API_BASE_URL}/api/enrich-progressive?plan_id=${data.plan_id}`,
        { withCredentials: false }
      );
      
      eventSource.onmessage = (event) => {
        const update = JSON.parse(event.data);
        
        if (update.status === 'activity_enriched') {
          // Check if this is transportation data
          if (update.type === 'transport_to') {
            setTransportationTo(update.data);
          } else if (update.type === 'transport_back') {
            setTransportationBack(update.data);
          } else {
            // Regular activity enrichment
            const key = `${update.day}_${update.activity}`;
            setEnrichedActivities(prev => ({ ...prev, [key]: update.data }));
            setExpandedActivities(prev => ({ ...prev, [key]: true }));
          }
        } else if (update.status === 'complete') {
          eventSource.close();
          setIsEnriching(false);
        } else if (update.error) {
          eventSource.close();
          setIsEnriching(false);
          alert('Enrichment error: ' + update.error);
        }
      };
      
      eventSource.onerror = () => {
        eventSource.close();
        setIsEnriching(false);
        alert('Connection error during enrichment');
      };
      
    } catch (err) {
      setIsEnriching(false);
      alert('Error: ' + err.message);
    }
  };

  const exportToCalendar = () => {
    const dates = data.parsed_constraints?.constraints?.dates;
    if (!dates || !dates.includes(' to ')) {
      setShowDateModal(true);
      return;
    }

    performCalendarExport(dates);
  };

  const handleDateModalSubmit = () => {
    if (!calendarDates.start || !calendarDates.end) {
      alert('Please provide both start and end dates');
      return;
    }

    const dates = `${calendarDates.start} to ${calendarDates.end}`;
    
    // Save dates to plan data
    data.parsed_constraints.constraints.dates = dates;
    
    setShowDateModal(false);
    performCalendarExport(dates);
  };

  const performCalendarExport = (dates) => {
    const [startDate] = dates.split(' to ');
    let icsContent = 'BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//TravelMind//Travel Itinerary//EN\n';

    data.itinerary.forEach((day, idx) => {
      const dayDate = new Date(startDate);
      dayDate.setDate(dayDate.getDate() + idx);
      const dateStr = dayDate.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';

      day.activities.forEach(activity => {
        icsContent += `BEGIN:VEVENT\n`;
        icsContent += `DTSTART:${dateStr}\n`;
        icsContent += `SUMMARY:${activity.name}\n`;
        icsContent += `DESCRIPTION:${activity.description || ''}\n`;
        icsContent += `LOCATION:${data.destination?.name}\n`;
        icsContent += `END:VEVENT\n`;
      });
    });

    icsContent += 'END:VCALENDAR';

    const blob = new Blob([icsContent], { type: 'text/calendar' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${data.destination?.name}-itinerary.ics`;
    a.click();
  };

  const exportToTextFile = () => {
    let content = `${data.destination?.name}, ${data.destination?.country}\n\n`;
    content += `${data.overview || ''}\n\n`;

    data.itinerary.forEach((day, dayIdx) => {
      content += `DAY ${day.day_number}: ${day.title}\n`;
      content += `Theme: ${day.theme}\n\n`;

      // Add transportation to destination for first day
      if (dayIdx === 0 && transportationTo) {
        content += `✈️ ${transportationTo.name}\n`;
        content += `${transportationTo.description}\n\n`;
        if (transportationTo.options && transportationTo.options.length > 0) {
          content += `Transportation Options:\n`;
          transportationTo.options.forEach(opt => {
            content += `  ${opt.mode}: ${opt.details}\n`;
            if (opt.duration) content += `    Duration: ${opt.duration}\n`;
            if (opt.cost_range) content += `    Cost: ${opt.cost_range}\n`;
          });
          content += `\n`;
        }
        if (transportationTo.recommended_option) {
          content += `Recommended: ${transportationTo.recommended_option}\n\n`;
        }
        if (transportationTo.tips && transportationTo.tips.length > 0) {
          content += `Tips:\n`;
          transportationTo.tips.forEach(tip => content += `  - ${tip}\n`);
          content += `\n`;
        }
      }

      day.activities.forEach((activity, actIdx) => {
        const key = `${dayIdx}_${actIdx}`;
        const enriched = enrichedActivities[key]?.activity || enrichedActivities[key];

        content += `  • ${activity.name}\n`;
        if (activity.time_slot) content += `    Time: ${activity.time_slot}\n`;
        if (activity.description) content += `    ${activity.description}\n`;
        
        if (enriched) {
          if (enriched.description) content += `    Details: ${enriched.description}\n`;
          if (enriched.tips) enriched.tips.forEach(tip => content += `    - ${tip}\n`);
        }
        content += `\n`;
      });

      // Add return transportation for last day
      if (dayIdx === data.itinerary.length - 1 && transportationBack) {
        content += `🏠 ${transportationBack.name}\n`;
        content += `${transportationBack.description}\n\n`;
        if (transportationBack.options && transportationBack.options.length > 0) {
          content += `Transportation Options:\n`;
          transportationBack.options.forEach(opt => {
            content += `  ${opt.mode}: ${opt.details}\n`;
            if (opt.duration) content += `    Duration: ${opt.duration}\n`;
            if (opt.cost_range) content += `    Cost: ${opt.cost_range}\n`;
          });
          content += `\n`;
        }
        if (transportationBack.recommended_option) {
          content += `Recommended: ${transportationBack.recommended_option}\n\n`;
        }
        if (transportationBack.tips && transportationBack.tips.length > 0) {
          content += `Tips:\n`;
          transportationBack.tips.forEach(tip => content += `  - ${tip}\n`);
          content += `\n`;
        }
      }

      content += `\n`;
    });

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${data.destination?.name}-itinerary.txt`;
    a.click();
  };

  const handleRefineSubmit = (e) => {
    e.preventDefault();
    onRefine(refinements);
    setShowRefineForm(false);
    setRefinements({});
  };

  return (
    <div className={styles.container}>
      {/* Destination Header */}
      <div className={styles.header}>
        <div className={styles.destinationInfo}>
          <h2 className={styles.destinationName}>
            📍 {data.destination?.name}, {data.destination?.country}
          </h2>
          <div className={styles.score}>
            Match Score: <strong>{data.destination?.score}/100</strong>
          </div>
        </div>
        
        <div className={styles.reasoning}>
          <p>{data.destination?.reasoning}</p>
        </div>

        {data.destination?.highlights && (
          <div className={styles.highlights}>
            <h4>🌟 Highlights</h4>
            <ul>
              {data.destination.highlights.map((h, i) => (
                <li key={i}>{h}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Warnings and Assumptions */}
      {(data.warnings?.length > 0 || data.assumptions?.length > 0) && (
        <div className={styles.notices}>
          {data.warnings?.length > 0 && (
            <div className={styles.warnings}>
              <h4>⚠️ Warnings</h4>
              <ul>
                {data.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
          
          {data.assumptions?.length > 0 && (
            <div className={styles.assumptions}>
              <h4>💭 Assumptions</h4>
              <ul>
                {data.assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Enhanced Plan Summary - Show if this is an enhanced plan */}
      {data.mode === 'plan_enhancement' && (
        <div className={styles.enhancedSummary}>
          <div className={styles.enhancementBadge}>
            ✨ Enhanced Plan
            {data.action_performed && (
              <span className={styles.actionBadge}>
                {data.action_performed === 'enhance' && '💎 Details Added'}
                {data.action_performed === 'modify' && '🔧 Modified'}
                {data.action_performed === 'fill_gaps' && '📝 Gaps Filled'}
                {data.action_performed === 'optimize' && '⚡ Optimized'}
              </span>
            )}
          </div>
          
          {data.enhancements_summary && (
            <div className={styles.enhancementDetails}>
              <strong>What We Enhanced:</strong>
              <p>{data.enhancements_summary}</p>
            </div>
          )}
          
          {data.total_estimated_cost && (
            <div className={styles.totalCost}>
              <strong>Total Estimated Cost:</strong> ${data.total_estimated_cost}
            </div>
          )}
          
          {data.practical_tips && data.practical_tips.length > 0 && (
            <div className={styles.practicalTips}>
              <strong>💡 Practical Tips:</strong>
              <ul>
                {data.practical_tips.map((tip, i) => (
                  <li key={i}>{tip}</li>
                ))}
              </ul>
            </div>
          )}
          
          {data.original_plan && (
            <details className={styles.originalPlan}>
              <summary>📋 View Your Original Plan</summary>
              <pre>{data.original_plan}</pre>
            </details>
          )}
        </div>
      )}

      {/* Hotel Recommendations - Show if available */}
      {data.hotel_recommendations && data.hotel_recommendations.length > 0 && (
        <div className={styles.hotelRecommendations}>
          <h3>🏨 Recommended Hotels</h3>
          <div className={styles.hotelGrid}>
            {data.hotel_recommendations.map((hotel, idx) => (
              <div key={idx} className={styles.hotelCard}>
                <div className={styles.hotelHeader}>
                  <h4>{hotel.name}</h4>
                  <span className={`${styles.hotelCategory} ${styles[hotel.category?.toLowerCase().replace(/[\s-]/g, '')]}`}>
                    {hotel.category}
                  </span>
                </div>
                <div className={styles.hotelDetails}>
                  <div className={styles.hotelPrice}>💰 {hotel.price_range}</div>
                  <div className={styles.hotelLocation}>📍 {hotel.location}</div>
                  <p className={styles.hotelDescription}>{hotel.description}</p>
                  {hotel.best_for && (
                    <div className={styles.hotelBestFor}>
                      <strong>Best for:</strong> {hotel.best_for}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Itinerary Overview */}
      {data.overview && (
        <div className={styles.overview}>
          <h3>Overview</h3>
          <p>{data.overview}</p>
          {data.pacing_notes && <p><em>{data.pacing_notes}</em></p>}
        </div>
      )}

      {/* Daily Itinerary */}
      <div className={styles.itinerary}>
        <h3>📅 Day-by-Day Itinerary</h3>
        {data.itinerary?.map((day, idx) => (
          <div key={idx} className={styles.day}>
            <div className={styles.dayHeader}>
              <h4>
                Day {day.day_number}: {day.title}
              </h4>
              <span className={styles.theme}>{day.theme}</span>
            </div>

            <div className={styles.activities}>
              {/* Transportation TO destination - show before first day's activities */}
              {idx === 0 && transportationTo && (
                <div className={styles.transportSubtitle}>
                  <h4>✈️ {transportationTo.name}</h4>
                  <p>{transportationTo.description}</p>
                  {transportationTo.options && transportationTo.options.length > 0 && (
                    <div>
                      <strong>Transportation Options:</strong>
                      {transportationTo.options.map((opt, i) => (
                        <div key={i} style={{marginLeft: '1rem', marginTop: '0.5rem'}}>
                          <strong>{opt.mode}:</strong> {opt.details}
                          {opt.duration && <div>• Duration: {opt.duration}</div>}
                          {opt.cost_range && <div>• Cost: {opt.cost_range}</div>}
                        </div>
                      ))}
                    </div>
                  )}
                  {transportationTo.recommended_option && (
                    <div style={{marginTop: '0.5rem'}}>
                      <strong>💡 Recommended:</strong> {transportationTo.recommended_option}
                    </div>
                  )}
                  {transportationTo.tips && transportationTo.tips.length > 0 && (
                    <div style={{marginTop: '0.5rem'}}>
                      <strong>Tips:</strong>
                      <ul>
                        {transportationTo.tips.map((tip, i) => <li key={i}>{tip}</li>)}
                      </ul>
                    </div>
                  )}
                  {transportationTo.sources && transportationTo.sources.length > 0 && (
                    <div style={{marginTop: '0.5rem'}}>
                      <strong>🔗 Booking Links:</strong>
                      {transportationTo.sources.map((src, i) => (
                        <div key={i}>
                          <a href={src} target="_blank" rel="noopener noreferrer">{src}</a>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {day.activities?.map((activity, actIdx) => {
                const key = `${idx}_${actIdx}`;
                const enriched = enrichedActivities[key];
                const isExpanded = expandedActivities[key];
                const isLoading = loadingActivities[key];
                
                return (
                  <div key={actIdx} className={`${styles.activity} ${isEnriching && !enrichedActivities[key] ? styles.activityEnriching : ''}`}>
                    {isEnriching && !enrichedActivities[key] && (
                      <div className={styles.enrichingIndicator}>⏳</div>
                    )}
                    {enrichedActivities[key] && <div className={styles.enrichedIndicator}>✓</div>}
                    
                    <div className={styles.activityHeaderRow}>
                      <div>
                        <h5>{activity.name}</h5>
                        {activity.description && (
                          <p className={styles.description}>{activity.description}</p>
                        )}
                        <div className={styles.activityDetails}>
                          {activity.type && (
                            <span className={styles.badge}>{activity.type}</span>
                          )}
                          {activity.cost_estimate && (
                            <span className={styles.cost}>💰 ${activity.cost_estimate}</span>
                          )}
                          {activity.booking_info && (
                            <span className={styles.booking}>{activity.booking_info}</span>
                          )}
                        </div>
                      </div>
                      <div className={styles.activityRight}>
                        <div className={styles.activityMeta}>
                          {activity.time_slot && (
                            <span className={styles.time}>🕒 {activity.time_slot}</span>
                          )}
                          {activity.duration && (
                            <span className={styles.duration}>⏱️ {activity.duration}</span>
                          )}
                          {activity.priority && (
                            <span className={`${styles.priority} ${styles[activity.priority]}`}>
                              {activity.priority}
                            </span>
                          )}
                        </div>
                        {/* Only show Details button for non-enhanced plans that need enrichment */}
                        {data.mode !== 'plan_enhancement' && (
                          <button
                            onClick={() => enrichSingleActivity(idx, actIdx, activity)}
                            className={styles.expandButton}
                            disabled={isLoading}
                          >
                            {isLoading ? '⏳' : isExpanded ? '▼ Hide' : '▶ Details'}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className={styles.enrichedDetails}>
                        {isLoading ? (
                          <div>⏳ Loading details...</div>
                        ) : enriched ? (
                          <>
                            {/* Handle nested structure - enriched.activity or direct enriched */}
                            {(() => {
                              const actData = enriched.activity || enriched;
                              
                              return (
                                <>
                                  {actData.description && (
                                    <div className={styles.enrichDescription}>
                                      <strong>📖 About:</strong>
                                      <ul className={styles.descriptionList}>
                                        {typeof actData.description === 'string' 
                                          ? actData.description.split('.').filter(s => s.trim()).map((sentence, i) => (
                                              <li key={i}>{sentence.trim()}.</li>
                                            ))
                                          : <li>{actData.description}</li>
                                        }
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {/* Costs - Only show if has actual data */}
                                  {actData.costs && actData.costs.average_meal_price && actData.costs.average_meal_price.low_end && (
                                    <div className={styles.costDetails}>
                                      <strong>💵 Costs:</strong>
                                      <div>• Per person: ${actData.costs.average_meal_price.low_end} - ${actData.costs.average_meal_price.high_end}</div>
                                      {actData.costs.additional_costs?.beverages && (
                                        <div>• {actData.costs.additional_costs.beverages}</div>
                                      )}
                                    </div>
                                  )}
                                  
                                  {/* Timing - Only show if has values */}
                                  {actData.specific_timing?.dinner_hours?.start && actData.specific_timing?.dinner_hours?.end && (
                                    <div className={styles.timing}>
                                      <strong>🕐 Hours:</strong> {actData.specific_timing.dinner_hours.start} - {actData.specific_timing.dinner_hours.end}
                                    </div>
                                  )}
                                  
                                  {/* Transport */}
                                  {actData.transport && actData.transport.options && (
                                    <div className={styles.transport}>
                                      <strong>🚗 How to Get There:</strong>
                                      {actData.transport.options.map((opt, i) => (
                                        <div key={i}>• {opt.type}: {opt.details}</div>
                                      ))}
                                    </div>
                                  )}
                                  
                                  {/* Hotel Examples - Show for accommodation activities */}
                                  {actData.hotel_examples && actData.hotel_examples.length > 0 && (
                                    <div className={styles.restaurantOptions} style={{background: '#f0f9ff', borderLeftColor: '#3b82f6'}}>
                                      <strong style={{color: '#1e40af'}}>🏨 Hotel Recommendations:</strong>
                                      <div className={styles.restaurantGrid}>
                                        {actData.hotel_examples.map((hotel, hIdx) => (
                                          <div key={hIdx} className={styles.restaurantCard} style={{borderColor: '#60a5fa'}}>
                                            <div className={styles.restaurantName} style={{color: '#1e40af'}}>{hotel.name}</div>
                                            <div className={styles.restaurantDetails}>
                                              <span className={styles.cuisine} style={{background: '#fef3c7', color: '#92400e'}}>{hotel.category}</span>
                                              <span className={styles.priceRange}>{hotel.price_per_night}</span>
                                            </div>
                                            {hotel.location && (
                                              <div className={styles.specialties} style={{color: '#1e40af'}}>📍 {hotel.location}</div>
                                            )}
                                            {hotel.amenities && (
                                              <div className={styles.specialties} style={{color: '#0c4a6e', fontStyle: 'normal'}}>✨ {hotel.amenities}</div>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                  
                                  {/* Restaurant Options - Show for dining activities */}
                                  {actData.restaurant_options && actData.restaurant_options.length > 0 && (
                                    <div className={styles.restaurantOptions}>
                                      <strong>🍽️ Restaurant Recommendations:</strong>
                                      <div className={styles.restaurantGrid}>
                                        {actData.restaurant_options.map((restaurant, rIdx) => (
                                          <div key={rIdx} className={styles.restaurantCard}>
                                            <div className={styles.restaurantName}>{restaurant.name}</div>
                                            <div className={styles.restaurantDetails}>
                                              <span className={styles.cuisine}>{restaurant.cuisine}</span>
                                              <span className={styles.priceRange}>{restaurant.price_range}</span>
                                            </div>
                                            {restaurant.specialties && (
                                              <div className={styles.specialties}>{restaurant.specialties}</div>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                  
                                  {/* Tips */}
                                  {actData.tips && actData.tips.length > 0 && (
                                    <div className={styles.enrichTips}>
                                      <strong>💡 Insider Tips:</strong>
                                      <ul>
                                        {actData.tips.map((tip, i) => <li key={i}>{tip}</li>)}
                                      </ul>
                                    </div>
                                  )}
                                  
                                  {/* Official Links - Now validated by backend */}
                                  {(() => {
                                    const links = Array.isArray(actData.official_links) ? actData.official_links : [];
                                    return links.length > 0 ? (
                                      <div className={styles.sources}>
                                        <strong>🔗 Official Links:</strong>
                                        {links.map((link, i) => {
                                          const url = typeof link === 'string' ? link : (link.url || link.link || '');
                                          const name = typeof link === 'string' ? url : (link.name || url);
                                          return (
                                            <div key={i}>
                                              <a href={url} target="_blank" rel="noopener noreferrer">{name}</a>
                                            </div>
                                          );
                                        })}
                                      </div>
                                    ) : null;
                                  })()}
                                  
                                  {/* Sources - Now validated by backend */}
                                  {(() => {
                                    const sources = Array.isArray(actData.sources) ? actData.sources : [];
                                    return sources.length > 0 ? (
                                      <div className={styles.sources}>
                                        <strong>📚 Sources:</strong>
                                        {sources.map((src, i) => {
                                          const url = typeof src === 'string' ? src : (src.url || src.link || '');
                                          const title = typeof src === 'string' ? url : (src.title || url);
                                          return (
                                            <div key={i}>
                                              <a href={url} target="_blank" rel="noopener noreferrer">{title}</a>
                                            </div>
                                          );
                                        })}
                                      </div>
                                    ) : null;
                                  })()}
                                </>
                              );
                            })()}
                          </>
                        ) : (
                          <div>No enriched data available</div>
                        )}
                      </div>
                    )}

                    {/* Show resort examples directly for enhanced plans - for accommodation activities */}
                    {data.mode === 'plan_enhancement' && activity.resort_examples && activity.resort_examples.length > 0 && (
                      <div className={styles.resortOptions}>
                        <strong>🏨 Luxury Resort Examples:</strong>
                        <div className={styles.resortGrid}>
                          {activity.resort_examples.map((resort, rIdx) => (
                            <div key={rIdx} className={styles.resortCard}>
                              <div className={styles.resortName}>{resort.name}</div>
                              <div className={styles.resortDetails}>
                                <span className={styles.resortCategory}>{resort.category}</span>
                                <span className={styles.resortPrice}>{resort.price_per_night}</span>
                              </div>
                              {resort.amenities && (
                                <div className={styles.resortAmenities}>✨ {resort.amenities}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Show restaurant options directly for enhanced plans */}
                    {data.mode === 'plan_enhancement' && activity.restaurant_options && activity.restaurant_options.length > 0 && (
                      <div className={styles.restaurantOptions}>
                        <strong>🍽️ Restaurant Recommendations:</strong>
                        <div className={styles.restaurantGrid}>
                          {activity.restaurant_options.map((restaurant, rIdx) => (
                            <div key={rIdx} className={styles.restaurantCard}>
                              <div className={styles.restaurantName}>{restaurant.name}</div>
                              <div className={styles.restaurantDetails}>
                                <span className={styles.cuisine}>{restaurant.cuisine}</span>
                                <span className={styles.priceRange}>{restaurant.price_range}</span>
                              </div>
                              {restaurant.specialties && (
                                <div className={styles.specialties}>{restaurant.specialties}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {activity.tips && (
                      <div className={styles.tips}>
                        <strong>💡 Tips:</strong>
                        {Array.isArray(activity.tips) ? (
                          <ul>
                            {activity.tips.map((tip, tipIdx) => (
                              <li key={tipIdx}>{tip}</li>
                            ))}
                          </ul>
                        ) : (
                          <p>{activity.tips}</p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Transportation BACK home - show after last day's activities */}
              {idx === data.itinerary.length - 1 && transportationBack && (
                <div className={styles.transportSubtitle}>
                  <h4>🏠 {transportationBack.name}</h4>
                  <p>{transportationBack.description}</p>
                  {transportationBack.options && transportationBack.options.length > 0 && (
                    <div>
                      <strong>Transportation Options:</strong>
                      {transportationBack.options.map((opt, i) => (
                        <div key={i} style={{marginLeft: '1rem', marginTop: '0.5rem'}}>
                          <strong>{opt.mode}:</strong> {opt.details}
                          {opt.duration && <div>• Duration: {opt.duration}</div>}
                          {opt.cost_range && <div>• Cost: {opt.cost_range}</div>}
                        </div>
                      ))}
                    </div>
                  )}
                  {transportationBack.recommended_option && (
                    <div style={{marginTop: '0.5rem'}}>
                      <strong>💡 Recommended:</strong> {transportationBack.recommended_option}
                    </div>
                  )}
                  {transportationBack.tips && transportationBack.tips.length > 0 && (
                    <div style={{marginTop: '0.5rem'}}>
                      <strong>Tips:</strong>
                      <ul>
                        {transportationBack.tips.map((tip, i) => <li key={i}>{tip}</li>)}
                      </ul>
                    </div>
                  )}
                  {transportationBack.sources && transportationBack.sources.length > 0 && (
                    <div style={{marginTop: '0.5rem'}}>
                      <strong>🔗 Booking Links:</strong>
                      {transportationBack.sources.map((src, i) => (
                        <div key={i}>
                          <a href={src} target="_blank" rel="noopener noreferrer">{src}</a>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {day.budget_breakdown && (
              <div className={styles.budgetBreakdown}>
                <strong>Daily Budget:</strong> ${day.budget_breakdown.total}
                {day.budget_breakdown.activities && (
                  <span> (Activities: ${day.budget_breakdown.activities}, Meals: ${day.budget_breakdown.meals}, Transport: ${day.budget_breakdown.transport})</span>
                )}
              </div>
            )}

            {day.notes && (
              <div className={styles.dayNotes}>
                <em>{day.notes}</em>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className={styles.actions}>
        {data.level === 'medium' && (
          <button 
            onClick={handleProgressiveEnrichment}
            className={styles.enrichButton}
            disabled={loading || isEnriching}
          >
            {isEnriching ? '⏳ Enriching Activities...' : '✨ Add Full Details (timing, costs, tips)'}
          </button>
        )}
        <button 
          onClick={() => setShowRefineForm(!showRefineForm)}
          className={styles.primaryButton}
          disabled={loading}
        >
          🔄 Refine Plan
        </button>
        <button 
          onClick={onAlternatives}
          className={styles.secondaryButton}
          disabled={loading}
        >
          🌐 View Alternatives
        </button>
      </div>
      
      {/* Export Actions */}
      <div className={styles.exportActions}>
        <button 
          onClick={() => exportToCalendar()}
          className={styles.exportButton}
        >
          📅 Export to Calendar
        </button>
        <button 
          onClick={() => exportToTextFile()}
          className={styles.exportButton}
        >
          📄 Export to Text File
        </button>
      </div>

      {/* Date Modal for Calendar Export */}
      {showDateModal && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h3>📅 Set Travel Dates</h3>
            <p>Please provide your trip dates to export to calendar</p>
            <div className={styles.dateInputs}>
              <div className={styles.formGroup}>
                <label>Start Date:</label>
                <input
                  type="date"
                  value={calendarDates.start}
                  onChange={(e) => setCalendarDates({...calendarDates, start: e.target.value})}
                />
              </div>
              <div className={styles.formGroup}>
                <label>End Date:</label>
                <input
                  type="date"
                  value={calendarDates.end}
                  onChange={(e) => setCalendarDates({...calendarDates, end: e.target.value})}
                />
              </div>
            </div>
            <div className={styles.modalActions}>
              <button onClick={handleDateModalSubmit} className={styles.primaryButton}>
                Export to Calendar
              </button>
              <button onClick={() => setShowDateModal(false)} className={styles.secondaryButton}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Refine Form */}
      {showRefineForm && (
        <div className={styles.refineForm}>
          <h4>Refine Your Plan</h4>
          <form onSubmit={handleRefineSubmit}>
            <div className={styles.formGroup}>
              <label>Travel Dates:</label>
              <div className={styles.dateInputs}>
                <input
                  type="date"
                  value={refinements.start_date || ''}
                  onChange={(e) => setRefinements({ ...refinements, start_date: e.target.value })}
                  placeholder="Start"
                />
                <span style={{margin: '0 0.5rem'}}>to</span>
                <input
                  type="date"
                  value={refinements.end_date || ''}
                  onChange={(e) => setRefinements({ ...refinements, end_date: e.target.value })}
                  placeholder="End"
                />
              </div>
            </div>
            <div className={styles.formGroup}>
              <label>New Budget:</label>
              <select
                value={refinements.budget_range || ''}
                onChange={(e) => {
                  const budgetRanges = { '$': 1500, '$$': 3500, '$$$': 6000, '$$$$': 10000 };
                  setRefinements({ 
                    ...refinements, 
                    budget_range: e.target.value,
                    budget: e.target.value === 'custom' ? undefined : budgetRanges[e.target.value]
                  });
                }}
              >
                <option value="">Keep current</option>
                <option value="$">$ Budget</option>
                <option value="$$">$$ Moderate</option>
                <option value="$$$">$$$ Comfortable</option>
                <option value="$$$$">$$$$ Luxury</option>
                <option value="custom">Custom Amount</option>
              </select>
              {refinements.budget_range === 'custom' && (
                <input
                  type="number"
                  value={refinements.budget_custom || ''}
                  onChange={(e) => setRefinements({ ...refinements, budget_custom: e.target.value, budget: parseFloat(e.target.value) })}
                  placeholder="Enter amount"
                  style={{marginTop: '0.5rem'}}
                />
              )}
            </div>
            <div className={styles.formGroup}>
              <label>Pace:</label>
              <select
                value={refinements.pace || ''}
                onChange={(e) => setRefinements({ ...refinements, pace: e.target.value })}
              >
                <option value="">Keep current</option>
                <option value="relaxed">Relaxed</option>
                <option value="moderate">Moderate</option>
                <option value="packed">Packed</option>
              </select>
            </div>
            <div className={styles.formActions}>
              <button type="submit" className={styles.primaryButton}>Apply Changes</button>
              <button 
                type="button" 
                onClick={() => setShowRefineForm(false)}
                className={styles.secondaryButton}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Processing Time */}
      {data.processing_time && (
        <div className={styles.meta}>
          <small>Generated in {data.processing_time.toFixed(2)}s | Plan ID: {data.plan_id}</small>
        </div>
      )}
    </div>
  );
}
