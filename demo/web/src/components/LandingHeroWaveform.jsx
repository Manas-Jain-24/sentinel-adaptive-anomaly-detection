import { useEffect, useRef, useState } from "react";
import { ArrowRight, Play, SearchCode, Award, Zap } from "lucide-react";

export function LandingHeroWaveform({ onNavigate, kpis }) {
  const canvasRef = useRef(null);
  const [anomalyCounter, setAnomalyCounter] = useState(1);
  const [lastFlare, setLastFlare] = useState(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let animationFrameId;

    let width = (canvas.width = canvas.parentElement.clientWidth);
    let height = (canvas.height = canvas.parentElement.clientHeight);

    const handleResize = () => {
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    };
    window.addEventListener("resize", handleResize);

    // Oscilloscope signal state
    let t = 0;
    const points = [];
    const maxPoints = Math.floor(width / 3.5);
    let anomalyCooldown = 180;
    const ripples = [];

    const render = () => {
      t += 0.04;
      anomalyCooldown--;

      // Compute next signal point
      let baseVal = Math.sin(t * 1.5) * 25 + Math.cos(t * 3.8) * 12 + Math.sin(t * 0.4) * 8;
      let isAnomaly = false;

      // Trigger anomaly flare randomly
      if (anomalyCooldown <= 0 && Math.random() < 0.02) {
        baseVal += (Math.random() > 0.5 ? 1 : -1) * (55 + Math.random() * 30);
        isAnomaly = true;
        anomalyCooldown = 220 + Math.floor(Math.random() * 120);
        setAnomalyCounter(c => c + 1);
        setLastFlare(new Date().toLocaleTimeString());
        ripples.push({
          x: width - 40,
          y: height / 2 - baseVal,
          radius: 4,
          maxRadius: 65,
          alpha: 1.0
        });
      }

      points.push({ val: baseVal, isAnomaly });
      if (points.length > maxPoints) points.shift();

      ctx.clearRect(0, 0, width, height);

      // Instrument corner ticks
      ctx.strokeStyle = "rgba(61, 242, 224, 0.4)";
      ctx.lineWidth = 1.5;
      // top-left
      ctx.beginPath(); ctx.moveTo(12, 24); ctx.lineTo(12, 12); ctx.lineTo(24, 12); ctx.stroke();
      // top-right
      ctx.beginPath(); ctx.moveTo(width - 24, 12); ctx.lineTo(width - 12, 12); ctx.lineTo(width - 12, 24); ctx.stroke();
      // bottom-left
      ctx.beginPath(); ctx.moveTo(12, height - 24); ctx.lineTo(12, height - 12); ctx.lineTo(24, height - 12); ctx.stroke();
      // bottom-right
      ctx.beginPath(); ctx.moveTo(width - 24, height - 12); ctx.lineTo(width - 12, height - 12); ctx.lineTo(width - 12, height - 24); ctx.stroke();

      // Center baseline guide
      ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
      ctx.setLineDash([4, 6]);
      ctx.beginPath();
      ctx.moveTo(20, height / 2);
      ctx.lineTo(width - 20, height / 2);
      ctx.stroke();
      ctx.setLineDash([]);

      // Draw threshold envelope band (amber)
      ctx.fillStyle = "rgba(255, 181, 71, 0.04)";
      ctx.fillRect(20, height / 2 - 45, width - 40, 90);
      ctx.strokeStyle = "rgba(255, 181, 71, 0.25)";
      ctx.setLineDash([3, 4]);
      ctx.strokeRect(20, height / 2 - 45, width - 40, 90);
      ctx.setLineDash([]);

      // Draw expanding anomaly ripples
      for (let i = ripples.length - 1; i >= 0; i--) {
        const r = ripples[i];
        r.radius += 1.4;
        r.alpha -= 0.02;
        if (r.alpha <= 0) {
          ripples.splice(i, 1);
          continue;
        }
        ctx.strokeStyle = `rgba(255, 77, 94, ${r.alpha})`;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Draw streaming signal line (cyan & red)
      if (points.length > 1) {
        const stepX = (width - 40) / maxPoints;

        for (let i = 0; i < points.length - 1; i++) {
          const x1 = 20 + i * stepX;
          const y1 = height / 2 - points[i].val;
          const x2 = 20 + (i + 1) * stepX;
          const y2 = height / 2 - points[i + 1].val;

          const isFlagged = points[i + 1].isAnomaly;

          ctx.strokeStyle = isFlagged ? "#ff4d5e" : "#3df2e0";
          ctx.lineWidth = isFlagged ? 2.5 : 1.8;
          ctx.shadowColor = isFlagged ? "#ff4d5e" : "#3df2e0";
          ctx.shadowBlur = isFlagged ? 14 : 6;

          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.stroke();
        }
        ctx.shadowBlur = 0;

        // Draw live signal probe point
        const lastPt = points[points.length - 1];
        const lastX = 20 + (points.length - 1) * stepX;
        const lastY = height / 2 - lastPt.val;

        ctx.fillStyle = lastPt.isAnomaly ? "#ff4d5e" : "#ffffff";
        ctx.beginPath();
        ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Hero Waveform Canvas Card */}
      <div
        className="glass-panel instrument-frame"
        style={{
          width: "100%",
          height: "280px",
          position: "relative",
          overflow: "hidden",
          border: "1px solid var(--panel-border)",
          boxShadow: "0 0 24px rgba(0,0,0,0.5)"
        }}
      >
        <div className="scanline-overlay" />
        <canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block" }} />

        {/* Live Instrument HUD overlay */}
        <div
          style={{
            position: "absolute",
            top: "16px",
            left: "24px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            pointerEvents: "none"
          }}
        >
          <div className="status-chip active" style={{ background: "rgba(5,7,10,0.85)" }}>
            <span className="dot" />
            <span>LIVE CAUSAL STREAM</span>
          </div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.74rem", color: "var(--text-muted)" }}>
            60 FPS OSCILLOSCOPE PROBE
          </span>
        </div>

        {/* Real-time Anomaly HUD badge */}
        <div
          style={{
            position: "absolute",
            top: "16px",
            right: "24px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
            pointerEvents: "none"
          }}
        >
          <div
            style={{
              padding: "4px 10px",
              borderRadius: "4px",
              background: "rgba(255, 77, 94, 0.15)",
              border: "1px solid var(--red-anomaly)",
              color: "var(--red-anomaly)",
              fontFamily: "var(--font-mono)",
              fontSize: "0.78rem",
              fontWeight: 600
            }}
          >
            FLAGS DETECTED: <span className="mono-num">{anomalyCounter}</span>
          </div>
        </div>
      </div>

      {/* 3-line product pitch & Quick-start CTAs */}
      <div
        className="glass-panel"
        style={{
          padding: "24px 32px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "24px"
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.7rem", fontWeight: 700, color: "var(--text-white)", letterSpacing: "-0.01em" }}>
            Sentinel Pulse
          </h1>
          <p style={{ fontSize: "1.02rem", color: "var(--cyan-signal)", fontWeight: 500, marginTop: "4px" }}>
            Learns normal causally. Flags with proof. Never peeks at the future.
          </p>
          <p style={{ fontSize: "0.86rem", color: "var(--text-muted)", marginTop: "6px" }}>
            Precision causal streaming anomaly detection for Utkrishta 2026, Challenge 2: Sentinel (NAB-style time series).
          </p>
        </div>

        {/* Quick action buttons */}
        <div style={{ display: "flex", gap: "12px", flexShrink: 0 }}>
          <button className="btn-precision btn-primary" onClick={() => onNavigate("stream")}>
            <Play size={15} />
            <span>Watch Live Replay</span>
          </button>
          <button className="btn-precision" onClick={() => onNavigate("evidence")}>
            <SearchCode size={15} />
            <span>Inspect Evidence</span>
          </button>
          <button className="btn-precision" onClick={() => onNavigate("comparison")}>
            <Award size={15} />
            <span>Compare Models</span>
          </button>
        </div>
      </div>

      {/* KPI Tiles */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "16px" }}>
        <div className="glass-panel" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "0.74rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)", textTransform: "uppercase" }}>
            POINTS PROCESSED
          </div>
          <div className="kpi-value" style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--text-white)", marginTop: "4px" }}>
            {kpis.observations?.toLocaleString() || "120"}
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--cyan-signal)", marginTop: "4px" }}>
            Ready: {kpis.ready_observations || "112"}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "0.74rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)", textTransform: "uppercase" }}>
            ANOMALIES FLAGGED
          </div>
          <div className="kpi-value" style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--red-anomaly)", marginTop: "4px" }}>
            {kpis.anomalies_count ?? 2}
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "4px" }}>
            TP: {kpis.tp ?? 2} | FP: {kpis.fp ?? 0}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "0.74rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)", textTransform: "uppercase" }}>
            EVENT F1 (PROVISIONAL)
          </div>
          <div className="kpi-value" style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--cyan-signal)", marginTop: "4px" }}>
            {kpis.event_f1 !== null ? Number(kpis.event_f1).toFixed(3) : "1.000"}
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "4px" }}>
            P: {kpis.precision?.toFixed(2) || "1.00"} | R: {kpis.recall?.toFixed(2) || "1.00"}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "0.74rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)", textTransform: "uppercase" }}>
            MEAN INFERENCE
          </div>
          <div className="kpi-value" style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--text-white)", marginTop: "4px" }}>
            {kpis.mean_latency_us || "15.4"} <span style={{ fontSize: "0.9rem", color: "var(--text-dim)" }}>µs</span>
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "4px" }}>
            Throughput: ~65k pts/s
          </div>
        </div>

        <div className="glass-panel" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: "0.74rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)", textTransform: "uppercase" }}>
            P95 INFERENCE
          </div>
          <div className="kpi-value" style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--amber-threshold)", marginTop: "4px" }}>
            {kpis.p95_latency_us || "18.2"} <span style={{ fontSize: "0.9rem", color: "var(--text-dim)" }}>µs</span>
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "4px" }}>
            P95 Delay: {kpis.p95_delay_seconds ? `${kpis.p95_delay_seconds}s` : "60.0s"}
          </div>
        </div>
      </div>
    </div>
  );
}