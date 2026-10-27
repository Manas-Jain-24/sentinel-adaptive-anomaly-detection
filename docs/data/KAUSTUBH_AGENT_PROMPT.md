# Copyable prompt for the receiving coding agent

Continue the EXISTING Sentinel hackathon project by reviewing and using Kaustubh's published PR:
https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/2

Do not start a new project. Confirm my developer identity and authorized scope before editing
owned modules if I have not already supplied them. Kaustubh is the original owner of this work;
this prompt does not authorize taking over another developer's active tasks or merging main.

1. Inspect the PR's latest head, diff, discussion and checks. Inspect local status/branch/history,
   verify the GitHub remote, and preserve all uncommitted work. Read AGENTS.md, README.md,
   docs/START_HERE.md, docs/CURRENT_STATE.md, docs/ARCHITECTURE.md, docs/INTERFACES.md,
   tasks/KAUSTUBH.md, my own personal task file, tasks/INTEGRATION.md and docs/HANDOFF_PROTOCOL.md.
   Then read docs/HANDOFFS/KS-06_kaustubh_20261026T163753Z_publication.md and data-specific docs.
   Central summaries describe merged main; this PR's code/commits/latest handoff establish its
   unmerged work. Earlier local-only phase records are historical; the branch is now published.
2. Fetch and inspect feat/kaustubh/KS-01-02-03-06-data-workstream safely. KS-01 inventory/provenance,
   KS-02 bounded causal features, KS-03 deterministic leakage-checked splits, and KS-06 synthetic
   stress/integration coverage are implemented. Local verification was 191 passed/1 skipped on
   Windows/Python 3.12; the skip required symlink privilege. Inspect current CI rather than assuming
   Python 3.11/3.13/Linux passed. Reproduce README setup/checks using fresh output directories.
3. Review the actual implementation, reproduce any issue before fixing it, and recheck each phase.
   Existing shared interfaces and the default MAD starter remain unchanged. The new feature/
   manifest/split components are not yet wired into the default CLI/harness. Obtain the required
   owner review: Ayush for manifests/order/config, Manas for feature semantics, Mayank for splits/
   leakage/consumer use. Coordinate adoption under their existing tasks and branches; continue
   only work owned by me or explicitly handed over. Do not duplicate active implementations.
4. Record sufficient effective lookback, separate context from scored targets, and review persistent
   model/calibration state policy. Fixed floors have units; contaminated warmup can define the
   reference; observation lags can lose physical seasonal meaning after gaps. Do not change shared
   contracts silently, feed labels to inference, fit future statistics, or claim synthetic tests
   establish official detection quality. Follow the repository's contract-approval process.
5. KS-04 (official adapter) and KS-05 (real EDA/train-only periodicity) remain BLOCKED: no official
   starter pack, authorized development labels, prescribed partitions or Q01/Q09 answers exist.
   The intended future intake path C:\Users\HP\Desktop\EngimaxIota hackathon\data\official\ was
   reported to contain only README; it may not exist on this machine. Request actual authorized
   inputs from the operator when needed. Do not fetch public NAB as a substitute, infer raw UTC,
   copy hidden labels or fabricate EDA. When assets/answers arrive, finish KS-04 actual sample
   mapping/tests while preserving raw bytes and separate truth, then KS-05 on frozen training data.
6. Work on an appropriate feature branch, run relevant/full tests, lint/format/types/repository
   checks and smoke tests. Fix findings, update only my own task file and a unique handoff, and
   record exact results/commits/remaining work. Ayush updates CURRENT_STATE/TASK_BOARD/INTEGRATION
   after reviewed integration. Do not reset/clean destructively, force-push, auto-merge main or
   mark blocked/review-pending tasks DONE. Report completed work and the next real unblocked action.

Proceed with authorized unblocked work, not just a generic plan. If only external blockers remain,
state the exact required inputs and leave a reproducible handoff without inventing completion.
