# Integrated task board

Primary maintainer: **Ayush**. Other developers update their personal task files and unique
handoffs; Ayush reconciles this board after reviewing/merging evidence. No assigned implementation
task below is marked done merely because a starter for its subsystem exists.

| Workstream | Ready first tasks | Later tasks | Externally blocked |
|---|---|---|---|
| [Ayush](AYUSH.md) | AY-03 follow-up in review; AY-01 published in #7; AY-02 proposal awaits review | AY-05 integration; AY-06 after profiling | AY-02 implementation: approved state contract; AY-04: official schema/entrypoint |
| [Kaustubh](KAUSTUBH.md) | KS-01/02/03/06 merged in #2; reader/replay follow-up in review | Review #7 feature/config/support and MY-02 split adoption | KS-04/05: pack/permissions/labels/partitions/Q01/Q09 |
| [Manas](MANAS.md) | MN-01 merged in #1; #3 residual/#4 quantile open; #7 wiring open | #5 guard/forecast draft; MN-06 after gates | MN-05: permitted data/harness/freeze gates |
| [Mayank](MAYANK.md) | MY-01/MY-03 merged in #6; MY-02 harness TODO | MY-05 preparation; #7 artifact review | MY-04: scorer; MY-06: frozen results |

All 24 task statuses/effort/dependencies are in the personal files. **INIT-01 is DONE** for the
foundation scope; verified completion and exact checks are recorded in CURRENT_STATE/VALIDATION.
No official-data experiment or submission milestone is complete.

Audit: 2026-10-27 (Asia/Calcutta), refreshed exact main `3d18760`; see
[verified state](../docs/CURRENT_STATE.md) and the
[integration handoff](../docs/HANDOFFS/AY-03_ayush_20261027T113928Z_integration-review.md).
Main suite266 passed / 1 Windows privilege skip; exact-head CI four successful jobs. Rows report
inspected integration, distinct from historical personal-task snapshots and pending follow-ups.

First integration target: **M4 / G1** in [MILESTONES](MILESTONES.md): causal baseline plus one
residual path, manifests/splits, event golden tests, reproducible comparison, CLI/optional viewer.
P0 official-data adapter/scorer/export run in parallel when assets arrive; G2 is the actual valid
fallback submission gate. Use TODO -> IN_PROGRESS -> IN_REVIEW -> DONE with BLOCKED plus reason
when genuinely dependent on missing input. Include handoff and PR references when statuses change.
