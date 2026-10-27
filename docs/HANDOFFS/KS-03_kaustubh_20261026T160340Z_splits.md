# KS-03 - reviewed frozen split tooling

- Developer/original owner: Kaustubh; no transfer.
- Authored: 2026-10-26 21:33:40 +05:30 (Asia/Kolkata), 16:03:40 UTC.
- Status: IN_REVIEW; implementation tested, Ayush/Mayank human review pending.
- Branch: `feat/kaustubh/KS-01-02-03-06-data-workstream`.
- Implementation commit: `8047bc4bc7ff9c975c1901ad10af1cd26fe7e720`.
- Sharing: local only/not pushed. Another computer cannot retrieve the implementation yet.
- Objective: deterministic inventory-backed group/chronological partitions with explicit
  feature-context permission and no overlapping cross-partition finite example supports.

## Files, implementation, decisions

`src/sentinel/data/splits.py` provides SplitManifest, SplitRange, GroupAssignment, ChronologicalCut,
build_group_split, build_chronological_split, split_digest, write_split_manifest and
validate_split_manifest. `tests/data/test_splits.py` supplies 45 focused cases. Read
[DATA_SPLITS](../DATA_SPLITS.md) for field/interval semantics and executable usage, and the
[synthetic example](../data/synthetic-fixture-split.json) for actual committed output.

Group holdout uses a complete explicit group mapping, requires train plus validation, and keeps
related series together. Chronological mode uses explicit per-series train/calibration cuts; it
does not claim group-held-out generalization. Random allocation and label-dependent cut selection
are absent. No seed is needed for deterministic explicit declarations.

All indices are per-series, zero-based, exclusive stop. Target t consumes [t-L,t]. Reset warms
inside each raw partition. Carry permits preceding context and removes the previous partition's
last L targets, reserving non-overlapping supports. N=30/cuts12,22/L3 carry targets are [3,9),
[12,19),[22,30). Small segments fail rather than silently relaxing boundaries. Carry means context
permission, not checkpoint/state transfer; longer composed/model horizons need reviewed policy.

The separate `sentinel_split_v1` format embeds source hashes and canonical logical inventory
SHA256. The split digest covers its complete canonical logical JSON. Source-backed validation
rebuilds all ranges/statistics from a validated inventory and declarations, rejecting wrong
schemas/types/fields, repeated declarations, stale hashes and weakened purge/context metadata.
An externally frozen digest is required to detect intentional changes of otherwise valid cuts;
validation establishes consistency, not author authentication or organizer permission.

Existing shared Observation/FeatureFrame/config/run.json are unchanged. New data-owned schemas
await Ayush/Mayank review before adoption. No label access, raw data modification, auto-sorting,
imputation, future-fitted statistics, public NAB substitution or official result is introduced.

## Verification and review

Missing-module failure was observed before implementation. One initial tamper-test case selected
an already-zero context field; its unchanged payload correctly validated. The test was corrected
to modify the intended calibration context. No production workaround was made for that test error.

Actual final commands (repo root, Windows/Python 3.12.14), each exit 0:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/data/test_splits.py --basetemp outputs/pytest-ks03-integration
.\.venv\Scripts\python.exe -m pytest --basetemp outputs/pytest-ks03-reviewed
.\.venv\Scripts\python.exe -m ruff check --no-cache .
.\.venv\Scripts\python.exe -m ruff format --check --no-cache .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe scripts/check_repository.py
git diff --cached --check
```

Focused tests 45 passed; full suite 169 passed/1 skipped (170 collected). Ruff lint clean,
20 files formatted. Mypy 15 source files clean. Repository docs/links/tasks/PDF hash pass;
checker reruns after phase records. Windows cannot create the escaping-symlink fixture, so that
previous case still skips. Python 3.11/3.13 and Linux not executed.

The committed 16-point example validates against its actual inventory/source. It uses L2/cuts6,11
and targets [2,4),[6,9),[11,16), for W2/min_history2 software checks only. Digest:
`9c698b379793b97f7a6922baed0f6bf75de0fc5f3618413f5564d6fde6e5214f`.
It is not the W32 starter config or an official partition. An integration case independently
checks target level/delta and equality with uninterrupted RollingFeatureExtractor replay.

Independent reviewer reproduced tests/checks, probed malformed fields and many chronological
boundaries, and reported no Critical/Important/Minor findings. Scratch results are ignored under
outputs/review-ks03. Agent review is not Ayush/Mayank approval. No performance/F1 benchmark ran.

## Remaining work and exact next actions

No known phase bug remains on the executed environment. Data/horizon/permission/group declarations
remain operator responsibilities. Official assets/Q01/Q09 answers remain absent; KS-04/05 blocked.

1. Complete KS-06 synthetic stress/integration and limitations report, then independently review,
   fix findings, run all required checks and create a unique handoff/personal progress update.
2. When publication is authorized under ADR-09, push this named task-set branch and open a PR to
   main. Request Ayush manifest/order review, Mayank split/leakage review, Manas feature review.
   Do not merge main or change central integration records independently.
3. Consumer adoption must use actual declared context/targets, freeze the digest before results,
   choose lookback for the complete feature horizon, exclude context from metrics and coordinate
   any persistent detector-state policy separately. No pipeline/harness adoption is claimed yet.
4. Another machine must retrieve the real shared branch/commit after publication; local commits
   and ignored scratch outputs are not remotely accessible until that sharing step exists.

Prepared PR addition: inventory-linked explicit group/chronological splits, conservative boundary
purging, source-backed tamper checks and bounded causal feature replay parity on synthetic inputs.
