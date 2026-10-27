import React, { useState } from 'react';
import { Copy, Check, FileText, Hash, Settings, Cpu, HardDrive, Terminal } from 'lucide-react';

export function ManifestTab({ manifest, onShowToast }) {
  const [copiedKey, setCopiedKey] = useState(null);
  const [showRaw, setShowRaw] = useState(false);

  if (!manifest) {
    return (
      <div className="regal-card" style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>No run manifest loaded.</p>
      </div>
    );
  }

  const handleCopy = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    if (onShowToast) onShowToast(`Copied ${key} to clipboard!`);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const totalTimeMicros = (manifest.detector_total_ns / 1000).toFixed(1);
  const avgPointMicros = manifest.observations > 0
    ? (manifest.detector_total_ns / manifest.observations / 1000).toFixed(2)
    : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', width: '100%' }}>
      {/* Header Banner */}
      <div className="regal-card" style={{ padding: '1.5rem', borderLeft: '4px solid var(--gold-primary)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
              <span className="serif-heading" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Run Manifest & Audit Trail
              </span>
              <span className="pill-badge pill-scope" style={{ fontSize: '0.72rem' }}>
                {manifest.evaluation_scope}
              </span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
              Algorithm: <strong>{manifest.algorithm}</strong> • Schema: v{manifest.schema_version} • Sentinel Pulse v{manifest.package_version}
            </p>
          </div>

          <button
            onClick={() => setShowRaw(prev => !prev)}
            className="btn-regal"
            style={{ fontSize: '0.78rem', padding: '0.45rem 0.85rem' }}
          >
            <Terminal size={14} />
            <span>{showRaw ? 'Structured View' : 'Raw JSON'}</span>
          </button>
        </div>
      </div>

      {showRaw ? (
        /* Raw JSON Display */
        <div className="regal-card" style={{ padding: '1.5rem' }}>
          <pre className="mono-num" style={{
            fontSize: '0.8rem',
            color: 'var(--gold-light)',
            overflowX: 'auto',
            background: 'var(--bg-surface)',
            padding: '1.25rem',
            borderRadius: '6px',
            border: '1px solid var(--gold-border)'
          }}>
            {JSON.stringify(manifest, null, 2)}
          </pre>
        </div>
      ) : (
        <>
          {/* Cryptographic Checksums Card */}
          <div className="regal-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Hash size={18} style={{ color: 'var(--gold-primary)' }} />
              <h3 className="serif-heading" style={{ fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                Immutable Cryptographic Checksums
              </h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
              {/* Input SHA-256 */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.75rem 1rem',
                background: 'var(--bg-surface)',
                borderRadius: '6px',
                border: '1px solid var(--gold-border)',
                flexWrap: 'wrap',
                gap: '0.5rem'
              }}>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Input Stream SHA-256</div>
                  <div style={{ color: 'var(--text-primary)', wordBreak: 'break-all' }}>{manifest.input_sha256}</div>
                </div>
                <button
                  onClick={() => handleCopy(manifest.input_sha256, 'input_sha256')}
                  className="btn-regal"
                  style={{ padding: '0.35rem 0.65rem', fontSize: '0.72rem' }}
                  title="Copy SHA-256 to clipboard"
                >
                  {copiedKey === 'input_sha256' ? <Check size={14} style={{ color: 'var(--teal-normal)' }} /> : <Copy size={14} />}
                  <span>{copiedKey === 'input_sha256' ? 'Copied' : 'Copy'}</span>
                </button>
              </div>

              {/* Predictions SHA-256 */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.75rem 1rem',
                background: 'var(--bg-surface)',
                borderRadius: '6px',
                border: '1px solid var(--gold-border)',
                flexWrap: 'wrap',
                gap: '0.5rem'
              }}>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Predictions Artifact SHA-256</div>
                  <div style={{ color: 'var(--text-primary)', wordBreak: 'break-all' }}>{manifest.predictions_sha256}</div>
                </div>
                <button
                  onClick={() => handleCopy(manifest.predictions_sha256, 'predictions_sha256')}
                  className="btn-regal"
                  style={{ padding: '0.35rem 0.65rem', fontSize: '0.72rem' }}
                  title="Copy SHA-256 to clipboard"
                >
                  {copiedKey === 'predictions_sha256' ? <Check size={14} style={{ color: 'var(--teal-normal)' }} /> : <Copy size={14} />}
                  <span>{copiedKey === 'predictions_sha256' ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Configuration & Pipeline Settings Card */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '1.25rem'
          }}>
            {/* Detector Config */}
            <div className="regal-card" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <Settings size={18} style={{ color: 'var(--gold-primary)' }} />
                <h3 className="serif-heading" style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                  Detector Parameters
                </h3>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--gold-border)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Rolling Window Size:</span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{manifest.config.window_size}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--gold-border)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Minimum History (Warmup):</span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{manifest.config.min_history} points</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--gold-border)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Decision Threshold:</span>
                  <span style={{ color: 'var(--gold-light)', fontWeight: 600 }}>{manifest.config.threshold.toFixed(1)}x MAD</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--gold-border)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Scale Floor (min scale):</span>
                  <span style={{ color: 'var(--text-primary)' }}>{manifest.config.scale_floor}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Max Active Series Bounded:</span>
                  <span style={{ color: 'var(--text-primary)' }}>{manifest.config.max_series}</span>
                </div>
              </div>
            </div>

            {/* Execution Provenance */}
            <div className="regal-card" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <Cpu size={18} style={{ color: 'var(--gold-primary)' }} />
                <h3 className="serif-heading" style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                  Execution Provenance
                </h3>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--gold-border)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Total In-Process Time:</span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{totalTimeMicros} µs ({manifest.detector_total_ns} ns)</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--gold-border)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Average Latency Per Point:</span>
                  <span style={{ color: 'var(--teal-normal)', fontWeight: 600 }}>{avgPointMicros} µs / point</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--gold-border)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Python Version:</span>
                  <span style={{ color: 'var(--text-primary)' }}>{manifest.python}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--gold-border)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Host Platform:</span>
                  <span style={{ color: 'var(--text-primary)' }}>{manifest.platform}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Official Submission Ready:</span>
                  <span style={{ color: manifest.official_submission_ready ? 'var(--teal-normal)' : 'var(--amber-warn)' }}>
                    {manifest.official_submission_ready ? 'YES' : 'NO (Starter Only)'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
