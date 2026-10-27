# KS-01 - canonical inventory and provenance validation

- Developer/original owner: Kaustubh; no ownership transfer.
- Authored: 2026-10-26 20:50:32 +05:30 (Asia/Kolkata); filename uses 15:20:32 UTC.
- Status: IN_REVIEW. Software acceptance cases verified on synthetic data; owner review/merge pending.
- Branch: `feat/kaustubh/KS-01-inventory`.
- Reviewed starting main: `d7158d62eb8fa4e4c5d4907238d03c5989967083`.
- Implementation commit: `9092d118201c62fec318a28afc9f9670a55745a8`.
- Shared location: **local only**, in the developer checkout. No remote branch or PR exists for
  this task. Another machine cannot access the implementation until it is pushed/shared.
- Objective: auditable source/permission declarations and strict reproducible canonical-data
  inventory now, followed by actual official-data inventory once authorized assets arrive.

## Recovered project state and scope

The workspace was initially empty. The existing repository was cloned without changing any
previous checkout. Remote inspection/clone found only main and three foundation/publication
commits; no KS task was already in progress. AGENTS, README, START_HERE, CURRENT_STATE, PRD,
ARCHITECTURE, INTERFACES, IMPLEMENTATION_PLAN, task board, KAUSTUBH, INTEGRATION, HANDOFF_PROTOCOL,
EXPERIMENT_PLAN, testing strategy, ADRs and official PDF were inspected. Actual code had the
strict reader and starter detector but no inventory, features, or splits. Baseline: 24 tests pass.

KS-01 was the highest-priority unblocked assigned task. KS-04/05 remain blocked by organizer
assets/permissions/timezone/labels. No other developer's work was taken over. Central integration
records, shared contracts/config, CLI/pipeline, detectors, and evaluation were left unchanged.

## Completed implementation and files

- `src/sentinel/data/inventory.py`: frozen typed SourceSpec, SeriesInventory, SourceInventory,
  InventoryManifest; build_inventory, write_inventory, validate_inventory. Stdlib only.
- `tests/data/test_inventory.py`: hand-derived interleaved traces, normalized instants, cadence,
  one-point/extreme-finite values, declared/unknown/off-grid gaps, missing permission/source,
  schema errors, duplicate/backwards times, nonfinite values, contained paths, source mutation,
  deterministic ordering/no overwrite, strict JSON and tamper/stale-source detection.
- [Data-format documentation](../DATA_INVENTORY.md): exact fields, semantics, API, executable
  PowerShell example, operational limitations, consumer-review obligations.
- [Committed synthetic audit](../data/synthetic-fixture-inventory.json): 16 fixture observations,
  one series, 2026-01-01T00:00:00Z through 00:15:00Z, 60-second cadence, range 9.9 to 15, no gaps.
- [Personal task record](../../tasks/KAUSTUBH.md): IN_REVIEW and actual progress/remaining work.

## Decisions, interfaces, and limitations

- Keep the new `sentinel_inventory_v1` format inside the data subsystem, pending review by
  Ayush/Mayank before adoption. No existing shared interface is extended or broken, and no
  contract approval/ADR is invented. Consumers still use current v1.0 interfaces.
- Require source, permission_basis, group_id, dataset_id, and supported scope explicitly.
  These are operator assertions, not independently verified access rights or data classification.
- Read canonical input using existing data.io; enforce chronology per series without sorting
  rows. No labels, raw NAB mapping, imputation, resampling, or hidden evaluation are introduced.
- Compute descriptive full-file interval statistics offline only. Never use these to fit
  features/calibration on validation/test. Gaps need declared cadence; off-grid intervals make
  exact missing-step count unavailable. Unknown cadence produces null gap counts, not zero.
- Reject repeated source files or series spanning files until a shard contract is reviewed.
  A source has one declared group/cadence; use separate files for heterogeneous declarations.
- Integer-microsecond interval arithmetic avoids float modulo errors. Regression tests found
  and fixed rejection of valid 249-microsecond cadence and overflow from an oversized cadence int.
- Raw-byte hashes before/after parsing catch ordinary file mutation. Inputs must remain stable;
  this is not a filesystem snapshot. Exact medians retain O(N) intervals. No runtime benchmark ran.
- Deterministic JSON has LF newlines, sorted keys/sources/series, no machine/time fields, and no
  NaN/Inf. Existing manifests are not overwritten. Validation re-audits every source/statistic,
  rejecting duplicate keys, unknown fields/versions/types and stale hashes instead of repairing.

## Actual commands and results

Commands run from repository root using the installed `.venv` on Windows/Python 3.12.14:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/data --basetemp outputs/pytest-inventory-artifact-check
.\.venv\Scripts\python.exe -m pytest --basetemp outputs/pytest-ks01-final
.\.venv\Scripts\python.exe -m ruff check --no-cache .
.\.venv\Scripts\python.exe -m ruff format --check --no-cache .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/check_repository.py
git diff --check
.\.venv\Scripts\python.exe -m sentinel run --input tests/fixtures/synthetic_stream.csv --config configs/starter.json --output-dir outputs/ks01-cli-smoke-001 --dataset-id synthetic-fixture-v1 --scope synthetic_smoke
.\.venv\Scripts\python.exe -m sentinel evaluate --run-dir outputs/ks01-cli-smoke-001 --windows tests/fixtures/synthetic_windows.json
```

All commands above exited 0. Owned tests: **70 passed, 1 skipped**; full suite: **94 passed,
1 skipped** (95 collected, including all 24 foundation cases). Ruff: lint clean, 16 files
formatted. Mypy: 13 source files clean. Pip: no broken requirements. Repository checker after
the handoff/task additions: 32 mandatory documents, 95 links, 24 task IDs, PDF hash valid.
Git staged whitespace check also passed. The implementation and this continuity record are
saved in local commits on the same feature branch; no publication has occurred.

Skip: escaping-symlink test cannot create a Windows symlink (WinError 1314); run it on a capable
reviewer/CI host. Python 3.11/3.13 and Linux were not executed here. Basetemp is under ignored
outputs because default sandbox temporary-directory permissions were unsuitable. Use fresh
basetemp/output directories for reproduction. Initial system Python 3.14 venv/ensurepip setup
failed; bundled Python 3.12 was used to create the environment. Existing pinned dependencies
were installed; no pyproject/dependency pins changed. Pip was subsequently bootstrapped locally.

The first inventory test failed because the module was absent, then passed after implementation.
Two later cadence regressions were observed failing before their fixes. Full verification above
was rerun after the last source/test changes.

Synthetic CLI smoke: 16 observations, 8 ready, 1 anomalous; provisional_event_trigger_f1_v0
reported TP=1/FP=0/FN=0, F1=1.0, zero delay. This is artificial-event wiring evidence only,
**not an official result or runtime/performance measurement**. A separate Python assertion verified
that the committed audit's checksum and observation count match outputs/ks01-cli-smoke-001/run.json:
SHA256 `19f5d1794d37aa238c6420bb192f0316c03cb645e0dc3170e266f41155cb54de`.
The example also validates through validate_inventory and an owned fixture-reproducibility test.
Smoke outputs are ignored/local; the synthetic input and audited manifest are committed.

## Review, remaining work, and exact continuation

Independent agent review completed with no Critical, Important, or Minor findings. The reviewer
independently reproduced 94 passing tests/1 skipped, strict mypy (13 files), owned Ruff checks,
the committed fixture validation, and rejection of additional malformed nested manifests.
This is not a substitute for Ayush/Mayank approval.
No known failing software case remains on the executed environment. The symlink path case and
other CI environments remain unverified here. Official assets remain an external blocker.

1. Inspect the actual Git state and this handoff; reproduce the relevant checks above using fresh
   output paths. Do not treat agent review as approval from teammates.
2. When publication is authorized (ADR-09), push `feat/kaustubh/KS-01-inventory` to origin and open
   a PR to main. Do not merge main or force-push. Add the actual shared branch/PR reference in a
   later handoff or PR. Until then all implementation/continuation work remains local only.
3. Ayush reviews manifest/schema/order integration; Mayank reviews inventory usability for
   splits/evaluation. Review the new format before wiring it to shared run/harness consumers.
   Ayush alone synchronizes CURRENT_STATE/TASK_BOARD/INTEGRATION after verified integration.
4. Next assigned engineering task: **KS-02**, on a separate feature branch from the current
   reviewed base. Coordinate bounded extractor configuration with Ayush/Manas; preserve the
   existing FeatureFrame contract and test past-only causality. KS-03 follows separately.
5. When official assets arrive, follow KS-04 mapping/permission rules, then audit permitted
   canonical data with a real declared scope/source/group/cadence; never relabel this fixture NAB.

## Prepared PR summary

Title: `KS-01: audit canonical data with reproducible provenance manifests`

Canonical CSV ingestion had no auditable inventory. Add explicit source/permission/group
declarations, exact file fingerprints and per-series cadence/gap statistics, plus deterministic
JSON writing and source-backed validation. Include the synthetic fixture audit and data-owned
tests; shared inference/config/run contracts remain compatible. Scope is synthetic software
validation only, with official data still unavailable.

Validation: 94 tests passed, 1 Windows symlink case skipped; Ruff, mypy, dependency/repository
checks and existing CLI smoke passed. Request Ayush/Mayank review; link this handoff and the
implementation commit. No official benchmark result, shared-schema approval, or merge is claimed.
