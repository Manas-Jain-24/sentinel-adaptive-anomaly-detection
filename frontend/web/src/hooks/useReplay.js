import { useState, useEffect, useRef, useCallback } from 'react';

export function useReplay(predictions = [], onAnomalyFlare = null) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1.0);
  const [selectedSeries, setSelectedSeries] = useState('all');

  const timerRef = useRef(null);

  // Extract all available series IDs
  const availableSeries = Array.from(new Set(predictions.map(p => p.series_id)));

  // Filtered predictions by selected series
  const filteredPredictions = selectedSeries === 'all'
    ? predictions
    : predictions.filter(p => p.series_id === selectedSeries);

  const totalPoints = filteredPredictions.length;

  const currentPoint = totalPoints > 0 && currentIndex < totalPoints
    ? filteredPredictions[currentIndex]
    : null;

  // History up to current point (strictly causal!)
  const causalHistory = filteredPredictions.slice(0, currentIndex + 1);

  const seekTo = useCallback((index) => {
    if (totalPoints === 0) return;
    const clamped = Math.max(0, Math.min(index, totalPoints - 1));
    setCurrentIndex(clamped);

    // If seeking to an anomaly, trigger flare
    if (onAnomalyFlare && filteredPredictions[clamped]?.label === 'ANOMALOUS') {
      onAnomalyFlare(filteredPredictions[clamped]);
    }
  }, [totalPoints, filteredPredictions, onAnomalyFlare]);

  const stepForward = useCallback(() => {
    if (totalPoints === 0) return;
    setCurrentIndex(prev => {
      const next = Math.min(prev + 1, totalPoints - 1);
      if (onAnomalyFlare && filteredPredictions[next]?.label === 'ANOMALOUS') {
        onAnomalyFlare(filteredPredictions[next]);
      }
      return next;
    });
  }, [totalPoints, filteredPredictions, onAnomalyFlare]);

  const stepBackward = useCallback(() => {
    setCurrentIndex(prev => Math.max(prev - 1, 0));
  }, []);

  const togglePlay = useCallback(() => {
    setIsPlaying(prev => {
      // If at end, loop to start
      if (!prev && currentIndex >= totalPoints - 1) {
        setCurrentIndex(0);
      }
      return !prev;
    });
  }, [currentIndex, totalPoints]);

  const play = useCallback(() => setIsPlaying(true), []);
  const pause = useCallback(() => setIsPlaying(false), []);

  // Interval-driven playback
  useEffect(() => {
    if (!isPlaying) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    const intervalMs = Math.max(80, Math.round(900 / speed));

    timerRef.current = setInterval(() => {
      setCurrentIndex(prev => {
        if (prev >= totalPoints - 1) {
          setIsPlaying(false);
          return prev;
        }
        const next = prev + 1;
        if (onAnomalyFlare && filteredPredictions[next]?.label === 'ANOMALOUS') {
          onAnomalyFlare(filteredPredictions[next]);
        }
        return next;
      });
    }, intervalMs);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, speed, totalPoints, filteredPredictions, onAnomalyFlare]);

  // Keyboard controls (Space to play/pause, Left/Right arrows to step)
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignore if user is typing in an input
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) {
        return;
      }

      if (e.code === 'Space') {
        e.preventDefault();
        togglePlay();
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        stepForward();
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        stepBackward();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [togglePlay, stepForward, stepBackward]);

  return {
    currentIndex,
    totalPoints,
    currentPoint,
    causalHistory,
    isPlaying,
    speed,
    selectedSeries,
    availableSeries,
    seekTo,
    stepForward,
    stepBackward,
    togglePlay,
    play,
    pause,
    setSpeed,
    setSelectedSeries
  };
}
