import { Play, Pause, SkipBack, SkipForward, ChevronLeft, ChevronRight, FastForward, Shield } from "lucide-react";

export function ReplayBar({
  isPlaying,
  onTogglePlay,
  onStepForward,
  onStepBackward,
  onPrevAnomaly,
  onNextAnomaly,
  speed,
  onChangeSpeed,
  currentIndex,
  totalPoints,
  onSeek,
  causalMode,
  onToggleCausal
}) {
  const speeds = [0.5, 1, 2, 4, 8, 16];

  return (
    <div
      className="glass-panel"
      style={{
        padding: "14px 20px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "20px"
      }}
    >
      {/* Left: Playback Controls */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <button
          className="btn-precision"
          onClick={onStepBackward}
          title="Step Backward (Arrow Left)"
          style={{ padding: "8px 10px" }}
        >
          <SkipBack size={15} />
        </button>

        <button
          className={`btn-precision ${isPlaying ? "btn-danger" : "btn-primary"}`}
          onClick={onTogglePlay}
          title="Play / Pause Replay (Space)"
          style={{ padding: "8px 16px", minWidth: "90px", justifyContent: "center" }}
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} />}
          <span>{isPlaying ? "PAUSE" : "REPLAY"}</span>
        </button>

        <button
          className="btn-precision"
          onClick={onStepForward}
          title="Step Forward (Arrow Right)"
          style={{ padding: "8px 10px" }}
        >
          <SkipForward size={15} />
        </button>

        {/* Anomaly Jumpers */}
        <div style={{ display: "flex", gap: "4px", marginLeft: "12px" }}>
          <button
            className="btn-precision"
            onClick={onPrevAnomaly}
            title="Previous Anomaly Flag ([ key)"
            style={{ padding: "6px 10px", fontSize: "0.75rem" }}
          >
            <ChevronLeft size={14} />
            <span>Prev Flag</span>
          </button>
          <button
            className="btn-precision"
            onClick={onNextAnomaly}
            title="Next Anomaly Flag (] key)"
            style={{ padding: "6px 10px", fontSize: "0.75rem" }}
          >
            <span>Next Flag</span>
            <ChevronRight size={14} />
          </button>
        </div>
      </div>

      {/* Center: Scrubber Range Slider */}
      <div style={{ flex: 1, display: "flex", alignItems: "center", gap: "12px" }}>
        <span className="mono-num" style={{ fontSize: "0.75rem", color: "var(--text-dim)", minWidth: "35px" }}>
          {currentIndex}
        </span>
        <input
          type="range"
          min={0}
          max={Math.max(0, totalPoints - 1)}
          value={currentIndex}
          onChange={(e) => onSeek(Number(e.target.value))}
          style={{
            flex: 1,
            accentColor: "var(--cyan-signal)",
            cursor: "pointer",
            height: "5px"
          }}
        />
        <span className="mono-num" style={{ fontSize: "0.75rem", color: "var(--text-dim)", minWidth: "35px", textAlign: "right" }}>
          {totalPoints - 1}
        </span>
      </div>

      {/* Right: Speed & Causal Mode Toggle */}
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        {/* Speed Selector */}
        <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
          <FastForward size={14} style={{ color: "var(--text-dim)" }} />
          <div style={{ display: "flex", gap: "3px" }}>
            {speeds.map(s => (
              <button
                key={s}
                onClick={() => onChangeSpeed(s)}
                style={{
                  padding: "3px 6px",
                  borderRadius: "3px",
                  fontSize: "0.7rem",
                  fontFamily: "var(--font-mono)",
                  cursor: "pointer",
                  background: speed === s ? "var(--cyan-signal)" : "rgba(255,255,255,0.05)",
                  color: speed === s ? "var(--bg-obsidian-950)" : "var(--text-muted)",
                  border: "1px solid var(--panel-border)"
                }}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>

        {/* Causal Mode Toggle */}
        <button
          onClick={onToggleCausal}
          className="btn-precision"
          style={{
            borderColor: causalMode ? "var(--cyan-signal)" : "var(--panel-border)",
            background: causalMode ? "var(--cyan-translucent)" : "transparent",
            color: causalMode ? "var(--cyan-signal)" : "var(--text-dim)",
            padding: "6px 12px",
            fontSize: "0.74rem"
          }}
          title="Causal mode: strictly hides future points from the screen during replay"
        >
          <Shield size={14} />
          <span>CAUSAL MODE: {causalMode ? "ON" : "OFF"}</span>
        </button>
      </div>
    </div>
  );
}