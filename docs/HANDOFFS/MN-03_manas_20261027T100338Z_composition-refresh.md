# MN-03 composition refresh

Owner: Manas. Status: IN_REVIEW. Branch: `feat/manas/MN-03-prior-quantile`.
PR: https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/4
Dependency: refreshed PR #3 at `891a853` (full SHA available in Git).
Original calibration implementation: `6480a0e0824428c34795c8863223c0a8d6cc4694`.

Merged the MN-02 branch (including reviewed main `50f4000`) into MN-03.
Preserved all three task records, detector modules and unique handoffs. Reconciled
owned package/task conflicts. Calibration/residual integration tests now require
actual modules with direct imports. No data, shared-contract/config or CLI changes.

## Actual checks

With `.venv/Scripts/python.exe`:
- `-m pytest -q --basetemp outputs/pytest-MN03-refresh-002 --tb=short`:
  434 passed, one Windows symlink privilege skip. No optional composition skips.
- `-m ruff check .`: passed.
- `-m ruff format --check --no-cache .`: 33 files formatted.
- `-m mypy`: 19 source files passed.
- `scripts/check_repository.py`: 32 docs, 170 links, 24 tasks/PDF hash passed.
- `git diff --check`: passed.

The first conflict-resolution script failed before writing due to Windows cp1252
Git-output decoding. Checks run immediately afterwards therefore reported unresolved
merge markers/collection errors; explicit UTF-8 decoding fixed the script, then all
checks above were rerun. No committed code contains conflict markers.

## Review and continuation

Review/merge PR #3 before PR #4; do not merge main automatically. Ayush owns actual
CLI/config/metadata adoption, Mayank the harness/scientific review, Kaustubh features.
Next unblocked work is MN-04 synthetic policy comparison; real-data promotion and
MN-05 selection remain blocked. MN-06 requires A/B gates. Default CLI still MAD.
At authorship this refresh is local; commit/push and use the final PR head for retrieval.
