# AY-03 / AY-02 / AY-05 integration review handoff

- Executing scope/original owners: Ayush integration and Kaustubh data, explicitly assigned by
  the user and confirmed together. Detector/evaluator/frontend ownership remains with their owners.
- Authored: 2026-10-27 (Asia/Calcutta); filename timestamp uses UTC.
- Status: AY-03 IN_REVIEW; AY-02 implementation BLOCKED on contract approval; AY-05 IN_PROGRESS.
- Branch: `fix/kaustubh/KS-06-integration-review`, from exact main `8c1be6fdd167c741ad1de0123d48bda3effbab12`.
- Implementation: **05d2ee4ce733943baf46e36ee5bb40ef9aaa1594**. This later record is documentation.
- Shared location: feature branch/PR published after final verification; the PR identifies its
  actual final head and CI. At authorship this documentation is local. Do not infer publication
  or a main merge from a prepared PR body; use the final publication addendum/remote evidence.
- Objective: review #7, finish remaining replay/error coverage without duplication, propose safe
  checkpoint boundaries, and correct integrated records only from executed/recovered evidence.

## Recovery, plan and authorization

Initial checkout was clean on KS branch `954bd1b`; no uncommitted files needed moving. First
sandbox fetch failed (`getaddrinfo thread failed to start`); approved-network `git fetch --all`
succeeded. `git pull --ff-only` on the original branch was already up to date. No reset/stash/
force push/branch deletion/main merge. A clean task branch was made from fetched main.
Exact #7 was temporarily checked out read-only, tested, then the task branch restored before edits.

Read AGENTS/README/START_HERE/CURRENT_STATE/ARCHITECTURE/INTERFACES, both assigned tasks,
INTEGRATION/HANDOFF_PROTOCOL, data inventory/features/splits/stress, KS/AY/Manas/Mayank handoffs,
original three-page PDF, questions, ADRs, traceability and submission checklist. Official page 2
requires the organizer-prepared NAB subset and page 3 organizer-schema results; no assets or exact
semantics can be inferred from that requirement. Challenge 1's run budget is not applied here.

Executed plan: recover/fetch -> review PR heads/ownership/contracts/actual CI -> reproduce defects
and write failing reader tests -> minimal owned fix -> remaining v1 replay/fallback coverage ->
checkpoint proposal without API implementation -> independent review -> exact-base/#7 compatibility
gates -> central-record corrections -> commit/candidate gates -> publish PR and request reviews.
User explicitly requested publication, completed/remaining work and both ownership scopes.

## Actual review findings and resolution

All open PRs: #3 `891a853`, #4 `8907b47`, #5 draft `9339ac2`, #7 `a52dd28`. At recovery each had
zero comments/reviews/inline threads. Four PR-matrix jobs succeeded for each; #7 additionally
had four successful push jobs. [Remote snapshot](../validation/AY-03_20261027T113928Z/remote-review.json)
records exact SHAs/job IDs. Main's exact-head check-runs also had four successes in run 40494596951.
The legacy combined-status endpoint was empty; it was not counted as CI success/failure.

#7 already includes AY-01 `a859457`, #3/#4/#5 history, factory/model config, additive metadata/
hashes/profiling and bounded Windows publication retries. Shared typed contracts, base config,
data code and final evaluator diff are unchanged. No breaking change was approved by inference.
Its proposal records scoped human implementation authorization; affected-owner approval is still
separate. Default MAD remains backward compatible in tested traces. W+C is saturated bounded
history support, not split permission/enforcement. Sample lag is not physical time after gaps.

Two inherited defects reproduced on exact #7 and main:

- CSV `s,...,"1` ending at EOF was accepted as value 1 and could be published/audited as valid.
- csv field-limit failure escaped as `_csv.Error`, bypassing expected CLI exit 2 handling.

`src/sentinel/data/io.py` now uses strict parser mode and translates csv.Error to ContractError
with input path/approximate line. Existing row errors now also identify the file. No caller API,
schema/config/dependency changed. Invalid bytes were never legitimate canonical CSV. Eight owned
regressions exercise reader/inventory/CLI and valid multiline/escaped quoting. Seven failed before
fix, one valid control passed; all eight passed after fix. Initial valid-control failure was test
fixture CRLF translation on Windows; fixed the fixture to write explicit LF before rechecking red.

`tests/pipeline/test_replay_contract.py` adds 14 cases: Protocol double/golden interleaved results,
independent replay equivalence, no read-ahead on early close, source/cardinality failures,
KeyboardInterrupt/RuntimeError/OSError cleanup after first point, manifest-write failure, preserving
file/directory collisions, missing-input CLI and real MAD reset/full-replay fallback. Caller owns
input iterator closure; closing replay does not silently consume it. No new pipeline logic or
duplicate #7 Windows retry implementation was needed. Existing retry/collision cases were reviewed.

AY-02 [proposal](AY-02_ayush_20261027T113440Z_checkpoint-proposal.md) recommends full replay now,
optional parallel state protocol later, baseline-only bundle with consumed cursor and complete
prediction prefix, all identities validated before atomic restore/publication. Stateful residual/
calibration/forecast cannot be serialized by inspecting their private fields. No new state API,
checkpoint/--resume, corrupted-state validator or approved ADR was implemented or claimed.

## Actual commands/results

All local Python commands use existing `.venv/Scripts/python.exe`, Windows/Python 3.12.14.
Use fresh paths; existing output directories are preserved. Every listed successful check exited 0.

```powershell
git fetch --all
git pull --ff-only
git switch -c fix/kaustubh/KS-06-integration-review origin/main
.\.venv\Scripts\python.exe -m pytest --basetemp outputs/pytest-review-main-20261027
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/check_repository.py
git switch --detach a52dd287e276bc9f4596394934999852d7bb3d55
.\.venv\Scripts\python.exe -m pytest -q --basetemp outputs/pytest-review-pr7-20261027
# Repeated Ruff/mypy/repository checks at #7, then restored task branch before edits.
git switch fix/kaustubh/KS-06-integration-review
.\.venv\Scripts\python.exe -m pytest tests/data/test_io_errors.py -q --basetemp outputs/pytest-csv-red2-20261027 --tb=line
# Expected exit 1: seven failed, one passed; fix reader, then:
.\.venv\Scripts\python.exe -m pytest tests/data/test_io_errors.py -q --basetemp outputs/pytest-csv-green-20261027 --tb=short
.\.venv\Scripts\python.exe -m pytest tests/data tests/pipeline -q --basetemp outputs/pytest-review-owned-20261027 --tb=short
.\.venv\Scripts\python.exe -m pytest -q --basetemp outputs/pytest-candidate-precommit-20261027 --tb=short
git diff --check
git diff --cached --check
```

- Exact main:266 passed / 1 skip, Ruff 25 files, mypy 16 source files, repository 139 links; CLI smoke
  independently reproduced from main archive with 16 points, provisional TP/FP/FN=1/0/0.
- Exact #7:609 passed / 1 skip, Ruff 48 files, mypy 23 source files, repository 199 links.
- New tests 22 passed; owned data/pipeline 189 passed / 1 skip; pre-record full candidate 288 passed/
  1 skip, Ruff 27 files, mypy 16 files. Pip check no broken requirements; repository/whitespace pass.
- Independent reviewer: no actionable findings; 22 focused and213 data/pipeline/foundation passed,
  1 skip. This is agent review, not human or named-owner approval.
- #7 Git archive plus ONLY io.py and the two new test files:631 passed / 1 skip; Ruff 50 files,
  mypy 23, repository 199 links. Default and short-quantile CLI smokes passed before/after, semantic
  rows equal excluding elapsed_ns; default also equals main. Short quantile smoke uses fallback,
  not the calibrated long-trace path. Existing long-trace quantile miss regression also passed.
- Single skip throughout: Windows lacks symlink privilege. Remote Linux/Windows matrix checked
  independently, not inferred from local results. Frontend build/browser QA not run here.

[Compatibility evidence](../validation/AY-03_20261027T113928Z/compatibility.json) stores actual
commands/stdout/stderr, source refs, overlay hashes, metrics and comparisons. Archives were extracted
only after checking every path stayed inside a fresh output directory and no links/special entries
existed. Their package imports were verified. No branch/merge was changed by compatibility testing.
Archive source provenance is explicitly unavailable; the evidence identifies ref+overlays instead
of borrowing the parent checkout's revision. Full run artifacts remain local/ignored under outputs.

Required smoke invocation (the pre-record candidate used outputs/review-main-smoke-20261027;
the evidence also records archived-main/#7 before/after paths):

```powershell
.\.venv\Scripts\python.exe -m sentinel run --input tests/fixtures/synthetic_stream.csv --config configs/starter.json --output-dir outputs/review-main-smoke-20261027 --dataset-id synthetic-fixture-v1 --scope synthetic_smoke
.\.venv\Scripts\python.exe -m sentinel evaluate --run-dir outputs/review-main-smoke-20261027 --windows tests/fixtures/synthetic_windows.json
```

No official metric/data/runtime claim: all smokes synthetic, metric_id provisional_event_trigger_f1_v0,
official_metric=false. Timing is execution evidence only, not a performance comparison.

## Remaining work, reviews and precise continuation

1. Fetch this feature PR, inspect its latest head/checks/reviews and rerun README gates on that
   exact commit. Final publication records actual head, commands and CI; main merge remains prohibited
   without authorization. CURRENT_STATE/TASK_BOARD/INTEGRATION describe audited main only.
2. Manas reviews #7 selected detector/state/feature semantics and this inherited reader fix;
   Ayush reviews public CLI/metadata/publication; Mayank reviews artifacts/metric interpretation/
   target masks. Post a scoped COMMENT review of #7; never invent an APPROVE. Request affected
   reviewers on this follow-up. Final publication addendum reports the actual communication state.
3. Coordinate #3 -> #4 -> #5 dependency history or explicit #7 aggregate review, avoid cherry-pick
   duplication, then integrate only reviewed authorized work. No such merge occurred in this task.
4. Obtain and record AY-02 Ayush/affected-owner approvals/required ADR, then implement approved
   baseline-only persistence with real corruption/resume goldens. Current fallback stays full replay.
5. Mayank retains MY-02 config/split-driven harness: source-backed inventory/split validation,
   frozen hashes, reviewed reset/carry permission, adequate W+C support, context excluded from metrics.
   Viewer adoption of #7's richer model/provenance metadata remains his review/work.
6. KS-04/05 remain BLOCKED: official organizer pack and authorized development labels, provenance/
   access permission, prescribed partitions and Q01/Q09 timezone/cadence/columns/missingness answers.
   Local data/official only README; remote files/PRs/issues/releases provide no pack/answer. A private
   participant portal was not accessible. No timezone/cadence/permissions/public NAB substitution.
7. Official scorer/schema/goldens, context/update/runtime/entrypoint/deadline answers also missing.
   No official parity, real EDA, model freeze, release or submission. Reconcile shared summaries
   again only after a real reviewed merge and fresh gates on that exact integration commit.

Relevant files: reader; two new owned test modules; AY-02 proposal; tasks/AYUSH and KAUSTUBH;
central records under explicit user scope; this handoff, the data handoff and validation JSON.
No other-owner implementation or task record, raw input/labels, secret, dependency or model changed.


### Concurrent-main preservation before publication

Main advanced to `3d18760e709c9ef4fe897d90d7dd0888c10bd046` with Mayank's separate demo/web
addition. Verified no Python/config/test/CI diff from the original audited main. Feature-only
merge `137cad38a6cb4a82971549649683a220f195abdc` preserves the upstream files unchanged;
no merge into main or other-owner edit. Refreshed exact-main archive: 266 passed / 1 Windows
symlink skip, Ruff 25 files, mypy 16, repository 139 links and README smoke TP/FP/FN=1/0/0.
Four exact-head CI jobs succeeded in run 40498576245. Initial archive pytest had 178 passed /
89 setup errors because the local harness omitted its outputs parent; created the parent and
reran successfully with fresh basetemp. Failed command is retained in compatibility evidence.
No viewer build/browser QA or comparison-result validity is claimed. Final feature candidate
is checked after this preservation/record update; PR identifies exact head and actual CI.
