/**
 * Slide-ready 2x PNG / SVG figure capture with provenance metadata stamp.
 */
export function exportCanvasAsPng(canvas, filename = "sentinel-chart.png", metadata = {}) {
  if (!canvas) return;
  
  // Create 2x resolution canvas
  const exportCanvas = document.createElement("canvas");
  const ctx = exportCanvas.getContext("2d");
  const scale = 2;
  
  exportCanvas.width = canvas.width * scale;
  exportCanvas.height = canvas.height * scale;
  ctx.scale(scale, scale);
  
  // Draw original canvas
  ctx.drawImage(canvas, 0, 0);
  
  // Draw metadata stamp in bottom-right corner
  const stampText = `Run: ${metadata.run_id || "demo"} | Scope: ${metadata.scope || "synthetic_smoke"} | Sentinel Pulse`;
  ctx.font = "11px 'JetBrains Mono', monospace";
  ctx.textAlign = "right";
  ctx.textBaseline = "bottom";
  ctx.fillStyle = "rgba(148, 163, 184, 0.7)";
  ctx.fillText(stampText, canvas.width - 12, canvas.height - 8);

  // Trigger download
  const url = exportCanvas.toDataURL("image/png");
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  return { filename, url, timestamp: new Date().toISOString() };
}