# AY-01 additive manifest proposal

- Author/owner: Ayush; authored 2026-10-26 14:50:42 UTC.
- Branch: `feat/ayush/AY-01-run-provenance-profiling`, based on inspected `origin/main` at
  `d7158d62eb8fa4e4c5d4907238d03c5989967083` (publication documentation only).
- Status: implementation proposal; affected-owner review pending. No peer approval is claimed.
- Producers/consumers: Ayush replay/CLI; Mayank evaluation/harness/viewer; Kaustubh split manifests.

## Problem and compatibility

Existing v1 `run.json` has input/prediction checksums, resolved config, Python/platform,
counts and total detector process time. It cannot identify source changes, the full installed
environment, an operator-supplied split, or runtime distributions/workload. AY-01 adds nested
`provenance`, `profiling`, and `workload` objects. Existing fields, prediction schema, scope,
detector Protocol, configuration, and evaluator semantics remain compatible.

Old example: `{"schema_version":"1.0","detector_total_ns":123,...}`.
New example: the same fields plus `{"provenance":{"version":"1.0",...},
"profiling":{...},"workload":{...}}`. Readers may ignore unknown additive fields under v1.
Whole-file replay remains the recovery fallback. No official format is proposed.

## Proposed field semantics

- Source: full Git HEAD and dirty status of the tracked package checkout, including untracked
  nonignored files. Unknown/unavailable Git is explicit null plus reason, never a fabricated
  clean revision or the unrelated caller's checkout.
- Config/environment: SHA256 of UTF-8 sorted-key compact JSON with finite numbers only;
  config hashes the resolved config; environment records Python/platform/hardware and sorted
  installed distribution names/versions. Snapshot contents are included to verify each digest.
- Optional `--split-manifest PATH`: preserve exact bytes as `split-manifest.snapshot`, hash
  that snapshot, and declare checksum-only provenance. No KS-03 schema or membership validation
  is invented; absent input is null. Split bytes/labels never enter inference.
- Timing: nanoseconds using a monotonic clock; all, ready, learning-warmup, first-process-per-series
  (cold), and subsequent-process (warm) regions. Cold excludes construction and imports.
  Bounded integer histograms report nearest-rank p50/p95 **upper bounds**, with less than 1/128
  relative bin overestimate (exact through 255 ns), counts/min/max/totals. Profiling memory
  grows with duration magnitude, not stream length; no unbounded timing list is retained.
- End-to-end replay covers predictions open through close, including CSV open/read,
  parsing/routing/construction/process/serialization/writing/profiling.
  A separate prepublication duration includes provenance/setup. Exact boundaries must be recorded;
  final manifest write/rename, CLI imports/argument parsing and evaluation are excluded.
- Workload: actual point/series/readiness counts, per-series timestamp coverage, configured
  history/cardinality limits, and cadence policy. No peak-memory or benchmark claim is added.

## Validation and integration

Golden/invariant tests will verify canonical hashes, dirty/clean/unavailable source identity,
opaque split preservation and unchanged predictions, approximate quantile bounds and populations,
bounded profiling storage, explicit measured regions, existing evaluator compatibility, and
atomic failure on invalid inputs. README checks and synthetic replay/evaluation must pass.

Ayush's request authorizes AY-01 implementation for review; Mayank should review artifact semantics,
and Kaustubh split provenance, before integration. No breaking contract or architectural change
is intended. The existing manifest can be restored by removing these additive objects and the
optional split snapshot/CLI argument together; old saved runs require no migration.

This proposal is local-only until committed and shared. A final unique handoff will record actual
implementation, verification, differences from this proposal, and exact integration actions.
