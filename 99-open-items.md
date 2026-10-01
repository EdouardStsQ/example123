# Open items — NY_SCH BOX batch jobs, Tier 2 PRE

Seeded 2026-09-29; items 4–4d updated 2026-10-01. Each item names who it waits on. Mechanism-level questions (true for any branch) are
also in [`box-batch-chain.md` §7](../../../../docs/reference/job-chains/box-batch-chain.md#7-open-questions).

| # | Item | Waits on | Blocks |
|---|---|---|---|
| 1 | **How NY BOX jobs in Tier 2 pass the book**: `PGT_NY.f_executegroup` has no `P_LABEL` / `P_SUBLABEL`; BOX "by Book" events filter on `#LABEL#`. Upgrade `PGT_NY`, a BOX-owned wrapper, or other? **Narrowed 2026-10-01:** `mbjbox.sh` jobs are **not affected** — they take the book from their MBJ row and run through `PKG_BATCHPROCESS_MBJ`, not the wrapper `[stated: BOX dev]`. Open only for `db.conf` "by Book" jobs | **BOX Lead** (checkpoint 3), after the inventory (item 4) | `db.conf` "by Book" jobs |
| 2 | Which wrapper NY BOX jobs call (`PGT_NY` assumed) | BOX team | the `db.conf` design |
| 3 | Confirm the reference branch (proposal: SLB London `20087.4`, Tier 1) | BOX team (checkpoint 1) | the inventory |
| 4 | Tier 1 PROD `db.conf` **and `shell.conf`** saved unchanged in [`runs/_reference/tier1-prod/`](../../../_reference/tier1-prod/README.md), then `parse_job_confs.py` (J-R1); SLB's MBJ rows (J-R2). Inventory covers product chains **and** generic jobs, old names included | operator | the inventory |
| 4b | ~~What `mbjbox.sh` / `MBJBOXACC.jar` reads and calls~~ **Closed 2026-10-01:** reads `T_BOX_MBJ_PROPERTIES_S`, calls `PKG_BATCHPROCESS_MBJ`; `0000` = time `[stated: BOX dev]`. **Left:** (a) `PKG_BATCHPROCESS_MBJ` present, valid, same version and covering NY's instruments in Tier 2 (J-E9); (b) `GBOCL_MBJBATCH` + `MBJBOXACC.jar` installed on Tier 2's Unix server with `conf/BOX` pointing at Tier 2 | (a) operator; (b) BOX team / Unix | every `mbjbox.sh` job for NY |
| 4e | NY's MBJ rows (J-R2 shape, [Madrid evidence](01-evidence/J-R2-mbj-properties-madrid-REF.md)): one row per job = branch `20007.4`, instrument, group, label (the NY book's), sub-label, parallelism / MIC / monitoring copied from the reference, `INSTANZE = 'AUKI'`, `FK_PARENT` NULL, `FK_OWNER_OBJ = 35000182.65`. Screen object `35000182.65` ✅ in Tier 2, identical to Tier 1, no pre-commit (J-T8, 2026-10-01). Table structure read (32 cols, [evidence](01-evidence/J-R2b-mbj-properties-describe.md)); `RETURN_DATA` ∈ {0, 1}. **Left:** (a) `FK_CALENDAR` for NY — which calendar (probably not the reference's); (b) `RECOVER_*`, `RETURN_DATA`, `MIC_EOD` (NOT NULL) values — copy from SLB's rows (J-R2 profile query); (c) J-R2 for SLB | operator, then `sigom-box-acc-configs-agent` | every `mbjbox.sh` job for NY |
| 4c | Instrument family numbers for CAP and CDS in `GMBX<n>` (0–7 known) | BOX team | names of CAP/CDS jobs |
| 4d | Tier 2 `db.conf` + `shell.conf` (J-T5) copied into `runs/_reference/tier2-pre/` | operator / Devin | J-T5 (expect no NY BOX jobs) |
| 5 | SLB's Control-M jobs and folders in Tier 1 (J-R4); the Tier 2 Control-M folder repos | Devin / BOX team | the dependencies in the matrix |
| 6 | ~~Job-name token~~ **Closed 2026-09-30:** the label code without its `X` — `XNY02` → `GMBX3NY02D07` `[stated: operator]` | — | — |
| 7 | NY's 22 books: skill `set-up-book-labels` on [`../books/`](../books/README.md) checks their labels (Q-10f) and proposes the inserts; the BOX FE team decides the dummy and the PK rule, and runs the proposal | operator; BOX FE team | every per-book job |
| 7b | ~~Instruments per book~~ **Closed 2026-09-30:** every book × every approved instrument, plus the dummy per instrument `[stated: operator]` | — | — |
| 7c | ~~P2 vs fixed PKs~~ **Closed 2026-09-30:** books and the dummy are one skill with one PK rule (fixed PKs given by the BOX FE team, or their allocation expression) | — | — |
| 8 | Catalog fingerprint in both tiers (J-C5) | operator | catalog ✅ beyond `2735.65` |
| 9 | ~~Who reads `T_BOX_MBJ_PROPERTIES_S`~~ **Closed 2026-10-01:** `MBJBOXACC.jar` via `mbjbox.sh` `[stated: BOX dev]`. Still: where the table is in each tier (J-E6 first query), engine core versions (J-E8) | operator | code citations |
| 10 | The FE configuration for NY_SCH in Tier 2 (FE run 7) | FE agent run | ACC jobs process nothing without it |
