import { useEffect, useRef, useState, useCallback } from "react";
import { Camera, ZoomIn, ZoomOut, RefreshCw, Eye } from "lucide-react";
import { decimateMinMax } from "../lib/decimation";
import { exportCanvasAsPng } from "../lib/exportFigure";

export function SyncedChart({
  predictions = [],
  windows = [],
  currentIndex = null,
  causalMode = true,
  onSelectPoint,
  onCaptureFigure,
  runMetadata = {}
}) {
  const containerRef = useRef(null);
  const mainCanvasRef = useRef(null);
  const scoreCanvasRef = useRef(null);

  // Zoom & Pan state
  const [viewRange, setViewRange] = useState({ start: 0, end: predictions.length });
  const [hoverIndex, setHoverIndex] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef(0);

  // Keep viewRange synced if predictions change
  useEffect(() => {
    setViewRange({ start: 0, end: predictions.length });
  }, [predictions.length]);

  // Points visible under causal mode
  const effectiveMaxIndex = (causalMode && currentIndex !== null)
    ? Math.min(currentIndex, predictions.length - 1)
    : predictions.length - 1;

  // Render function
  const render = useCallback(() => {
    const mainCanvas = mainCanvasRef.current;
    const scoreCanvas = scoreCanvasRef.current;
    if (!mainCanvas || !scoreCanvas || predictions.length === 0) return;

    const mainCtx = mainCanvas.getContext("2d");
    const scoreCtx = scoreCanvas.getContext("2d");

    const width = (mainCanvas.width = scoreCanvas.width = mainCanvas.parentElement.clientWidth);
    const mainHeight = (mainCanvas.height = 310);
    const scoreHeight = (scoreCanvas.height = 140);

    const padLeft = 65;
    const padRight = 30;
    const padTop = 25;
    const padBottom = 25;

    const plotWidth = width - padLeft - padRight;
    const plotHeightMain = mainHeight - padTop - padBottom;
    const plotHeightScore = scoreHeight - padTop - padBottom;

    // Determine slice to show
    const sliceStart = Math.max(0, Math.min(viewRange.start, predictions.length - 2));
    const sliceEnd = Math.min(predictions.length, Math.max(sliceStart + 2, viewRange.end));
    const rawVisible = predictions.slice(sliceStart, sliceEnd);

    // Filter by causal cutoff if applicable
    const visibleData = rawVisible.filter(p => p.index <= effectiveMaxIndex);

    // Min/Max decimation for high-speed 60fps rendering
    const decimated = decimateMinMax(visibleData, plotWidth);

    // Value bounds
    let minVal = Infinity;
    let maxVal = -Infinity;
    let maxScore = 8.0;

    for (const p of visibleData) {
      if (p.value < minVal) minVal = p.value;
      if (p.value > maxVal) maxVal = p.value;
      const b = p.evidence?.baseline;
      const s = p.evidence?.scale;
      if (b !== null && s !== null) {
        if (b - s * 2 < minVal) minVal = b - s * 2;
        if (b + s * 2 > maxVal) maxVal = b + s * 2;
      }
      if (p.score !== null && p.score > maxScore) maxScore = p.score;
      if (p.threshold > maxScore) maxScore = p.threshold;
    }

    if (minVal === Infinity) { minVal = 0; maxVal = 100; }
    const valPad = (maxVal - minVal) * 0.12 || 5;
    minVal -= valPad;
    maxVal += valPad;
    maxScore *= 1.15;

    // Coordinate mappers
    const getX = (idx) => padLeft + ((idx - sliceStart) / (sliceEnd - sliceStart - 1)) * plotWidth;
    const getYMain = (val) => padTop + plotHeightMain - ((val - minVal) / (maxVal - minVal)) * plotHeightMain;
    const getYScore = (score) => padTop + plotHeightScore - ((score || 0) / maxScore) * plotHeightScore;

    // --- MAIN CANVAS DRAWING ---
    mainCtx.clearRect(0, 0, width, mainHeight);

    // Instrument ticks
    mainCtx.strokeStyle = "rgba(61, 242, 224, 0.4)";
    mainCtx.lineWidth = 1.5;
    mainCtx.beginPath(); mainCtx.moveTo(10, 20); mainCtx.lineTo(10, 10); mainCtx.lineTo(20, 10); mainCtx.stroke();
    mainCtx.beginPath(); mainCtx.moveTo(width - 20, 10); mainCtx.lineTo(width - 10, 10); mainCtx.lineTo(width - 10, 20); mainCtx.stroke();

    // Grid lines & Y-axis labels
    mainCtx.strokeStyle = "rgba(255, 255, 255, 0.05)";
    mainCtx.fillStyle = "rgba(148, 163, 184, 0.7)";
    mainCtx.font = "10px 'JetBrains Mono', monospace";
    mainCtx.textAlign = "right";

    const ySteps = 4;
    for (let i = 0; i <= ySteps; i++) {
      const v = minVal + (i / ySteps) * (maxVal - minVal);
      const y = getYMain(v);
      mainCtx.beginPath();
      mainCtx.moveTo(padLeft, y);
      mainCtx.lineTo(width - padRight, y);
      mainCtx.stroke();
      mainCtx.fillText(v.toFixed(1), padLeft - 8, y + 3);
    }

    // Draw Ground-Truth Anomaly Windows (translucent soft violet #8B7CFF)
    for (const win of windows) {
      const wStartMs = win.start_ms;
      const wEndMs = win.end_ms;

      // Find indices in predictions
      const startIdx = predictions.findIndex(p => new Date(p.timestamp).getTime() >= wStartMs);
      const endIdx = predictions.findIndex(p => new Date(p.timestamp).getTime() >= wEndMs);

      const sI = startIdx !== -1 ? startIdx : 0;
      const eI = endIdx !== -1 ? endIdx : predictions.length - 1;

      if (eI >= sliceStart && sI <= sliceEnd) {
        const x1 = Math.max(padLeft, getX(sI));
        const x2 = Math.min(width - padRight, getX(eI));
        const wWidth = Math.max(8, x2 - x1);

        mainCtx.fillStyle = "rgba(139, 124, 255, 0.18)";
        mainCtx.fillRect(x1, padTop, wWidth, plotHeightMain);

        mainCtx.strokeStyle = "rgba(139, 124, 255, 0.6)";
        mainCtx.setLineDash([3, 3]);
        mainCtx.strokeRect(x1, padTop, wWidth, plotHeightMain);
        mainCtx.setLineDash([]);

        mainCtx.fillStyle = "#8b7cff";
        mainCtx.font = "9px 'JetBrains Mono', monospace";
        mainCtx.textAlign = "left";
        mainCtx.fillText("TRUTH WINDOW", x1 + 4, padTop + 14);
      }
    }

    // Warmup shading (points with ready === false)
    const firstReadyIdx = predictions.findIndex(p => p.ready);
    if (firstReadyIdx > 0 && firstReadyIdx >= sliceStart) {
      const xWarmup = Math.min(width - padRight, getX(firstReadyIdx));
      mainCtx.fillStyle = "rgba(255, 255, 255, 0.03)";
      mainCtx.fillRect(padLeft, padTop, xWarmup - padLeft, plotHeightMain);
      mainCtx.fillStyle = "rgba(148, 163, 184, 0.6)";
      mainCtx.font = "9px 'JetBrains Mono', monospace";
      mainCtx.textAlign = "left";
      mainCtx.fillText("WARMUP REGION (READY=FALSE)", padLeft + 8, padTop + 28);
    }

    // Draw Rolling MAD Envelope (shaded amber band #FFB547)
    mainCtx.fillStyle = "rgba(255, 181, 71, 0.08)";
    mainCtx.beginPath();
    let startedBand = false;
    for (let i = 0; i < decimated.length; i++) {
      const p = decimated[i];
      const b = p.evidence?.baseline;
      const s = p.evidence?.scale;
      if (b !== null && s !== null && p.ready) {
        const x = getX(p.index);
        const yTop = getYMain(b + s * p.threshold);
        if (!startedBand) {
          mainCtx.moveTo(x, yTop);
          startedBand = true;
        } else {
          mainCtx.lineTo(x, yTop);
        }
      }
    }
    for (let i = decimated.length - 1; i >= 0; i--) {
      const p = decimated[i];
      const b = p.evidence?.baseline;
      const s = p.evidence?.scale;
      if (b !== null && s !== null && p.ready) {
        const x = getX(p.index);
        const yBot = getYMain(b - s * p.threshold);
        mainCtx.lineTo(x, yBot);
      }
    }
    mainCtx.closePath();
    mainCtx.fill();

    // Draw Baseline Expectation (amber dashed line #FFB547)
    mainCtx.strokeStyle = "rgba(255, 181, 71, 0.75)";
    mainCtx.lineWidth = 1.3;
    mainCtx.setLineDash([4, 4]);
    mainCtx.beginPath();
    let startedBase = false;
    for (const p of decimated) {
      const b = p.evidence?.baseline;
      if (b !== null && p.ready) {
        const x = getX(p.index);
        const y = getYMain(b);
        if (!startedBase) { mainCtx.moveTo(x, y); startedBase = true; }
        else { mainCtx.lineTo(x, y); }
      }
    }
    mainCtx.stroke();
    mainCtx.setLineDash([]);

    // Draw Actual Value Signal (electric cyan line #3DF2E0)
    mainCtx.strokeStyle = "#3df2e0";
    mainCtx.lineWidth = 2.0;
    mainCtx.shadowColor = "rgba(61, 242, 224, 0.4)";
    mainCtx.shadowBlur = 8;
    mainCtx.beginPath();
    let startedVal = false;
    for (const p of decimated) {
      const x = getX(p.index);
      const y = getYMain(p.value);
      if (!startedVal) { mainCtx.moveTo(x, y); startedVal = true; }
      else { mainCtx.lineTo(x, y); }
    }
    mainCtx.stroke();
    mainCtx.shadowBlur = 0;

    // Draw Anomaly Markers (pulsing signal red #FF4D5E)
    for (const p of visibleData) {
      if (p.label === "ANOMALOUS") {
        const x = getX(p.index);
        const y = getYMain(p.value);

        // Glow ring
        mainCtx.fillStyle = "rgba(255, 77, 94, 0.25)";
        mainCtx.beginPath();
        mainCtx.arc(x, y, 9, 0, Math.PI * 2);
        mainCtx.fill();

        // Inner solid core
        mainCtx.fillStyle = "#ff4d5e";
        mainCtx.beginPath();
        mainCtx.arc(x, y, 4.5, 0, Math.PI * 2);
        mainCtx.fill();
        mainCtx.strokeStyle = "#ffffff";
        mainCtx.lineWidth = 1.5;
        mainCtx.stroke();
      }
    }

    // --- SCORE STRIP CANVAS DRAWING ---
    scoreCtx.clearRect(0, 0, width, scoreHeight);

    // Score Grid & Y labels
    scoreCtx.strokeStyle = "rgba(255, 255, 255, 0.05)";
    scoreCtx.fillStyle = "rgba(148, 163, 184, 0.7)";
    scoreCtx.font = "10px 'JetBrains Mono', monospace";
    scoreCtx.textAlign = "right";

    const thVal = predictions[0]?.threshold || 4.0;
    const thY = getYScore(thVal);

    // Draw applied threshold line (amber #FFB547)
    scoreCtx.strokeStyle = "#ffb547";
    scoreCtx.lineWidth = 1.4;
    scoreCtx.setLineDash([5, 4]);
    scoreCtx.beginPath();
    scoreCtx.moveTo(padLeft, thY);
    scoreCtx.lineTo(width - padRight, thY);
    scoreCtx.stroke();
    scoreCtx.setLineDash([]);

    scoreCtx.fillStyle = "#ffb547";
    scoreCtx.fillText(`TH: ${thVal.toFixed(1)}`, padLeft - 8, thY + 3);

    // Draw Score Line (cyan below threshold, red above)
    scoreCtx.lineWidth = 1.8;
    scoreCtx.beginPath();
    let startedScore = false;
    for (const p of decimated) {
      if (p.score !== null) {
        const x = getX(p.index);
        const y = getYScore(p.score);
        if (!startedScore) { scoreCtx.moveTo(x, y); startedScore = true; }
        else { scoreCtx.lineTo(x, y); }
      }
    }
    scoreCtx.strokeStyle = "rgba(61, 242, 224, 0.85)";
    scoreCtx.stroke();

    // Binary label ribbon at bottom of score strip
    const ribbonY = scoreHeight - 12;
    for (const p of decimated) {
      const x = getX(p.index);
      const isAnom = p.label === "ANOMALOUS";
      scoreCtx.fillStyle = isAnom ? "#ff4d5e" : "rgba(61, 242, 224, 0.25)";
      scoreCtx.fillRect(x - 2, ribbonY, 4, 6);
    }

    // --- SYNCHRONIZED CROSSHAIR ---
    const activeIdx = hoverIndex !== null ? hoverIndex : currentIndex;
    if (activeIdx !== null && activeIdx >= sliceStart && activeIdx <= sliceEnd) {
      const p = predictions[activeIdx];
      if (p && p.index <= effectiveMaxIndex) {
        const cx = getX(p.index);

        // Vertical crosshair line
        mainCtx.strokeStyle = "rgba(255, 255, 255, 0.35)";
        mainCtx.setLineDash([2, 2]);
        mainCtx.beginPath(); mainCtx.moveTo(cx, padTop); mainCtx.lineTo(cx, mainHeight - padBottom); mainCtx.stroke();
        scoreCtx.strokeStyle = "rgba(255, 255, 255, 0.35)";
        scoreCtx.setLineDash([2, 2]);
        scoreCtx.beginPath(); scoreCtx.moveTo(cx, padTop); scoreCtx.lineTo(cx, scoreHeight - padBottom); scoreCtx.stroke();
        mainCtx.setLineDash([]);
        scoreCtx.setLineDash([]);

        // Highlight probe point
        const cy = getYMain(p.value);
        mainCtx.fillStyle = p.label === "ANOMALOUS" ? "#ff4d5e" : "#3df2e0";
        mainCtx.beginPath(); mainCtx.arc(cx, cy, 6, 0, Math.PI * 2); mainCtx.fill();
        mainCtx.strokeStyle = "#ffffff"; mainCtx.lineWidth = 2; mainCtx.stroke();
      }
    }
  }, [predictions, windows, viewRange, hoverIndex, currentIndex, causalMode, effectiveMaxIndex]);

  useEffect(() => {
    render();
  }, [render]);

  // Mouse interactivity (zoom with wheel, pan with drag, hover crosshair)
  const handleWheel = (e) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 0.85 : 1.18;
    const currentSpan = viewRange.end - viewRange.start;
    const newSpan = Math.max(16, Math.min(predictions.length, Math.round(currentSpan * factor)));
    const center = Math.round((viewRange.start + viewRange.end) / 2);

    let newStart = Math.max(0, center - Math.round(newSpan / 2));
    let newEnd = Math.min(predictions.length, newStart + newSpan);
    if (newEnd - newStart < newSpan) {
      newStart = Math.max(0, newEnd - newSpan);
    }
    setViewRange({ start: newStart, end: newEnd });
  };

  const handleMouseDown = (e) => {
    setIsDragging(true);
    dragStartRef.current = e.clientX;
  };

  const handleMouseMove = (e) => {
    const mainCanvas = mainCanvasRef.current;
    if (!mainCanvas) return;
    const rect = mainCanvas.getBoundingClientRect();
    const padLeft = 65;
    const padRight = 30;
    const plotWidth = rect.width - padLeft - padRight;

    if (isDragging) {
      const dx = e.clientX - dragStartRef.current;
      dragStartRef.current = e.clientX;
      const span = viewRange.end - viewRange.start;
      const indexShift = Math.round((-dx / plotWidth) * span);

      let newStart = Math.max(0, Math.min(predictions.length - span, viewRange.start + indexShift));
      let newEnd = newStart + span;
      setViewRange({ start: newStart, end: newEnd });
    } else {
      // Find hovered index
      const relX = e.clientX - rect.left - padLeft;
      if (relX >= 0 && relX <= plotWidth) {
        const ratio = relX / plotWidth;
        const targetIndex = Math.round(viewRange.start + ratio * (viewRange.end - viewRange.start - 1));
        if (targetIndex >= 0 && targetIndex < predictions.length) {
          setHoverIndex(targetIndex);
        }
      } else {
        setHoverIndex(null);
      }
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleClick = () => {
    if (hoverIndex !== null && predictions[hoverIndex]) {
      const pt = predictions[hoverIndex];
      if (onSelectPoint) onSelectPoint(pt);
    }
  };

  const handleDoubleClick = () => {
    // Reset view
    setViewRange({ start: 0, end: predictions.length });
  };

  // Capture Figure for slide deck
  const handleCapture = () => {
    const mainCanvas = mainCanvasRef.current;
    if (!mainCanvas) return;
    const result = exportCanvasAsPng(mainCanvas, `sentinel-stream-run-${runMetadata.run_id || "demo"}.png`, {
      run_id: runMetadata.run_id || "synthetic-fixture-v1",
      scope: runMetadata.scope || "synthetic_smoke"
    });
    if (onCaptureFigure && result) onCaptureFigure(result);
  };

  const activePoint = hoverIndex !== null ? predictions[hoverIndex] : (predictions[currentIndex] || null);

  return (
    <div className="glass-panel" ref={containerRef} style={{ padding: "20px 24px", position: "relative" }}>
      {/* Chart Top Header & Legend */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "18px" }}>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-white)", letterSpacing: "0.04em" }}>
            CAUSAL SIGNAL & THRESHOLD TRACE
          </span>

          {/* Color Meaning Legend */}
          <div style={{ display: "flex", alignItems: "center", gap: "14px", fontSize: "0.72rem", fontFamily: "var(--font-mono)" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "var(--cyan-signal)" }}>
              <span style={{ width: "12px", height: "2.5px", background: "var(--cyan-signal)" }} /> Actual Value
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "var(--amber-threshold)" }}>
              <span style={{ width: "12px", height: "2px", borderTop: "2px dashed var(--amber-threshold)" }} /> Baseline (Median)
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "var(--red-anomaly)" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--red-anomaly)" }} /> Flagged Anomaly
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "var(--violet-window)" }}>
              <span style={{ width: "12px", height: "8px", background: "var(--violet-translucent)", border: "1px dashed var(--violet-window)" }} /> Truth Window
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <button
            className="btn-precision"
            onClick={handleCapture}
            style={{ padding: "5px 10px", fontSize: "0.74rem" }}
            title="Capture for 10-slide presentation deck (2x PNG with provenance stamp)"
          >
            <Camera size={13} />
            <span>Capture for Slides</span>
          </button>
          <button
            className="btn-precision"
            onClick={handleDoubleClick}
            style={{ padding: "5px 10px", fontSize: "0.74rem" }}
            title="Reset Zoom / Fit Range"
          >
            <RefreshCw size={13} />
            <span>Reset Zoom</span>
          </button>
        </div>
      </div>

      {/* Main Signal Canvas */}
      <div
        style={{ cursor: isDragging ? "grabbing" : "crosshair", position: "relative" }}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
      >
        <canvas ref={mainCanvasRef} style={{ width: "100%", height: "310px", display: "block" }} />
      </div>

      {/* Divider with Anomaly Score Label */}
      <div style={{ padding: "8px 0 4px 65px", fontSize: "0.72rem", fontFamily: "var(--font-mono)", color: "var(--text-dim)", textTransform: "uppercase" }}>
        STATISTICAL ANOMALY SCORE (RESIDUAL / SCALE) & BINARY LABEL RIBBON
      </div>

      {/* Synchronized Score Strip Canvas */}
      <div
        style={{ cursor: isDragging ? "grabbing" : "crosshair", position: "relative" }}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
      >
        <canvas ref={scoreCanvasRef} style={{ width: "100%", height: "140px", display: "block" }} />
      </div>

      {/* Synced Crosshair Tooltip Bar */}
      {activePoint && (
        <div
          style={{
            marginTop: "12px",
            padding: "8px 16px",
            background: "rgba(5, 7, 10, 0.9)",
            border: "1px solid var(--panel-border)",
            borderRadius: "var(--radius-sm)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: "0.75rem",
            fontFamily: "var(--font-mono)"
          }}
        >
          <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
            <span style={{ color: "var(--text-dim)" }}>Time: <strong style={{ color: "var(--text-white)" }}>{activePoint.timestamp}</strong></span>
            <span style={{ color: "var(--text-dim)" }}>Val: <strong style={{ color: "var(--cyan-signal)" }}>{activePoint.value.toFixed(2)}</strong></span>
            <span style={{ color: "var(--text-dim)" }}>Base: <strong style={{ color: "var(--amber-threshold)" }}>{activePoint.evidence?.baseline?.toFixed(2) ?? "N/A"}</strong></span>
            <span style={{ color: "var(--text-dim)" }}>Res: <strong style={{ color: "var(--text-white)" }}>{activePoint.evidence?.residual?.toFixed(2) ?? "N/A"}</strong></span>
            <span style={{ color: "var(--text-dim)" }}>Score: <strong style={{ color: activePoint.label === "ANOMALOUS" ? "var(--red-anomaly)" : "var(--cyan-signal)" }}>{activePoint.score?.toFixed(2) ?? "null (warmup)"}</strong></span>
            <span style={{ color: "var(--text-dim)" }}>Th: <strong style={{ color: "var(--amber-threshold)" }}>{activePoint.threshold.toFixed(2)}</strong></span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span
              style={{
                padding: "2px 8px",
                borderRadius: "3px",
                fontWeight: 600,
                background: activePoint.label === "ANOMALOUS" ? "rgba(255, 77, 94, 0.2)" : "rgba(61, 242, 224, 0.15)",
                color: activePoint.label === "ANOMALOUS" ? "var(--red-anomaly)" : "var(--cyan-signal)",
                border: `1px solid ${activePoint.label === "ANOMALOUS" ? "var(--red-anomaly)" : "var(--cyan-signal)"}`
              }}
            >
              {activePoint.label}
            </span>
            {activePoint.label === "ANOMALOUS" && (
              <span style={{ color: "var(--text-dim)", fontSize: "0.7rem", cursor: "pointer", textDecoration: "underline" }}>
                Click to inspect evidence [E]
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}