import { useState, useEffect } from 'react';
import styles from '../styles/LoadingScreen.module.css';

export default function LoadingScreen({ detailLevel = 'medium' }) {
  const [dots, setDots] = useState('');
  const [messageIndex, setMessageIndex] = useState(0);

  const messages = {
    high_level: [
      'Searching for perfect destinations...',
      'Analyzing your preferences...',
      'Finding the best matches...',
      'Almost there...'
    ],
    medium: [
      'Creating your itinerary...',
      'Planning daily activities...',
      'Organizing your trip...',
      'Finalizing details...'
    ],
    full: [
      'Adding detailed information...',
      'Calculating costs and timing...',
      'Finding insider tips...',
      'Polishing your itinerary...'
    ]
  };

  const currentMessages = messages[detailLevel] || messages.medium;

  useEffect(() => {
    // Cycle through messages
    const messageInterval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % currentMessages.length);
    }, 3000);

    // Animate dots
    const dotInterval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? '' : prev + '.'));
    }, 500);

    return () => {
      clearInterval(messageInterval);
      clearInterval(dotInterval);
    };
  }, [currentMessages.length]);

  return (
    <div className={styles.container}>
      <div className={styles.content}>
        {/* Large Animated Loader */}
        <div className={styles.spinner}></div>

        {/* Main Message */}
        <h2 className={styles.message}>
          {currentMessages[messageIndex]}{dots}
        </h2>

        {/* Estimated Time */}
        <div className={styles.estimate}>
          <p>
            This may take <strong>
              {detailLevel === 'high_level' ? '20-30' : detailLevel === 'medium' ? '60-90' : '90-120'} seconds
            </strong>
          </p>
          <p className={styles.subtext}>Please wait, AI is working...</p>
        </div>
      </div>
    </div>
  );
}
