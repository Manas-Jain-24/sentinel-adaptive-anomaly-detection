import { useEffect, useRef } from "react";
import { Play, SearchCode, Award } from "lucide-react";

const display = (value, digits = 3) => typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "N/A";

export function LandingHeroWaveform({ onNavigate, kpis, predictions = [] }) {
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const draw = () => {
      const width = canvas.parentElement.clientWidth;
      const height = canvas.parentElement.clientHeight;
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.floor(width * ratio); canvas.height = Math.floor(height * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0); ctx.clearRect(0, 0, width, height);
      const valid = predictions.filter(p => Number.isFinite(p.value));
      if (!valid.length) return;
      const min = Math.min(...valid.map(p => p.value)); const max = Math.max(...valid.map(p => p.value)); const span = max - min || 1; const pad = 28;
      const x = i => pad + (i / Math.max(1, valid.length - 1)) * (width - 2 * pad);
      const y = value => height - pad - ((value - min) / span) * (height - 2 * pad);
      ctx.strokeStyle = "rgba(255,255,255,0.08)"; ctx.setLineDash([4, 6]); ctx.beginPath(); ctx.moveTo(pad, height / 2); ctx.lineTo(width - pad, height / 2); ctx.stroke(); ctx.setLineDash([]);
      for (let i = 1; i < valid.length; i++) {
        const flagged = valid[i].label === "ANOMALOUS"; ctx.strokeStyle = flagged ? "#ff4d5e" : "#3df2e0"; ctx.lineWidth = flagged ? 2.5 : 1.8;
        ctx.beginPath(); ctx.moveTo(x(i - 1), y(valid[i - 1].value)); ctx.lineTo(x(i), y(valid[i].value)); ctx.stroke();
        if (flagged) { ctx.fillStyle = "#ff4d5e"; ctx.beginPath(); ctx.arc(x(i), y(valid[i].value), 4, 0, Math.PI * 2); ctx.fill(); }
      }
    };
    draw(); const observer = new ResizeObserver(draw); observer.observe(canvas.parentElement); return () => observer.disconnect();
  }, [predictions]);
  const flagged = kpis.anomalies_count ?? 0;
  return <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
    <div className="glass-panel instrument-frame" style={{ width: "100%", height: "280px", position: "relative", overflow: "hidden", border: "1px solid var(--panel-border)", boxShadow: "0 0 24px rgba(0,0,0,0.5)" }}>
      <div className="scanline-overlay" /><canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block" }} />
      <div style={{ position: "absolute", top: "16px", left: "24px", display: "flex", alignItems: "center", gap: "12px", pointerEvents: "none" }}><div className="status-chip active" style={{ background: "rgba(5,7,10,0.85)" }}><span className="dot" /><span>SAVED DETECTOR TRACE</span></div><span style={{ fontFamily: "var(--font-mono)", fontSize: "0.74rem", color: "var(--text-muted)" }}>SYNTHETIC SMOKE · {predictions.length} POINTS</span></div>
      <div style={{ position: "absolute", top: "16px", right: "24px", padding: "4px 10px", borderRadius: "4px", background: "rgba(255,77,94,0.15)", border: "1px solid var(--red-anomaly)", color: "var(--red-anomaly)", fontFamily: "var(--font-mono)", fontSize: "0.78rem", fontWeight: 600 }}>FLAGS IN SAVED RUN: {flagged}</div>
    </div>
    <div className="glass-panel" style={{ padding: "24px 32px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "24px" }}><div><h1 style={{ fontSize: "1.7rem", fontWeight: 700, color: "var(--text-white)", letterSpacing: "-0.01em" }}>Sentinel Pulse</h1><p style={{ fontSize: "1.02rem", color: "var(--cyan-signal)", fontWeight: 500, marginTop: "4px" }}>Causal streaming anomaly detection with numerical evidence.</p><p style={{ fontSize: "0.86rem", color: "var(--text-muted)", marginTop: "6px" }}>Saved synthetic software demo for Utkrishta 2026, Challenge 2: Sentinel. No official benchmark claim.</p></div><div style={{ display: "flex", gap: "12px", flexShrink: 0 }}><button className="btn-precision btn-primary" onClick={() => onNavigate("stream")}><Play size={15} /><span>Replay Saved Trace</span></button><button className="btn-precision" onClick={() => onNavigate("evidence")}><SearchCode size={15} /><span>Inspect Evidence</span></button><button className="btn-precision" onClick={() => onNavigate("comparison")}><Award size={15} /><span>Compare Runs</span></button></div></div>
    <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "16px" }}><Kpi label="POINTS PROCESSED" value={kpis.observations?.toLocaleString() ?? "N/A"} hint={`Ready: ${kpis.ready_observations ?? "N/A"}`} /><Kpi label="ANOMALIES FLAGGED" value={kpis.anomalies_count ?? "N/A"} hint={`TP: ${kpis.tp ?? "N/A"} | FP: ${kpis.fp ?? "N/A"}`} color="var(--red-anomaly)" /><Kpi label="EVENT F1 · PROVISIONAL" value={display(kpis.event_f1)} hint={`P: ${display(kpis.precision, 2)} | R: ${display(kpis.recall, 2)}`} color="var(--cyan-signal)" /><Kpi label="MEAN PROCESS TIME" value={typeof kpis.mean_latency_us === "number" ? `${display(kpis.mean_latency_us, 1)} µs` : "N/A"} hint="This run · process() only" /><Kpi label="P95 PROCESS TIME" value={typeof kpis.p95_latency_us === "number" ? `${display(kpis.p95_latency_us, 1)} µs` : "N/A"} hint={`P95 event delay: ${typeof kpis.p95_delay_seconds === "number" ? `${display(kpis.p95_delay_seconds, 1)} s` : "N/A"}`} color="var(--amber-threshold)" /></div>
  </div>;
}

function Kpi({ label, value, hint, color = "var(--text-white)" }) { return <div className="glass-panel" style={{ padding: "18px 20px" }}><div style={{ fontSize: "0.74rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)", textTransform: "uppercase" }}>{label}</div><div className="kpi-value" style={{ fontSize: "1.8rem", fontWeight: 700, color, marginTop: "4px" }}>{value}</div><div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "4px" }}>{hint}</div></div>; }
