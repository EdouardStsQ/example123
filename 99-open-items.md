# Open items — NY_SCH BOX batch jobs, Tier 2 PRE

Seeded 2026-09-29; items 4–4d updated 2026-10-01. Each item names who it waits on. Mechanism-level questions (true for any branch) are
also in [`box-batch-chain.md` §7](../../../../docs/reference/job-chains/box-batch-chain.md#7-open-questions).

| # | Item | Waits on | Blocks |
|---|---|---|---|
| 1 | **How NY BOX jobs in Tier 2 pass the book**: `PGT_NY.f_executegroup` has no `P_LABEL` / `P_SUBLABEL`; BOX "by Book" events filter on `#LABEL#`. Upgrade `PGT_NY`, a BOX-owned wrapper, `T_BOX_MBJ_PROPERTIES_S`, or other? | **BOX Lead** (checkpoint 3), after J-E6 | every "by Book" job |
| 2 | Which wrapper NY BOX jobs call (`PGT_NY` assumed) | BOX team | the `db.conf` design |
| 3 | Confirm the reference branch (proposal: SLB London `20087.4`, Tier 1) | BOX team (checkpoint 1) | the inventory |
| 4 | Tier 1 PROD `db.conf` **and `shell.conf`** saved unchanged in [`runs/_reference/tier1-prod/`](../../../_reference/tier1-prod/README.md), then `parse_job_confs.py` (J-R1); SLB's MBJ rows (J-R2). Inventory covers product chains **and** generic jobs, old names included | operator | the inventory |
| 4b | `bin/mbjbox.sh` source (J-X3): does it read `T_BOX_MBJ_PROPERTIES_S` by job name for branch / instrument / book / group? If so, item 1 may be solved without changing `PGT_NY` | operator (Unix copy), then BOX team | item 1 |
| 4c | Instrument family numbers for CAP and CDS in `GMBX<n>` (0–7 known) | BOX team | names of CAP/CDS jobs |
| 4d | Tier 2 `db.conf` + `shell.conf` (J-T5) copied into `runs/_reference/tier2-pre/` | operator / Devin | J-T5 (expect no NY BOX jobs) |
| 5 | SLB's Control-M jobs and folders in Tier 1 (J-R4); the Tier 2 Control-M folder repos | Devin / BOX team | the dependencies in the matrix |
| 6 | ~~Job-name token~~ **Closed 2026-09-30:** the label code without its `X` — `XNY02` → `GMBX3NY02D07` `[stated: operator]` | — | — |
| 7 | NY's 22 books: skill `set-up-book-labels` on [`../books/`](../books/README.md) checks their labels (Q-10f) and proposes the inserts; the BOX FE team decides the dummy and the PK rule, and runs the proposal | operator; BOX FE team | every per-book job |
| 7b | ~~Instruments per book~~ **Closed 2026-09-30:** every book × every approved instrument, plus the dummy per instrument `[stated: operator]` | — | — |
| 7c | ~~P2 vs fixed PKs~~ **Closed 2026-09-30:** books and the dummy are one skill with one PK rule (fixed PKs given by the BOX FE team, or their allocation expression) | — | — |
| 8 | Catalog fingerprint in both tiers (J-C5) | operator | catalog ✅ beyond `2735.65` |
| 9 | Who reads `T_BOX_MBJ_PROPERTIES_S` (J-E6), and engine core versions (J-E8) | operator, then BOX team | item 1; code citations |
| 10 | The FE configuration for NY_SCH in Tier 2 (FE run 7) | FE agent run | ACC jobs process nothing without it |
