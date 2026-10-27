import React, { useRef, useEffect, useState, useMemo } from 'react';

export function StreamingChart({
  predictions = [],
  currentIndex = 0,
  onSelectPoint = null,
  theme = 'dark'
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  // Only consider points strictly up to currentIndex (causal constraint)
  const visiblePoints = useMemo(() => {
    return predictions.slice(0, currentIndex + 1);
  }, [predictions, currentIndex]);

  // Compute min/max value bounds for stable scaling
  const { minVal, maxVal, warmupEndIndex } = useMemo(() => {
    if (predictions.length === 0) {
      return { minVal: 0, maxVal: 20, warmupEndIndex: 0 };
    }

    let min = Infinity;
    let max = -Infinity;
    let lastWarmup = -1;

    for (let i = 0; i < predictions.length; i++) {
      const p = predictions[i];
      if (p.value < min) min = p.value;
      if (p.value > max) max = p.value;

      // Include evidence baseline and MAD bands if available
      if (p.evidence?.baseline !== null && p.evidence?.scale !== null) {
        const top = p.evidence.baseline + (p.threshold || 4.0) * p.evidence.scale;
        const btm = p.evidence.baseline - (p.threshold || 4.0) * p.evidence.scale;
        if (top > max) max = top;
        if (btm < min) min = btm;
      }

      if (!p.ready) {
        lastWarmup = i;
      }
    }

    // Add 15% padding
    const padding = (max - min) * 0.15 || 2.0;
    return {
      minVal: min - padding,
      maxVal: max + padding,
      warmupEndIndex: lastWarmup
    };
  }, [predictions]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;

    const width = container.clientWidth;
    const height = container.clientHeight || 420;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    ctx.scale(dpr, dpr);

    const isDark = theme === 'dark';
    ctx.clearRect(0, 0, width, height);

    const padding = { top: 40, right: 40, bottom: 50, left: 60 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    if (predictions.length === 0) {
      ctx.fillStyle = isDark ? '#9AA7B7' : '#485465';
      ctx.font = '14px "Inter", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('No streaming predictions loaded', width / 2, height / 2);
      return;
    }

    // Total slots based on full dataset to keep horizontal scale consistent
    const totalSlots = Math.max(predictions.length - 1, 1);

    const getX = (idx) => padding.left + (idx / totalSlots) * chartW;
    const getY = (val) => padding.top + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;

    // 1. Grid lines and Y-axis labels
    const yTicks = 5;
    ctx.strokeStyle = isDark ? 'rgba(201, 162, 75, 0.08)' : 'rgba(148, 113, 36, 0.08)';
    ctx.lineWidth = 1;
    ctx.fillStyle = isDark ? 'rgba(154, 167, 183, 0.65)' : 'rgba(72, 84, 101, 0.65)';
    ctx.font = '11px "JetBrains Mono", monospace';
    ctx.textAlign = 'right';

    for (let i = 0; i <= yTicks; i++) {
      const frac = i / yTicks;
      const val = minVal + frac * (maxVal - minVal);
      const y = padding.top + chartH - frac * chartH;

      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      ctx.fillText(val.toFixed(1), padding.left - 10, y + 4);
    }

    // 2. Warmup Region Shading
    if (warmupEndIndex >= 0) {
      const warmupEndX = Math.min(getX(warmupEndIndex + 0.5), getX(currentIndex));
      if (warmupEndX > padding.left) {
        ctx.save();
        ctx.fillStyle = isDark ? 'rgba(201, 162, 75, 0.06)' : 'rgba(148, 113, 36, 0.06)';
        ctx.fillRect(padding.left, padding.top, warmupEndX - padding.left, chartH);

        // Warmup hatched diagonal lines
        ctx.strokeStyle = isDark ? 'rgba(201, 162, 75, 0.08)' : 'rgba(148, 113, 36, 0.08)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let x = padding.left - chartH; x < warmupEndX; x += 16) {
          ctx.moveTo(Math.max(padding.left, x), padding.top + chartH);
          ctx.lineTo(Math.min(warmupEndX, x + chartH), padding.top);
        }
        ctx.stroke();

        // Warmup label
        ctx.fillStyle = isDark ? 'rgba(201, 162, 75, 0.75)' : 'rgba(148, 113, 36, 0.75)';
        ctx.font = '10px "Inter", sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('Warming up (ready=false, score=null)', padding.left + 8, padding.top + 18);
        ctx.restore();
      }
    }

    // 3. Draw MAD Anomaly Bounds (Pre-update baseline +/- threshold * scale)
    const bandPoints = visiblePoints.filter(p => p.ready && p.evidence.baseline !== null && p.evidence.scale !== null);
    if (bandPoints.length > 1) {
      ctx.save();
      ctx.beginPath();
      // Upper bound
      for (let i = 0; i < bandPoints.length; i++) {
        const p = bandPoints[i];
        const thresh = p.threshold || 4.0;
        const upper = p.evidence.baseline + thresh * p.evidence.scale;
        const x = getX(p.index);
        const y = getY(upper);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      // Lower bound
      for (let i = bandPoints.length - 1; i >= 0; i--) {
        const p = bandPoints[i];
        const thresh = p.threshold || 4.0;
        const lower = p.evidence.baseline - thresh * p.evidence.scale;
        const x = getX(p.index);
        const y = getY(lower);
        ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.fillStyle = isDark ? 'rgba(92, 131, 149, 0.12)' : 'rgba(61, 100, 119, 0.12)';
      ctx.fill();

      // Draw dashed baseline center
      ctx.beginPath();
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = isDark ? 'rgba(92, 131, 149, 0.45)' : 'rgba(61, 100, 119, 0.45)';
      ctx.lineWidth = 1;
      for (let i = 0; i < bandPoints.length; i++) {
        const p = bandPoints[i];
        const x = getX(p.index);
        const y = getY(p.evidence.baseline);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
      ctx.restore();
    }

    // 4. Draw Streaming Observation Line (Causal history only)
    if (visiblePoints.length > 0) {
      ctx.beginPath();
      ctx.lineWidth = 2.4;
      ctx.strokeStyle = isDark ? '#E2DAC8' : '#1C2534'; // Ivory or Ink

      for (let i = 0; i < visiblePoints.length; i++) {
        const p = visiblePoints[i];
        const x = getX(p.index);
        const y = getY(p.value);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // 5. Draw Point Dots and Anomaly Beacons
      for (let i = 0; i < visiblePoints.length; i++) {
        const p = visiblePoints[i];
        const x = getX(p.index);
        const y = getY(p.value);

        if (p.label === 'ANOMALOUS') {
          // Crimson Anomaly Beacon with Outer Pulsing Rings
          ctx.save();
          // Outer beacon ring
          ctx.beginPath();
          ctx.arc(x, y, 11, 0, Math.PI * 2);
          ctx.strokeStyle = isDark ? 'rgba(214, 69, 79, 0.45)' : 'rgba(186, 45, 54, 0.45)';
          ctx.lineWidth = 2;
          ctx.stroke();

          // Middle glow ring
          ctx.beginPath();
          ctx.arc(x, y, 7, 0, Math.PI * 2);
          ctx.fillStyle = isDark ? 'rgba(179, 54, 62, 0.4)' : 'rgba(158, 36, 44, 0.4)';
          ctx.fill();

          // Core crimson dot
          ctx.beginPath();
          ctx.arc(x, y, 4.5, 0, Math.PI * 2);
          ctx.fillStyle = isDark ? '#D6454F' : '#BA2D36';
          ctx.fill();
          ctx.restore();
        } else if (!p.ready) {
          // Warmup point: small amber/gold ring
          ctx.beginPath();
          ctx.arc(x, y, 2.5, 0, Math.PI * 2);
          ctx.fillStyle = isDark ? '#C9A24B' : '#947124';
          ctx.fill();
        } else {
          // Normal point: subtle teal-slate dot
          ctx.beginPath();
          ctx.arc(x, y, 3, 0, Math.PI * 2);
          ctx.fillStyle = isDark ? '#5C8395' : '#3D6477';
          ctx.fill();
        }
      }

      // Draw active playhead beacon
      if (visiblePoints.length > 0) {
        const activePoint = visiblePoints[visiblePoints.length - 1];
        const activeX = getX(activePoint.index);
        const activeY = getY(activePoint.value);

        ctx.save();
        ctx.beginPath();
        ctx.arc(activeX, activeY, 8, 0, Math.PI * 2);
        ctx.strokeStyle = activePoint.label === 'ANOMALOUS' ? 'var(--crimson-light)' : 'var(--gold-primary)';
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.restore();
      }
    }

    // 6. Draw X-axis Timestamps
    const xStep = Math.max(1, Math.floor(predictions.length / 6));
    ctx.fillStyle = isDark ? 'rgba(154, 167, 183, 0.7)' : 'rgba(72, 84, 101, 0.7)';
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';

    for (let i = 0; i < predictions.length; i += xStep) {
      const p = predictions[i];
      const x = getX(i);
      const timeStr = p.timestamp.substring(11, 16); // "HH:MM"
      ctx.fillText(timeStr, x, padding.top + chartH + 20);
    }

  }, [predictions, currentIndex, visiblePoints, minVal, maxVal, warmupEndIndex, theme]);

  // Handle canvas mouse move for interactive tooltip
  const handleMouseMove = (e) => {
    const canvas = canvasRef.current;
    if (!canvas || visiblePoints.length === 0) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const padding = { top: 40, right: 40, bottom: 50, left: 60 };
    const chartW = rect.width - padding.left - padding.right;
    const totalSlots = Math.max(predictions.length - 1, 1);

    // Find nearest point
    let nearest = null;
    let nearestDist = 24; // 24px hit tolerance

    for (let i = 0; i < visiblePoints.length; i++) {
      const p = visiblePoints[i];
      const px = padding.left + (p.index / totalSlots) * chartW;
      const dist = Math.abs(mouseX - px);

      if (dist < nearestDist) {
        nearestDist = dist;
        nearest = p;
      }
    }

    if (nearest) {
      setHoveredPoint(nearest);
      setTooltipPos({ x: e.clientX, y: e.clientY });
    } else {
      setHoveredPoint(null);
    }
  };

  const handleClick = () => {
    if (hoveredPoint && onSelectPoint) {
      onSelectPoint(hoveredPoint);
    }
  };

  return (
    <div
      ref={containerRef}
      style={{ position: 'relative', width: '100%', height: '420px', cursor: hoveredPoint ? 'pointer' : 'crosshair' }}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setHoveredPoint(null)}
      onClick={handleClick}
    >
      <canvas ref={canvasRef} style={{ display: 'block' }} />

      {/* Floating Hover Tooltip */}
      {hoveredPoint && (
        <div
          style={{
            position: 'fixed',
            left: `${tooltipPos.x + 14}px`,
            top: `${tooltipPos.y - 45}px`,
            zIndex: 1000,
            pointerEvents: 'none',
            background: 'var(--bg-drawer)',
            border: `1px solid ${hoveredPoint.label === 'ANOMALOUS' ? 'var(--crimson-border)' : 'var(--gold-border)'}`,
            borderRadius: '6px',
            padding: '0.65rem 0.85rem',
            boxShadow: 'var(--shadow-subtle)',
            fontSize: '0.75rem',
            lineHeight: 1.4,
            backdropFilter: 'blur(8px)',
            minWidth: '170px'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
            <span style={{ fontWeight: 600, color: 'var(--gold-primary)', fontFamily: 'var(--font-serif)' }}>
              Step #{hoveredPoint.index}
            </span>
            <span className={`pill-badge ${hoveredPoint.label === 'ANOMALOUS' ? 'pill-anomaly' : (!hoveredPoint.ready ? 'pill-warmup' : 'pill-normal')}`} style={{ fontSize: '0.62rem', padding: '0.1rem 0.4rem' }}>
              {hoveredPoint.ready ? hoveredPoint.label : 'WARMUP'}
            </span>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
            <div>Value: <strong style={{ color: 'var(--text-primary)' }}>{hoveredPoint.value.toFixed(2)}</strong></div>
            <div>Score: <strong style={{ color: hoveredPoint.label === 'ANOMALOUS' ? 'var(--crimson-light)' : 'var(--text-primary)' }}>{hoveredPoint.score !== null ? hoveredPoint.score.toFixed(3) : 'null'}</strong></div>
            <div>Thresh: {hoveredPoint.threshold.toFixed(2)}</div>
            <div>Time: {hoveredPoint.timestamp.substring(11, 19)}Z</div>
          </div>
          <div style={{ marginTop: '0.4rem', borderTop: '1px solid var(--gold-border)', paddingTop: '0.3rem', fontSize: '0.68rem', color: 'var(--gold-light)' }}>
            Click to inspect evidence
          </div>
        </div>
      )}
    </div>
  );
}
