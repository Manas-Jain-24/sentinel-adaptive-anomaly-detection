import React from 'react';
import { X, ShieldAlert, Cpu, Database, Compass, Sliders, CheckCircle } from 'lucide-react';

export function EvidenceDrawer({ point, onClose }) {
  if (!point) return null;

  const { evidence, value, score, threshold, label, ready, elapsed_ns, timestamp, series_id, index } = point;

  const isAnomalous = label === 'ANOMALOUS';
  const baseline = evidence?.baseline;
  const scale = evidence?.scale;
  const residual = evidence?.residual;
  const historySize = evidence?.history_size || 0;
  const reason = evidence?.reason || 'unspecified';
  const componentScores = evidence?.component_scores || {};
  const elapsedMicros = (elapsed_ns / 1000).toFixed(2);

  // Plain-language interpretability explanation
  let plainReason = '';
  if (!ready) {
    plainReason = `System is warming up (${historySize} points observed, minimum required history not yet reached). Baseline estimation is provisional.`;
  } else if (isAnomalous) {
    plainReason = `Observation value (${value.toFixed(2)}) deviated by ${Math.abs(residual || 0).toFixed(2)} units from the rolling median baseline (${baseline?.toFixed(2)}), exceeding the calibrated anomaly threshold (${threshold.toFixed(1)}x MAD scale).`;
  } else {
    plainReason = `Observation value (${value.toFixed(2)}) falls within expected operating envelope (rolling median: ${baseline?.toFixed(2)}, tolerance: ±${((scale || 0) * threshold).toFixed(2)}).`;
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      width: '100%',
      maxWidth: '460px',
      height: '100vh',
      backgroundColor: 'var(--bg-drawer)',
      borderLeft: '1px solid var(--gold-border-strong)',
      boxShadow: 'var(--shadow-subtle)',
      zIndex: 200,
      display: 'flex',
      flexDirection: 'column',
      padding: '1.5rem',
      overflowY: 'auto',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      animation: 'slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1)'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: isAnomalous ? 'var(--crimson-light)' : (!ready ? 'var(--amber-warn)' : 'var(--teal-normal)')
            }}></span>
            <span className="serif-heading" style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Step #{index} Evidence Audit
            </span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Series: {series_id} • {timestamp.substring(11, 19)} UTC
          </p>
        </div>

        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: '1px solid var(--gold-border)',
            borderRadius: '4px',
            color: 'var(--gold-primary)',
            padding: '0.35rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          aria-label="Close evidence drawer"
        >
          <X size={18} />
        </button>
      </div>

      {/* State & Verdict Banner */}
      <div style={{
        padding: '0.85rem 1rem',
        borderRadius: '6px',
        backgroundColor: isAnomalous ? 'var(--crimson-bg)' : (!ready ? 'var(--amber-bg)' : 'var(--teal-bg)'),
        border: `1px solid ${isAnomalous ? 'var(--crimson-border)' : (!ready ? 'var(--gold-border)' : 'var(--teal-border)')}`,
        marginBottom: '1.5rem'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
          <span style={{
            fontFamily: 'var(--font-serif)',
            fontWeight: 700,
            fontSize: '0.95rem',
            letterSpacing: '0.06em',
            color: isAnomalous ? 'var(--crimson-light)' : (!ready ? 'var(--amber-warn)' : 'var(--teal-normal)')
          }}>
            {isAnomalous ? 'ANOMALOUS OBSERVATION' : (!ready ? 'WARMUP INGESTION' : 'NORMAL SIGNAL')}
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: 600 }}>
            Score: {score !== null ? score.toFixed(3) : 'null'}
          </span>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-primary)', lineHeight: 1.45 }}>
          {plainReason}
        </p>
      </div>

      {/* Numerical Evidence Breakdown */}
      <h3 className="serif-heading" style={{ fontSize: '0.9rem', color: 'var(--gold-primary)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        Statistical Pre-Update Evidence
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.65rem', marginBottom: '1.5rem' }}>
        <div className="regal-card" style={{ padding: '0.75rem' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Observed Value ($y_t$)</div>
          <div className="mono-num" style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            {value.toFixed(3)}
          </div>
        </div>

        <div className="regal-card" style={{ padding: '0.75rem' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Prior Baseline ($\hat{y}_t$)</div>
          <div className="mono-num" style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--gold-light)' }}>
            {baseline !== null ? baseline.toFixed(3) : 'N/A (warmup)'}
          </div>
        </div>

        <div className="regal-card" style={{ padding: '0.75rem' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Residual Deviation</div>
          <div className="mono-num" style={{ fontSize: '1.15rem', fontWeight: 600, color: isAnomalous ? 'var(--crimson-light)' : 'var(--text-primary)' }}>
            {residual !== null ? (residual > 0 ? `+${residual.toFixed(3)}` : residual.toFixed(3)) : 'null'}
          </div>
        </div>

        <div className="regal-card" style={{ padding: '0.75rem' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Scale ($1.4826 \times \text{MAD}$)</div>
          <div className="mono-num" style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            {scale !== null ? scale.toFixed(4) : 'null'}
          </div>
        </div>
      </div>

      {/* Threshold & Calibration Details */}
      <h3 className="serif-heading" style={{ fontSize: '0.9rem', color: 'var(--gold-primary)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        Threshold & Execution Timing
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.5rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', borderBottom: '1px solid var(--gold-border)' }}>
          <span style={{ color: 'var(--text-muted)' }}>Decision Threshold</span>
          <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{threshold.toFixed(2)}x scale</span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', borderBottom: '1px solid var(--gold-border)' }}>
          <span style={{ color: 'var(--text-muted)' }}>Causal History Window</span>
          <span style={{ color: 'var(--text-primary)' }}>{historySize} points</span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', borderBottom: '1px solid var(--gold-border)' }}>
          <span style={{ color: 'var(--text-muted)' }}>Algorithmic Reason</span>
          <span style={{ color: 'var(--gold-light)' }}>{reason}</span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', borderBottom: '1px solid var(--gold-border)' }}>
          <span style={{ color: 'var(--text-muted)' }}>Detector In-Process Latency</span>
          <span style={{ color: 'var(--text-primary)' }}>{elapsedMicros} µs ({elapsed_ns} ns)</span>
        </div>

        {Object.keys(componentScores).length > 0 && (
          <div style={{ padding: '0.5rem' }}>
            <div style={{ color: 'var(--text-muted)', marginBottom: '0.35rem' }}>Component Scores Breakdown:</div>
            {Object.entries(componentScores).map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', paddingLeft: '0.5rem' }}>
                <span style={{ color: 'var(--gold-dark)' }}>{k}:</span>
                <span style={{ color: 'var(--text-primary)' }}>{typeof v === 'number' ? v.toFixed(3) : v}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Causal Integrity Guarantee Notice */}
      <div style={{
        marginTop: 'auto',
        padding: '0.75rem',
        borderRadius: '4px',
        border: '1px solid var(--gold-border)',
        fontSize: '0.72rem',
        color: 'var(--text-muted)',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.5rem'
      }}>
        <CheckCircle size={15} style={{ color: 'var(--gold-primary)', flexShrink: 0, marginTop: '2px' }} />
        <span>
          <strong>Causal Guarantee</strong>: This evidence was recorded strictly before incorporating $y_t$ into state. No future points were visible.
        </span>
      </div>
    </div>
  );
}
