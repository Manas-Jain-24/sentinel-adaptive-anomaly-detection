import React, { useState } from 'react';
import { Layers, Sparkles, Plus, CheckCircle, ArrowRight, Shield, Clock, Target } from 'lucide-react';

export function ExperimentsTab({ currentRun, onOpenUpload }) {
  // Built-in benchmark comparison data reflecting the Level B research blueprint
  const plannedExperiments = [
    {
      id: 'EXP-00-baseline',
      name: 'Rolling MAD Starter',
      category: 'Foundation (Current)',
      features: 'Univariate Rolling History (W=32, min_history=8)',
      scoring: 'Absolute standardized deviation from rolling median',
      threshold: 'Static 4.0x MAD',
      f1: '1.000 (synthetic)',
      latency: '22 µs',
      status: 'VERIFIED_STARTER',
      notes: 'Current runnable baseline in main. Bounded CPU state.'
    },
    {
      id: 'EXP-01-seasonal',
      name: 'Causal Seasonal-Naive Residual',
      category: 'Planned Level B',
      features: 'Pre-update seasonal expectation + Level residual',
      scoring: 'Bounded max-combination of level and delta',
      threshold: 'Causal empirical quantile calibration',
      f1: 'Pending Level B',
      latency: '~35 µs (projected)',
      status: 'PLANNED',
      notes: 'Tests whether periodic context reduces false alarms on periodic series.'
    },
    {
      id: 'EXP-02-adaptive-ensemble',
      name: 'Guarded Adaptive Ensemble',
      category: 'Planned Level B',
      features: 'Level + Delta + Seasonal residuals with quarantine',
      scoring: 'Residual magnitude with capped influence update',
      threshold: 'Online sliding-window adaptive threshold',
      f1: 'Pending Level B',
      latency: '~60 µs (projected)',
      status: 'PLANNED',
      notes: 'Combines multiple past-only residual branches with shadow drift protection.'
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', width: '100%' }}>
      {/* Level B Ribbon Banner */}
      <div className="regal-card" style={{
        padding: '1.5rem',
        position: 'relative',
        overflow: 'hidden',
        borderLeft: '4px solid var(--gold-primary)'
      }}>
        {/* Decorative Watermark Ribbon */}
        <div style={{
          position: 'absolute',
          top: '16px',
          right: '-32px',
          transform: 'rotate(45deg)',
          backgroundColor: 'var(--gold-primary)',
          color: '#070B14',
          fontFamily: 'var(--font-serif)',
          fontSize: '0.68rem',
          fontWeight: 700,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          padding: '0.25rem 2.5rem',
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          pointerEvents: 'none'
        }}>
          Level B Planned
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
          <Sparkles size={20} style={{ color: 'var(--gold-primary)' }} />
          <h2 className="serif-heading" style={{ fontSize: '1.25rem', color: 'var(--text-primary)' }}>
            Comparative Experiment Harness
          </h2>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', maxWidth: '750px', lineHeight: 1.55 }}>
          The Level B research roadmap systematically compares candidate detectors on frozen, group-held-out splits.
          The current foundation establishes the verified <strong>Rolling MAD Starter</strong>. Future candidates will be integrated
          as independent, causal modules without disturbing the shared interface.
        </p>
      </div>

      {/* Model Comparison Table */}
      <div className="regal-card" style={{ padding: '1.5rem', overflowX: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h3 className="serif-heading" style={{ fontSize: '1.1rem', color: 'var(--text-primary)' }}>
              Candidate Architecture Trajectory
            </h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Ablation candidates and performance targets under Challenge 2 guidelines.
            </p>
          </div>

          <button
            onClick={onOpenUpload}
            className="btn-regal"
            style={{ fontSize: '0.78rem', padding: '0.45rem 0.85rem' }}
          >
            <Plus size={14} />
            <span>Load Additional Run</span>
          </button>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--gold-border)', textAlign: 'left', color: 'var(--gold-primary)', fontFamily: 'var(--font-serif)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
              <th style={{ padding: '0.75rem 0.6rem' }}>Model / Experiment</th>
              <th style={{ padding: '0.75rem 0.6rem' }}>Feature Representation</th>
              <th style={{ padding: '0.75rem 0.6rem' }}>Scoring Logic</th>
              <th style={{ padding: '0.75rem 0.6rem' }}>Adaptive Threshold</th>
              <th style={{ padding: '0.75rem 0.6rem' }}>Latency</th>
              <th style={{ padding: '0.75rem 0.6rem' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {plannedExperiments.map((exp) => (
              <tr key={exp.id} style={{ borderBottom: '1px solid rgba(201, 162, 75, 0.12)' }}>
                <td style={{ padding: '0.85rem 0.6rem' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-serif)', fontSize: '0.9rem' }}>
                    {exp.name}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--gold-light)', fontFamily: 'var(--font-mono)' }}>
                    {exp.id} • {exp.category}
                  </div>
                </td>
                <td style={{ padding: '0.85rem 0.6rem', color: 'var(--text-secondary)' }}>
                  {exp.features}
                </td>
                <td style={{ padding: '0.85rem 0.6rem', color: 'var(--text-secondary)' }}>
                  {exp.scoring}
                </td>
                <td style={{ padding: '0.85rem 0.6rem', color: 'var(--text-secondary)' }}>
                  {exp.threshold}
                </td>
                <td style={{ padding: '0.85rem 0.6rem', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                  {exp.latency}
                </td>
                <td style={{ padding: '0.85rem 0.6rem' }}>
                  <span className={`pill-badge ${exp.status === 'VERIFIED_STARTER' ? 'pill-normal' : 'pill-warmup'}`} style={{ fontSize: '0.68rem' }}>
                    {exp.status === 'VERIFIED_STARTER' ? 'ACTIVE STARTER' : 'IN ROADMAP'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Level B Promotion Gates Card */}
      <div className="regal-card" style={{ padding: '1.5rem' }}>
        <h3 className="serif-heading" style={{ fontSize: '1.1rem', color: 'var(--gold-primary)', marginBottom: '0.75rem', textTransform: 'uppercase' }}>
          Level B Promotion Gates (PRD §4.3)
        </h3>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
          To prevent unnecessary architectural bloat, candidate detectors must pass four verified gates before replacing the baseline:
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
          <div style={{ padding: '1rem', background: 'var(--bg-surface)', border: '1px solid var(--gold-border)', borderRadius: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem', color: 'var(--gold-primary)', fontWeight: 600 }}>
              <Shield size={16} />
              Gate 1: Causal Isolation
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Zero future leakage. Prefix replay decisions must remain bitwise identical when future observations are appended.
            </div>
          </div>

          <div style={{ padding: '1rem', background: 'var(--bg-surface)', border: '1px solid var(--gold-border)', borderRadius: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem', color: 'var(--gold-primary)', fontWeight: 600 }}>
              <Target size={16} />
              Gate 2: Event F1 Superiority
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Must achieve a statistically defensible improvement in event F1 on held-out group splits over the rolling MAD starter.
            </div>
          </div>

          <div style={{ padding: '1rem', background: 'var(--bg-surface)', border: '1px solid var(--gold-border)', borderRadius: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem', color: 'var(--gold-primary)', fontWeight: 600 }}>
              <Clock size={16} />
              Gate 3: Microsecond Budget
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Per-window inference latency must remain bounded under 100 microseconds on CPU without unbounded memory consumption.
            </div>
          </div>

          <div style={{ padding: '1rem', background: 'var(--bg-surface)', border: '1px solid var(--gold-border)', borderRadius: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem', color: 'var(--gold-primary)', fontWeight: 600 }}>
              <CheckCircle size={16} />
              Gate 4: Schema Parity
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Must produce identical output schemas and numerical evidence fields consumable by the official exporter.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
