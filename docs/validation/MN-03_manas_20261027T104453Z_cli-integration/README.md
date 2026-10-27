# Synthetic CLI integration evidence

Scope: synthetic software integration only. No official/NAB data, candidate promotion,
model training or hidden evaluation. All seven CLI run/evaluate attempts succeeded.
Source: clean `beaa4182206275670c0cf02181847a07101fb4ee`; verification head adds only
README and one regression. Exact commands, hashes, resolved settings, metrics,
profiling and actual failures/checks are in verification.json. Each subdirectory
contains unchanged saved predictions/run manifest and the actual evaluation result.

`stream.csv` is hand-authored: 96 one-second points repeating [10,10.1,10,9.9], with
value 25 at index 64. `windows.json` declares exactly that synthetic point as an event.
The lag-four example is predeclared, never estimated using labels. `legacy-mad` and
`readme-quantile` use the repository's separate 16-point synthetic fixture/windows.
Both are declared wiring fixtures, not representative quality measurements.

All 16 legacy MAD semantic rows match Ayush's saved pre-integration baseline after
excluding elapsed_ns. Quantile smoke on 96 points uses 40 fallback rows (including
eight feature-warmup rows), then 56 nearest-rank rows. At index 40 normal tied scores
start an alert episode continuing through the actual spike at 64; its trigger precedes
the truth window, so provisional TP/FP/FN=0/1/1. The next high prior score raises the
threshold and ends the episode at 65. The regression preserves this limitation without
changing thresholds/labels/metric to conceal it. Seasonal lag-four also produces one
false episode. Keep MAD as the default; no model is promoted by these checks.

Reproduce using commands in verification.json with fresh output directories; elapsed
values/source revisions/environment may differ. Evaluate long saved artifacts using
this directory's windows.json and the unchanged provisional evaluator. Old fixture runs
use tests/fixtures/synthetic_windows.json. Saved output hashes must match before use.

Ayush must review the scoped additive model manifest/settings and publication retry.
Mayank can now use genuine outputs for MY-02/MY-03 without waiting for official data;
authorized-data experiments still require official pack/permissions/split/time answers.

## New-main compatibility follow-up

During integration Mayank PR #6 merged into main `b301c07`. This feature branch now
includes those original commits. Full Python checks: 609 passed, 1 Windows symlink
privilege skip. Mayank's newly merged evaluator/source tests initially failed four
lint findings and formatting. Minimal formatting/import cleanup preserves every
production evaluator function AST; no metric logic changed. Follow-up focused
evaluation/CLI/publication checks passed 58 cases.

`latest-evaluator-compatibility.json` records validation of all seven archived runs
by merged MY-01, preserving scalar counts/delays and adding its diagnostic fields.
`frontend-artifact-compatibility.json` records Node execution of Mayank's actual
parser/scalar evaluator on all seven saved runs, agreeing with Python counts/F1.
Browser rendering/build was not performed in this integration session. The parser
discards model/provenance/profiling metadata, and model-specific chart/inspector
semantics remain for Mayank review; no claim of full advanced viewer support.
Original smoke source evidence remains unchanged and identifies clean `beaa418`.
