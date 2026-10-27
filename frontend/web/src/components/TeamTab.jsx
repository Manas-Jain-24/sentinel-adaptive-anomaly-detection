import React from 'react';
import { Users, ExternalLink, Shield, Code, Award, CheckCircle } from 'lucide-react';

export function TeamTab() {
  const teamMembers = [
    {
      name: 'Ayush',
      role: 'Core Integration & Systems Lead',
      ownership: 'CLI, streaming orchestration, persistence, export, contracts, CI & integration records.',
      files: 'pipeline.py, cli.py, config.py, contracts.py, tests/test_foundation.py',
      badge: 'Architecture & CI'
    },
    {
      name: 'Kaustubh',
      role: 'Data Engineering & Feature Specialist',
      ownership: 'Dataset adaptation, canonical ingestion, causal feature extractors, split & provenance manifests.',
      files: 'src/sentinel/data/, tests/data/, data/official/ adapters',
      badge: 'Data & Features'
    },
    {
      name: 'Manas',
      role: 'Detection & ML Research Engineer',
      ownership: 'Detection baselines, residual scoring, calibration, adaptive thresholds & guarded adaptation.',
      files: 'src/sentinel/detectors/, tests/detectors/, models/ baseline',
      badge: 'Anomaly Models'
    },
    {
      name: 'Mayank',
      role: 'Evaluation & Visualization Engineer',
      ownership: 'Event-based evaluation, golden matching tests, experiment harness, result visualization & demo.',
      files: 'src/sentinel/evaluation/, tests/evaluation/, frontend/web/, experiments/',
      badge: 'Evaluation & UI'
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem', width: '100%' }}>
      {/* Header Banner */}
      <div className="regal-card" style={{ padding: '2rem', textAlign: 'center', position: 'relative' }}>
        <h2 className="serif-heading" style={{ fontSize: '1.75rem', color: 'var(--text-primary)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
          Sentinel Engineering Team
        </h2>
        <p className="serif-heading" style={{ fontSize: '1rem', color: 'var(--gold-primary)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '1.25rem' }}>
          Utkrishta 2026 • Challenge 2: Sentinel
        </p>
        <p style={{ maxWidth: '680px', margin: '0 auto', fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          Four engineers with rigorous boundary separation and durable handoff protocols.
          Building a causal, interpretable, lightweight time-series anomaly detection system for streaming environments.
        </p>

        <div style={{ marginTop: '1.5rem' }}>
          <a
            href="https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-regal btn-regal-primary"
            style={{ fontSize: '0.85rem' }}
          >
            <Code size={16} />
            <span>View GitHub Repository</span>
            <ExternalLink size={14} />
          </a>
        </div>
      </div>

      {/* 4 Developer Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '1.25rem'
      }}>
        {teamMembers.map((member) => (
          <div key={member.name} className="regal-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
              <div>
                <h3 className="serif-heading" style={{ fontSize: '1.25rem', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  {member.name}
                </h3>
                <div style={{ fontSize: '0.75rem', color: 'var(--gold-primary)', fontWeight: 600 }}>
                  {member.role}
                </div>
              </div>

              <span className="pill-badge pill-scope" style={{ fontSize: '0.65rem' }}>
                {member.badge}
              </span>
            </div>

            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '1.25rem', flex: 1 }}>
              {member.ownership}
            </p>

            <div style={{
              borderTop: '1px solid var(--gold-border)',
              paddingTop: '0.75rem',
              fontSize: '0.72rem',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)'
            }}>
              <span style={{ color: 'var(--gold-light)' }}>Owned Modules:</span> {member.files}
            </div>
          </div>
        ))}
      </div>

      {/* Challenge Track Background Card */}
      <div className="regal-card" style={{ padding: '1.75rem' }}>
        <h3 className="serif-heading" style={{ fontSize: '1.15rem', color: 'var(--gold-primary)', marginBottom: '0.75rem', textTransform: 'uppercase' }}>
          About Utkrishta Challenge 2: Sentinel
        </h3>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <p>
            The official objective is baseline learning from streaming time-series data and identifying observations
            or windows that deviate significantly. For every flagged event, the system produces continuous anomaly scores,
            a binary <code style={{ color: 'var(--gold-light)' }}>NORMAL/ANOMALOUS</code> label, and interpretable evidence explaining the flag.
          </p>
          <p>
            <strong>Track Specifications:</strong> Numenta Anomaly Benchmark (NAB) subset with hidden test windows.
            Evaluated on primary <em>Event-Based F1 Score</em>, precision, recall, detection delay (onset to trigger latency),
            and streaming inference runtime.
          </p>
        </div>
      </div>
    </div>
  );
}
