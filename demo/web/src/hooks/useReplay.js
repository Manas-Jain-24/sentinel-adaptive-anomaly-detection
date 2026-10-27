import { useState, useEffect, useRef, useCallback } from "react";

export function useReplay(predictions = [], onOpenEvidence) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1); // 0.5x, 1x, 2x, 4x, 8x, 16x
  const [currentIndex, setCurrentIndex] = useState(0);
  const [causalMode, setCausalMode] = useState(true);
  const animationRef = useRef(null);
  const lastTickRef = useRef(performance.now());

  const totalPoints = predictions.length;

  const anomalies = predictions.filter(p => p.label === "ANOMALOUS");

  // Step forward
  const stepForward = useCallback(() => {
    setCurrentIndex(prev => Math.min(prev + 1, totalPoints - 1));
  }, [totalPoints]);

  // Step backward
  const stepBackward = useCallback(() => {
    setCurrentIndex(prev => Math.max(prev - 1, 0));
  }, []);

  // Jump to anomaly
  const jumpToAnomaly = useCallback((direction = "next") => {
    if (anomalies.length === 0) return;
    if (direction === "next") {
      const next = anomalies.find(a => a.index > currentIndex);
      if (next) setCurrentIndex(next.index);
      else setCurrentIndex(anomalies[0].index);
    } else {
      const prev = [...anomalies].reverse().find(a => a.index < currentIndex);
      if (prev) setCurrentIndex(prev.index);
      else setCurrentIndex(anomalies[anomalies.length - 1].index);
    }
  }, [anomalies, currentIndex]);

  // Play loop
  useEffect(() => {
    if (!isPlaying || totalPoints === 0) return;

    const intervalMs = Math.max(16, 250 / speed);

    const loop = (time) => {
      if (time - lastTickRef.current >= intervalMs) {
        lastTickRef.current = time;
        setCurrentIndex(prev => {
          if (prev >= totalPoints - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }
      animationRef.current = requestAnimationFrame(loop);
    };

    animationRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animationRef.current);
  }, [isPlaying, speed, totalPoints]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignore if user is typing in an input
      if (["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;

      if (e.code === "Space") {
        e.preventDefault();
        setIsPlaying(p => !p);
      } else if (e.code === "ArrowRight") {
        e.preventDefault();
        stepForward();
      } else if (e.code === "ArrowLeft") {
        e.preventDefault();
        stepBackward();
      } else if (e.key === "[") {
        e.preventDefault();
        jumpToAnomaly("prev");
      } else if (e.key === "]") {
        e.preventDefault();
        jumpToAnomaly("next");
      } else if (e.key === "e" || e.key === "E") {
        e.preventDefault();
        if (onOpenEvidence) onOpenEvidence();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [stepForward, stepBackward, jumpToAnomaly, onOpenEvidence]);

  return {
    isPlaying,
    setIsPlaying,
    speed,
    setSpeed,
    currentIndex,
    setCurrentIndex,
    causalMode,
    setCausalMode,
    stepForward,
    stepBackward,
    jumpToAnomaly,
    totalPoints,
    currentPoint: predictions[currentIndex] || null
  };
}