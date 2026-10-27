import React, { useState } from 'react';
import { Play, Pause, SkipForward, SkipBack, Gauge, Clock, ShieldCheck, AlertTriangle, Eye, Layers } from 'lucide-react';
import { StreamingChart } from './StreamingChart';
import { EvidenceDrawer } from './EvidenceDrawer';

export function ReplayTab({ replayState, theme }) {
  const {
    currentIndex,
    totalPoints,
    currentPoint,
    isPlaying,
    speed,
    selectedSeries,
    availableSeries,
    seekTo,
    stepForward,
    stepBackward,
    togglePlay,
    setSpeed,
    setSelectedSeries
  } = replayState;

  const [inspectPoint, setInspectPoint] = useState(null);

  // Speed options
  const speedOptions = [0.5, 1, 2, 4, 8];

  const isAnomalous = currentPoint?.label === 'ANOMALOUS';
  const isWarmup = currentPoint && !currentPoint.ready;
  const score = currentPoint?.score;
  const threshold = currentPoint?.threshold || 4.0;

  // Score meter ratio (clamped to 0..1.2 for gauge display)
  const scoreRatio = score !== null ? Math.min(score / (threshold * 1.5), 1.2) : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', width: '100%' }}>
      {/* HUD Cards: Current Status, Score Meter, Timing */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1rem'
      }}>
        {/* Card 1: Live State & Label */}
        <div className="regal-card" style={{ padding: '1.1rem 1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Streaming Detector Verdict
            </span>
            {isAnomalous ? (
              <AlertTriangle size={17} style={{ color: 'var(--crimson-light)' }} />
            ) : (
              <ShieldCheck size={17} style={{ color: 'var(--teal-normal)' }} />
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.65rem' }}>
            <span
              className={`pill-badge ${isAnomalous ? 'pill-anomaly pulse-crimson' : (isWarmup ? 'pill-warmup' : 'pill-normal')}`}
              style={{ fontSize: '0.9rem', padding: '0.25rem 0.8rem', fontWeight: 700 }}
            >
              {isWarmup ? 'WARMING UP' : (isAnomalous ? 'ANOMALOUS' : 'NORMAL')}
            </span>
            <span className="mono-num" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Step {currentIndex + 1} of {totalPoints}
            </span>
          </div>

          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem', fontFamily: 'var(--font-mono)' }}>
            Obs: {currentPoint ? currentPoint.value.toFixed(2) : '--'} • Time: {currentPoint ? currentPoint.timestamp.substring(11, 19) + 'Z' : '--'}
          </div>
        </div>

        {/* Card 2: Anomaly Score Meter */}
        <div className="regal-card" style={{ padding: '1.1rem 1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Standardized Score ($\sigma$)
            </span>
            <Gauge size={16} style={{ color: 'var(--gold-primary)' }} />
          </div>

          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
            <span className="mono-num" style={{
              fontSize: '1.5rem',
              fontWeight: 700,
              color: isAnomalous ? 'var(--crimson-light)' : 'var(--text-primary)'
            }}>
              {score !== null ? score.toFixed(2) : 'null'}
            </span>
            <span className="mono-num" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Threshold: {threshold.toFixed(1)}
            </span>
          </div>

          {/* Linear Progress Meter */}
          <div style={{
            width: '100%',
            height: '6px',
            backgroundColor: 'rgba(201, 162, 75, 0.1)',
            borderRadius: '3px',
            overflow: 'hidden',
            marginTop: '0.65rem',
            position: 'relative'
          }}>
            <div style={{
              position: 'absolute',
              left: `${(1 / 1.5) * 100}%`,
              top: 0,
              bottom: 0,
              width: '2px',
              backgroundColor: 'var(--gold-primary)',
              zIndex: 2
            }} title="Decision Threshold" />
            <div style={{
              height: '100%',
              width: `${Math.min(scoreRatio * 100, 100)}%`,
              backgroundColor: isAnomalous ? 'var(--crimson-light)' : 'var(--teal-normal)',
              transition: 'width 0.15s ease'
            }} />
          </div>
        </div>

        {/* Card 3: In-Process Latency & Hardware Timing */}
        <div className="regal-card" style={{ padding: '1.1rem 1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Execution Latency
            </span>
            <Clock size={16} style={{ color: 'var(--gold-primary)' }} />
          </div>

          <div className="mono-num" style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {currentPoint ? (currentPoint.elapsed_ns / 1000).toFixed(1) : '--'} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>µs</span>
          </div>

          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            {currentPoint?.elapsed_ns || 0} nanoseconds • Zero network/GPU overhead
          </div>
        </div>
      </div>

      {/* Main Chart Viewer Card */}
      <div className="regal-card" style={{ padding: '1.25rem 1.5rem', position: 'relative' }}>
        {/* Top Header of Chart */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1rem',
          flexWrap: 'wrap',
          gap: '0.75rem'
        }}>
          <div>
            <h2 className="serif-heading" style={{ fontSize: '1.15rem', color: 'var(--text-primary)' }}>
              Causal Streaming Trajectory
            </h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Points emerge causally. Shaded envelope represents pre-update rolling median ± 4.0 MAD.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {/* Series selector if multiple series */}
            {availableSeries.length > 1 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem' }}>
                <Layers size={14} style={{ color: 'var(--gold-primary)' }} />
                <select
                  value={selectedSeries}
                  onChange={(e) => setSelectedSeries(e.target.value)}
                  style={{
                    background: 'var(--bg-surface)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--gold-border)',
                    borderRadius: '4px',
                    padding: '0.25rem 0.5rem',
                    fontSize: '0.78rem'
                  }}
                >
                  <option value="all">All Series</option>
                  {availableSeries.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            )}

            {currentPoint && (
              <button
                onClick={() => setInspectPoint(currentPoint)}
                className="btn-regal"
                style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
              >
                <Eye size={13} />
                <span>Inspect Evidence</span>
              </button>
            )}
          </div>
        </div>

        {/* Custom Canvas Chart */}
        <StreamingChart
          predictions={replayState.filteredPredictions || replayState.causalHistory}
          currentIndex={currentIndex}
          onSelectPoint={(p) => setInspectPoint(p)}
          theme={theme}
        />

        {/* Interactive Playback Control Toolbar */}
        <div style={{
          marginTop: '1.25rem',
          paddingTop: '1rem',
          borderTop: '1px solid var(--gold-border)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem'
        }}>
          {/* Scrubber slider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span className="mono-num" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', width: '45px' }}>
              0
            </span>
            <input
              type="range"
              min="0"
              max={Math.max(totalPoints - 1, 0)}
              value={currentIndex}
              onChange={(e) => seekTo(parseInt(e.target.value, 10))}
              style={{
                flex: 1,
                accentColor: 'var(--gold-primary)',
                cursor: 'pointer'
              }}
              aria-label="Replay stream scrubber"
            />
            <span className="mono-num" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', width: '45px', textAlign: 'right' }}>
              {totalPoints}
            </span>
          </div>

          {/* Action buttons & Speed selector */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <button
                onClick={stepBackward}
                disabled={currentIndex === 0}
                className="btn-regal"
                style={{ padding: '0.45rem', opacity: currentIndex === 0 ? 0.4 : 1 }}
                title="Step backward (Arrow Left)"
                aria-label="Step backward"
              >
                <SkipBack size={16} />
              </button>

              <button
                onClick={togglePlay}
                className="btn-regal btn-regal-primary"
                style={{ padding: '0.5rem 1.25rem' }}
                title="Play or pause replay (Spacebar)"
                aria-label={isPlaying ? 'Pause replay' : 'Play replay'}
              >
                {isPlaying ? <Pause size={17} /> : <Play size={17} />}
                <span>{isPlaying ? 'Pause' : 'Stream Replay'}</span>
              </button>

              <button
                onClick={stepForward}
                disabled={currentIndex >= totalPoints - 1}
                className="btn-regal"
                style={{ padding: '0.45rem', opacity: currentIndex >= totalPoints - 1 ? 0.4 : 1 }}
                title="Step forward (Arrow Right)"
                aria-label="Step forward"
              >
                <SkipForward size={16} />
              </button>
            </div>

            {/* Speed Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginRight: '0.25rem' }}>Speed:</span>
              {speedOptions.map(s => (
                <button
                  key={s}
                  onClick={() => setSpeed(s)}
                  style={{
                    padding: '0.25rem 0.55rem',
                    fontSize: '0.75rem',
                    fontFamily: 'var(--font-mono)',
                    borderRadius: '3px',
                    border: speed === s ? '1px solid var(--gold-primary)' : '1px solid var(--gold-border)',
                    background: speed === s ? 'var(--gold-glow)' : 'transparent',
                    color: speed === s ? 'var(--gold-primary)' : 'var(--text-secondary)',
                    cursor: 'pointer'
                  }}
                >
                  {s}x
                </button>
              ))}
            </div>

            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Keyboard: <kbd style={{ padding: '0.15rem 0.35rem', background: 'var(--bg-surface)', border: '1px solid var(--gold-border)', borderRadius: '3px' }}>Space</kbd> play/pause • <kbd style={{ padding: '0.15rem 0.35rem', background: 'var(--bg-surface)', border: '1px solid var(--gold-border)', borderRadius: '3px' }}>← / →</kbd> step
            </div>
          </div>
        </div>
      </div>

      {/* Side Evidence Drawer */}
      <EvidenceDrawer point={inspectPoint} onClose={() => setInspectPoint(null)} />
    </div>
  );
}
