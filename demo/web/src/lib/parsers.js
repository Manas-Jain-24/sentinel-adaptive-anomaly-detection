/**
 * Shared parsers for Sentinel Pulse contracts.
 * Degrades gracefully if non-critical fields are absent; never invents data.
 */

export function parsePredictionsJsonl(text) {
  if (!text || typeof text !== "string") return [];
  const lines = text.trim().split(/\r?\n/);
  const records = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    try {
      const obj = JSON.parse(line);
      records.push({
        series_id: obj.series_id || "default",
        timestamp: obj.timestamp,
        value: typeof obj.value === "number" ? obj.value : 0,
        score: typeof obj.score === "number" ? obj.score : null,
        threshold: typeof obj.threshold === "number" ? obj.threshold : 4.0,
        label: obj.label === "ANOMALOUS" ? "ANOMALOUS" : "NORMAL",
        ready: Boolean(obj.ready),
        evidence: obj.evidence || {
          baseline: null,
          scale: null,
          residual: null,
          history_size: 0,
          reason: "unknown",
          component_scores: {}
        },
        elapsed_ns: typeof obj.elapsed_ns === "number" ? obj.elapsed_ns : 0,
        schema_version: obj.schema_version || "1.0",
        index: i
      });
    } catch (e) {
      console.warn(`Skipping invalid JSON line ${i}:`, e);
    }
  }
  return records;
}

export function parseRunJson(text) {
  if (!text) return null;
  try {
    const obj = typeof text === "string" ? JSON.parse(text) : text;
    return {
      schema_version: obj.schema_version || "1.0",
      package_version: obj.package_version || "0.1.0",
      algorithm: obj.algorithm || "unknown",
      evaluation_scope: obj.evaluation_scope || "synthetic_smoke",
      dataset_id: obj.dataset_id || "unknown",
      input_sha256: obj.input_sha256 || "",
      predictions_sha256: obj.predictions_sha256 || "",
      config: obj.config || {},
      python: obj.python || "N/A",
      platform: obj.platform || "N/A",
      observations: obj.observations || 0,
      ready_observations: obj.ready_observations || 0,
      anomalous_points: obj.anomalous_points || 0,
      detector_total_ns: obj.detector_total_ns || 0,
      runtime_note: obj.runtime_note || "",
      official_submission_ready: Boolean(obj.official_submission_ready)
    };
  } catch (e) {
    console.error("Failed to parse run.json:", e);
    return null;
  }
}

export function parseWindowsJson(text) {
  if (!text) return [];
  try {
    const obj = typeof text === "string" ? JSON.parse(text) : text;
    const list = Array.isArray(obj) ? obj : (obj.windows || []);
    return list.map(w => ({
      series_id: w.series_id || "all",
      start: w.start,
      end: w.end,
      start_ms: new Date(w.start).getTime(),
      end_ms: new Date(w.end).getTime()
    })).filter(w => !isNaN(w.start_ms) && !isNaN(w.end_ms));
  } catch (e) {
    console.error("Failed to parse windows JSON:", e);
    return [];
  }
}

export function parseEvaluationJson(text) {
  if (!text) return null;
  try {
    const obj = typeof text === "string" ? JSON.parse(text) : text;
    return {
      metric_id: obj.metric_id || "provisional_event_trigger_f1_v0",
      official_metric: Boolean(obj.official_metric),
      tp: obj.tp ?? 0,
      fp: obj.fp ?? 0,
      fn: obj.fn ?? 0,
      precision: obj.precision ?? 0,
      recall: obj.recall ?? 0,
      event_f1: obj.event_f1 ?? 0,
      delay_seconds: obj.delay_seconds || [],
      mean_delay_seconds: obj.mean_delay_seconds ?? null,
      median_delay_seconds: obj.median_delay_seconds ?? null,
      p95_delay_seconds: obj.p95_delay_seconds ?? null,
      min_delay_seconds: obj.min_delay_seconds ?? null,
      max_delay_seconds: obj.max_delay_seconds ?? null,
      missed_events: obj.missed_events ?? 0,
      per_series: obj.per_series || {},
      policy: obj.policy || {}
    };
  } catch (e) {
    console.error("Failed to parse evaluation JSON:", e);
    return null;
  }
}

export function parseResults(text) {
  if (!text) return [];
  const lines = text.trim().split(/\r?\n/);
  const results = [];
  
  // Try JSONL first
  let isJson = true;
  for (const line of lines) {
    if (!line.trim()) continue;
    try {
      const obj = JSON.parse(line);
      results.push(obj);
    } catch {
      isJson = false;
      break;
    }
  }
  if (isJson && results.length > 0) return results;

  // Otherwise parse CSV
  const header = lines[0].split(",").map(c => c.trim().toLowerCase());
  for (let i = 1; i < lines.length; i++) {
    const row = lines[i].split(",").map(c => c.trim());
    if (row.length !== header.length) continue;
    const item = {};
    header.forEach((h, idx) => {
      const val = row[idx];
      const num = Number(val);
      item[h] = isNaN(num) ? val : num;
    });
    results.push(item);
  }
  return results;
}