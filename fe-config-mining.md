# Query catalogue — BOX FE branch config mining

The queries `sigom-box-fe-configs-agent` runs (or hands to a human to run) to gather the evidence its
walk needs. Branch-agnostic: every query is parameterised, nothing here names a branch.

Companion docs: the agent's charter
[`agents/sigom-box-fe-configs-agent/AGENT.md`](../../../agents/sigom-box-fe-configs-agent/AGENT.md),
the procedure [`docs/process/03-fe-sigom-config-procedure.md`](../../process/03-fe-sigom-config-procedure.md),
and the table/field evidence in
[`fe-branch-configuration.md`](../branch-config/fe-branch-configuration.md).

**Status:** first draft. Table and schema names are confirmed (see `fe-branch-configuration.md` §2);
**column names are only confirmed where this file says so.** Several queries below are deliberately
`SELECT *` for that reason — we know the table and the join key, not the full column list. Tightening
them to explicit column lists is a task for the first real run, not something to guess at now.

---

## Conventions

**Placeholders** are written `&&NAME` (SQL\*Plus / SQLcl / SQL Developer substitution variables). If
your tool doesn't support substitution, replace the token literally. The parameters used here:

| Placeholder | Meaning | Where it comes from |
|---|---|---|
| `&&BRANCH_CODE` | The branch's business code (e.g. a 6-letter branch mnemonic) | Run input |
| `&&BRANCH_PK` | The branch's GBO primary key | **Q-G1** — never typed by hand |
| `&&FE_CONFIG_PK` | The FE configuration header PK | **Q-01** (existing) or allocated at apply time (new) |
| `&&CURVE_PK` | A fixing curve header PK | **Q-03** |

**Which database** each query runs against matters as much as the SQL. Every query below carries an
`Env` tag:

| Env tag | Meaning |
|---|---|
| `GBO` | The GBO database being mined (for a Tier 2 branch, GBO Tier 2 — `DEVENG`, `PGT_*`) |
| `BOX` | The BOX target database/environment the config will land in (`BOX_FE`) |
| `both` | Run in **both**, save two CSVs, compare them. Do not assume a Tier 1 result holds in Tier 2 |
| `shared` | `PGT_MRK` / `PGT_SYS.PGT_DOMAINS` — one copy serving both; run wherever convenient |

**Output naming.** Each query has an ID. The result CSV is named after it exactly —
`Q-G1-branch-identity.csv` — in the run's `01-evidence/` folder. The agent detects missing evidence
by filename, so the name is the contract, not a suggestion.

**Join style.** New queries below use ANSI `JOIN` syntax. Where the corpus records a query in the
bank's original comma-join form (Q-04), both are shown — they're equivalent; the ANSI form just makes
the join conditions impossible to misread when an agent is generating them.

---

## Gate queries — run these first, in order

Nothing in the walk is valid until all four gates pass. Q-G3 and Q-G4 are currently the two blocking
unknowns for any real run.

### Q-G1 — Branch identity `Env: GBO`

**Purpose:** resolve `&&BRANCH_CODE` to its GBO primary key and core attributes. Every later query
depends on `&&BRANCH_PK`; this is the only place it may come from.

```sql
SELECT *
FROM   PGT_STC.T_PGT_BRANCH_S
WHERE  UPPER(<CODE_COLUMN>) = UPPER('&&BRANCH_CODE');
```

`SELECT *` and `<CODE_COLUMN>` are both deliberate: this repo has confirmed the table, its PK values
for Madrid/London/NY, and the FK fields `FK_ENTITY` / `FK_CURRENCY` / `FK_CALENDAR` /
`FK_LOCALGROUP` — but **not** the name of the column holding the branch code or description.
`branch-config-surface.md` §6 records this table as an overloaded ~137-row registry. So: first run
`SELECT * FROM PGT_STC.T_PGT_BRANCH_S FETCH FIRST 20 ROWS ONLY;` to learn the column names, record
them in this file, then come back and parameterise properly.

**Expect:** exactly one row. Zero → the branch doesn't exist in GBO; propose the GBO handoff and stop
(`GBO-created` is a blocking gate). More than one → the code isn't unique; resolve with an SME before
proceeding.

**Capture explicitly:** `PK`, `FK_ENTITY`, `FK_CURRENCY`, `FK_CALENDAR`, `FK_LOCALGROUP`. The last one
is the branch **group** and drives the whole ACC side — see `branch-config-surface.md`.

→ `Q-G1-branch-identity.csv`

### Q-G2 — GBO configuration tree `Env: GBO`

**Purpose:** confirm the branch's GBO config tree exists and is complete, three levels deep.

```sql
SELECT bc.*
FROM   PGT_STC.T_PGT_BRANCH_CONFIG_S bc
WHERE  bc.FK_BRANCH = &&BRANCH_PK;

SELECT bi.*
FROM   PGT_STC.T_PGT_BRANCH_INST_S bi
WHERE  bi.FK_PARENT IN (
         SELECT bc.PK
         FROM   PGT_STC.T_PGT_BRANCH_CONFIG_S bc
         WHERE  bc.FK_BRANCH = &&BRANCH_PK);

SELECT bic.*
FROM   PGT_STC.T_PGT_BRANCH_INS_CONFIG_S bic
WHERE  bic.FK_PARENT IN (
         SELECT bi.PK
         FROM   PGT_STC.T_PGT_BRANCH_INST_S bi
         WHERE  bi.FK_PARENT IN (
                  SELECT bc.PK
                  FROM   PGT_STC.T_PGT_BRANCH_CONFIG_S bc
                  WHERE  bc.FK_BRANCH = &&BRANCH_PK));
```

**Expect:** at least one row at each level for a live branch. Record what `FK_MISCONFIG` on the
branch-config row resolves to — it points at GBO's own FE store (`DEVENG.T_PGT_ENGCONF_S`), which is
a *different* store from BOX's `BOX_FE.T_BOX_ENGCONF_S`. Do not conflate them.

**Known trap:** for NY in Tier 1, `FK_MISCONFIG = 2.22` did not resolve and child rows were missing.
That proved nothing about Tier 2. Absence in the wrong tier is not a finding.

→ `Q-G2-gbo-config-tree.csv` (three files, suffixed `-1`, `-2`, `-3`)

### Q-G3 — PK generation mechanism `Env: BOX` ⛔ **blocking**

**Purpose:** establish how primary keys are allocated for each table the walk writes to. Until this
is answered the agent may not emit a single `INSERT` (charter hard rule 2). This is currently the
single biggest blocker to producing executable SQL.

```sql
-- (a) Sequences that look related to the target tables
SELECT SEQUENCE_OWNER, SEQUENCE_NAME, MIN_VALUE, MAX_VALUE, INCREMENT_BY, LAST_NUMBER
FROM   ALL_SEQUENCES
WHERE  SEQUENCE_OWNER IN ('BOX_FE','PGT_SYS','PGT_STC')
ORDER  BY SEQUENCE_OWNER, SEQUENCE_NAME;

-- (b) Triggers on the target tables (a PK is often allocated here)
SELECT OWNER, TRIGGER_NAME, TRIGGER_TYPE, TRIGGERING_EVENT,
       TABLE_OWNER, TABLE_NAME, STATUS
FROM   ALL_TRIGGERS
WHERE  TABLE_OWNER = 'BOX_FE'
AND    TABLE_NAME IN (
         'T_BOX_ENGCONF_S','T_BOX_ENGCONF_X','T_BOX_ENGFCURVE_S','T_BOX_ENGLKFC_X',
         'T_BOX_ENGACCRCONF_S','T_BOX_CONFIG_ACCRUAL_S','T_BOX_FIXING_BY_INSTR_S',
         'T_BOX_ENGZCCONF_S','T_BOX_ENGCURRENCYBASIS_S','T_BOX_CONF_BY_BOOK_S');

-- (c) Column-level defaults on the PK column
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, NULLABLE, DATA_DEFAULT
FROM   ALL_TAB_COLUMNS
WHERE  OWNER = 'BOX_FE'
AND    TABLE_NAME IN (
         'T_BOX_ENGCONF_S','T_BOX_ENGCONF_X','T_BOX_ENGFCURVE_S','T_BOX_ENGLKFC_X',
         'T_BOX_ENGACCRCONF_S','T_BOX_CONFIG_ACCRUAL_S','T_BOX_FIXING_BY_INSTR_S',
         'T_BOX_ENGZCCONF_S','T_BOX_ENGCURRENCYBASIS_S','T_BOX_CONF_BY_BOOK_S')
AND    (COLUMN_NAME = 'PK' OR DATA_DEFAULT IS NOT NULL)
ORDER  BY TABLE_NAME, COLUMN_ID;
```

**Note:** `ALL_TRIGGERS.TRIGGER_BODY` is a `LONG` and won't export cleanly to CSV. Export the
metadata above, then read any relevant trigger's source separately
(`DBMS_METADATA.GET_DDL('TRIGGER', …)`).

**Interpreting it.** Four possible answers, and they are not equivalent: a sequence the application
calls; a `BEFORE INSERT` trigger that allocates silently; a column default; or **SIGOM-side
allocation in application code**, in which case none of (a)–(c) will show anything and a raw `INSERT`
may not be a safe way to create the row at all. That last case is the one that matters most —
finding nothing here is itself a significant result, not an inconclusive one.

**Also worth knowing:** the observed PK *format* (`132.21`, `20087.4`, `3.4`) is still an open
question in `sigom-reference.md`. A sequence returning plain integers wouldn't explain it, so if (a)
is the answer, something else is composing the final value — find that too.

→ `Q-G3-pk-mechanism.csv` (three files, suffixed `-sequences`, `-triggers`, `-defaults`)

### Q-G4 — Target schema completeness `Env: both` ⛔ **blocking**

**Purpose:** confirm every table the walk writes to actually exists in the target environment.
Relevant right now: Tier 2 PRE is known to be missing a substantial number of `BOX_FE` tables.

Run in **both** the reference environment (Tier 1) and the target, then diff the two CSVs. Tier 1 and
Tier 2 are separate databases, so this is a compare-two-results exercise, not a single join.

```sql
SELECT t.TABLE_NAME,
       (SELECT COUNT(*) FROM ALL_TAB_COLUMNS c
        WHERE c.OWNER = t.OWNER AND c.TABLE_NAME = t.TABLE_NAME) AS COLUMN_COUNT
FROM   ALL_TABLES t
WHERE  t.OWNER = 'BOX_FE'
AND    t.TABLE_NAME IN (
         'T_BOX_ENGCONF_S','T_BOX_ENGCONF_X','T_BOX_ENGFCURVE_S','T_BOX_ENGLKFC_X',
         'T_BOX_ENGACCRCONF_S','T_BOX_CONFIG_ACCRUAL_S','T_BOX_FIXING_BY_INSTR_S',
         'T_BOX_ENGZCCONF_S','T_BOX_ENGCURRENCYBASIS_S','T_BOX_CONF_BY_BOOK_S',
         'T_BOX_ENGDAYS_MATURED_S','T_BOX_ENGSETUP_S',
         'T_BOX_FIXING_ASSIGNMENT_S','T_BOX_BRPROCCAL_S')
ORDER  BY t.TABLE_NAME;

-- Views the walk depends on
SELECT VIEW_NAME FROM ALL_VIEWS
WHERE  OWNER = 'BOX_FE' AND VIEW_NAME = 'V_BOX_PROC_INSTR_S';
```

**Expect:** 14 table rows and 1 view row in a complete environment. A table present in Tier 1 and
absent in the target is a provisioning gap → the agent produces the provisioning artifact (schema
diff + DDL **sourced** from `cib-boxfin-dbboxfe`, never authored) and blocks. A table present in both
but with a **different column count** is more serious than an absent one: it means the environments
have diverged, and the walk's assumptions may not hold. Escalate rather than proceeding.

→ `Q-G4-schema-presence.csv` (two files, suffixed `-tier1`, `-target`)

---

## Walk queries

One per config object, numbered to match the charter's walk steps. Each has a GBO read (the evidence)
and, where useful, a BOX read (what's already there).

### Q-01 — FE configuration association: the fork `Env: BOX`

**Purpose:** the single most important question in the walk — does an FE configuration already cover
this branch? Everything downstream is either "adapt what exists" or "build new" depending on this.

```sql
SELECT x.*
FROM   BOX_FE.T_BOX_ENGCONF_X x
WHERE  x.FK_BS = &&BRANCH_PK;
```

**Expect:** zero or one row. One → capture its `FK_PARENT` as `&&FE_CONFIG_PK` and assess the
existing aggregate. Zero → `CONFIRMED_ABSENT`; the branch has no BOX FE configuration and one must be
proposed.

**If zero, also run this** — candidate configurations to rank by evidence. A matching row is a
*proposal aid* and evidence of what's structurally possible; it is never authorisation to copy a
value (charter hard rule 5):

```sql
SELECT c.PK, c.DESCRIPTION, c.FK_CURRENCY, c.FK_CALENDAR,
       c.FK_SOURCE_FRONT, c.FK_SOURCE_BACK, c.FK_CURVEMAN, c.FK_CURVEACC
FROM   BOX_FE.T_BOX_ENGCONF_S c;
```

→ `Q-01-fe-association.csv`, `Q-01b-candidate-configs.csv`

### Q-02 — Generic header `Env: GBO` + `BOX`

**Purpose:** the seven configuration defaults. GBO side is the evidence; BOX side is the target shape.

```sql
-- GBO (the evidence)
SELECT * FROM DEVENG.T_PGT_ENGCONF_S
WHERE  PK = <FK_MISCONFIG from Q-G2>;

-- BOX (existing, only if Q-01 returned a row)
SELECT * FROM BOX_FE.T_BOX_ENGCONF_S
WHERE  PK = &&FE_CONFIG_PK;
```

**Confirmed columns:** `DESCRIPTION`, `FK_CALENDAR`, `FK_CURRENCY`, `FK_CURVEMAN`, `FK_CURVEACC`,
`FK_SOURCE_FRONT`, `FK_SOURCE_BACK`.

**Sub-order for the findings:** currency + calendar first (they're the compatibility criteria), then
the two source systems, then the two curve references, then description. A Tier 1 caution worth
carrying: the ESP and SLB configurations share calendar, currency **and** both source systems, yet
use different curves. Shared scalars prove nothing about curves.

→ `Q-02-generic-gbo.csv`, `Q-02b-generic-box.csv`

### Q-03 — Fixing curve headers `Env: GBO` + `BOX`

```sql
SELECT * FROM DEVENG.T_PGT_ENGFCURVE_S
WHERE  PK IN (<FK_CURVEMAN>, <FK_CURVEACC> from Q-02);

SELECT * FROM BOX_FE.T_BOX_ENGFCURVE_S;
```

**Trap:** `Fixing Curve` appears as a SIGOM leaf under **both** `Control > Configuration` and
`Control > Historical Data`. Confirm which population you're reading before comparing.

→ `Q-03-curve-headers-gbo.csv`, `Q-03b-curve-headers-box.csv`

### Q-04 — Quote-reference array `Env: GBO` (linkage) + `shared` (references)

**Purpose:** the array of quotes behind a curve. `[confirmed: DB via BOX Lead, 2026-09-10]` — this is
the one query in the catalogue whose full join is confirmed end to end.

```sql
SELECT *
FROM        DEVENG.T_PGT_ENGLKFC_X          t1
JOIN        PGT_MRK.T_PGT_QUOTE_REFERENCE_S t3 ON t1.FK_BS          = t3.PK
JOIN        PGT_MRK.T_PGT_QUOTE_SOURCE_S    t4 ON t3.FK_QUOTESOURCE = t4.PK
JOIN        PGT_SYS.PGT_DOMAINS             t5 ON t3.FK_QUOTETYPE   = t5.PK;
```

Original comma-join form as recorded, and the BOX-side variant — **only the first table changes**,
because `PGT_MRK` and `PGT_SYS.PGT_DOMAINS` are shared by BOX and GBO:

```sql
SELECT *
FROM   BOX_FE.T_BOX_ENGLKFC_X       T1,   -- DEVENG.T_PGT_ENGLKFC_X on the GBO side
       PGT_MRK.T_PGT_QUOTE_REFERENCE_S T3,
       PGT_MRK.T_PGT_QUOTE_SOURCE_S    T4,
       PGT_SYS.PGT_DOMAINS             T5
WHERE  T1.FK_BS = T3.PK
AND    T3.FK_QUOTESOURCE = T4.PK
AND    T3.FK_QUOTETYPE   = T5.PK;
```

**Mining implication:** because the reference/source/domain tables are shared, there is no separate
"GBO version" of them to find. Only the `ENGLKFC_X` linkage rows are module- and curve-specific, and
they are the only part that needs mining per branch.

→ `Q-04-quote-array-gbo.csv`, `Q-04b-quote-array-box.csv`

### Q-05 — Accrual defaults `Env: GBO` + `BOX`

```sql
SELECT * FROM DEVENG.T_PGT_ENGACCRCONF_S WHERE FK_PARENT = <GBO config PK>;
SELECT * FROM BOX_FE.T_BOX_ENGACCRCONF_S WHERE FK_PARENT = &&FE_CONFIG_PK;
```

**Expect:** one row per in-scope instrument. Tier 1 baseline for calibration: 8 rows (ESP), 7 rows
(SLB) — different counts for two live branches, which is the point. Don't treat either as a target.

→ `Q-05-accrual-gbo.csv`, `Q-05b-accrual-box.csv`

### Q-06 — Accrual exceptions `Env: GBO` + `BOX`

```sql
SELECT * FROM DEVENG.T_PGT_CONFIG_ACCRUAL_S WHERE FK_PARENT = <GBO config PK>;
SELECT * FROM BOX_FE.T_BOX_CONFIG_ACCRUAL_S WHERE FK_PARENT = &&FE_CONFIG_PK;
```

Grain: configuration × instrument × strategy × instrument-type × **branch**. This is one of the few
child tables carrying a branch column of its own — check whether it needs a row per branch even when
the parent configuration is shared. Tier 1: 6 rows (ESP), 5 (SLB).

→ `Q-06-accrual-exceptions-gbo.csv`, `Q-06b-accrual-exceptions-box.csv`

### Q-07 — Fixing exceptions `Env: GBO` + `BOX`

**Purpose:** processed-instrument → curve override. Two objects, joined through a view.

```sql
SELECT f.*, v.*
FROM   DEVENG.T_PGT_FIXING_BY_INSTR_S f
JOIN   DEVENG.V_PGT_PROC_INSTR_S      v ON f.FK_INSTRUMENT = v.PK;

SELECT f.*, v.*
FROM   BOX_FE.T_BOX_FIXING_BY_INSTR_S f
JOIN   BOX_FE.V_BOX_PROC_INSTR_S      v ON f.FK_INSTRUMENT = v.PK;
```

**Do not confuse with `T_BOX_FIXING_ASSIGNMENT_S`** (Q-11) — separate tables, separate roles. This
one is configured; that one is derived.

→ `Q-07-fixing-exceptions-gbo.csv`, `Q-07b-fixing-exceptions-box.csv`

### Q-08 — Yield curve `Env: GBO` + `BOX`

```sql
SELECT * FROM DEVENG.T_PGT_ENGZCCONF_S WHERE FK_PARENT = <GBO config PK>;
SELECT * FROM BOX_FE.T_BOX_ENGZCCONF_S WHERE FK_PARENT = &&FE_CONFIG_PK;
```

Table name confirmed 2026-09-10; **the `FK_PARENT` join is assumed, not confirmed** — this table's
relationship to the header was an open question until the name was supplied, and the linking column
hasn't been witnessed. Verify the FK before trusting a zero-row result: an empty result from a wrong
join column looks exactly like a genuine absence. `[open-question]`

→ `Q-08-yield-curve-gbo.csv`, `Q-08b-yield-curve-box.csv`

### Q-09 — Currency basis `Env: GBO` + `BOX`

```sql
SELECT * FROM DEVENG.T_PGT_ENGCURRENCYBASIS_S WHERE FK_PARENT = <GBO config PK>;
SELECT * FROM BOX_FE.T_BOX_ENGCURRENCYBASIS_S WHERE FK_PARENT = &&FE_CONFIG_PK;
```

Same caution as Q-08 on the `FK_PARENT` assumption. This table previously had DDL but no observed
rows, so a zero-row result here is genuinely ambiguous between "not configured for this branch" and
"not used at all". `[open-question]`

→ `Q-09-currency-basis-gbo.csv`, `Q-09b-currency-basis-box.csv`

### Q-10 — Book: batch execution registration `Env: BOX` only — confirmed no GBO side

**Purpose:** the largest surface in the walk, and — per a BOX FE Developer, 2026-09-11 — not merely
configuration: a row here for `(branch, instrument)` is what registers that combination for the FE
batch to actually execute ("the books which are created there for X branch and X instrument are the
ones that are executed"). See `fe-branch-configuration.md`'s "Book — batch execution registration"
section for the full explanation. `T_BOX_CONF_BY_BOOK_S` is **confirmed new BOX functionality with no
GBO precedent** — there is no `DEVENG` twin to query, so unlike every other object in this catalogue
this one has no `Env: GBO` read. Don't go looking for one.

**Canonical query** `[confirmed: DB via BOX FE Developer, 2026-09-11]` — this is what the Book tab of
the BOX FE MIS config actually shows, per the developer who supplied it. Prefer this joined form over
a bare `SELECT *`; it resolves `FK_INSTRUMENT` and `FK_LABEL` to their human-readable values in one
pass:

```sql
SELECT T1.PK,
       BR.PK,   BR.DESCRIPTION,                    -- branch
       T3.PK,   T3.DESCRIPTION,                    -- instrument
       T4.PK,   T4.CODE || ' - ' || T4.DESCRIPTION  -- book label
FROM   BOX_FE.T_BOX_CONF_BY_BOOK_S    T1,
       PGT_STC.T_PGT_BRANCH_S         BR,
       PGT_SYS.T_PGT_SUB_PRODUCT_S    T3,
       PGT_SYS.PGT_DOMAINS            T4
WHERE  T1.FK_BRANCH     = BR.PK
AND    T1.FK_INSTRUMENT = T3.PK
AND    T1.FK_LABEL      = T4.PK
```

Filter to the run's branch by adding `AND T1.FK_BRANCH = &&BRANCH_PK` (or `AND BR.PK = &&BRANCH_PK`,
equivalently, once the join is in place). Two things this join establishes, detailed in full in
`fe-branch-configuration.md`'s "The confirmed join" subsection: `FK_INSTRUMENT` resolves to
`PGT_SYS.T_PGT_SUB_PRODUCT_S` — the same Sub-Product level as `../box-data-model.md`'s Product
classification hierarchy, not a BOX_FE-specific instrument table; and `FK_LABEL` resolves to
`PGT_SYS.PGT_DOMAINS`, the **second** confirmed use of that generic enumeration table in this
catalogue (the first is the quote type in Q-04).

**Book, confirmed identical to the Data-Lake Book dimension.** The same developer: *"The books are
the books that we have in the Data Lake (Lago)."* This is the same dimension `../fe-raw-data-stage.md`
already confirmed independently ("RAW `BOOK` is a separate BOX/Data Lake processing Book dimension,
not the Murex buy/sell portfolio") — so the Data-Lake/Murex book enumeration for a branch (already
needed for the Control-M batch build, see `../job-chains/control-m-batch-layer.md` §4 step 2) is the
same evidence this query's `FK_LABEL` values should match against, not a second independent source to
gather.

**A promising but unverified match with Control-M's `<BOOK-ABBREV>` naming.** Sample rows from this
query include a `PGT_DOMAINS` entry `XLB01 - HPE FIXED INCOME SLB`; `control-m-batch-layer.md` §3 lists
a `<BOOK-ABBREV>` example `FIXINSLB` = "HPE FIXED INCOME SLB" — an exact description match, against
that document's own unresolved open question about where its book-abbreviation list comes from.
`[open-question]` — flagged there and here, not settled: confirm same PK space / same count before
treating `PGT_DOMAINS` as that lookup table.

**Existing Tier 1 branches as structural reference, not as a value source.** Tier 1 volumes: 373 rows
(ESP), 112 (SLB) — evidence that the count is real and branch-specific, never a target to match.
`../../process/checklists/acc-add-product-checklist.md` has a worked example of this table's shape,
including labels resolving through `PGT_DOMAINS.PK` (e.g. `3743.21 → XLB08 / SLB RATES VOL`) — useful
for understanding the columns, never for copying a value. Grain is
configuration × branch × instrument × label/book, and the runtime queue maker resolves it by
`(FK_BRANCH, FK_INSTRUMENT)`.

**Because there's no GBO side, this query alone cannot produce a proposal.** It shows what exists
today (BOX-side fact), not what NY_SCH needs. Every row this table needs for a new branch comes from a
named SME decision on which instruments/books require batch-processing, informed by the Data-Lake/
Murex book enumeration above — record that decision explicitly rather than treating a query result as
sufficient.

→ `Q-10-book-box.csv`

### Q-11 — Derived data: verify, never write `Env: BOX`

**Purpose:** confirm these follow from the config above and are not objects to create.

```sql
-- Follows the header's curve selection; its own FK_PARENT is a separate relationship
SELECT COUNT(*) AS ASSIGNMENT_ROWS
FROM   BOX_FE.T_BOX_FIXING_ASSIGNMENT_S
WHERE  FK_FIXINGCURVE_ACC = <FK_CURVEACC from Q-02>
   OR  FK_FIXINGCURVE_MAN = <FK_CURVEMAN from Q-02>;

-- Runtime activity, NOT configuration selection
SELECT FK_BRANCH, FK_INSTRUMENT, FK_CONFIG, FK_FIXCURVE, COUNT(*) AS ROWS_FOUND
FROM   BOX_FE.T_BOX_BRPROCCAL_S
WHERE  FK_BRANCH = &&BRANCH_PK
GROUP  BY FK_BRANCH, FK_INSTRUMENT, FK_CONFIG, FK_FIXCURVE;
```

**Reading it correctly:** in the Tier 1 extracts, **zero** queue rows had `FK_CONFIG` or
`FK_FIXCURVE` populated. A null there does not mean missing configuration — these tables prove
activity in the queried tier, nothing more. Do not let a null drive a config decision.

→ `Q-11-derived-verify.csv`

### Q-12 — Rule out the not-branch-scoped tables `Env: BOX`

**Purpose:** turn "these two aren't branch config" from an assertion into evidence — prove the
absence of a branch column rather than asserting it.

```sql
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM   ALL_TAB_COLUMNS
WHERE  OWNER = 'BOX_FE'
AND    TABLE_NAME IN ('T_BOX_ENGDAYS_MATURED_S','T_BOX_ENGSETUP_S')
ORDER  BY TABLE_NAME, COLUMN_ID;

SELECT * FROM BOX_FE.T_BOX_ENGDAYS_MATURED_S;
SELECT * FROM BOX_FE.T_BOX_ENGSETUP_S;
```

**Expect:** no branch/`FK_BS`/`FK_BRANCH` column in either. That result is what justifies
`NOT_BRANCH_SCOPED`. If a branch column *does* appear, the walk is missing two config objects and the
charter needs correcting — flag it loudly rather than quietly adding them.

→ `Q-12-not-branch-scoped.csv` (three files: `-columns`, `-days-matured`, `-engsetup`)

---

## Coverage check

| Walk step | Query | Confidence in the query itself |
|---|---|---|
| Gate 0a | Q-G1 | Table confirmed; **code column name unknown** |
| Gate 0b | Q-G2 | Tree confirmed |
| Gate 0d | Q-G3 | Dictionary queries are sound; **the answer is unknown** |
| Gate 0e | Q-G4 | Sound |
| 1 | Q-01 | `FK_BS` join confirmed |
| 2 | Q-02 | Columns confirmed |
| 3 | Q-03 | Table confirmed |
| 4 | Q-04 | **Full join confirmed** |
| 5 | Q-05 | Table confirmed; `FK_PARENT` assumed |
| 6 | Q-06 | Table confirmed; `FK_PARENT` assumed |
| 7 | Q-07 | **Join confirmed** |
| 8 | Q-08 | Table confirmed; join `[open-question]` |
| 9 | Q-09 | Table confirmed; join `[open-question]`; rows never observed |
| 10 | Q-10 | **Full join confirmed** (branch/sub-product/label); no GBO side exists — confirmed, not a gap (2026-09-11) |
| 11 | Q-11 | Relationships confirmed |
| 12 | Q-12 | Sound |

Three queries still rest on an assumed or unconfirmed join/column (Q-G1, Q-08, Q-09) — down from four
as of 2026-09-11, when Q-10's uncertainty was resolved the good way: not by finding the predicted GBO
table, but by a BOX FE Developer confirming none exists. Each remaining one is flagged inline above;
none should be allowed to produce a silent zero-row "absence" finding. Fix them on the first real run
and update this table — a zero-row result from a wrong join column is the most plausible way this
whole walk produces a confidently wrong answer.
