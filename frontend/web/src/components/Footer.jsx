import React from 'react';
import { Shield, ExternalLink } from 'lucide-react';

export function Footer({ scope = 'synthetic_smoke' }) {
  return (
    <footer style={{
      marginTop: 'auto',
      width: '100%',
      borderTop: '1px solid var(--gold-border)',
      background: 'var(--bg-card)',
      backdropFilter: 'blur(12px)',
      padding: '1.5rem',
      fontSize: '0.78rem',
      color: 'var(--text-muted)'
    }}>
      <div style={{
        maxWidth: '1440px',
        margin: '0 auto',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        {/* Left: Project & Challenge Attribution */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Shield size={16} style={{ color: 'var(--gold-primary)' }} />
          <span>
            <strong>Sentinel Pulse</strong> • Utkrishta 2026 AI/ML Hackathon (Challenge 2: Sentinel)
          </span>
        </div>

        {/* Center: Strict Honesty Disclosure */}
        <div style={{
          textAlign: 'center',
          color: 'var(--text-secondary)',
          fontStyle: 'italic',
          background: 'rgba(201, 162, 75, 0.05)',
          padding: '0.35rem 0.85rem',
          borderRadius: '4px',
          border: '1px solid var(--gold-border)'
        }}>
          Provisional metric. Software wiring demonstration, not an official evaluation.
        </div>

        {/* Right: Data Scope Pill Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="pill-badge pill-scope" style={{ fontSize: '0.68rem' }}>
            Data Scope: {scope}
          </span>
        </div>
      </div>
    </footer>
  );
}
