# 0022. BOX ACC configs phase 2: the SQL rendered from one values file, PKs from the tables' sequences, global objects .65

Date: 2026-10-28
Status: accepted (built; first run on DGBOUS to come)

## Context

`sigom-box-acc-configs-agent` phase 1 writes the gap matrix and the portfolio-properties report, no SQL. The operator
wants the SQL step, first run in DEV (DGBOUS) `[operator, 2026-10-28]`, "very similar to the FE configs agent". Facts
it must respect: a portfolio property's lists are generated (`f_GenTopicCond`) from the local property; save-time
routines compute columns (`p_StatusPortFolio`, `p_AccountPrecommit`, `p_TopicsPreCommit`); missing topics and standard
historics are global objects with `.65` PKs (ADR 0018); BOX's PK functions append **the installation's** auth code
(`.44` in Tier 2) — none hands out a `.65` PK in a Tier 2 session.

## Decision

1. **As the FE configs agent** (ADR 0006): the agent writes **`03-sql/acc-values.json`** — every value with its
   source, from the gap run's evidence and the operator's answers (the condition map, the clash choices, the
   multi-account answers, the column maps); **`scripts/render_acc_sql.py`** renders the SQL and refuses any value it
   cannot render safely (open, masked, unsourced, a condition / topic the local property lacks, a clash, a computed or
   reserved column). Delivery: PL/SQL run by the operator in SQL Developer — no Liquibase changeset (closes charter
   open question 2).
2. **Files**: a **precheck** (read-only: auth code, group / branch, the routines' signatures in `ALL_ARGUMENTS`, each
   table's sequence ahead of the highest PK of the installation's fraction, NOT NULL columns supplied, columns that
   exist, topics / accounts / conditions present, the `.65` range free) whose saved output must say `ACC PRECHECK OK`
   **for the same values** (sha256) before anything else renders; a **rehearsal** (ends `ROLLBACK`, problems
   listed); the **config** (one block, `COMMIT` only with no problem — any error undoes it all); a **verify**; the
   **rollback** rendered from the config's saved output (exactly its `CREATED|` rows, children first) and
   **`global_pk_rollback.sql`** (only the `.65` objects).
3. **Rows made the way SIGOM makes them**: topics → `p_TopicsPreCommit`; account (+ its date rule) →
   `p_AccountPrecommit`; local property + its four arrays (topics by `CODE`, conditions by the target's PK);
   portfolio property (`DESCRIPTION` = GBO's) → `f_GenTopicCond` → each list row's account → each condition's value →
   no row without an account → `p_StatusPortFolio` → `STATUS` must be `Valid` (unless `expect_invalid`, clash mode b);
   other branch rows (cross account config, conf instrument type, net CCS plan) with their natural key checked first.
4. **PKs**: the table's own sequence (`BOX_ACC.SPK_<table>` unless `pk.sequences` says otherwise — as the MBJ rows,
   BOX dev 2026-10-26) + the installation's fraction, each checked (fraction, not used). **Global objects `.65`**
   `[operator, 2026-10-28]`: a `.65` PK can be written from a Tier 2 session — the database accepts it — but no
   sequence or SIGOM function allocates it, so the number part comes from **`global_pk.<table>.start`**: the range the
   BOX team agreed (PRE, PROD — so PRE's rows never take a number PROD will use), or **`next-free`** in a DEV
   environment only (the highest `.65` + 1, read when the block runs). The precheck checks the range is free.

## Consequences

- New: `scripts/render_acc_sql.py`, its tests, `templates/acc-values.example.json`, kickoff
  `prompts/tier2-sql.md`; the charter's phase 2 "built".
- Counter mode (`T___SEQUENCE`, A-P5 c) is not supported: a table in that mode → the BOX dev names its sequence.
- A condition value that names a portfolio / counterparty / entity is refused (charter open question 10).
- The NY rows need a new gap run under ADR 0020 first (the values come from its evidence).
