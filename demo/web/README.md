# Sentinel Pulse — Precision Mission Control Demo

Interactive demonstration, live signal oscilloscope, and artifact viewer for **Sentinel Pulse** (Utkrishta 2026, Challenge 2: Sentinel).

Designed as a flight-deck telemetry / oscilloscope instrument: **"Mission control for time"**.

## Quickstart

```bash
cd demo/web

# Install dependencies (React 19, Motion, Lucide-React)
npm install

# Run the local development server (starts on http://localhost:5174)
npm run dev

# Build the production bundle
npm run build
```

## Views & Instrument Capabilities

1. **Overview**: Live signal oscilloscope hero waveform, 3-line product pitch, real-time KPI tiles (observations, ready count, event F1, inference speed).
2. **Stream Viewer (Hero Feature)**:
   - Dual synchronized canvas strips: Actual signal (cyan `#3DF2E0`) vs Baseline expectation (amber `#FFB547`) with shaded rolling MAD envelope, flagged anomalies (red `#FF4D5E`), ground-truth anomaly windows (soft violet `#8B7CFF`), and shaded warmup region.
   - Synchronized statistical score strip with threshold line and binary label ribbon (`NORMAL` / `ANOMALOUS`).
   - Causal replay controls: Play/pause, step forward/backward, jump between anomaly flags, speed selection (0.5x to 16x), and scrubber slider.
   - Synchronized crosshair tooltip with full numerical readout.
   - Slide capture button: exports 2x resolution PNG with provenance stamps.
3. **Evidence Inspector**:
   - Ranked, filterable list of flagged timestamps.
   - "Anatomy of a Flag": Observed value, pre-update baseline, scale, residual deviation, standardized score, threshold, and margin crossed.
   - Interactive statistical residual number-line diagram.
   - Dynamically generated plain-English proof derived strictly from numeric fields.
   - Contract verification badge ("Scored before history update; zero lookahead leakage").
4. **Model Comparison**:
   - Sortable multi-run leaderboard: Event F1, Precision, Recall, Mean Delay, Latency, Throughput, Commit SHA, Status.
   - Multi-criteria radar chart across judged axes.
   - Pareto frontier scatter plot (Event F1 vs. Latency).
5. **Run Manifest & Integrity**:
   - Collapsible run metadata viewer.
   - SHA-256 verification chip: recomputes SHA-256 in-browser via `crypto.subtle` and validates against manifest.
6. **Figure Shelf**:
   - Slide deck gallery of all captured figures for the 10-slide competition presentation deck.

## Data Provenance & Honesty

- **Scope**: Labeled `synthetic_smoke` by default.
- **Metric**: Displayed as `provisional_event_trigger_f1_v0 (provisional, not the official scorer)`.
- **Contract Compliant**: All fields parsed strictly from `src/sentinel/contracts.py` schemas.