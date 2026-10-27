import React from 'react';
import { HeroPulse } from './HeroPulse';
import { Activity, Shield, ArrowRight, Upload, CheckCircle, Info, AlertCircle, Cpu, FileCode2, Scale } from 'lucide-react';

export function OverviewTab({ onGoToReplay, onOpenUpload, theme }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem', width: '100%' }}>
      {/* Hero Section */}
      <div className="regal-card" style={{
        padding: '2.5rem 2rem',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Subtle royal background glow */}
        <div style={{
          position: 'absolute',
          top: '-30%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '500px',
          height: '250px',
          background: 'radial-gradient(circle, var(--gold-glow) 0%, transparent 70%)',
          pointerEvents: 'none'
        }} />

        {/* 3 Honest Status Chips */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '0.65rem', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
          <span className="pill-badge pill-normal" style={{ fontSize: '0.72rem' }}>
            <CheckCircle size={12} />
            Runnable Starter
          </span>
          <span className="pill-badge pill-scope" style={{ fontSize: '0.72rem' }}>
            <Info size={12} />
            Synthetic Data Only
          </span>
          <span className="pill-badge pill-warmup" style={{ fontSize: '0.72rem' }}>
            <AlertCircle size={12} />
            No Official Benchmark Yet
          </span>
        </div>

        <h1 className="serif-heading" style={{
          fontSize: 'clamp(2.2rem, 5vw, 3.8rem)',
          fontWeight: 700,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          marginBottom: '0.5rem',
          color: 'var(--text-primary)',
          textShadow: '0 0 25px var(--gold-glow)'
        }}>
          Sentinel Pulse
        </h1>

        <p className="serif-heading" style={{
          fontSize: 'clamp(1rem, 2vw, 1.35rem)',
          color: 'var(--gold-primary)',
          letterSpacing: '0.15em',
          textTransform: 'uppercase',
          marginBottom: '1.5rem',
          fontWeight: 500
        }}>
          Causal. Interpretable. Streaming.
        </p>

        <p style={{
          maxWidth: '720px',
          margin: '0 auto 2rem auto',
          fontSize: '0.95rem',
          color: 'var(--text-secondary)',
          lineHeight: 1.65
        }}>
          A lightweight time-series anomaly detection engine designed for <strong>Utkrishta 2026 (Challenge 2)</strong>.
          Learns normal behavior dynamically from streaming data, provides mathematical evidence for every alert,
          and measures detection latency with zero temporal leakage.
        </p>

        {/* Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap', marginBottom: '2.5rem' }}>
          <button
            onClick={onGoToReplay}
            className="btn-regal btn-regal-primary"
            style={{ padding: '0.75rem 1.75rem', fontSize: '0.9rem' }}
          >
            <Activity size={18} />
            <span>Watch Live Replay</span>
            <ArrowRight size={16} />
          </button>

          <button
            onClick={onOpenUpload}
            className="btn-regal"
            style={{ padding: '0.75rem 1.5rem', fontSize: '0.9rem' }}
          >
            <Upload size={16} />
            <span>Load Your Run</span>
          </button>
        </div>

        {/* Animated ECG Pulse Line with Radar Sweep */}
        <div style={{ marginTop: '1rem', borderTop: '1px solid var(--gold-border)', paddingTop: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Observatory Pulse Waveform • Radar Sweep Active
          </div>
          <HeroPulse theme={theme} isAnomaly={false} />
        </div>
      </div>

      {/* Architectural Pillars / Pipeline Cards */}
      <div>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <h2 className="serif-heading" style={{ fontSize: '1.5rem', color: 'var(--gold-primary)', textTransform: 'uppercase' }}>
            Core Engineering Principles
          </h2>
          <div className="double-divider" style={{ maxWidth: '280px', margin: '0.65rem auto 1.25rem auto' }} />
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
            Engineered strictly for production streaming constraints. Zero hindsight adjustments, zero future leakage.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '1.25rem'
        }}>
          {/* Card 1 */}
          <div className="regal-card" style={{ padding: '1.5rem' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '6px',
              background: 'var(--gold-glow)',
              border: '1px solid var(--gold-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--gold-primary)',
              marginBottom: '1rem'
            }}>
              <Shield size={20} />
            </div>
            <h3 className="serif-heading" style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
              Strict Temporal Causality
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.55 }}>
              Each observation is scored against historical statistics <em>before</em> state is updated. No centered rolling windows, no global scalers, and no future leakage.
            </p>
          </div>

          {/* Card 2 */}
          <div className="regal-card" style={{ padding: '1.5rem' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '6px',
              background: 'var(--gold-glow)',
              border: '1px solid var(--gold-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--gold-primary)',
              marginBottom: '1rem'
            }}>
              <Scale size={20} />
            </div>
            <h3 className="serif-heading" style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
              Transparent Evidence
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.55 }}>
              Every flagged event generates a structured evidence payload: prior median baseline, scale factor, deviation magnitude, and threshold rationale.
            </p>
          </div>

          {/* Card 3 */}
          <div className="regal-card" style={{ padding: '1.5rem' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '6px',
              background: 'var(--gold-glow)',
              border: '1px solid var(--gold-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--gold-primary)',
              marginBottom: '1rem'
            }}>
              <Cpu size={20} />
            </div>
            <h3 className="serif-heading" style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
              Microsecond Latency
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.55 }}>
              Executes in pure CPU memory (&lt;30 microseconds per point). Runs smoothly in local environments without heavy server or GPU requirements.
            </p>
          </div>

          {/* Card 4 */}
          <div className="regal-card" style={{ padding: '1.5rem' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '6px',
              background: 'var(--gold-glow)',
              border: '1px solid var(--gold-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--gold-primary)',
              marginBottom: '1rem'
            }}>
              <FileCode2 size={20} />
            </div>
            <h3 className="serif-heading" style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
              Event-Based Evaluation
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.55 }}>
              Evaluates true positive temporal windows, false alarm penalties, and onset-to-trigger delay using the provisional event F1 metric.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
