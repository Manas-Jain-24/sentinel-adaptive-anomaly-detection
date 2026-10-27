import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useRunData } from "./hooks/useRunData";
import { useReplay } from "./hooks/useReplay";
import { BackgroundGrid } from "./components/BackgroundGrid";
import { BootSequence } from "./components/BootSequence";
import { RailNav } from "./components/RailNav";
import { TopBar } from "./components/TopBar";
import { UploadModal, HelpModal } from "./components/ManifestView";

// Views
import { OverviewView } from "./views/OverviewView";
import { StreamViewerView } from "./views/StreamViewerView";
import { EvidenceView } from "./views/EvidenceView";
import { ComparisonView } from "./views/ComparisonView";
import { ManifestView } from "./views/ManifestView";
import { FiguresView } from "./views/FiguresView";

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [projectorMode, setProjectorMode] = useState(false);
  const [bootDone, setBootDone] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [capturedFigures, setCapturedFigures] = useState([]);

  const {
    loading,
    error,
    predictions,
    predictionsRaw,
    runManifest,
    windows,
    evaluation,
    modelResults,
    sourceName,
    selectedSeries,
    setSelectedSeries,
    seriesList,
    loadCustomFiles
  } = useRunData();

  const handleOpenEvidence = () => {
    setActiveTab("evidence");
  };

  const replay = useReplay(predictions, handleOpenEvidence);

  const handleSelectPointFromChart = (point) => {
    setSelectedPoint(point);
    if (point.label === "ANOMALOUS") {
      setActiveTab("evidence");
    }
  };

  const handleCaptureFigure = (fig) => {
    setCapturedFigures(prev => [fig, ...prev]);
  };

  // Derive KPIs for Overview
  const kpis = {
    observations: runManifest?.observations ?? predictions.length,
    ready_observations: runManifest?.ready_observations ?? predictions.filter(p => p.ready).length,
    anomalies_count: predictions.filter(p => p.label === "ANOMALOUS").length,
    tp: evaluation?.tp ?? null,
    fp: evaluation?.fp ?? null,
    fn: evaluation?.fn ?? null,
    precision: evaluation?.precision ?? null,
    recall: evaluation?.recall ?? null,
    event_f1: evaluation?.event_f1 ?? null,
    mean_latency_us: runManifest?.detector_total_ns && runManifest?.observations
      ? runManifest.detector_total_ns / (runManifest.observations * 1000)
      : null,
    p95_latency_us: null,
    p95_delay_seconds: evaluation?.p95_delay_seconds ?? null
  };

  return (
    <div className={projectorMode ? "projector-mode" : ""} style={{ minHeight: "100vh", display: "flex", position: "relative" }}>
      {/* Background Interactive Dot Grid */}
      <BackgroundGrid />

      {/* Initial Boot Sequence (~1.5s) */}
      {!bootDone && <BootSequence onComplete={() => setBootDone(true)} />}

      {/* Left Vertical Rail Navigation */}
      <RailNav
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        projectorMode={projectorMode}
        setProjectorMode={setProjectorMode}
        onOpenHelp={() => setIsHelpOpen(true)}
      />

      {/* Main Terminal Stage */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, zIndex: 10 }}>
        {/* Top Header Bar */}
        <TopBar
          runManifest={runManifest}
          sourceName={sourceName}
          onOpenUpload={() => setIsUploadOpen(true)}
        />

        {/* View Container */}
        <main style={{ flex: 1, padding: "28px 32px", overflowY: "auto" }}>
          {error && (
            <div style={{ padding: "14px 18px", borderRadius: "4px", background: "rgba(255,77,94,0.15)", border: "1px solid var(--red-anomaly)", color: "var(--red-anomaly)", marginBottom: "20px", fontSize: "0.85rem" }}>
              <strong>Error:</strong> {error}
            </div>
          )}

          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
            >
              {activeTab === "overview" && (
                <OverviewView onNavigate={setActiveTab} kpis={kpis} predictions={predictions} />
              )}

              {activeTab === "stream" && (
                <StreamViewerView
                  predictions={predictions}
                  windows={windows}
                  replay={replay}
                  onSelectPoint={handleSelectPointFromChart}
                  onCaptureFigure={handleCaptureFigure}
                  runMetadata={{
                    run_id: runManifest?.dataset_id,
                    scope: runManifest?.evaluation_scope
                  }}
                  selectedSeries={selectedSeries}
                  setSelectedSeries={setSelectedSeries}
                  seriesList={seriesList}
                />
              )}

              {activeTab === "evidence" && (
                <EvidenceView
                  predictions={predictions}
                  windows={windows}
                  selectedPoint={selectedPoint}
                  onSelectPoint={setSelectedPoint}
                />
              )}

              {activeTab === "comparison" && (
                <ComparisonView
                  results={modelResults}
                  onSelectRun={(m) => {
                    setActiveTab("stream");
                  }}
                />
              )}

              {activeTab === "manifest" && (
                <ManifestView
                  runManifest={runManifest}
                  predictions={predictions}
                  predictionsRaw={predictionsRaw}
                />
              )}

              {activeTab === "figures" && (
                <FiguresView
                  figures={capturedFigures}
                />
              )}
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Provenance footer */}
        <footer style={{ padding: "12px 32px", borderTop: "1px solid var(--panel-border)", background: "rgba(5, 7, 10, 0.9)", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.72rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
          <span>Software demonstration on synthetic data. Not an official or NAB result. Metric is provisional.</span>
          <span>Utkrishta 2026 · Challenge 2: Sentinel · Sentinel Pulse project</span>
        </footer>
      </div>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUpload={loadCustomFiles}
      />

      {/* Help Modal */}
      <HelpModal
        isOpen={isHelpOpen}
        onClose={() => setIsHelpOpen(false)}
      />
    </div>
  );
}