# MN-03: scoped detector/CLI integration proposal

Owner executing: Manas. Shared-file custodian: Ayush. Status: proposed implementation
for review, not an invented peer approval. Client date 2026-10-27, Asia/Calcutta.

Human authorization: after recommending integration now (Ayush CLI/factory/metadata,
Mayank harness in parallel), the user explicitly said "do then". This authorizes a
feature-branch integration increment across Ayush-owned CLI/pipeline and model config
examples. It does not transfer ongoing task ownership, authorize a main merge, invent
Ayush approval, or permit breaking existing contracts. Review remains required.

## Existing contract / gap

run_file always constructs RollingMADStarter and identifies rolling_mad_starter.
DetectorConfig/starter.json remains the strict five-key legacy config. Published
MN-02/03 implement scores/calibration but lack saved-run/CLI selection. AY-01 adds
source/environment hashes, explicit timing populations and checksum-only split snapshots.
CURRENT_STATE still describes initialization; actual Git/code/tests establish newer work.

## Backward-compatible change

Keep legacy config, default MAD, Detector/Prediction/Evidence and evaluation semantics.
Add optional --detector mad|zscore|residual OR --model-config PATH (mutually exclusive).
New detector-local model config carries selector, explicit seasonal use/lag and optional
complete empirical-calibration settings. Reuse existing factories/extractor/calibrator;
construct independent per-series state. Never expose guards or unloaded TSFM selectors.

Add optional keyword-only model_config to run_file; preserve all old positional calls.
Keep existing config/config_sha256 meaning; add model metadata/model_config_sha256 and
combined run_config_sha256 so model changes cannot masquerade as identical MAD configs.
Record actual feature/calibration settings, implementation paths, algorithm identity and
bounded-history lookback (W+C for saturated calibrated models), marked as not partition
validation. Existing optional split manifest remains opaque checksum provenance only.
No automatic split selection, fitting, label ingestion or guessed data semantics.

## Affected owners and review

Ayush: CLI/pipeline/manifests and additive interface documentation. Manas: selector,
factory/score semantics. Kaustubh: real feature constructor settings. Mayank: consumers,
future partition/harness adoption. No shared prediction schema or required old field
changes; no new package dependency. No architecture replacement or major/breaking ADR.
Ayush and affected-owner reviews are still pending on the integration PR.

## Verification and rollback

Before edits combined upstream snapshot: 523 passed, 1 Windows symlink privilege skip.
Test default semantic parity, actual CLI algorithm/evidence/config hashes, independent
interleaved state, quantile and seasonal composition, prefix causality, invalid settings,
output collision/error cleanup, profiling and opaque split preservation. Run full suite,
Ruff lint/format, strict mypy, repository checker and README plus model CLI smokes.
Disable options/use the unchanged starter command to return to MAD. Commit/push feature
branch and unique handoff; main and central integration records stay for authorized review.
