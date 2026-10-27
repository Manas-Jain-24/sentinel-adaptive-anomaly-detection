# Prepared PR: audit data, emit causal features, and freeze leakage-checked splits

Publication status: **shared, open [PR #2](https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/2)**,
created at the user's explicit request on 2026-10-26. Branch:
`feat/kaustubh/KS-01-02-03-06-data-workstream`; base: reviewed foundation main. No merge performed.
Earlier phase handoffs saying local-only describe historical snapshots, superseded by the
[publication handoff](../HANDOFFS/KS-06_kaustubh_20261026T163753Z_publication.md).

## Outcome

Canonical ingestion lacked provenance inventory, implemented feature frames, and frozen split
tooling. Add explicit source/permission manifests with source-backed validation, bounded causal
rolling features, deterministic group/chronological splits with boundary purging, and synthetic
robustness/integration coverage. Tasks **KS-01, KS-02, KS-03, KS-06** are ready for owner review;
**KS-04/05 remain blocked** by the confirmed missing starter pack and Q01/Q09 answers.

## Scope and contracts

- Owned source: `src/sentinel/data/inventory.py`, `features.py`, `splits.py`.
- Owned tests: `tests/data/test_inventory.py`, `test_features.py`, `test_splits.py`, `test_stress.py`.
- Data documentation/examples, unique handoffs, and `tasks/KAUSTUBH.md` updated.
- Existing Observation/FeatureFrame/FeatureExtractor, DetectorConfig, CLI/pipeline and run.json
  contracts unchanged. No new dependencies or modifications to other owners' implementations.
- New `sentinel_inventory_v1` / `sentinel_split_v1` schemas and feature constructor controls are
  proposed data-owned APIs. Ayush/Manas/Mayank review precedes shared config/harness adoption;
  no shared contract approval is claimed. No breaking change or automatic main merge.
- Data scope is synthetic software validation only. Labels never enter features or split builders.
  No official benchmark, real EDA, hidden-label tuning or public NAB substitution.

## Verification

- Final full pytest: **191 passed, 1 skipped** on Windows/Python 3.12.14 (192 collected).
- Single skip: escaping-symlink test lacks Windows privilege; run on capable CI/reviewer host.
- Ruff lint and format pass (21 files), strict mypy passes (15 source files), pip dependency check,
  repository consistency/PDF checksum and Git whitespace checks pass.
- Fresh synthetic CLI replay/evaluation and source hash/count parity pass. The artificial event
  yields provisional TP=1/FP=0/FN=0; this is wiring evidence, not official detection performance.
- Independent review after every phase. Two KS-02 issues (DST ordering, integer overflow error
  translation) received failing regressions, fixes and reviewer rechecks. No remaining findings;
  the agent reviews do not supply human approval. Python 3.11/3.13/Linux not executed here.

## Handoff and integration

Implementation commits:

| Task | Commit |
|---|---|
| KS-01 | `9092d118201c62fec318a28afc9f9670a55745a8` |
| KS-02 | `2b991a9b4b218ac74f447f0ff8b253d899cbef7a` |
| KS-03 | `8047bc4bc7ff9c975c1901ad10af1cd26fe7e720` |
| KS-06 | `04b91e86be5c5fca377c1f3049c96969c9b81318` |

See [final handoff](../HANDOFFS/KS-06_kaustubh_20261026T161521Z_final-workstream.md),
[features](../DATA_FEATURES.md), [splits](../DATA_SPLITS.md) and [stress limits](../DATA_STRESS.md).
Ayush reviews manifests/order/config integration, Manas feature semantics, Mayank split/leakage
and consumer usability. Fixed floors, contaminated warmup, sample-lag gap limitations and
persistent-state policy are explicit. Review and freeze effective feature history/context rules
before harness use. Ayush synchronizes CURRENT_STATE/TASK_BOARD/INTEGRATION after verification.

The user explicitly authorized publication and friend-agent continuation. The feature branch and
implementation commits are now retrievable; ignored smoke/review artifacts remain local.
See the [copyable agent prompt](KAUSTUBH_AGENT_PROMPT.md). When actual
official assets arrive, preserve raw bytes, confirm permission/timezone/columns, complete KS-04
organizer sample mapping, then KS-05 train-only EDA. Do not infer those answers from this fixture.
