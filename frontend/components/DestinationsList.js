import styles from '../styles/DestinationsList.module.css';

export default function DestinationsList({ data, onSelectDestination, onRefine }) {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>🎯 Recommended Destinations</h2>
        <p className={styles.reasoning}>{data.reasoning}</p>
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

      {/* Destinations Grid */}
      <div className={styles.destinations}>
        {data.destinations?.map((dest, idx) => (
          <div key={idx} className={styles.destination}>
            <div className={styles.destinationHeader}>
              <h3>
                {idx === 0 && '🥇 '}
                {idx === 1 && '🥈 '}
                {idx === 2 && '🥉 '}
                {dest.name}{dest.country ? `, ${dest.country}` : ''}
              </h3>
              <div className={styles.score}>
                <span className={styles.scoreValue}>{dest.score}</span>
                <span className={styles.scoreLabel}>/100</span>
              </div>
            </div>

            <div className={styles.reasoning}>
              <p>{dest.reasoning}</p>
            </div>

            <div className={styles.bestFor}>
              <strong>🎯 Best For:</strong> {dest.best_for}
            </div>

            {dest.highlights && (
              <div className={styles.highlights}>
                <strong>🌟 Highlights:</strong>
                <ul>
                  {dest.highlights.map((h, i) => (
                    <li key={i}>{h}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className={styles.details}>
              {dest.distance_info && (
                <div className={styles.distance}>
                  <strong>📏 Distance:</strong> {dest.distance_info}
                </div>
              )}
              
              <div className={styles.cost}>
                <strong>💰 Est. Daily Cost:</strong> ${dest.estimated_daily_cost}
              </div>
              
              {dest.considerations && (
                <div className={styles.considerations}>
                  <strong>ℹ️ Considerations:</strong> {dest.considerations}
                </div>
              )}

              {dest.budget_warning && (
                <div className={styles.budgetWarning}>
                  ⚠️ {dest.budget_warning}
                </div>
              )}

              {dest.budget_note && (
                <div className={styles.budgetNote}>
                  💡 {dest.budget_note}
                </div>
              )}
            </div>

            <button
              onClick={() => onSelectDestination(dest)}
              className={styles.selectButton}
            >
              Create Detailed Itinerary →
            </button>
          </div>
        ))}
      </div>

      {/* Processing Time */}
      {data.processing_time && (
        <div className={styles.meta}>
          <small>Generated in {data.processing_time.toFixed(2)}s | Plan ID: {data.plan_id}</small>
        </div>
      )}
    </div>
  );
}
