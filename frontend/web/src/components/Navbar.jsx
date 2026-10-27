import React from 'react';
import { Shield, Sun, Moon, Upload, Activity, Layers, BarChart2, FileText, Users, Eye } from 'lucide-react';

export function Navbar({ activeTab, setActiveTab, theme, toggleTheme, onOpenUpload, scope = 'synthetic_smoke' }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: Eye },
    { id: 'replay', label: 'Live Replay', icon: Activity },
    { id: 'evaluation', label: 'Event Evaluation', icon: BarChart2 },
    { id: 'experiments', label: 'Experiments', icon: Layers },
    { id: 'manifest', label: 'Run Manifest', icon: FileText },
    { id: 'team', label: 'Team & About', icon: Users },
  ];

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      width: '100%',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      background: 'var(--bg-card)',
      borderBottom: '1px solid var(--gold-border)',
      boxShadow: 'var(--shadow-subtle)',
    }}>
      <div style={{
        maxWidth: '1440px',
        margin: '0 auto',
        padding: '0.75rem 1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
        flexWrap: 'wrap'
      }}>
        {/* Brand Crest & Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '6px',
            background: 'linear-gradient(135deg, rgba(201, 162, 75, 0.2) 0%, rgba(201, 162, 75, 0.05) 100%)',
            border: '1px solid var(--gold-border-strong)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--gold-primary)',
            boxShadow: 'var(--shadow-gold)'
          }}>
            <Shield size={22} strokeWidth={2.2} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <span className="serif-heading" style={{
                fontSize: '1.25rem',
                fontWeight: 700,
                letterSpacing: '0.12em',
                color: 'var(--text-primary)',
                textTransform: 'uppercase'
              }}>
                Sentinel Pulse
              </span>
              <span className="pill-badge pill-scope" style={{ fontSize: '0.68rem', padding: '0.15rem 0.5rem' }}>
                <span style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--gold-primary)',
                  display: 'inline-block'
                }}></span>
                {scope}
              </span>
            </div>
            <p style={{
              fontSize: '0.72rem',
              color: 'var(--text-muted)',
              letterSpacing: '0.05em',
              textTransform: 'uppercase'
            }}>
              Causal Streaming Anomaly Detection • Utkrishta '26 (Ch 2)
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', flexWrap: 'wrap' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  position: 'relative',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  padding: '0.5rem 0.85rem',
                  fontSize: '0.82rem',
                  fontWeight: isActive ? 600 : 500,
                  fontFamily: 'var(--font-serif)',
                  letterSpacing: '0.04em',
                  color: isActive ? 'var(--gold-primary)' : 'var(--text-secondary)',
                  background: isActive ? 'rgba(201, 162, 75, 0.12)' : 'transparent',
                  border: isActive ? '1px solid var(--gold-border)' : '1px solid transparent',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)'
                }}
              >
                <Icon size={15} strokeWidth={isActive ? 2.2 : 1.8} />
                <span>{item.label}</span>
                {isActive && (
                  <span style={{
                    position: 'absolute',
                    bottom: '-1px',
                    left: '15%',
                    right: '15%',
                    height: '2px',
                    backgroundColor: 'var(--gold-primary)',
                    boxShadow: '0 0 8px var(--gold-primary)'
                  }} />
                )}
              </button>
            );
          })}
        </nav>

        {/* Action Controls: Load Run & Theme Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <button
            onClick={onOpenUpload}
            className="btn-regal"
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.78rem' }}
            title="Load your custom run.json or predictions.jsonl"
          >
            <Upload size={14} />
            <span>Load Run</span>
          </button>

          <button
            onClick={toggleTheme}
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '4px',
              background: 'transparent',
              border: '1px solid var(--gold-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--gold-primary)',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)'
            }}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
          </button>
        </div>
      </div>
    </header>
  );
}
