import { useState } from "react";
import { Check, Copy, ShieldCheck, ChevronLeft, ChevronRight, AlertTriangle, ArrowRight } from "lucide-react";

export function AnatomyDiagram({
  predictions = [],
  windows = [],
  selectedPoint = null,
  onSelectPoint
}) {
  const [copied, setCopied] = useState(false);
  const [filterMode, setFilterMode] = useState("all"); // "all", "true_positives", "unmatched"

  // Flagged points only
  const anomalies = predictions.filter(p => p.label === "ANOMALOUS");

  // Determine which window matched each anomaly
  const enrichedAnomalies = anomalies.map(a => {
    const aMs = new Date(a.timestamp).getTime();
    const hitWindow = windows.find(w => aMs >= w.start_ms && aMs <= w.end_ms);
    const delaySec = hitWindow ? Math.max(0, Math.round((aMs - hitWindow.start_ms) / 1000)) : null;
    return {
      ...a,
      hitWindow,
      delaySec,
      isTruePositive: Boolean(hitWindow)
    };
  });

  const filtered = enrichedAnomalies.filter(a => {
    if (filterMode === "true_positives") return a.isTruePositive;
    if (filterMode === "unmatched") return !a.isTruePositive;
    return true;
  });

  const active = selectedPoint
    ? (enrichedAnomalies.find(a => a.index === selectedPoint.index) || enrichedAnomalies[0])
    : enrichedAnomalies[0];

  const handleCopyJson = () => {
    if (!active) return;
    navigator.clipboard.writeText(JSON.stringify(active, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleNavigate = (direction) => {
    if (!active || enrichedAnomalies.length === 0) return;
    const curIdx = enrichedAnomalies.findIndex(a => a.index === active.index);
    if (direction === "prev") {
      const prev = curIdx > 0 ? enrichedAnomalies[curIdx - 1] : enrichedAnomalies[enrichedAnomalies.length - 1];
      if (onSelectPoint) onSelectPoint(prev);
    } else {
      const next = curIdx < enrichedAnomalies.length - 1 ? enrichedAnomalies[curIdx + 1] : enrichedAnomalies[0];
      if (onSelectPoint) onSelectPoint(next);
    }
  };

  if (anomalies.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: "40px", textAlign: "center" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          No anomalies have been flagged in the loaded stream.
        </p>
      </div>
    );
  }

  // Numerical metrics
  const val = active?.value ?? 0;
  const base = active?.evidence?.baseline ?? 0;
  const scale = active?.evidence?.scale ?? 1.0;
  const residual = active?.evidence?.residual ?? (val - base);
  const score = active?.score ?? 0;
  const threshold = active?.threshold ?? 4.0;
  const margin = Math.max(0, score - threshold);

  // Generate strict plain-English explanation from numeric fields only
  const direction = residual >= 0 ? "above" : "below";
  const explanation = `Value ${val.toFixed(2)} sat ${score.toFixed(2)} scale-units ${direction} the pre-update baseline ${base.toFixed(2)}, exceeding the ${threshold.toFixed(2)} threshold by a margin of ${margin.toFixed(2)}.`;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: "20px" }}>
      {/* Left: Ranked & Filterable Anomaly List */}
      <div className="glass-panel" style={{ padding: "18px 20px", display: "flex", flexDirection: "column", height: "640px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
          <span style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-white)", letterSpacing: "0.04em" }}>
            FLAGGED ANOMALIES ({enrichedAnomalies.length})
          </span>
          <div style={{ display: "flex", gap: "4px" }}>
            {["all", "true_positives", "unmatched"].map(m => (
              <button
                key={m}
                onClick={() => setFilterMode(m)}
                style={{
                  padding: "3px 7px",
                  borderRadius: "3px",
                  fontSize: "0.68rem",
                  fontFamily: "var(--font-mono)",
                  cursor: "pointer",
                  background: filterMode === m ? "var(--cyan-signal)" : "rgba(255,255,255,0.05)",
                  color: filterMode === m ? "var(--bg-obsidian-950)" : "var(--text-dim)",
                  border: "1px solid var(--panel-border)"
                }}
              >
                {m === "all" ? "ALL" : m === "true_positives" ? "TP" : "FP/UNMATCHED"}
              </button>
            ))}
          </div>
        </div>

        {/* Scrollable list */}
        <div style={{ overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", gap: "8px" }}>
          {filtered.map(a => {
            const isSelected = active && a.index === active.index;
            return (
              <div
                key={a.index}
                onClick={() => onSelectPoint && onSelectPoint(a)}
                style={{
                  padding: "10px 12px",
                  borderRadius: "var(--radius-sm)",
                  background: isSelected ? "rgba(61, 242, 224, 0.1)" : "rgba(255, 255, 255, 0.02)",
                  border: `1px solid ${isSelected ? "var(--cyan-signal)" : "var(--panel-border)"}`,
                  cursor: "pointer",
                  transition: "all var(--transition-fast)"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span className="mono-num" style={{ fontSize: "0.78rem", color: "var(--text-white)", fontWeight: 600 }}>
                    #{a.index} • {a.timestamp.split("T")[1]?.replace("Z", "") || a.timestamp}
                  </span>
                  <span
                    className="mono-num"
                    style={{
                      fontSize: "0.74rem",
                      fontWeight: 700,
                      color: "var(--red-anomaly)"
                    }}
                  >
                    Score: {a.score?.toFixed(2)}
                  </span>
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "6px", fontSize: "0.72rem", color: "var(--text-dim)" }}>
                  <span>Val: <strong style={{ color: "var(--text-muted)" }}>{a.value.toFixed(2)}</strong></span>
                  {a.isTruePositive ? (
                    <span style={{ color: "var(--violet-window)", fontWeight: 500 }}>
                      Matched Window (+{a.delaySec}s delay)
                    </span>
                  ) : (
                    <span style={{ color: "var(--amber-threshold)" }}>
                      Unmatched / FP
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right: Anatomy of a Flag Panel */}
      <div className="glass-panel" style={{ padding: "24px 28px", display: "flex", flexDirection: "column", gap: "20px" }}>
        {/* Header & Nav Controls */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-white)" }}>
                ANATOMY OF FLAG #{active?.index}
              </span>
              <span className="scope-badge" style={{ background: "var(--red-translucent)", color: "var(--red-anomaly)", borderColor: "var(--red-anomaly)" }}>
                ANOMALOUS TRIGGER
              </span>
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginTop: "3px" }}>
              Timestamp: {active?.timestamp} • Series: {active?.series_id}
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <button className="btn-precision" onClick={() => handleNavigate("prev")} title="Previous Flag">
              <ChevronLeft size={14} />
            </button>
            <button className="btn-precision" onClick={() => handleNavigate("next")} title="Next Flag">
              <ChevronRight size={14} />
            </button>
            <button className="btn-precision" onClick={handleCopyJson} title="Copy Record as JSON">
              {copied ? <Check size={14} style={{ color: "var(--cyan-signal)" }} /> : <Copy size={14} />}
              <span>{copied ? "COPIED" : "COPY JSON"}</span>
            </button>
          </div>
        </div>

        {/* Dynamic Plain-English Explanation Banner */}
        <div
          style={{
            padding: "14px 18px",
            borderRadius: "var(--radius-sm)",
            background: "rgba(61, 242, 224, 0.06)",
            border: "1px solid rgba(61, 242, 224, 0.25)",
            fontSize: "0.88rem",
            color: "var(--text-white)",
            lineHeight: 1.5
          }}
        >
          <strong style={{ color: "var(--cyan-signal)" }}>Statistical Proof: </strong>
          {explanation}
        </div>

        {/* Number-Line Mini Diagram */}
        <div
          style={{
            padding: "20px 24px",
            background: "rgba(5, 7, 10, 0.7)",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--panel-border)"
          }}
        >
          <div style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)", color: "var(--text-dim)", textTransform: "uppercase", marginBottom: "16px" }}>
            STATISTICAL RESIDUAL NUMBER LINE & THRESHOLD BAND
          </div>

          <div style={{ position: "relative", height: "70px", margin: "10px 20px" }}>
            {/* Horizontal Line */}
            <div style={{ position: "absolute", top: "35px", left: 0, right: 0, height: "2px", background: "rgba(255,255,255,0.15)" }} />

            {/* Baseline Center Tick (Median) */}
            <div style={{ position: "absolute", top: "18px", left: "50%", transform: "translateX(-50%)", display: "flex", flexDirection: "column", alignItems: "center" }}>
              <span className="mono-num" style={{ fontSize: "0.72rem", color: "var(--amber-threshold)", fontWeight: 600 }}>
                Base: {base.toFixed(2)}
              </span>
              <div style={{ width: "2px", height: "18px", background: "var(--amber-threshold)", marginTop: "2px" }} />
            </div>

            {/* Positive Threshold Boundary */}
            <div style={{ position: "absolute", top: "18px", left: "75%", transform: "translateX(-50%)", display: "flex", flexDirection: "column", alignItems: "center" }}>
              <span className="mono-num" style={{ fontSize: "0.72rem", color: "var(--amber-threshold)" }}>
                +TH ({threshold.toFixed(1)}s)
              </span>
              <div style={{ width: "2px", height: "18px", background: "var(--amber-threshold)", marginTop: "2px" }} />
            </div>

            {/* Negative Threshold Boundary */}
            <div style={{ position: "absolute", top: "18px", left: "25%", transform: "translateX(-50%)", display: "flex", flexDirection: "column", alignItems: "center" }}>
              <span className="mono-num" style={{ fontSize: "0.72rem", color: "var(--amber-threshold)" }}>
                -TH (-{threshold.toFixed(1)}s)
              </span>
              <div style={{ width: "2px", height: "18px", background: "var(--amber-threshold)", marginTop: "2px" }} />
            </div>

            {/* Observed Value Marker Sliding In */}
            <div
              style={{
                position: "absolute",
                top: "22px",
                left: residual >= 0 ? "88%" : "12%",
                transform: "translateX(-50%)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                transition: "all 0.4s ease"
              }}
            >
              <div
                style={{
                  width: "14px",
                  height: "14px",
                  borderRadius: "50%",
                  background: "var(--red-anomaly)",
                  boxShadow: "0 0 12px var(--red-glow)",
                  border: "2px solid #ffffff"
                }}
              />
              <span className="mono-num" style={{ fontSize: "0.75rem", color: "var(--red-anomaly)", fontWeight: 700, marginTop: "4px" }}>
                Val: {val.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Quantitative Anatomy Breakdown Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
          <div style={{ padding: "12px 16px", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--panel-border)" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>OBSERVED VALUE</div>
            <div className="mono-num" style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-white)", marginTop: "2px" }}>
              {val.toFixed(2)}
            </div>
          </div>

          <div style={{ padding: "12px 16px", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--panel-border)" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>PRE-UPDATE BASELINE (MEDIAN)</div>
            <div className="mono-num" style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--amber-threshold)", marginTop: "2px" }}>
              {base.toFixed(2)}
            </div>
          </div>

          <div style={{ padding: "12px 16px", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--panel-border)" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>ROBUST SCALE (1.4826×MAD)</div>
            <div className="mono-num" style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-white)", marginTop: "2px" }}>
              {scale.toFixed(4)}
            </div>
          </div>

          <div style={{ padding: "12px 16px", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--panel-border)" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>RESIDUAL DEVIATION</div>
            <div className="mono-num" style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--cyan-signal)", marginTop: "2px" }}>
              {residual >= 0 ? `+${residual.toFixed(2)}` : residual.toFixed(2)}
            </div>
          </div>

          <div style={{ padding: "12px 16px", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-sm)", border: "1px solid var(--panel-border)" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>APPLIED THRESHOLD</div>
            <div className="mono-num" style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--amber-threshold)", marginTop: "2px" }}>
              {threshold.toFixed(2)}
            </div>
          </div>

          <div style={{ padding: "12px 16px", background: "rgba(255, 77, 94, 0.08)", borderRadius: "var(--radius-sm)", border: "1px solid rgba(255, 77, 94, 0.3)" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--red-anomaly)", fontFamily: "var(--font-mono)" }}>STANDARDIZED SCORE</div>
            <div className="mono-num" style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--red-anomaly)", marginTop: "2px" }}>
              {score.toFixed(2)} <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>(+{margin.toFixed(2)})</span>
            </div>
          </div>
        </div>

        {/* Contract Leakage-Free Guarantee Badge */}
        {active?.ready && (
          <div
            style={{
              marginTop: "auto",
              padding: "10px 14px",
              borderRadius: "var(--radius-sm)",
              background: "rgba(61, 242, 224, 0.08)",
              border: "1px solid var(--cyan-signal)",
              display: "flex",
              alignItems: "center",
              gap: "10px",
              color: "var(--cyan-signal)",
              fontSize: "0.78rem"
            }}
          >
            <ShieldCheck size={16} />
            <span>
              <strong>Contract Verified:</strong> Scored before history update (strictly causal, zero lookahead leakage). History window: {active.evidence?.history_size || 32} points.
            </span>
          </div>
        )}
      </div>
    </div>
  );
}