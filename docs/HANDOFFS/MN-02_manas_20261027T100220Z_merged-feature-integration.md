# MN-02 merged-feature integration refresh

Developer/owner: Manas. Status: IN_REVIEW. Branch: `feat/manas/MN-02-residual`.
Base now includes reviewed main `50f40009f4ddd757b5dfb7ac1c34e379d6801ac1`.
Existing implementation: `8129bff278bd08853722bcb7dbab71293a769618`.
PR: https://github.com/Manas-Jain-24/sentinel-adaptive-anomaly-detection/pull/3

## Changes

Merged reviewed main into this feature branch; preserved complete MN-01 and MN-02
historical task records and all detector/data implementation. Reconciled only the
owned task file and detector package description. MN-01 is DONE (PR #1 merged).
Real extractor/partition consumer tests now import the merged data modules directly;
missing required integration code cannot silently skip those tests. No shared
contracts, data-owned implementation, pipeline, CLI or central integration records changed.

## Actual verification

Commands use `.venv/Scripts/python.exe` from the repository root.

- `-m pytest tests/detectors -x -q --basetemp outputs/pytest-MN02-refresh-001`: 145 passed.
- `-m pytest -q --basetemp outputs/pytest-MN02-refresh-002 --tb=short`: 336 passed,
  one Windows symlink-privilege skip. No feature-consumer skips.
- `-m ruff check .`: passed.
- `-m ruff format --check --no-cache .`: 28 files formatted.
- `-m mypy`: 17 source files passed.
- `scripts/check_repository.py`: 32 docs, 157 links, 24 tasks and PDF hash passed.
- `git diff --check`: passed.

An initial plain pytest invocation produced 237 passes and 100 setup errors because
the sandbox could not create pytest numbered directories under its default Temp.
Using a fresh repository-local `--basetemp` resolved this without source changes.
No official benchmark, data fitting, dependency addition or main merge performed.

## Next actions / sharing

Commit this resolved feature merge and push PR #3; do not merge main. Refresh PR #4
against this branch for composition tests. Reviewers: Kaustubh for feature semantics,
Mayank for causal/split correctness, Ayush for integration. Ayush must reconcile stale
central summaries after review. Default CLI remains MAD; model factory/config/metadata
integration belongs to Ayush. Official-data selection remains blocked.
At authorship the refresh is local; retrieve the final published PR head after push.
