import React, { useState, useEffect, useCallback } from 'react';
import { useTheme } from './hooks/useTheme';
import { useReplay } from './hooks/useReplay';
import { parsePredictions, parseRunManifest, parseWindows } from './lib/parsers';

import { BackgroundCanvas } from './components/BackgroundCanvas';
import { Navbar } from './components/Navbar';
import { OverviewTab } from './components/OverviewTab';
import { ReplayTab } from './components/ReplayTab';
import { EvaluationTab } from './components/EvaluationTab';
import { ExperimentsTab } from './components/ExperimentsTab';
import { ManifestTab } from './components/ManifestTab';
import { TeamTab } from './components/TeamTab';
import { UploadModal } from './components/UploadModal';
import { Footer } from './components/Footer';
import { Toast } from './components/Toast';

export function App() {
  const { theme, toggleTheme } = useTheme();

  const [activeTab, setActiveTab] = useState('overview');
  const [predictions, setPredictions] = useState([]);
  const [manifest, setManifest] = useState(null);
  const [windows, setWindows] = useState([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isAnomalyFlare, setIsAnomalyFlare] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const showToast = useCallback((msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3000);
  }, []);

  // Anomaly flare animation callback
  const handleAnomalyFlare = useCallback(() => {
    setIsAnomalyFlare(true);
    setTimeout(() => setIsAnomalyFlare(false), 900);
  }, []);

  // Initialize playback replay hook
  const replayState = useReplay(predictions, handleAnomalyFlare);

  // Load bundled demo artifacts on startup
  const loadBundledDemo = useCallback(async () => {
    setIsLoading(true);
    try {
      const [predRes, manRes, winRes] = await Promise.all([
        fetch('/demo/predictions.jsonl').then(r => r.text()),
        fetch('/demo/run.json').then(r => r.text()),
        fetch('/demo/windows.json').then(r => r.text()).catch(() => '')
      ]);

      const parsedPreds = parsePredictions(predRes);
      const parsedMan = parseRunManifest(manRes);
      const parsedWins = parseWindows(winRes);

      setPredictions(parsedPreds);
      setManifest(parsedMan);
      setWindows(parsedWins);
    } catch (err) {
      console.error('[Sentinel Pulse] Failed to load bundled demo:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBundledDemo();
  }, [loadBundledDemo]);

  // Apply custom uploaded run
  const handleApplyCustomRun = ({ predictions: customPreds, manifest: customMan, windows: customWins }) => {
    setPredictions(customPreds);
    if (customMan) setManifest(customMan);
    if (customWins && customWins.length > 0) setWindows(customWins);
    replayState.seekTo(0);
    showToast(`Loaded ${customPreds.length} observations!`);
  };

  const scope = manifest?.evaluation_scope || 'synthetic_smoke';

  return (
    <div style={{
      position: 'relative',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 1
    }}>
      {/* 1. Full-screen Constellation Background */}
      <BackgroundCanvas theme={theme} />

      {/* 2. Sticky Glass Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        theme={theme}
        toggleTheme={toggleTheme}
        onOpenUpload={() => setIsUploadOpen(true)}
        scope={scope}
      />

      {/* 3. Main Content Container */}
      <main style={{
        flex: 1,
        maxWidth: '1440px',
        width: '100%',
        margin: '0 auto',
        padding: '2rem 1.5rem',
        position: 'relative',
        zIndex: 2
      }}>
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '5rem 0', color: 'var(--gold-primary)', fontFamily: 'var(--font-serif)' }}>
            <div style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Synchronizing Sentinel Observatory...</div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Loading causal streaming artifacts</p>
          </div>
        ) : (
          <>
            {activeTab === 'overview' && (
              <OverviewTab
                onGoToReplay={() => setActiveTab('replay')}
                onOpenUpload={() => setIsUploadOpen(true)}
                theme={theme}
              />
            )}

            {activeTab === 'replay' && (
              <ReplayTab
                replayState={replayState}
                theme={theme}
              />
            )}

            {activeTab === 'evaluation' && (
              <EvaluationTab
                predictions={predictions}
                windows={windows}
                scope={scope}
              />
            )}

            {activeTab === 'experiments' && (
              <ExperimentsTab
                currentRun={manifest}
                onOpenUpload={() => setIsUploadOpen(true)}
              />
            )}

            {activeTab === 'manifest' && (
              <ManifestTab
                manifest={manifest}
                onShowToast={showToast}
              />
            )}

            {activeTab === 'team' && (
              <TeamTab />
            )}
          </>
        )}
      </main>

      {/* 4. Footer */}
      <Footer scope={scope} />

      {/* 5. Upload Modal & Toast */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onApplyCustomRun={handleApplyCustomRun}
        onResetDemo={loadBundledDemo}
      />

      <Toast message={toastMessage} />
    </div>
  );
}
