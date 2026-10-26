# Milestones and release gates

Priorities: P0 = valid core/submission, P1 = competitive improvement/reliability, P2 = optional
research. One effort unit ~= a focused half-day with verification, not a known hackathon schedule.
Ranges overlap across people; do not sum them into a fabricated deadline. Milestones are planned
unless CURRENT_STATE provides actual evidence. INIT-01 covers M1-M3 only at initialization.

| Milestone | Objective / tasks / owners | Dependencies / priority / rough effort | Deliverables and acceptance/integration gate | Risk / fallback |
|---|---|---|---|---|
| M1 Requirements and research | INIT-01; initialization, Ayush custodian | PDF/internet; P0; 2-3 units | Official extraction/traceability, primary-source research, >=5 concepts, honest selection; inspect complete PDF | Missing assets -> explicit questions, no guessed rules |
| M2 Architecture and contracts | INIT-01; all owners review later | M1; P0; 2 units | PRD, six diagrams, typed schemas, ownership/handoff agreement; consistent docs | Incompatible assumptions -> contract process |
| M3 Repository foundation | INIT-01; Ayush integration owner | M2; P0; 2-3 units | Installable package, causal starter, synthetic tests/CLI/checks; G0 verified results | Environment issue -> stdlib core and explicit setup blocker |
| M4 Working baseline integration | AY-01/02/03, KS-01/02/03, MN-01/02/03, MY-01/02; all four | M3; P0; 6-9 parallel units | G1: independent stream replay, features, baseline/candidate, manifests, golden metrics, experiment artifacts; synthetic and permitted dev findings separate | Assets absent -> finish wiring, keep official gate blocked |
| M5 Valid Level A and advanced candidate | KS-04, AY-04, MY-04; MN-04/05; all four | M4 + organizer assets; P0 A, P1 B; 4-7 units | G2: official adapter/scorer/export parity, reproducible baseline; guarded candidate only if tested | Scorer/schema unknown -> do not claim valid submission; simplify B |
| M6 Experiments and optimization | EXP-01..07/12, KS-05/06, MN-05, MY-02, AY-06 | Frozen development splits + M5; P1; 4-7 units | Paired results, detector/Chronos-2/TimesFM-3 ablations, error slices, runtime/robustness; B promotion gate | Sparse events/overfit/model terms -> simpler A and uncertainty disclosure |
| M7 Final system integration | AY-05, MY-06; all provide handoffs | M5/M6; P0; 2-3 units | G3: reviewed candidate or A, checks, exact configs/hashes and source commit | Advanced regression -> freeze last valid A |
| M8 Viewer and demo | MY-03/05; all supply evidence | Artifacts from M4; P1 viewer/P0 demo; 3-4 units in parallel | Provenance-labeled trace/evidence, genuine comparison, offline rehearsal | UI failure -> CLI and saved/video outputs |
| M9 Performance and robustness | AY-06, KS-06, MN-04, MY-06 | Candidate integrated; P1; 2-3 units | Hardware-tagged timing/memory, gap/shift/flatline stress, no numerical regression | Costly branch -> disable/remove, rerun gates |
| M10 Submission preparation | AY-04/05, MY-05/06; all review | G2/G3, exact schema/deadline clarified; P0; 2-3 units | G4: untouched final evaluation, official predictions, exact 10 slides, demo, setup/handoff checklist | Last-minute failure -> reviewed valid baseline artifacts |

M1-M3 are completed for INIT-01's initialization scope, with actual evidence in CURRENT_STATE and
VALIDATION. M4-M10 remain planned/incomplete; official assets are still missing.

Level C tasks (MN-06, S1-S3) start after valid A and a measured B, with explicit go/no-go gates.
No plan depends on a stretch feature succeeding. First shared milestone after initialization is
M4/G1; obtaining assets/scorer/schema is an immediate external dependency, not a fabricated
completed milestone.
