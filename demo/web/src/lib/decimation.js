/**
 * Min-Max column decimation for rendering high-frequency NAB time series.
 * Preserves extreme spikes without dropping anomalies.
 */
export function decimateMinMax(data, targetWidth) {
  if (!data || data.length === 0) return [];
  if (data.length <= targetWidth * 2) return data;

  const bucketSize = data.length / targetWidth;
  const sampled = [];

  for (let i = 0; i < targetWidth; i++) {
    const start = Math.floor(i * bucketSize);
    const end = Math.min(Math.floor((i + 1) * bucketSize), data.length);
    if (start >= end) continue;

    let minPoint = data[start];
    let maxPoint = data[start];

    for (let j = start + 1; j < end; j++) {
      const pt = data[j];
      if (pt.value < minPoint.value) minPoint = pt;
      if (pt.value > maxPoint.value) maxPoint = pt;
      // Preserve any anomalous flags directly
      if (pt.label === "ANOMALOUS") {
        sampled.push(pt);
      }
    }

    if (minPoint.index < maxPoint.index) {
      sampled.push(minPoint);
      if (maxPoint !== minPoint) sampled.push(maxPoint);
    } else {
      sampled.push(maxPoint);
      if (minPoint !== maxPoint) sampled.push(minPoint);
    }
  }

  // Ensure chronological ordering and remove duplicates by index
  return sampled.filter((pt, index, self) => 
    index === self.findIndex(p => p.index === pt.index)
  ).sort((a, b) => a.index - b.index);
}