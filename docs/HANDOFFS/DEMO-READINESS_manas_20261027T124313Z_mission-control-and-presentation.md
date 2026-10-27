# Demo readiness handoff — Sentinel Pulse

- Task ID: DEMO-READINESS (user-requested cross-owner support; not a detector task)
- Developer: Manas
- Original owner: Mayank for the Mission Control UI/presentation workstream
- Status: IN_REVIEW
- Branch: `codex/demo-readiness`, based on local `origin/main` at `4a46101ce412c8c586e80007c206c559ee77a9c4`
- Implementation commit reference: `a342650c1112a0e0eaf8694bb5609d2fd216ede5`
- Shared location: `origin/codex/demo-readiness`; open PR [#10](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/10); not merged

## Objective and scope

Make the existing Sentinel Pulse synthetic demo internally consistent and prepare an evidence-based
10-slide Challenge 2 presentation. This work does not complete MN-05, choose the final detector, or
claim official benchmark performance. The user authorized updating GitHub and preparing the demo and
deck. Do not merge `main` without authorization.

## Implementation completed

- Rebuilt the bundled run from `frontend/web/public/demo/stream.csv` using the repository CLI and
  `configs/starter.json`; regenerated predictions, manifest, and provisional evaluation from the
  same input and two synthetic windows.
- Current artifact identity: scope `synthetic_smoke`, dataset `synthetic-mission-control-v1`,
  120 observations, 112 ready, TP/FP/FN `2/0/0`, provisional F1 `1.0`, mean/p95 event delay
  `60/60s`, detector total `1,774,600ns`. This is one fixture run, not a detector benchmark.
- Current hashes: input `d498daf1209999d8c920a2b403535e2460996097f664e993beae15f732651de0`, predictions
  `31ca47029d0b55cd916dfb5b6dd7bf259fc4e7217607dd9c6c80e035e7584fd2`, windows
  `bd3800584322f33119edb2ea972552f20dc5ca52257e9b9007b581e9b7b8b6fb`.
- Removed fake/planned model-comparison rows and the default “first row wins” badge. Missing run
  comparisons and P95 inference are shown as unavailable. Overview trace uses saved detector output,
  not random flags. The manifest page hashes the original JSONL text to avoid numeric reserialization
  changing the digest.
- Added `scripts/build_demo_artifacts.py`, UI run instructions, and root README links.
- Created `deliverables/Sentinel_Pulse_Challenge_2_Final_v2.pptx`: exactly 10 slides, one native
  result table, supplied AI/ML judging rubric and judges, real synthetic alert evidence, and explicit
  official-data/scorer blockers. Deck is editable. Rendered and visually inspected all ten slides;
  finalizer reported 10 slides, 0 package/layout findings, and successful re-import.
- A separate pre-existing untracked draft deck and `scripts/generate_presentation.py` were found in
  the workspace. They contain unsupported claims (for example, 609 tests and speed metrics). They
  were left untouched and are not included in this work.

## Files changed by this work

- `README.md`
- `frontend/web/README.md`
- `frontend/web/public/demo/{stream.csv,predictions.jsonl,run.json,evaluation.json,results.jsonl}`
- `frontend/web/src/App.jsx`
- `frontend/web/src/components/{LandingHeroWaveform.jsx,LeaderboardTable.jsx,ManifestView.jsx,TopBar.jsx}`
- `frontend/web/src/hooks/useRunData.js`
- `frontend/web/src/views/{ComparisonView.jsx,ManifestView.jsx,OverviewView.jsx}`
- `scripts/build_demo_artifacts.py`
- `deliverables/Sentinel_Pulse_Challenge_2_Final_v2.pptx`
- `tasks/MANAS.md`

## Actual verification

- `.venv\Scripts\python.exe scripts\build_demo_artifacts.py` — completed successfully.
- `.venv\Scripts\python.exe -m pytest -q` — 266 passed, 1 skipped. Skip: test requires Windows
  symlink privilege (`WinError 1314`).
- From `frontend/web`: `node.exe node_modules/vite/bin/vite.js build` — passed; 2,376 modules
  transformed, production bundle emitted.
- From the repository root, `.venv\Scripts\python.exe -m ruff check src tests scripts/build_demo_artifacts.py` — passed.
- From the repository root, `.venv\Scripts\python.exe -m ruff format --check src tests scripts/build_demo_artifacts.py` — passed.
- `.venv\Scripts\python.exe -m mypy` — 16 source files passed.
- `.venv\Scripts\python.exe scripts/check_repository.py` — passed (32 mandatory docs, 141 relative links, 24 unique tasks, official PDF hash).
- Whole-repository Ruff was also attempted and reports violations in the separate pre-existing untracked `scripts/generate_presentation.py`; that file was excluded from the PR.
- Deck generator/finalizer — passed with exactly 10 slides; package integrity, layout, font policy,
  native table presence and first-party import all passed. Rendered slide PNGs were visually checked.
- Browser visual inspection of the web UI — not completed: local-server access from the browser sandbox
  timed out / socket access was denied. Do not describe as passed.
- Official-data benchmark/scorer/schema validation — not run; inputs were not supplied.

## Blockers and interface dependencies

The official Challenge 2 starter pack, authorized labels and permissions, prescribed partitions,
scorer, output schema, and organizer answers to Q01/Q09 (timestamp and cadence semantics) remain
unavailable. Do not substitute NAB, guess timezone/cadence semantics, or report synthetic metrics as
official results. The current CLI remains the rolling MAD starter; no final candidate is selected.

## Exact next actions

1. Monitor PR #10 CI to completion and request/obtain Ayush's integration review plus Mayank's
   UI/presentation review; no separate comment has been posted.
2. Do not merge `main` without authorization. Ayush updates central integration records only after
   review/merge; Mayank remains the demo integration owner.
3. When official assets arrive, resolve permissions, partitions, scorer/schema and Q01/Q09 first;
   then do authorized train-only EDA and freeze an evaluation plan before claiming readiness.

## Integration and handoff state

The code and final deck are pushed on `origin/codex/demo-readiness` and shared through PR #10.
`MY-05` / official benchmark acceptance remains blocked. Ayush's CLI/central records and Mayank's live demo integration
remain review dependencies. This handoff records the actual work; it does not transfer permanent
ownership of those modules.
