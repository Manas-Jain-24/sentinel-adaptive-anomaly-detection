/**
 * Event-based evaluator implementing `provisional_event_trigger_f1_v0`.
 * Matches the exact algorithm in src/sentinel/evaluation/reference.py.
 */

export function evaluateEvents(predictions, windows) {
  if (!predictions || predictions.length === 0) {
    return {
      metric_id: "provisional_event_trigger_f1_v0",
      official_metric: false,
      tp: 0,
      fp: 0,
      fn: windows.length,
      precision: 0,
      recall: 0,
      event_f1: 0,
      delays: [],
      mean_delay: null,
      median_delay: null,
      matched_windows: [],
      events_breakdown: []
    };
  }

  // Group windows by series_id and sort by start
  const groupedWindows = {};
  windows.forEach((win, idx) => {
    if (!groupedWindows[win.series_id]) groupedWindows[win.series_id] = [];
    groupedWindows[win.series_id].push({
      ...win,
      id: `${win.series_id}-${idx}`,
      startTime: new Date(win.start).getTime(),
      endTime: new Date(win.end).getTime()
    });
  });

  Object.values(groupedWindows).forEach(wins => {
    wins.sort((a, b) => a.startTime - b.startTime);
  });

  const matched = new Set();
  const activeEpisodes = {};
  const delays = [];
  let tp = 0;
  let fp = 0;

  const eventsBreakdown = [];

  for (let i = 0; i < predictions.length; i++) {
    const row = predictions[i];
    const series = row.series_id;
    const t = new Date(row.timestamp).getTime();
    const isAnomalous = row.label === "ANOMALOUS";

    // Episode start trigger
    if (isAnomalous && !activeEpisodes[series]) {
      const seriesWins = groupedWindows[series] || [];
      const matchIndex = seriesWins.findIndex(
        (w, wIdx) => t >= w.startTime && t <= w.endTime && !matched.has(`${series}-${wIdx}`)
      );

      if (matchIndex === -1) {
        fp += 1;
        eventsBreakdown.push({
          type: "FALSE_ALARM",
          timestamp: row.timestamp,
          series_id: series,
          score: row.score,
          threshold: row.threshold,
          reason: "Trigger outside ground-truth window or duplicate trigger"
        });
      } else {
        matched.add(`${series}-${matchIndex}`);
        tp += 1;
        const matchedWin = seriesWins[matchIndex];
        const delaySeconds = (t - matchedWin.startTime) / 1000;
        delays.push(delaySeconds);

        eventsBreakdown.push({
          type: "HIT",
          timestamp: row.timestamp,
          series_id: series,
          window: matchedWin,
          delay_seconds: delaySeconds,
          score: row.score,
          threshold: row.threshold,
          reason: "Trigger matched ground-truth window"
        });
      }
    }

    activeEpisodes[series] = isAnomalous;
  }

  // Count misses (unmatched truth windows)
  windows.forEach((w, idx) => {
    const key = `${w.series_id}-${idx}`;
    if (!matched.has(key)) {
      eventsBreakdown.push({
        type: "MISS",
        series_id: w.series_id,
        window: w,
        reason: "Ground-truth anomaly window was not triggered"
      });
    }
  });

  const fn = windows.length - tp;
  const precision = tp + fp > 0 ? tp / (tp + fp) : 0;
  const recall = tp + fn > 0 ? tp / (tp + fn) : 0;
  const event_f1 = precision + recall > 0 ? (2 * precision * recall) / (precision + recall) : 0;

  const meanDelay = delays.length > 0 ? delays.reduce((a, b) => a + b, 0) / delays.length : null;
  const sortedDelays = [...delays].sort((a, b) => a - b);
  const medianDelay = sortedDelays.length > 0
    ? (sortedDelays.length % 2 === 0
        ? (sortedDelays[sortedDelays.length / 2 - 1] + sortedDelays[sortedDelays.length / 2]) / 2
        : sortedDelays[Math.floor(sortedDelays.length / 2)])
    : null;

  return {
    metric_id: "provisional_event_trigger_f1_v0",
    official_metric: false,
    tp,
    fp,
    fn,
    precision,
    recall,
    event_f1,
    delays,
    mean_delay: meanDelay,
    median_delay: medianDelay,
    events_breakdown: eventsBreakdown
  };
}
