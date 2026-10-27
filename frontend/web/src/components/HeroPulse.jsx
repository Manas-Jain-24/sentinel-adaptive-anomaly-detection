import React, { useEffect, useRef } from 'react';

export function HeroPulse({ isAnomaly = false, theme = 'dark' }) {
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const updateSize = () => {
      canvas.width = canvas.parentElement ? canvas.parentElement.clientWidth : window.innerWidth;
      canvas.height = 140;
    };
    updateSize();

    window.addEventListener('resize', updateSize);

    let sweepX = 0;
    let anomalyRipple = 0;
    let time = 0;

    const render = () => {
      time += 0.02;
      const width = canvas.width;
      const height = canvas.height;
      const midY = height / 2;

      ctx.clearRect(0, 0, width, height);

      // Advance radar sweep
      sweepX = (sweepX + 3.2) % width;

      // Anomaly flare handling
      if (isAnomaly) {
        anomalyRipple = 1.0;
      }
      if (anomalyRipple > 0.01) {
        anomalyRipple *= 0.94; // fade ripple
      } else {
        anomalyRipple = 0;
      }

      const isDark = theme === 'dark';
      const baseLineColor = isDark ? 'rgba(201, 162, 75, 0.15)' : 'rgba(148, 113, 36, 0.15)';
      const pulseColor = isDark ? 'rgba(201, 162, 75, 0.85)' : 'rgba(148, 113, 36, 0.9)';
      const crimsonColor = isDark ? 'rgba(214, 69, 79, 0.95)' : 'rgba(186, 45, 54, 0.95)';

      // 1. Draw subtle horizontal grid line
      ctx.strokeStyle = baseLineColor;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, midY);
      ctx.lineTo(width, midY);
      ctx.stroke();

      // 2. Generate ECG waveform path
      ctx.beginPath();
      ctx.lineWidth = anomalyRipple > 0 ? 2.5 : 1.8;

      for (let x = 0; x < width; x += 3) {
        let y = midY;

        // Distance from radar sweep
        const distFromSweep = (x - sweepX + width) % width;

        // Periodic ECG spikes every ~220px
        const cycle = (x + time * 120) % 240;
        if (cycle > 90 && cycle < 150) {
          const rel = cycle - 90;
          if (rel < 10) y -= rel * 1.5;
          else if (rel < 20) y += (rel - 10) * 3;
          else if (rel < 32) y -= (rel - 20) * 4.5; // sharp R wave
          else if (rel < 44) y += (rel - 32) * 3.5;
          else if (rel < 56) y -= (rel - 44) * 0.8; // T wave
        }

        // Anomaly flare perturbation
        if (anomalyRipple > 0) {
          const flutter = Math.sin(x * 0.05 + time * 20) * (anomalyRipple * 28);
          y += flutter;
        }

        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }

      // Stroke gradient: leading edge glow near sweepX
      const strokeGrad = ctx.createLinearGradient(0, 0, width, 0);
      const sweepFrac = sweepX / width;

      if (anomalyRipple > 0.1) {
        // Crimson anomaly flare
        ctx.strokeStyle = crimsonColor;
        ctx.shadowColor = 'rgba(179, 54, 62, 0.8)';
        ctx.shadowBlur = 20 * anomalyRipple;
      } else {
        // Regal gold pulse line with radar sweep highlight
        strokeGrad.addColorStop(0, pulseColor);
        strokeGrad.addColorStop(Math.max(0, sweepFrac - 0.1), pulseColor);
        strokeGrad.addColorStop(sweepFrac, isDark ? '#FFFFFF' : '#FFDF88');
        strokeGrad.addColorStop(Math.min(1, sweepFrac + 0.05), baseLineColor);
        strokeGrad.addColorStop(1, baseLineColor);

        ctx.strokeStyle = strokeGrad;
        ctx.shadowColor = 'rgba(201, 162, 75, 0.45)';
        ctx.shadowBlur = 8;
      }

      ctx.stroke();
      ctx.shadowBlur = 0; // reset

      // Draw radar sweep glowing dot
      ctx.beginPath();
      ctx.arc(sweepX, midY, anomalyRipple > 0 ? 5 : 3.5, 0, Math.PI * 2);
      ctx.fillStyle = anomalyRipple > 0 ? crimsonColor : (isDark ? '#FFF2CE' : '#947124');
      ctx.fill();

      // Soft ripple ring when anomaly flares
      if (anomalyRipple > 0.05) {
        ctx.beginPath();
        ctx.arc(sweepX, midY, (1 - anomalyRipple) * 55, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(179, 54, 62, ${anomalyRipple * 0.7})`;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      window.removeEventListener('resize', updateSize);
    };
  }, [isAnomaly, theme]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '140px', overflow: 'hidden' }}>
      <canvas
        ref={canvasRef}
        style={{ display: 'block', width: '100%', height: '100%' }}
      />
    </div>
  );
}
