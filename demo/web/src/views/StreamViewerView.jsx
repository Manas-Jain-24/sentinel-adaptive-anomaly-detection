// StreamViewerView.jsx
import { SyncedChart } from "../components/SyncedChart";
import { ReplayBar } from "../components/ReplayBar";

export function StreamViewerView({
  predictions = [],
  windows = [],
  replay,
  onSelectPoint,
  onCaptureFigure,
  runMetadata,
  selectedSeries,
  setSelectedSeries,
  seriesList = []
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Series Selector Bar */}
      {seriesList.length > 1 && (
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color: "var(--text-dim)" }}>
            SERIES SELECTOR:
          </span>
          <div style={{ display: "flex", gap: "6px" }}>
            {seriesList.map(s => (
              <button
                key={s}
                onClick={() => setSelectedSeries(s)}
                className="btn-precision"
                style={{
                  padding: "4px 10px",
                  fontSize: "0.72rem",
                  borderColor: selectedSeries === s ? "var(--cyan-signal)" : "var(--panel-border)",
                  color: selectedSeries === s ? "var(--cyan-signal)" : "var(--text-muted)"
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Dual-Canvas Synchronized Chart */}
      <SyncedChart
        predictions={predictions}
        windows={windows}
        currentIndex={replay.currentIndex}
        causalMode={replay.causalMode}
        onSelectPoint={onSelectPoint}
        onCaptureFigure={onCaptureFigure}
        runMetadata={runMetadata}
      />

      {/* Replay Controller Bar */}
      <ReplayBar
        isPlaying={replay.isPlaying}
        onTogglePlay={() => replay.setIsPlaying(p => !p)}
        onStepForward={replay.stepForward}
        onStepBackward={replay.stepBackward}
        onPrevAnomaly={() => replay.jumpToAnomaly("prev")}
        onNextAnomaly={() => replay.jumpToAnomaly("next")}
        speed={replay.speed}
        onChangeSpeed={replay.setSpeed}
        currentIndex={replay.currentIndex}
        totalPoints={replay.totalPoints}
        onSeek={replay.setCurrentIndex}
        causalMode={replay.causalMode}
        onToggleCausal={() => replay.setCausalMode(c => !c)}
      />
    </div>
  );
}