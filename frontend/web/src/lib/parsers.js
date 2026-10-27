/**
 * Strict parsers for Sentinel Pulse artifacts with graceful degradation.
 */

export function parsePredictions(jsonlText) {
  if (!jsonlText || typeof jsonlText !== 'string') {
    return [];
  }

  const lines = jsonlText.split(/\r?\n/).filter(line => line.trim().length > 0);
  const records = [];

  for (let i = 0; i < lines.length; i++) {
    try {
      const parsed = JSON.parse(lines[i]);
      if (!parsed.series_id || !parsed.timestamp) {
        continue;
      }

      records.push({
        index: i,
        series_id: String(parsed.series_id),
        timestamp: parsed.timestamp,
        value: typeof parsed.value === 'number' ? parsed.value : 0,
        score: typeof parsed.score === 'number' ? parsed.score : null,
        threshold: typeof parsed.threshold === 'number' ? parsed.threshold : 4.0,
        label: parsed.label === 'ANOMALOUS' ? 'ANOMALOUS' : 'NORMAL',
        ready: Boolean(parsed.ready),
        elapsed_ns: typeof parsed.elapsed_ns === 'number' ? parsed.elapsed_ns : 0,
        schema_version: parsed.schema_version || '1.0',
        evidence: {
          baseline: parsed.evidence && typeof parsed.evidence.baseline === 'number' ? parsed.evidence.baseline : null,
          scale: parsed.evidence && typeof parsed.evidence.scale === 'number' ? parsed.evidence.scale : null,
          residual: parsed.evidence && typeof parsed.evidence.residual === 'number' ? parsed.evidence.residual : null,
          history_size: parsed.evidence && typeof parsed.evidence.history_size === 'number' ? parsed.evidence.history_size : 0,
          reason: (parsed.evidence && parsed.evidence.reason) || (parsed.ready ? 'score_evaluated' : 'warmup'),
          component_scores: (parsed.evidence && parsed.evidence.component_scores) || {}
        }
      });
    } catch (err) {
      console.warn(`[Sentinel Parser] Skipping malformed line ${i + 1}:`, err);
    }
  }

  return records;
}

export function parseRunManifest(jsonText) {
  if (!jsonText) return null;
  try {
    const raw = typeof jsonText === 'string' ? JSON.parse(jsonText) : jsonText;
    return {
      schema_version: raw.schema_version || '1.0',
      package_version: raw.package_version || '0.1.0',
      algorithm: raw.algorithm || 'rolling_mad_starter',
      evaluation_scope: raw.evaluation_scope || 'synthetic_smoke',
      dataset_id: raw.dataset_id || 'unknown-dataset',
      input_sha256: raw.input_sha256 || 'unknown',
      predictions_sha256: raw.predictions_sha256 || 'unknown',
      config: raw.config || {
        window_size: 32,
        min_history: 8,
        threshold: 4.0,
        scale_floor: 0.1,
        max_series: 100
      },
      python: raw.python || '3.12+',
      platform: raw.platform || 'unknown-platform',
      observations: raw.observations || 0,
      ready_observations: raw.ready_observations || 0,
      anomalous_points: raw.anomalous_points || 0,
      detector_total_ns: raw.detector_total_ns || 0,
      runtime_note: raw.runtime_note || '',
      official_submission_ready: Boolean(raw.official_submission_ready)
    };
  } catch (err) {
    console.error('[Sentinel Parser] Failed to parse run.json:', err);
    return null;
  }
}

export function parseWindows(jsonText) {
  if (!jsonText) return [];
  try {
    const raw = typeof jsonText === 'string' ? JSON.parse(jsonText) : jsonText;
    const windowList = Array.isArray(raw) ? raw : (raw.windows || []);
    return windowList
      .filter(w => w && w.series_id && w.start && w.end)
      .map(w => ({
        series_id: String(w.series_id),
        start: w.start,
        end: w.end,
        startTime: new Date(w.start).getTime(),
        endTime: new Date(w.end).getTime()
      }));
  } catch (err) {
    console.error('[Sentinel Parser] Failed to parse windows JSON:', err);
    return [];
  }
}
