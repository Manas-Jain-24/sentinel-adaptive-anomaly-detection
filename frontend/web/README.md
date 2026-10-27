# Sentinel Pulse • Result Visualization & Streaming Demo Frontend

A high-precision, causal streaming anomaly detection frontend built for **Utkrishta 2026, Challenge 2: Sentinel**.

Designed with the **"Regal Watchtower"** aesthetic: authoritative, calm, precise, and minimalist. Combines deep ink-navy midnight tones, warm parchment daytime mode, antique gold accents, and muted crimson exclusively reserved for anomalous events.

---

## Key Features

1. **Causal Streaming Replay (`ReplayTab`)**:
   - Renders time series strictly causally point-by-point. Nothing from the future is ever rendered.
   - Dynamic canvas streaming chart showing original value trajectory and pre-update rolling median ± 4.0 MAD envelope.
   - Anomaly beacons flare crimson with pulsing outer rings upon detection.
   - Warmup period shaded and labeled (`ready=false, score=null`).
   - Interactive heads-up display: live state badge (`NORMAL` / `ANOMALOUS`), standardized score meter, and microsecond detector latency.
   - Interactive evidence inspection drawer with plain-language interpretability audit and component score breakdown.
   - Replay controls: Play/pause (Space), step forward/backward (Left/Right arrows), scrubber slider, and speed multiplier (0.5x to 8x).

2. **Parallax Constellation Wallpaper (`BackgroundCanvas`)**:
   - 3-layer parallax drifting constellation responding to mouse movement and scroll.
   - Transitions to warm drifting motes and ink lines in light theme.
   - Runs at 60fps with `requestAnimationFrame`, pauses when tab is hidden, respects `prefers-reduced-motion`.

3. **Animated Hero Pulse Line (`HeroPulse`)**:
   - ECG-style radar sweep line traversing the observatory screen.
   - Flares crimson and emits ripple waves whenever an anomaly is encountered.

4. **Event-Based Evaluation (`EvaluationTab`)**:
   - Evaluates ground-truth windows against model triggers using `provisional_event_trigger_f1_v0`.
   - Displays event F1 score, precision, recall, onset detection delay (mean and median), and false triggers.
   - Dual-lane temporal alignment strip aligning truth intervals with model trigger timestamps.
   - Detailed event matching table classifying hits, misses, and false alarms.

5. **Level B Experiment Roadmap (`ExperimentsTab`)**:
   - Candidate architecture trajectory table comparing the current Rolling MAD starter with planned Level B Seasonal-Naive and Guarded Adaptive Ensemble variants.
   - Promotion gate criteria (causal isolation, event F1 superiority, microsecond runtime, schema parity).

6. **Audit Trail & Cryptographic Verification (`ManifestTab`)**:
   - Displays package version, platform, Python version, parameters, and in-process execution timing.
   - SHA-256 checksums for input and prediction artifacts with single-click clipboard copying and toast notification.

7. **Zero-Backend Architecture & Local File Loading**:
   - Comes preloaded with bundled synthetic demo run (`public/demo/`).
   - Drag-and-drop or file-picker upload for custom `predictions.jsonl`, `run.json`, and `windows.json` parsed entirely in the browser.

---

## Technology Stack

- **Framework**: React 19 + Vite 5
- **Styling**: Vanilla CSS with comprehensive CSS custom property tokens (`tokens.css`, `global.css`)
- **Graphics & Animation**: Custom HTML5 Canvas (zero chart libraries for full motion control), Lucide React icons
- **Fonts**: Google Fonts (*Cinzel*, *Cormorant Garamond*, *Inter*, *JetBrains Mono*)
- **Theme Support**: Midnight (Dark) and Parchment (Light) with `localStorage` persistence and `prefers-color-scheme` synchronization.

---

## Local Development & Setup

From the repository root:

```bash
# Navigate to web frontend directory
cd frontend/web

# Install dependencies
npm install

# Start local development server (default: http://localhost:3000)
npm run dev

# Build production bundle
npm run build

# Preview production build locally
npm run preview
```

---

## Artifact Formats & Assumptions

The frontend ingests standard Sentinel Pulse outputs without modification:

- **`predictions.jsonl`**: One JSON record per streaming point with fields:
  `series_id`, `timestamp` (ISO-8601 UTC), `value`, `score` (float | null during warmup), `threshold`, `label` (`NORMAL` | `ANOMALOUS`), `ready` (bool), `elapsed_ns`, and `evidence` object (`baseline`, `scale`, `residual`, `history_size`, `reason`, `component_scores`).
- **`run.json`**: Manifest containing `dataset_id`, `evaluation_scope`, `algorithm`, `input_sha256`, `predictions_sha256`, `config`, and execution timing.
- **`windows.json`**: Ground-truth event intervals with `series_id`, `start`, and `end`.

Missing or non-standard fields degrade gracefully without throwing runtime errors.

---

## Honesty Disclosure

- The persistent data scope badge explicitly reflects the run origin (e.g., `synthetic_smoke`).
- Evaluation metrics are clearly identified as provisional software demonstrations and do not represent official organizer benchmarks or hidden evaluation scores.
