import React, { useMemo } from 'react';
import { evaluateEvents } from '../lib/evaluator';
import { BarChart2, CheckCircle2, AlertOctagon, HelpCircle, Clock, Zap, Target } from 'lucide-react';

export function EvaluationTab({ predictions = [], windows = [], scope = 'synthetic_smoke' }) {
  // Compute event evaluation metrics
  const evalMetrics = useMemo(() => {
    return evaluateEvents(predictions, windows);
  }, [predictions, windows]);

  const { tp, fp, fn, precision, recall, event_f1, mean_delay, median_delay, events_breakdown } = evalMetrics;

  // Timeline bounds calculation
  const timelineBounds = useMemo(() => {
    if (predictions.length === 0) return { start: 0, end: 1 };
    const start = new Date(predictions[0].timestamp).getTime();
    const end = new Date(predictions[predictions.length - 1].timestamp).getTime();
    return { start, end: Math.max(end, start + 1000) };
  }, [predictions]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', width: '100%' }}>
      {/* Header Banner with Provisional Metric Label */}
      <div className="regal-card" style={{ padding: '1.5rem', borderLeft: '4px solid var(--gold-primary)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
              <span className="serif-heading" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Event-Based Anomaly Evaluation
              </span>
              <span className="pill-badge pill-scope" style={{ fontSize: '0.72rem' }}>
                {scope}
              </span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
              Primary Metric: <code style={{ color: 'var(--gold-primary)', background: 'rgba(201,162,75,0.1)', padding: '0.15rem 0.4rem', borderRadius: '3px' }}>provisional_event_trigger_f1_v0</code>
              {' '}(provisional internal convention, awaiting official organizer scorer).
            </p>
          </div>

          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
            Ground Truth: {windows.length} event windows<br />
            Replay Points: {predictions.length} observations
          </div>
        </div>
      </div>

      {/* KPI Cards: F1, Precision, Recall, Mean Delay */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
        gap: '1rem'
      }}>
        {/* F1 Card */}
        <div className="regal-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Primary Event F1
            </span>
            <Target size={16} style={{ color: 'var(--gold-primary)' }} />
          </div>
          <div className="mono-num" style={{ fontSize: '2.1rem', fontWeight: 700, color: 'var(--gold-primary)' }}>
            {event_f1.toFixed(3)}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Harmonic mean of Event P & R
          </div>
        </div>

        {/* Precision Card */}
        <div className="regal-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Event Precision
            </span>
            <CheckCircle2 size={16} style={{ color: 'var(--teal-normal)' }} />
          </div>
          <div className="mono-num" style={{ fontSize: '2.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {(precision * 100).toFixed(1)}%
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            TP / (TP + FP) = {tp} / {tp + fp}
          </div>
        </div>

        {/* Recall Card */}
        <div className="regal-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Event Recall
            </span>
            <Zap size={16} style={{ color: 'var(--gold-light)' }} />
          </div>
          <div className="mono-num" style={{ fontSize: '2.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {(recall * 100).toFixed(1)}%
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            TP / (TP + FN) = {tp} / {tp + fn}
          </div>
        </div>

        {/* Detection Delay Card */}
        <div className="regal-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Onset Detection Delay
            </span>
            <Clock size={16} style={{ color: 'var(--gold-primary)' }} />
          </div>
          <div className="mono-num" style={{ fontSize: '2.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {mean_delay !== null ? `${mean_delay.toFixed(2)}s` : 'N/A'}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Median: {median_delay !== null ? `${median_delay.toFixed(2)}s` : 'N/A'} • Hits only
          </div>
        </div>
      </div>

      {/* Dual-Lane Timeline Strip: Ground Truth vs Model Triggers */}
      <div className="regal-card" style={{ padding: '1.5rem' }}>
        <h3 className="serif-heading" style={{ fontSize: '1.1rem', marginBottom: '0.35rem', color: 'var(--text-primary)' }}>
          Temporal Alignment Strip
        </h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          Top lane represents ground-truth anomaly windows. Bottom lane shows model trigger timestamps.
        </p>

        <div style={{ position: 'relative', height: '110px', backgroundColor: 'var(--bg-surface)', borderRadius: '6px', border: '1px solid var(--gold-border)', padding: '0.75rem 1rem' }}>
          {/* Lane 1: Ground Truth Windows */}
          <div style={{ position: 'relative', height: '36px', borderBottom: '1px dashed var(--gold-border)' }}>
            <span style={{ position: 'absolute', left: 0, top: '6px', fontSize: '0.7rem', color: 'var(--gold-light)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>
              Ground Truth:
            </span>

            {windows.map((w, idx) => {
              const startT = new Date(w.start).getTime();
              const endT = new Date(w.end).getTime();
              const leftPct = ((startT - timelineBounds.start) / (timelineBounds.end - timelineBounds.start)) * 100;
              const widthPct = Math.max(((endT - startT) / (timelineBounds.end - timelineBounds.start)) * 100, 2.5);

              return (
                <div
                  key={idx}
                  style={{
                    position: 'absolute',
                    left: `${Math.min(Math.max(leftPct, 15), 90)}%`,
                    width: `${widthPct}%`,
                    top: '4px',
                    height: '24px',
                    backgroundColor: 'rgba(201, 162, 75, 0.35)',
                    border: '1px solid var(--gold-primary)',
                    borderRadius: '3px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.68rem',
                    color: 'var(--text-primary)',
                    fontFamily: 'var(--font-mono)',
                    boxShadow: 'var(--shadow-gold)'
                  }}
                  title={`Window: ${w.start} to ${w.end}`}
                >
                  Win #{idx + 1}
                </div>
              );
            })}
          </div>

          {/* Lane 2: Model Anomaly Triggers */}
          <div style={{ position: 'relative', height: '36px', marginTop: '6px' }}>
            <span style={{ position: 'absolute', left: 0, top: '6px', fontSize: '0.7rem', color: 'var(--crimson-light)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>
              Triggers:
            </span>

            {predictions.filter(p => p.label === 'ANOMALOUS').map((p, idx) => {
              const t = new Date(p.timestamp).getTime();
              const leftPct = ((t - timelineBounds.start) / (timelineBounds.end - timelineBounds.start)) * 100;

              return (
                <div
                  key={idx}
                  style={{
                    position: 'absolute',
                    left: `${Math.min(Math.max(leftPct, 15), 95)}%`,
                    top: '2px',
                    width: '18px',
                    height: '26px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    transform: 'translateX(-50%)'
                  }}
                  title={`Trigger at ${p.timestamp} (Score: ${p.score?.toFixed(2)})`}
                >
                  <div style={{
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--crimson-light)',
                    boxShadow: '0 0 10px var(--crimson-light)',
                    border: '2px solid #FFF'
                  }} />
                  <div style={{ width: '2px', height: '14px', backgroundColor: 'var(--crimson-light)' }} />
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Events Breakdown Table */}
      <div className="regal-card" style={{ padding: '1.5rem', overflowX: 'auto' }}>
        <h3 className="serif-heading" style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>
          Detailed Event Matching Log
        </h3>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', fontFamily: 'var(--font-mono)' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--gold-border)', textAlign: 'left', color: 'var(--gold-primary)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
              <th style={{ padding: '0.65rem 0.5rem' }}>Status</th>
              <th style={{ padding: '0.65rem 0.5rem' }}>Series</th>
              <th style={{ padding: '0.65rem 0.5rem' }}>Timestamp / Interval</th>
              <th style={{ padding: '0.65rem 0.5rem' }}>Detection Delay</th>
              <th style={{ padding: '0.65rem 0.5rem' }}>Score</th>
              <th style={{ padding: '0.65rem 0.5rem' }}>Evaluator Reason</th>
            </tr>
          </thead>
          <tbody>
            {eventsBreakdown.map((item, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid rgba(201, 162, 75, 0.1)' }}>
                <td style={{ padding: '0.65rem 0.5rem' }}>
                  <span className={`pill-badge ${item.type === 'HIT' ? 'pill-normal' : (item.type === 'FALSE_ALARM' ? 'pill-anomaly' : 'pill-warmup')}`}>
                    {item.type}
                  </span>
                </td>
                <td style={{ padding: '0.65rem 0.5rem', color: 'var(--text-primary)' }}>{item.series_id}</td>
                <td style={{ padding: '0.65rem 0.5rem', color: 'var(--text-secondary)' }}>
                  {item.window ? `${item.window.start.substring(11, 19)} → ${item.window.end.substring(11, 19)}` : item.timestamp?.substring(11, 19)}
                </td>
                <td style={{ padding: '0.65rem 0.5rem', color: 'var(--text-primary)' }}>
                  {item.delay_seconds !== undefined ? `${item.delay_seconds.toFixed(2)}s` : '--'}
                </td>
                <td style={{ padding: '0.65rem 0.5rem', color: 'var(--text-primary)' }}>
                  {item.score !== undefined ? item.score.toFixed(2) : '--'}
                </td>
                <td style={{ padding: '0.65rem 0.5rem', color: 'var(--text-muted)' }}>{item.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
