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

Nothing in the walk is valid until all five gates pass. **Revised 2026-09-16:** Q-G2 is *narrowed* to
its first level — see that section. **Revised 2026-09-17:** Q-G3 is ✅ **resolved** — PKs come from
`F___SEQUENCE`. **Q-G4 is now the only blocking unknown**, and it is blocked on access rather than on
anything about the schema.

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

### Q-G2 — GBO configuration tree `Env: GBO` — **narrowed 2026-09-16 to level 1**

**Purpose:** resolve `FK_MISCONFIG` on the branch-config row to the branch's GBO MIS header. That
header is the source for the MIS configuration this walk mines, so this gate is load-bearing and
stays.

> **What changed, and what didn't.** `[stated: BOX Developer via Edouard, 2026-09-16]` Instrument
> scope for a new BOX branch is chosen from **what is already created and live in BOX**, not from the
> branch's GBO instrument configuration. So the two lower levels of this query —
> `T_PGT_BRANCH_INST_S` and `T_PGT_BRANCH_INS_CONFIG_S`, the *branch-instrument* tree — are no longer
> part of the gate. **Level 1 stays.** Mining the MIS config and Fixing Curve from GBO is unchanged.
>
> **The dropped levels were also broken, which is worth keeping on record.** The first live NY_SCH
> run returned level 1 only:
>
> | Branch | `FK_BRANCH` | `bc.PK` | `FK_MISCONFIG` | Levels 2–3 |
> |---|---|---|---|---|
> | NY_SCH (Tier 2) | `20007.4` | `141.35` | `64408.35` → resolves, "Configuracion -NY" | none |
> | Madrid (Tier 1) | `22.21` | `4.21` | `12.21` | **none** |
>
> The populated `FK_PARENT` values in `T_PGT_BRANCH_INST_S` are `34.44`, `43.44`, `46.44`, `175.21`,
> `201.35` and a block `1625.44`–`1641.44`. **Neither `4.21` nor `141.35` appears among them** — and
> Madrid is unambiguously live and fully configured. So the join
> `T_PGT_BRANCH_INST_S.FK_PARENT = T_PGT_BRANCH_CONFIG_S.PK` is **wrong**, and the empty result was a
> query defect, not evidence about NY_SCH. An earlier reading of this run concluded "confirmed real
> absence"; that conclusion was wrong and is retracted here.
>
> What `FK_PARENT` actually references is left open. It is not `bc.PK`, and not `FK_MISCONFIG` either
> (neither `12.21` nor `64408.35` is in the list). It cannot be recovered from constraint metadata,
> because this schema declares **no foreign keys at all** — see
> [`box-data-model.md`](../box-data-model.md). Answering it needs a GBO developer, or an empirical
> search for which object owns e.g. PK `34.44`. Recorded rather than solved: this walk no longer needs
> it, but anyone wanting the GBO instrument tree for another purpose will.
>
> **The generic lesson, which does apply everywhere:** always run a **known-good control** before
> recording `CONFIRMED_ABSENT`. Had this query required a Madrid run alongside the target branch, the
> broken join would have surfaced in one round instead of three.

**The level-1 query — this is the gate:**

```sql
SELECT bc.*
FROM   PGT_STC.T_PGT_BRANCH_CONFIG_S bc
WHERE  bc.FK_BRANCH = &&BRANCH_PK;
```

**Expect:** exactly one row. Record `FK_MISCONFIG` — it points at GBO's own FE store
(`DEVENG.T_PGT_ENGCONF_S`), which is a *different* store from BOX's `BOX_FE.T_BOX_ENGCONF_S`. Do not
conflate them. Confirm it resolves:

```sql
SELECT * FROM DEVENG.T_PGT_ENGCONF_S WHERE PK = <FK_MISCONFIG>;
```

→ `Q-G2-gbo-config-tree.csv`

**Levels 2–3, retained for reference only — not part of the gate, and the join is known wrong:**

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

*(Do not run these as a gate. If you need them for another purpose, fix the join first and validate any fix against Madrid, which must return rows.)*

### Q-G3 — PK generation mechanism `Env: BOX` ✅ **RESOLVED 2026-09-17**

> ## ✅ Gate 0d is closed. PKs come from `F___SEQUENCE`.
>
> `[confirmed: source via BOX FE Developer, 2026-09-17]` The mechanism is a database function:
>
> ```sql
> create or replace FUNCTION F___SEQUENCE ( TABLE_NAME VARCHAR2, seq_range VARCHAR2 ) RETURN NUMBER IS
>    VALUERETURNED NUMBER;  my_autor_code NUMBER;  longitud INTEGER;
> BEGIN
>    IF TABLE_NAME IN ('T_BOX_ENGPROCESS_S','T_BOX_ENGDOM_S') THEN
>        SELECT SQ_BOX_FINANENG3.NEXTVAL INTO VALUERETURNED FROM DUAL;
>    ELSE
>        SELECT SQ_BOX_FINANENG1.NEXTVAL INTO VALUERETURNED FROM DUAL;
>    END IF;
>
>    IF (seq_range = 'X') THEN
>        IF (pkg_engcore.fractional = -1) THEN
>            SELECT auth_code INTO my_autor_code FROM gom_glb_sys.t__CORE_INFO_S;
>            longitud := length(to_char(my_autor_code));
>            pkg_engcore.fractional := my_autor_code / power(10, longitud);
>        END IF;
>        valuereturned := valuereturned + pkg_engcore.fractional;
>    END IF;
>    RETURN VALUERETURNED;
> END;
> ```
>
> **How to read it.**
>
> | Element | What it means |
> |---|---|
> | `SQ_BOX_FINANENG1` | The sequence for **every table in this walk**. `SQ_BOX_FINANENG3` serves only `T_BOX_ENGPROCESS_S` and `T_BOX_ENGDOM_S`, which we never write |
> | One shared sequence | Confirms why PK integer parts are large, scattered and non-contiguous *within* a single table — many tables draw from the same counter |
> | `seq_range = 'X'` | Switches on the fractional suffix. All observed walk-table PKs carry one |
> | `auth_code` from `gom_glb_sys.t__CORE_INFO_S` | A **single global row per environment**. `[stated: BOX FE Developer]` "the auth_code suffix comes from the environment" |
> | `auth_code / 10^length(auth_code)` | `21 → 0.21`, `4 → 0.4`, `35 → 0.35`, `65 → 0.65` |
> | `pkg_engcore.fractional` | Cached in a package variable, computed once per session |
>
> **Every PK this repo has recorded is now explained**: `24095416 + 0.21 = 24.095.416,21` (SLB
> Accrual), `20007 + 0.4 = 20007.4` (NY_SCH branch), `141 + 0.35 = 141.35` (NY_SCH GBO branch-config),
> `3 + 0.4`, `132.21`, `333105.21`, `113.65`. The `<integer>.<integer>` convention the corpus flagged as
> unexplained from the beginning is closed.
>
> **What the agent does now:** call the function, never compute a value. Assign to a declared variable
> so children can reference their parent —
> `v_pk := F___SEQUENCE('T_BOX_ENGCONF_S','X');` then `INSERT … VALUES (v_pk, …)`. A literal PK is
> still a hard failure, and so is calling `SQ_BOX_FINANENG1.NEXTVAL` directly (it would omit the
> auth-code fraction).
>
> **Bonus: the SQL is environment-portable.** `auth_code` is read from the *target* environment at
> execution time, so a script written against Tier 1 produces correctly-suffixed Tier 2 PKs unchanged.
>
> **Still open** `[open-question]` — which walk tables are called with `seq_range = 'X'` versus some
> other value (all observed PKs carry a suffix, so `'X'` looks universal here, but it is not proven);
> and whether Book configuration is *promoted* via the export/import path described below, which
> `F___SEQUENCE` explains but does not settle.
>
> The queries and the interpretation notes below are **kept as the method** — they are how this gate
> would be answered for another schema, and their "finding nothing is a result" logic was correct: the
> dictionary genuinely showed no triggers and no defaults, because allocation lives in a function the
> application calls.

**Purpose (as originally written):** establish how primary keys are allocated for each table the walk
writes to. Until this is answered the agent may not emit a single `INSERT` (charter hard rule 3).

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

> 🔑 **Evidence now points at the fourth answer — check this before running Q-G3.**
> `[stated: team runbook, 2026-09-15]` The team's add-a-book runbook
> ([`../../process/04-add-book-procedure.md`](../../process/04-add-book-procedure.md) §2.5) describes
> configuring the Book in the SIGOM MIS screen and then *"export the book configuration file **with
> dynamic pk** to insert it into the environments"*. That is an **export/import** path, not an
> `INSERT` path — configure in the UI, export a file that carries the PK allocation, import it
> elsewhere. If that generalises beyond the Book tab, the answer to this gate is "SIGOM allocates, and
> config moves between environments as exported files", which would make hand-written `INSERT`s the
> wrong deliverable shape for at least some of the walk.
>
> So run Q-G3 as written — the dictionary answers are still worth having — but **also find the
> exporter**: which SIGOM action produces that file, what it contains, and whether an equivalent
> exists for the other config objects. A negative Q-G3 result plus this runbook sentence is close to a
> positive finding, not an inconclusive one.

> 🔑 **And a second, *different* mechanism — expect more than one answer.**
> `[confirmed: DML, 2026-09-16]` The `BOX_SYS.T_BOX_CROSS_REF_S` scripts
> ([`../tables/t-box-cross-ref-s.md`](../tables/t-box-cross-ref-s.md)) assign PKs as **hand-written
> literals** in versioned SQL committed to a repo (`113.65`, `114.65`, `117.65`) — no sequence, no
> trigger, no export. That is neither of the two answers above: the Book tab exports a file with a
> dynamic PK, while this static-data table has a human pick the number and a release script carry it.
>
> **The practical consequence for this gate: stop looking for *the* PK mechanism.** BOX evidently uses
> at least two, and Q-G3 should be answered **per table**, not once for the walk. A sequence found for
> one target table says nothing about the next. Record the answer table by table in the findings, and
> treat "no mechanism found for table X" as a real, specific blocker for X rather than a global one.
>
> The cross-ref scripts also show an **idempotency pattern worth copying** if the agent ever does emit
> DML: `delete … where PK in(<pk>) and trunc(PK)=sign(PK)*(abs(PK)-.65)` before each insert, making the
> script re-runnable while asserting the row belongs to the expected PK partition.

**Also worth knowing:** the observed PK *format* (`132.21`, `20087.4`, `3.4`) is still an open
question in `sigom-reference.md`. A sequence returning plain integers wouldn't explain it, so if (a)
is the answer, something else is composing the final value — find that too.

→ `Q-G3-pk-mechanism.csv` (three files, suffixed `-sequences`, `-triggers`, `-defaults`)

### Q-G4 — Target schema completeness `Env: both` ⛔ **blocking**

**Purpose:** confirm every table the walk writes to actually exists in the target environment.

> **⛔ Retraction, 2026-09-16 — "Tier 2 PRE is missing a substantial number of `BOX_FE` tables" was
> wrong, and is withdrawn.** `[confirmed: DB, 2026-09-16]` That conclusion came from a Tier 2 account
> with **no grants on the `BOX_FE` schema**. An Oracle session without privileges does not see missing
> tables — it sees *no rows in `ALL_TABLES`*, which is byte-for-byte identical to absence. The tables
> were invisible, not absent. Nothing is known about Tier 2 PRE's schema completeness either way; gate
> 0e for Tier 2 is `EVIDENCE_REQUIRED — blocked on access, not on schema`, and the related alarm about
> whether `BOX_FE` was ever deployed to Tier 2 at all is stood down.
>
> **This is the second absence-by-broken-access-path in this project** — Q-G2's join was the first.
> Hence the preflight below, which is now mandatory for this query and every other one in this
> catalogue.

### Preflight — mandatory before any result here is interpreted

Run this **first, in the same session**, and attach it to the run folder. A result set from a query
whose preflight was not run is not evidence.

```sql
SELECT USER                                                              AS CONNECTED_AS,
       SYS_CONTEXT('USERENV','DB_NAME')                                  AS DB_NAME,
       (SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER = 'BOX_FE')          AS BOXFE_VISIBLE,
       (SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER = 'DEVENG')          AS DEVENG_VISIBLE
FROM   dual;
```

`BOXFE_VISIBLE = 0` means **you are blind to the schema**, not that it is empty. Stop and report an
access problem; do not record an absence, do not produce a provisioning artifact, and do not diff
anything. The same applies to `DEVENG_VISIBLE = 0` for the GBO-side queries. `CONNECTED_AS` and
`DB_NAME` also settle which environment a CSV actually came from, which filename alone never proves.

Run Q-G4 in **both** the reference environment (Tier 1) and the target, then diff the two CSVs. Tier 1
and Tier 2 are separate databases, so this is a compare-two-results exercise, not a single join.

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
absent in the target is a provisioning gap **only if the preflight above showed non-zero
`BOXFE_VISIBLE` in the target** → the agent produces the provisioning artifact (schema diff + DDL
**sourced** from `cib-boxfin-dbboxfe`, never authored) and blocks. A table present in both but with a
**different column count** is more serious than an absent one: it means the environments have
diverged, and the walk's assumptions may not hold. Escalate rather than proceeding.

**Zero rows in the target is not a result.** With `BOXFE_VISIBLE = 0` it is an access failure; with
`BOXFE_VISIBLE` non-zero but all 14 absent, that is a real and very large finding that deserves its
own escalation rather than a routine provisioning list. Distinguish the two before writing anything
down — conflating them is exactly what happened on 2026-09-16.

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

**Trap — now resolved, 2026-09-16.** `Fixing Curve` appears as a SIGOM leaf under **both**
`Control > Configuration` and `Control > Historical Data`, and it was unclear which was which. It is
an input/output pair: **`Configuration` is what the batch reads; `Historical Data` is what the batch
writes.** Event group `ENG GN - Main Captura de las curvas de fixing BOX` (`2387.65`) reads the former
and populates the latter — see
[`../job-chains/fe-batch-event-groups.md`](../job-chains/fe-batch-event-groups.md) §1.1.

So: **mine `Configuration`.** A populated `Historical Data` is evidence the fixing batch has *run*, not
a second place config lives — and an empty one on a new branch means the batch hasn't run yet, which is
expected, not a config gap. Note also the upstream prerequisite: *PGT Quote Prices*
(`GBO \ Market Data \ Quote Prices \ Currency Pair`) must exist before that batch executes, which is a
dependency for the branch's curves to resolve at all.

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

### Q-05 — Accrual defaults **— and the per-branch instrument set** `Env: GBO` + `BOX`

> **This table answers two questions, 2026-09-17.** `[confirmed: DB via Edouard]` Besides holding
> accrual defaults, **`T_BOX_ENGACCRCONF_S` is where you read which instruments a branch has** — one
> row per instrument. It is the SIGOM MIS configuration's **Accrual tab**. Don't confuse it with
> `T_BOX_ENGINSTRUMENTS_S` (Processed Instruments), which is the global 18-row **menu** with no branch
> dimension. Menu vs. selection. This makes gate 0c verifiable rather than purely an SME assertion, and
> it makes walk step 6's row count **equal to** `PRODUCT_BOOK_SCOPE`.

```sql
SELECT * FROM DEVENG.T_PGT_ENGACCRCONF_S WHERE FK_PARENT = <GBO config PK>;
SELECT * FROM BOX_FE.T_BOX_ENGACCRCONF_S WHERE FK_PARENT = &&FE_CONFIG_PK;
```

**Expect:** one row per in-scope instrument. Tier 1 baseline for calibration: 8 rows (ESP), 7 rows
(SLB) — different counts for two live branches, which is the point. Don't treat either as a target.

> **⚠️ Row-count discrepancy, unresolved.** `[confirmed: DB via Edouard, 2026-09-17]` A direct read of
> SLB's Accrual tab in Tier 1 shows **nine** rows, not the seven recorded above: OTC Option, Cross
> Currency Swap, Swap, Cash Flow Matching, Deposit & Loan, Credit Derivatives, Forward Rate Agreement,
> Caps And Floors, Bond Return Swap. The 7-row figure is older and its provenance is not recorded here.
> Both are kept until someone re-runs the count. The direct 2026-09-17 observation is the better
> evidence; treat 9 as current and 7 as superseded-pending-confirmation. **Do not use either as a
> target for a new branch** — that is the whole point of this line.

### Q-05c — a reference branch's instrument set `Env: BOX` *(new 2026-09-17)*

**Purpose:** turn gate 0c from an SME phrase into a concrete enumeration. Run against a named
reference branch (SLB is the working hypothesis for NY_SCH), put the resulting list in front of the
SME, and have them confirm or amend it **in writing**.

```sql
SELECT a.FK_INSTRUMENT,
       i.DESCRIPTION AS INSTRUMENT_NAME
FROM   BOX_FE.T_BOX_ENGACCRCONF_S  a
JOIN   BOX_FE.T_BOX_ENGINSTRUMENTS_S i ON i.PK = a.FK_INSTRUMENT
WHERE  a.FK_PARENT = &&REFERENCE_FE_CONFIG_PK
ORDER  BY i.DESCRIPTION;
```

**Expect:** one row per instrument the reference branch has. **The join column is assumed** — confirm
`a.FK_INSTRUMENT = i.PK` before trusting it, and apply hard rule 8: if it returns zero rows for a
branch you know is live, the join is wrong, not the branch empty.

**What this authorises and what it does not.** It authorises proposing a *set*. It does **not**
authorise copying the reference branch's accrual **values** — hard rule 6 is unchanged, and NY is
USD/New York where SLB is not. Read the set; get it confirmed; never inherit it.

→ `Q-05-accrual-gbo.csv`, `Q-05b-accrual-box.csv`, `Q-05c-reference-instrument-set.csv`

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

> **Parked 2026-09-17, not resolved.** `[stated: BOX FE Developer via Edouard]` Both this table and
> `T_BOX_ENGCURRENCYBASIS_S` (Q-09) are **empty in Tier 1 PRE**, and the developer's read is that they
> therefore probably don't matter — explicitly offered as a guess, and parked as an open point rather
> than confirmed. Treat accordingly: the agent emits **no INSERT** for steps 9 and 10 by default and
> statuses them `EVIDENCE_REQUIRED` with this note attached — not `NOT_BRANCH_SCOPED`, and not
> `CONFIRMED_ABSENT`, because nobody has said the tables are unnecessary. Note also that the assumed
> `FK_PARENT` join **cannot be validated against an empty table**, so that question stays open too.
> Cheapest next check: look in Tier 1 **PRO** rather than PRE — one populated row would settle both
> the join and the purpose.

→ `Q-08-yield-curve-gbo.csv`, `Q-08b-yield-curve-box.csv`

### Q-09 — Currency basis `Env: GBO` + `BOX`

```sql
SELECT * FROM DEVENG.T_PGT_ENGCURRENCYBASIS_S WHERE FK_PARENT = <GBO config PK>;
SELECT * FROM BOX_FE.T_BOX_ENGCURRENCYBASIS_S WHERE FK_PARENT = &&FE_CONFIG_PK;
```

Same caution as Q-08 on the `FK_PARENT` assumption, and the same **parked 2026-09-17** note applies —
see Q-08. This table previously had DDL but no observed rows, and is now confirmed empty in Tier 1 PRE,
so a zero-row result remains ambiguous between "not configured for this branch" and "not used at all".
`[open-question]`

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

> **Developer guidance, 2026-09-17 — two concrete rules and an admitted gap.**
> `[stated: BOX FE Developer via Edouard]`
>
> 1. **At least one row per instrument is required.** That is why rows with a `0 - EMPTY` Book/Label
>    value exist — an instrument with no real book still needs a row, carrying the placeholder. So the
>    agent's expected row count for this step is *at minimum* one per in-scope instrument, and a
>    missing instrument is a defect rather than a legitimate omission.
> 2. **Use a branch that trades the same instrument as the reference.** "If NY_SCH trades the same
>    instruments as SLB, we can expect the same rows — values of Book/Label to be confirmed." So the
>    reference branch gives the **row set**; the Book/Label **values** still require confirmation.
>    This is the same split as Q-05c and does not weaken hard rule 6: copy the shape, never the values.
> 3. **The table's exact purpose is still not fully understood — by the developer either.** That is
>    worth stating plainly rather than papering over: this is the one walk step where the BOX side
>    itself lacks a confident account of what the configuration means. Treat proposals here as
>    `SME_DECISION_REQUIRED` by default, and do not let the two rules above read as a complete model.

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

> ✅ **Confirmed 2026-09-17.** `[stated: BOX FE Developer via Edouard]` Both tables are **global; a new
> branch needs nothing in them.** Run the query anyway as the evidence behind the status — the charter
> requires a status to trace to a result, not to a recollection — but the expected answer is now known
> rather than hypothesised.

→ `Q-12-not-branch-scoped.csv` (three files: `-columns`, `-days-matured`, `-engsetup`)

### Q-13 — Allowed Errors `Env: BOX` *(new 2026-09-17)*

**Purpose:** walk step 12. `BOX_FE.T_BOX_ERRORS_FE_S` — SIGOM path
`BOX - Financial Engine > Process Management > Allowed Errors` — defines **the error limit before a
process crashes**, `[stated: BOX FE Developer via Edouard, 2026-09-17]` **per instrument and per
branch**. It was absent from this catalogue and from the walk until the developer named it.

```sql
-- (a) Learn the columns first: the branch and instrument column names are NOT confirmed
SELECT COLUMN_NAME, DATA_TYPE, NULLABLE, DATA_DEFAULT
FROM   ALL_TAB_COLUMNS
WHERE  OWNER = 'BOX_FE' AND TABLE_NAME = 'T_BOX_ERRORS_FE_S'
ORDER  BY COLUMN_ID;

-- (b) A reference branch's rows, once (a) names the branch column
SELECT * FROM BOX_FE.T_BOX_ERRORS_FE_S WHERE <BRANCH_COLUMN> = &&REFERENCE_BRANCH_PK;

-- (c) Does a GBO twin exist? The naming rule predicts T_PGT_ERRORS_FE_S — verify, don't assume
SELECT OWNER, TABLE_NAME FROM ALL_TABLES
WHERE  TABLE_NAME LIKE '%ERRORS_FE%' OR TABLE_NAME LIKE '%ERROR%FE%';
```

**Expect:** rows per (branch, instrument). The row count should track the instrument scope, like
steps 6 and 11. `<BRANCH_COLUMN>` is deliberately a placeholder — run (a) first and record the real
names here.

**Three open points, all flagged rather than assumed:**

- **Is there a GBO source?** Unknown. If none exists, treat this like step 11 — BOX-only, no row to
  mine, shape from a reference branch plus an SME for the limits themselves.
- **What is the default limit, and is it safe to copy?** An error threshold is a risk parameter, not a
  structural value. Reading a reference branch tells you the shape; the number needs an SME.
- ⚠️ **The product-shaped `Branch` column.** Allowed Errors is one of the two BOX-DEV screens where the
  `Branch` column showed values like `BOX CCS` / `BOX FX` / `BOX IRS` rather than geographic branches
  (see [`../branch-config/fe-branch-configuration.md`](../branch-config/fe-branch-configuration.md)
  §2). If that is real rather than a dev-environment convention, **this step's grain is wrong**.
  Query (a) settles it: look at what the branch column actually holds. Do this early.

→ `Q-13-allowed-errors.csv` (three files: `-columns`, `-reference-branch`, `-gbo-twin-search`)

---

## Coverage check

| Walk step | Query | Confidence in the query itself |
|---|---|---|
| Gate 0a | Q-G1 | Table confirmed; **code column name unknown** |
| Gate 0b | Q-G2 | **Level 1 confirmed and working.** Levels 2–3 dropped 2026-09-16 — no longer in scope, and their join is proven wrong against Madrid |
| Gate 0d | Q-G3 | ✅ **RESOLVED 2026-09-17** — `F___SEQUENCE(<table>,'X')`: `SQ_BOX_FINANENG1` + environment auth code as a fraction |
| Gate 0e | Q-G4 | SQL is sound; **its 2026-09-16 Tier 2 result was not** — run without grants on `BOX_FE`, so it measured visibility, not existence. Retracted. Never interpret this query without the preflight |
| 1 | Q-01 | `FK_BS` join confirmed |
| 2 | Q-02 | Columns confirmed |
| 3 | Q-03 | Table confirmed |
| 4 | Q-04 | **Full join confirmed** |
| 5 | Q-05 | Table confirmed; `FK_PARENT` assumed. **Also the per-branch instrument set** (2026-09-17) |
| — | Q-05c | New 2026-09-17 — reference branch's instrument enumeration; `FK_INSTRUMENT → PK` join **assumed** |
| 6 | Q-06 | Table confirmed; `FK_PARENT` assumed |
| 7 | Q-07 | **Join confirmed** |
| 8 | Q-08 | Table confirmed; join `[open-question]`. **Empty in Tier 1 PRE (2026-09-17) — parked, not resolved** |
| 9 | Q-09 | Table confirmed; join `[open-question]`; rows never observed. **Confirmed empty in Tier 1 PRE (2026-09-17) — parked** |
| 10 | Q-10 | **Full join confirmed** (branch/sub-product/label); no GBO side exists — confirmed, not a gap (2026-09-11) |
| 11 | Q-11 | Relationships confirmed |
| 12 | Q-12 | Sound. **Answer now confirmed (2026-09-17): both tables global, no branch setup needed** |
| 13 | Q-13 | **New 2026-09-17** — Allowed Errors (`T_BOX_ERRORS_FE_S`). Table named by a BOX FE Developer; **column names, GBO twin and branch grain all unconfirmed** |

Three queries still rest on an assumed or unconfirmed join/column (Q-G1, Q-08, Q-09) — down from four
as of 2026-09-11, when Q-10's uncertainty was resolved the good way: not by finding the predicted GBO
table, but by a BOX FE Developer confirming none exists. Each remaining one is flagged inline above;
none should be allowed to produce a silent zero-row "absence" finding. Fix them on the first real run
and update this table — a zero-row result from a wrong join column is the most plausible way this
whole walk produces a confidently wrong answer.
