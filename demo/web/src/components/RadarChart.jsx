import { useEffect, useRef } from "react";

export function RadarChart({ results = [] }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const size = (canvas.width = canvas.height = 280);
    const center = size / 2;
    const radius = size * 0.38;

    const criteria = [
      { name: "Event F1", key: "event_f1", max: 1.0 },
      { name: "Precision", key: "precision", max: 1.0 },
      { name: "Recall", key: "recall", max: 1.0 },
      { name: "Low Delay", key: "mean_delay_sec", invert: true, max: 200 },
      { name: "Efficiency", key: "latency_us", invert: true, max: 100 }
    ];

    const angleStep = (Math.PI * 2) / criteria.length;

    ctx.clearRect(0, 0, size, size);

    // Draw concentric polygon webs
    const levels = 4;
    for (let l = 1; l <= levels; l++) {
      const r = (radius / levels) * l;
      ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
      ctx.beginPath();
      for (let i = 0; i < criteria.length; i++) {
        const angle = i * angleStep - Math.PI / 2;
        const x = center + Math.cos(angle) * r;
        const y = center + Math.sin(angle) * r;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.stroke();
    }

    // Draw radial spokes and labels
    ctx.font = "10px 'JetBrains Mono', monospace";
    ctx.fillStyle = "rgba(148, 163, 184, 0.8)";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    for (let i = 0; i < criteria.length; i++) {
      const angle = i * angleStep - Math.PI / 2;
      const x = center + Math.cos(angle) * radius;
      const y = center + Math.sin(angle) * radius;

      ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
      ctx.beginPath();
      ctx.moveTo(center, center);
      ctx.lineTo(x, y);
      ctx.stroke();

      const labelX = center + Math.cos(angle) * (radius + 20);
      const labelY = center + Math.sin(angle) * (radius + 20);
      ctx.fillText(criteria[i].name, labelX, labelY);
    }

    // Draw Model Polygons
    const colors = ["#3df2e0", "#ffb547", "#8b7cff", "#ff4d5e"];
    results.slice(0, 3).forEach((model, mIdx) => {
      const color = colors[mIdx % colors.length];
      ctx.fillStyle = `${color}25`;
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.8;

      ctx.beginPath();
      criteria.forEach((crit, i) => {
        const rawVal = model[crit.key] ?? 0;
        let norm = crit.invert
          ? Math.max(0.1, 1 - rawVal / crit.max)
          : Math.min(1.0, rawVal / crit.max);

        const r = radius * norm;
        const angle = i * angleStep - Math.PI / 2;
        const x = center + Math.cos(angle) * r;
        const y = center + Math.sin(angle) * r;

        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });
  }, [results]);

  return (
    <div className="glass-panel" style={{ padding: "18px 20px", display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-white)", letterSpacing: "0.04em", alignSelf: "flex-start", marginBottom: "8px" }}>
        MULTI-CRITERIA RADAR
      </div>
      <canvas ref={canvasRef} style={{ width: "280px", height: "280px" }} />
      <div style={{ display: "flex", gap: "14px", fontSize: "0.7rem", fontFamily: "var(--font-mono)", marginTop: "4px" }}>
        <span style={{ color: "#3df2e0" }}>• Rolling MAD</span>
        <span style={{ color: "#ffb547" }}>• Rolling Z-Score</span>
        <span style={{ color: "#8b7cff" }}>• Planned</span>
      </div>
    </div>
  );
}

export function ParetoScatter({ results = [] }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = (canvas.width = canvas.parentElement.clientWidth);
    const height = (canvas.height = 280);

    const padLeft = 45;
    const padRight = 30;
    const padTop = 30;
    const padBottom = 35;

    ctx.clearRect(0, 0, width, height);

    // Axes
    ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
    ctx.beginPath();
    ctx.moveTo(padLeft, padTop);
    ctx.lineTo(padLeft, height - padBottom);
    ctx.lineTo(width - padRight, height - padBottom);
    ctx.stroke();

    // Labels
    ctx.font = "10px 'JetBrains Mono', monospace";
    ctx.fillStyle = "rgba(148, 163, 184, 0.7)";
    ctx.textAlign = "center";
    ctx.fillText("Latency (µs) ? lower is faster", width / 2, height - 10);

    ctx.save();
    ctx.translate(14, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText("Event F1 ?", 0, 0);
    ctx.restore();

    // Map models to points
    const points = results.map(m => ({
      name: m.model_name || m.model_id,
      xVal: m.latency_us || 15,
      yVal: m.event_f1 || 0.8,
      isWinner: m.is_winner
    }));

    const maxLatency = Math.max(160, ...points.map(p => p.xVal));

    const getX = (lat) => padLeft + (lat / maxLatency) * (width - padLeft - padRight);
    const getY = (f1) => (height - padBottom) - (f1 / 1.0) * (height - padTop - padBottom);

    // Draw Pareto Frontier Line connecting optimal points
    const sortedPoints = [...points].sort((a, b) => a.xVal - b.xVal);
    ctx.strokeStyle = "rgba(61, 242, 224, 0.35)";
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    sortedPoints.forEach((p, idx) => {
      const x = getX(p.xVal);
      const y = getY(p.yVal);
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw Scatter points
    points.forEach(p => {
      const x = getX(p.xVal);
      const y = getY(p.yVal);

      ctx.fillStyle = p.isWinner ? "#3df2e0" : "#ffb547";
      ctx.beginPath();
      ctx.arc(x, y, p.isWinner ? 7 : 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.fillStyle = "rgba(240, 244, 248, 0.9)";
      ctx.font = "9px 'JetBrains Mono', monospace";
      ctx.textAlign = "left";
      ctx.fillText(p.name.split(" ")[0], x + 9, y + 3);
    });
  }, [results]);

  return (
    <div className="glass-panel" style={{ padding: "18px 20px" }}>
      <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-white)", letterSpacing: "0.04em", marginBottom: "8px" }}>
        PARETO EFFICIENCY (EVENT F1 VS. LATENCY)
      </div>
      <canvas ref={canvasRef} style={{ width: "100%", height: "280px", display: "block" }} />
    </div>
  );
}