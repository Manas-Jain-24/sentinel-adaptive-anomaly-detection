import React, { useState } from 'react';
import { X, Upload, FileText, CheckCircle2, RotateCcw, AlertTriangle } from 'lucide-react';
import { parsePredictions, parseRunManifest, parseWindows } from '../lib/parsers';

export function UploadModal({ isOpen, onClose, onApplyCustomRun, onResetDemo }) {
  if (!isOpen) return null;

  const [predictionsText, setPredictionsText] = useState('');
  const [manifestText, setManifestText] = useState('');
  const [windowsText, setWindowsText] = useState('');

  const [predictionsInfo, setPredictionsInfo] = useState(null);
  const [manifestInfo, setManifestInfo] = useState(null);
  const [windowsInfo, setWindowsInfo] = useState(null);

  const [errorMsg, setErrorMsg] = useState('');

  const handleFileUpload = (e, type) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (evt) => {
      const content = evt.target.result;
      try {
        if (type === 'predictions') {
          setPredictionsText(content);
          const parsed = parsePredictions(content);
          setPredictionsInfo({ count: parsed.length, fileName: file.name });
        } else if (type === 'manifest') {
          setManifestText(content);
          const parsed = parseRunManifest(content);
          setManifestInfo({
            algorithm: parsed?.algorithm,
            scope: parsed?.evaluation_scope,
            fileName: file.name
          });
        } else if (type === 'windows') {
          setWindowsText(content);
          const parsed = parseWindows(content);
          setWindowsInfo({ count: parsed.length, fileName: file.name });
        }
        setErrorMsg('');
      } catch (err) {
        setErrorMsg(`Failed to parse ${file.name}: ${err.message}`);
      }
    };
    reader.readAsText(file);
  };

  const handleApply = () => {
    if (!predictionsText) {
      setErrorMsg('Please upload at least a predictions.jsonl file.');
      return;
    }

    const predictions = parsePredictions(predictionsText);
    const manifest = manifestText ? parseRunManifest(manifestText) : null;
    const windows = windowsText ? parseWindows(windowsText) : [];

    if (predictions.length === 0) {
      setErrorMsg('No valid prediction records found in the uploaded file.');
      return;
    }

    onApplyCustomRun({ predictions, manifest, windows });
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      backgroundColor: 'var(--bg-overlay)',
      backdropFilter: 'blur(10px)',
      WebkitBackdropFilter: 'blur(10px)',
      zIndex: 500,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem'
    }}>
      <div className="regal-card" style={{
        maxWidth: '560px',
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto',
        padding: '2rem',
        position: 'relative',
        boxShadow: 'var(--shadow-gold)'
      }}>
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '1.25rem',
            right: '1.25rem',
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer'
          }}
          aria-label="Close upload modal"
        >
          <X size={20} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
          <Upload size={22} style={{ color: 'var(--gold-primary)' }} />
          <h2 className="serif-heading" style={{ fontSize: '1.35rem', color: 'var(--text-primary)' }}>
            Load Execution Run
          </h2>
        </div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          Select or drag your Sentinel Pulse output artifacts below. Processing and visualization occur strictly client-side.
        </p>

        {errorMsg && (
          <div style={{
            padding: '0.65rem 0.85rem',
            borderRadius: '4px',
            backgroundColor: 'var(--crimson-bg)',
            border: '1px solid var(--crimson-border)',
            color: 'var(--crimson-light)',
            fontSize: '0.78rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '1rem'
          }}>
            <AlertTriangle size={15} />
            <span>{errorMsg}</span>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.75rem' }}>
          {/* File Picker 1: predictions.jsonl */}
          <div style={{
            padding: '1rem',
            border: '1px dashed var(--gold-border-strong)',
            borderRadius: '6px',
            background: 'var(--bg-surface)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                1. predictions.jsonl <span style={{ color: 'var(--crimson-light)' }}>*</span>
              </span>
              {predictionsInfo && (
                <span className="pill-badge pill-normal" style={{ fontSize: '0.65rem' }}>
                  <CheckCircle2 size={12} />
                  {predictionsInfo.count} rows loaded
                </span>
              )}
            </div>
            <input
              type="file"
              accept=".jsonl,.txt"
              onChange={(e) => handleFileUpload(e, 'predictions')}
              style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}
            />
          </div>

          {/* File Picker 2: run.json */}
          <div style={{
            padding: '1rem',
            border: '1px dashed var(--gold-border)',
            borderRadius: '6px',
            background: 'var(--bg-surface)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                2. run.json (Manifest metadata)
              </span>
              {manifestInfo && (
                <span className="pill-badge pill-scope" style={{ fontSize: '0.65rem' }}>
                  {manifestInfo.scope}
                </span>
              )}
            </div>
            <input
              type="file"
              accept=".json"
              onChange={(e) => handleFileUpload(e, 'manifest')}
              style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}
            />
          </div>

          {/* File Picker 3: windows.json */}
          <div style={{
            padding: '1rem',
            border: '1px dashed var(--gold-border)',
            borderRadius: '6px',
            background: 'var(--bg-surface)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                3. windows.json (Optional Ground Truth)
              </span>
              {windowsInfo && (
                <span className="pill-badge pill-normal" style={{ fontSize: '0.65rem' }}>
                  {windowsInfo.count} windows
                </span>
              )}
            </div>
            <input
              type="file"
              accept=".json"
              onChange={(e) => handleFileUpload(e, 'windows')}
              style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}
            />
          </div>
        </div>

        {/* Buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => {
              onResetDemo();
              onClose();
            }}
            className="btn-regal"
            style={{ fontSize: '0.78rem' }}
          >
            <RotateCcw size={14} />
            <span>Reset to Demo Run</span>
          </button>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={onClose}
              className="btn-regal"
              style={{ fontSize: '0.78rem' }}
            >
              Cancel
            </button>
            <button
              onClick={handleApply}
              className="btn-regal btn-regal-primary"
              style={{ fontSize: '0.78rem' }}
            >
              Apply Run
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
