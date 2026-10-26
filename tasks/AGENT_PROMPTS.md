# Portable developer prompts

Use these in Codex, Antigravity, or another compatible agent with a local clone. They implement
the same reference workflow: recover repository context, identify ownership, inspect real Git/
code/tests, implement assigned work, validate, update personal task/handoff records, prepare review.
No original conversation is required. Replace identity/task values with actual assignments.

## Universal prompt

```text
I am <Ayush|Kaustubh|Manas|Mayank>, working on <TASK-ID> in Sentinel Pulse.
Read AGENTS.md, docs/START_HERE.md, docs/CURRENT_STATE.md, my tasks/<NAME>.md,
docs/INTERFACES.md, relevant architecture/research, and applicable handoffs.
Recover context from the repository, not any prior chat. Treat the official PDF as requirements
authority; PRD/ADRs/contracts as intended behavior; Git/code/config/real tests as implementation;
task files as ownership/plans; CURRENT_STATE as a summary to verify.

Inspect git status/branch/recent history, actual owned code/config/tests, and installed environment.
Preserve unrelated uncommitted work. Use my own task feature branch from reviewed main, never a
shared working branch. Identify the next unblocked assigned task and state its scope. Implement it
within my ownership and agreed contracts; use typed doubles/synthetic fixtures when dependencies
are incomplete, clearly labeling their scope. Do not implement other owners' final modules.

Keep inference causal and label-free; never invent official assets, scorer/schema, benchmark results,
test passes, or completed work. Propose breaking contracts/major architecture changes with affected
owners and get required approval before implementation. Keep the core independent of UI/services.

Run relevant tests plus required checks from README. Fix discovered issues and report actual results.
Update my personal task file and a uniquely named docs/HANDOFFS record with branch/commit if available,
objective, completed/remaining work, decisions, tests/results, blockers/dependencies, exact next actions.
Do not edit docs/CURRENT_STATE.md, tasks/TASK_BOARD.md, or tasks/INTEGRATION.md unless I am Ayush or
explicitly authorized; report proposed summary updates via my handoff/PR. Ayush reconciles them after
integration. Do not claim local-only uncommitted work is accessible on another machine.

Prepare a reviewable PR/handoff following tasks/INTEGRATION.md. Never automatically force-push,
reset/delete branches, or merge into main without authorization. Finish with changed files,
actual checks, unresolved risks, and the exact next task. If identity or a required approval is
missing, ask for that specific information while continuing independent authorized work.
```

## Personalized starting instructions

**Ayush:** Use the universal prompt with identity Ayush and task AY-01. Own orchestration,
reproducible manifests/profiling, persistence, export, and final integration. First tasks AY-01,
AY-02 proposal, AY-03. Maintain shared summaries only from verified integrated evidence.

**Kaustubh:** Use identity Kaustubh and task KS-01. Own data/provenance, causal features, and split
manifests. First tasks KS-01, KS-02, KS-03. Official assets are absent; audit synthetic fixtures
to develop tooling and keep raw NAB adapter/real EDA blocked until inputs arrive.

**Manas:** Use identity Manas and task MN-01. Own detector baselines/residuals/thresholds/adaptation.
First tasks MN-01, MN-02 with a FeatureExtractor double, MN-03. MN-05 now includes gated Chronos-2
and TimesFM-3 forecast-to-anomaly comparisons under EXP-12. Preserve the MAD fallback and require
experiments before promoting guards/ensembles. No tuning on hidden or untouched labels.

**Mayank:** Use identity Mayank and task MY-01. Own event scoring, experiment harness, and artifact
visualization. First tasks MY-01, MY-02 with starter runner, MY-03. Retain explicit provisional
metric identity and synthetic provenance; official scorer integration is blocked until supplied.

## Resuming another agent's work

Provide identity, task ID, and the unique handoff path. Read its shared commit/PR, fetch it using
the normal authorized Git workflow, compare to actual state, run the recorded checks, then continue
the exact next actions. If the handoff says local-only, obtain a shared commit/archive first;
conversation summaries cannot transfer files between machines.
