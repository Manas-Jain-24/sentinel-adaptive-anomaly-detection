# KS-06 / KS-01/02/03 data continuation and integration review

- Developer/original owner: Kaustubh; user also explicitly assigned Ayush integration scope and
  confirmed both. Other owners' implementation/task files remain untouched.
- Authored: 2026-10-27 (Asia/Calcutta); filename timestamp UTC.
- Status: original KS-01/02/03/06 merged; reader/replay follow-up IN_REVIEW; KS-04/05 BLOCKED.
- Branch: `fix/kaustubh/KS-06-integration-review`, from main `8c1be6fdd167c741ad1de0123d48bda3effbab12`.
- Implementation: **05d2ee4ce733943baf46e36ee5bb40ef9aaa1594**. Later records/publication commit follows.
- Shared location: published feature PR after final verification; final PR/addendum identifies
  the actual head/CI. This record was local at authorship. No main merge by this task.
- Objective: verify original data deliverables and #7 compatibility, repair reproduced owned
  reader defects, preserve official-data blockers and provide a portable continuation record.

## Recovered state and actual work

All remote branches fetched before work; existing KS branch `954bd1b` was clean and its pull
--ff-only already current. Old branch preserved; new branch starts at reviewed fetched main.
Read AGENTS, requested common/data docs, KS handoffs, AY/Manas/Mayank handoffs, original PDF,
questions, ADRs and current unchecked submission checklist. No conversation history was needed.

Actual implementation/tests establish inventory, bounded causal features, deterministic splits
and 22 original synthetic stress cases on main. GitHub #2 merged at `50f40009f4ddd757b5dfb7ac1c34e379d6801ac1`;
Manas APPROVED at 2026-10-26T18:45:23Z, Ayush/AJCoder01 APPROVED at 2026-10-27T08:40:00Z. A prior
COMMENTED agent review is distinct; no Mayank approval is claimed. KAUSTUBH statuses now reflect
original merged software, with this new follow-up explicitly IN_REVIEW and later adoption pending.

Reviewed open #3/#4/#5/#7 heads/diffs/comments/reviews/CI. #7 at `a52dd287e276bc9f4596394934999852d7bb3d55`
keeps data source, Observation/FeatureFrame/Detector and base config unchanged. Its factory passes
explicit W/min_history/floor/sample lag and records saturated W+C support for calibrated models.
No automatic period/cadence or whole-series fitting is introduced. Snapshotting a split is only
checksum provenance, not source verification, target filtering, permissions or support enforcement.
Those remain MY-02 consumer responsibilities under Mayank. No feature/split production change needed.

Two canonical-reader defects reproduced on both main and #7: unterminated quoted numeric field
accepted at EOF, and field-size `_csv.Error` escaping expected CLI failure handling. Owned fix in
`src/sentinel/data/io.py` enables strict parser mode and wraps csv.Error as contextual ContractError.
Valid multiline/escaped quoted fields and all existing schemas remain supported. Other row failures
also identify their path. Input bytes are never rewritten and no new dependency is introduced.

`tests/data/test_io_errors.py` adds 8 cases for malformed quotes, field-limit header/body, inventory
rejection, real CLI exit 2/no success JSON/staging cleanup, and valid quoted data. After fixing a
Windows LF fixture issue, seven regressions failed/one valid control passed before production fix;
all 8 passed afterward. Files are synthetic test fixtures only, never organizer/public NAB data.

Explicit Ayush scope additionally covers14 tests in `tests/pipeline/test_replay_contract.py`, the
AY-02 contract proposal and verified central-record updates. No pipeline/detector/evaluator/frontend
implementation or another owner's personal record changed. See the
[integration handoff](AY-03_ayush_20261027T113928Z_integration-review.md) for that work and commands.

## Commands and results

Windows/Python 3.12.14, existing pinned dev environment, repository root. Use fresh output paths.

```powershell
git fetch --all
git pull --ff-only
.\.venv\Scripts\python.exe -m pytest --basetemp outputs/pytest-review-main-20261027
.\.venv\Scripts\python.exe -m pytest tests/data/test_io_errors.py -q --basetemp outputs/pytest-csv-red2-20261027 --tb=line
# Expected pre-fix exit 1, seven failed/one control passed; after reader fix:
.\.venv\Scripts\python.exe -m pytest tests/data/test_io_errors.py -q --basetemp outputs/pytest-csv-green-20261027 --tb=short
.\.venv\Scripts\python.exe -m pytest tests/data tests/pipeline -q --basetemp outputs/pytest-review-owned-20261027 --tb=short
.\.venv\Scripts\python.exe -m pytest -q --basetemp outputs/pytest-candidate-precommit-20261027 --tb=short
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/check_repository.py
git diff --check
git diff --cached --check
```

Successful commands exited 0. Exact main 266 passed / 1 skip; reader 8 pass; owned data/pipeline 189
passed / 1 skip; full pre-record candidate 288 passed / 1 skip; Ruff 27 files; mypy 16 source files.
Independent agent review found no actionable defect and reproduced 22 focused /213 data-pipeline-
foundation passing cases with 1 skip. Agent review does not confer Ayush/Manas/Mayank approval.

Exact #7 suite 609 passed / 1 skip. Disposable #7 Git archive plus only io.py/new tests631 passed/
1 skip, Ruff 50 files, mypy 23 files and repository 199 links. Default and short-quantile before/after
smokes retain all 16 semantic rows excluding elapsed_ns; default also matches main. Each synthetic
smoke provisional TP/FP/FN=1/0/0. The short quantile trace uses fallback and does not establish
longer-trace quality. No runtime benchmark/official metric/real EDA claim. Single skip is unavailable
Windows symlink privilege; remote exact-head CI verified separately (main 4 and #7 eight successes).

[Compatibility evidence](../validation/AY-03_20261027T113928Z/compatibility.json) contains actual
snapshot source/overlay hashes, commands/results and metrics. Archive imports were checked and
source provenance was explicitly unavailable; this was not a merge. Raw local run artifacts
remain under ignored outputs. Final candidate commit/README gates/remote CI are in the publication
addendum and PR so evidence is not falsely attached to an earlier head.

## Exact official blockers and next actions

Local `data/official/` contains only README. Inspected main/open PR files/discussions, repository
issues and release assets contain no official pack/access link or Q01/Q09 answer. The repo has
no issues/release assets; no participant-portal access was supplied. This is evidence about the
accessible sources, not proof about an organizer's private portal. No outside asset was downloaded.

KS-04 requires actual organizer provenance and authorized pack/development labels/access/use
permission, prescribed train/validation/test partitions, hidden-window boundary, confirmed raw
timezone/cadence/columns/missingness/order semantics. KS-05 requires KS-04 and authorized frozen
training data/labels for real EDA/train-only periodicity. Both remain **BLOCKED**. Never infer UTC,
cadence, permissions or labels, copy public NAB labels/data, or fabricate data figures/event counts.

1. Fetch the published follow-up branch and verify head/CI/reviews; inspect this handoff and README
   gates with fresh paths. Review original main and #7 separately; do not duplicate Manas's wiring.
2. Ayush reviews manifest/order/config/API/publication; Manas feature causality/calibration/support;
   Mayank split leakage/reset-carry policy/target masks and artifact consumers. Review requests and
   #7 COMMENT review are coordination, not approvals; final addendum reports what was actually sent.
3. Keep model effective support (W+C where declared), context outside metrics and source-backed split
   validation/frozen digest under MY-02. Split carry is not checkpoint permission/state transfer.
4. AY-02 implementation waits for recorded owner approval/ADR where required; full replay remains
   valid. Official scorer/schema/runtime and Q04/Q08 update/context answers also remain missing.
5. When genuine pack/answers arrive, preserve raw bytes/labels outside Git unless explicitly
   allowed, record source/permissions/hashes/partitions, then implement/test actual sample mappings
   before KS-04 completion. Perform KS-05 only on permitted training prefixes.
6. Main merge/release/submission remain separately authorized actions. After a real reviewed merge,
   Ayush reruns exact-commit gates and reconciles records. No official-data completion is claimed.
