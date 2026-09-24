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

> ## ⚠️ Before asserting any join or identifier, check [`../confirmed-joins.md`](../confirmed-joins.md)
>
> One page listing every FK relationship and identifier this repo has confirmed. Three of the four
> query defects found on 2026-09-18 asserted a relationship that was **already confirmed elsewhere in
> this repo** — the information was scattered, not missing. Checking is now one page. **Recording a
> newly confirmed relationship there is part of confirming it.**

**Join style.** New queries below use ANSI `JOIN` syntax. Where the corpus records a query in the
bank's original comma-join form (Q-04), both are shown — they're equivalent; the ANSI form just makes
the join conditions impossible to misread when an agent is generating them.

---

## Gate queries — run these first, in order

Nothing in the walk is valid until all five pre-walk gates pass. A split-tier run also has **gate 0f**
(Q-14), evaluated after mining — but since 2026-09-18 that is a **one-time spot check per environment
pair**, not a per-run gate: `PGT_STC` and `PGT_SYS` are shared and identical everywhere. **Revised 2026-09-16:** Q-G2 is *narrowed* to
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

> ## ✅ `CODE` confirmed, 2026-09-18 — and a trap that has already cost one run
>
> `[confirmed: DB via Edouard]` The column is **`CODE`**, and `DESCRIPTION` exists alongside it. So the
> query above is now properly parameterised rather than provisional.
>
> **The trap: `SLB` and `ESP` are NOT branch codes.** They are abbreviations that appear inside
> *configuration descriptions* — "Configuracion -SCH (SLB)", "Tipos Cambio - SCH (ESP)". The branch
> `CODE` values are **`MADRID`** and **`LND BRANCH`**:
>
> | Branch `PK` | `CODE` | Appears in config descriptions as |
> |---|---|---|
> | `22.21` | `MADRID` | `(ESP)` |
> | `20087.4` | `LND BRANCH` | `(SLB)` |
>
> A run on 2026-09-18 searched `WHERE UPPER(CODE) IN ('SLB','ESP')` and found nothing. **This repo
> already carried both mappings** — `fe-branch-configuration.md` §1's baseline table shows config
> `132.21` *"Configuracion -SCH (ESP)"* against branch `22.21` **MADRID**, and `333105.21` *"(SLB)"*
> against `20087.4` **LND BRANCH**. Parenthetical abbreviations in a description are not identifiers;
> resolve a branch through `CODE`, or better, through the PK Q-G1 returns.

`SELECT *` remains deliberate: this repo has confirmed the table, its PK values for Madrid/London/NY,
the FK fields `FK_ENTITY` / `FK_CURRENCY` / `FK_CALENDAR` / `FK_LOCALGROUP`, and now `CODE` /
`DESCRIPTION` — but not the full column list. `branch-config-surface.md` §6 records this table as an
overloaded ~137-row registry, so read what comes back rather than assuming a shape.

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

### Q-G3b — Is `F___SEQUENCE` callable here? `Env: BOX` *(new 2026-09-18)*

**Purpose:** the generated SQL calls `F___SEQUENCE`, so the executing account must be able to reach it.
Establish **which schema owns it and who can execute it** — then qualify the call correctly.

```sql
-- (a) Who can execute it? NO GRANTEE FILTER — see the warning below.
SELECT * FROM ALL_TAB_PRIVS
WHERE  TABLE_NAME = 'F___SEQUENCE' AND PRIVILEGE = 'EXECUTE';

-- (b) Who owns it, and is it valid?
SELECT OWNER, OBJECT_NAME, OBJECT_TYPE, STATUS
FROM   ALL_OBJECTS WHERE OBJECT_NAME = 'F___SEQUENCE';

-- (c) Is there a synonym that makes it callable unqualified?
SELECT OWNER, SYNONYM_NAME, TABLE_OWNER, TABLE_NAME
FROM   ALL_SYNONYMS WHERE TABLE_NAME = 'F___SEQUENCE';

-- (d) The same for the pre-commit package (added 2026-09-24) - the rendered SQL calls both by OWNER.NAME
SELECT OWNER, OBJECT_NAME, OBJECT_TYPE, STATUS
FROM   ALL_OBJECTS WHERE OBJECT_NAME = 'PKG_ENGPRECOMMIT';
SELECT * FROM ALL_TAB_PRIVS WHERE TABLE_NAME = 'PKG_ENGPRECOMMIT' AND PRIVILEGE = 'EXECUTE';
```

**Record both owners in `values.json`** (`environment.sequence_function_owner` from (b),
`environment.precommit_package_owner` from (d)): the rendered SQL calls `<OWNER>.F___SEQUENCE` and
`<OWNER>.PKG_ENGPRECOMMIT`, which works whether or not a synonym exists. `STATUS` must be `VALID` for
both — an `INVALID` package is a stop and a question to the BOX FE team.

> ## ⚠️ Never filter a diagnostic query by the answer you expect
>
> `[confirmed: DB via Edouard, 2026-09-18]` A run asked this question as
> `… AND GRANTEE IN ('BOX_ADMIN','BOX_FE','PUBLIC')`, found no `PUBLIC`/`BOX_FE` grant, and reported a
> gate still open. Run unfiltered, the same query returns **seven grantees**. The filter could only ever
> confirm or fail to confirm a guess — it could not return the answer.
>
> **The rule: when the query's purpose is to *discover* a value, do not constrain the column that holds
> it.** `SELECT *` and read what comes back. Narrowing is for queries whose answer you already know and
> are verifying. This is the same failure shape as the earlier `CODE IN ('SLB','ESP')` miss: a guessed
> value in a `WHERE` clause turning a discovery question into a yes/no about the guess.

**Expect:** at least one grantee the executing account can use. If the function is owned by a schema the
account cannot reach and no synonym exists, that is a **DBA request** — name the owner and the grant
needed, and block. Do not work around it by inlining `SQ_BOX_FINANENG1.NEXTVAL`; that drops the
auth-code fraction.

→ `Q-G3b-function-reachability.csv` (three files: `-privs`, `-objects`, `-synonyms`)

### Q-G3c — The target's auth code, read and recorded `Env: BOX` (target tier) *(new 2026-09-23)* ⛔ **release gate 0d**

**Purpose:** make the auth code **visible**. `[stated: BOX FE expert via Edouard, 2026-09-23]` *"In the
PK generation, are you adding the auth code? Remember this is extremely important. If not, please add
it and make sure it's part of the verification script."*

**The answer is yes — and the defect is that nobody could see it.** `F___SEQUENCE(<table>,'X')` adds
the fraction itself (Q-G3's function body), so every run-3 PK carried it. But the script never showed
which auth code it expected, never checked what it got, and had no verification script at all. A
reviewer cannot sign what they cannot see.

```sql
-- (a) The auth code F___SEQUENCE will add in THIS environment
SELECT auth_code,
       auth_code / POWER(10, LENGTH(TO_CHAR(auth_code))) AS pk_fraction,
       (SELECT COUNT(*) FROM gom_glb_sys.t__CORE_INFO_S) AS core_info_rows   -- expect 1
FROM   gom_glb_sys.t__CORE_INFO_S;

-- (b) Name it — which environment does this suffix belong to? (Q-G5's registry)
SELECT * FROM PGT_SYS.T_PGT_SOURCE_S WHERE SIGOMID = <auth_code from (a)>;
```

**Expect:** exactly one row. Record it in `00-inputs.md` as `TARGET_AUTH_CODE: <auth_code>` and
`TARGET_PK_FRACTION: <pk_fraction>` — **from this CSV, never typed from memory**. `core_info_rows ≠ 1`
is a **stop**: the function's `SELECT … INTO` would fail at execution.

**How the result is used — three places, all mandatory:**

| Where | What it does |
|---|---|
| **Config script, every allocation** | `chk_pk(v_pk, '<table>')` after each `F___SEQUENCE` call: the PK's fractional part must equal `TARGET_PK_FRACTION`, or abort. **The first call precedes any INSERT**, so a script run in the wrong environment stops having written nothing. (The script cannot read `t__CORE_INFO_S` itself — the applying account sees `BOX_FE` only; `F___SEQUENCE` reads it with its owner's rights) |
| **Verification script** | Every row this run created is checked: `PK - TRUNC(PK) = TARGET_PK_FRACTION`. Zero violations expected |

> **The BOX FE team's own scripts write `BOX_FE.F___SEQUENCE('<T>',1) + 0.21`** — sequence without the
> fraction, then the auth code typed by hand. `[reference: BOX FE expert examples, 2026-09-23]` That
> gives the same PK in a `.21` environment and a wrong one anywhere else. **Do not copy it.** Keep
> `'X'`, which reads the code from the environment, and let the assertions prove it did. If a
> reviewer prefers the explicit form, the equivalent is `F___SEQUENCE('<T>',1) + v_fraction` with
> `v_fraction` read from (a) at runtime — **never a typed decimal**.

→ `Q-G3c-auth-code.csv`

### Q-G3d — What the called code and the target tables do `Env: BOX` (target tier) *(new 2026-09-24)* ⛔ **before the rehearsal**

**Purpose:** the rendered config block is safe only if (1) nothing it calls commits or rolls back in the
middle, (2) the columns it writes exist and every `NOT NULL` column is written, (3) new PKs cannot
collide. An independent review of the rendered SQL found these to be **assumptions** — this query makes
them evidence. Run it with the operator's read-only account; owners from Q-G3b.

```sql
-- (a) Transaction control inside the code the block calls. Expect: no COMMIT / ROLLBACK /
--     AUTONOMOUS_TRANSACTION in F___SEQUENCE or in P_ENGFixingCurve_PreCommit; the COMMIT in
--     p_check_Val_Curves_precommit is expected - and must be reached when there are NO step-8 rows
--     (if it is conditional, the config block stops with -20094 and keeps nothing: ask first).
--     Read the WHEN OTHERS lines: an error swallowed there would hide a failed check.
SELECT NAME, TYPE, LINE, TRIM(TEXT) AS TEXT
FROM   ALL_SOURCE
WHERE  OWNER IN (<owner of F___SEQUENCE>, <owner of PKG_ENGPRECOMMIT>)
AND    NAME IN ('F___SEQUENCE', 'PKG_ENGPRECOMMIT')
AND   (UPPER(TEXT) LIKE '%COMMIT%' OR UPPER(TEXT) LIKE '%ROLLBACK%'
       OR UPPER(TEXT) LIKE '%AUTONOMOUS_TRANSACTION%' OR UPPER(TEXT) LIKE '%WHEN OTHERS%'
       OR UPPER(TEXT) LIKE '%PROCEDURE %' OR UPPER(TEXT) LIKE '%FUNCTION %')
ORDER  BY NAME, TYPE, LINE;

-- (b) Triggers on the tables the block writes. Expect: none, or each one explained.
SELECT TABLE_NAME, TRIGGER_NAME, TRIGGER_TYPE, TRIGGERING_EVENT, STATUS
FROM   ALL_TRIGGERS
WHERE  TABLE_OWNER = 'BOX_FE'
AND    TABLE_NAME IN ('T_BOX_ENGCONF_S','T_BOX_ENGFCURVE_S','T_BOX_ENGLKFC_X','T_BOX_ENGCONF_X',
                      'T_BOX_ENGACCRCONF_S','T_BOX_CONFIG_ACCRUAL_S','T_BOX_FIXING_BY_INSTR_S',
                      'T_BOX_CONF_BY_BOOK_S','T_BOX_ERRORS_FE_S','T_BOX_ENGDAYS_MATURED_S');

-- (c) Primary / unique keys on those tables (the block also checks each new PK is unused).
SELECT TABLE_NAME, CONSTRAINT_NAME, CONSTRAINT_TYPE, STATUS
FROM   ALL_CONSTRAINTS
WHERE  OWNER = 'BOX_FE' AND CONSTRAINT_TYPE IN ('P','U')
AND    TABLE_NAME IN (<the same ten tables>);

-- (e) Every column of those tables - the file the renderer checks the templates against
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE,
       CASE WHEN DEFAULT_LENGTH > 0 THEN 'Y' ELSE 'N' END AS HAS_DEFAULT
FROM   ALL_TAB_COLUMNS
WHERE  OWNER = 'BOX_FE'
AND    TABLE_NAME IN (<the same ten tables>)
ORDER  BY TABLE_NAME, COLUMN_ID;
```

**How the result is used.** (e) is read by `scripts/render_sql.py`: a column the templates write that
does not exist (ORA-00904), a `NOT NULL` column without a default that they do not write (ORA-01400), or
a `DESCRIPTION` longer than its column (ORA-12899) is a **refusal before anything runs** — report it as a
template defect, never work round it. (a) and (b) are read by the agent: any `COMMIT`, `ROLLBACK` or
`AUTONOMOUS_TRANSACTION` in `F___SEQUENCE` or `P_ENGFixingCurve_PreCommit`, or a trigger that writes
elsewhere, is a **stop and a source question** — the rehearsal's promise that nothing is kept depends on
it. (The block also checks at run time that its transaction was never ended midway, error -20098, and
that the Config pre-commit really committed, -20094.) The block calls `DBMS_TRANSACTION`, granted to
`PUBLIC` by default; if a hardened database revoked it, the rehearsal fails to compile (PLS-00201) and
writes nothing — ask the DBA.

→ `Q-G3d-called-code.csv` (a), `Q-G3d-triggers.csv` (b), `Q-G3d-keys.csv` (c), **`Q-G3d-columns.csv`** (e)

### Q-G1b — Resolve a reference branch by picking, not by guessing `Env: GBO` *(new 2026-09-18)*

**Purpose:** several steps need a *reference* branch (Q-05c's instrument set, Q-10's Book shape, Q-13's
Allowed Errors shape). `&&BRANCH_PK` for the branch being onboarded comes from Q-G1 and is never typed —
**reference branches need the same discipline and did not have it.**

```sql
SELECT PK, CODE, DESCRIPTION
FROM   PGT_STC.T_PGT_BRANCH_S
ORDER  BY CODE;
```

**Read the list, pick the row, use its PK.** Do not write a `CODE = '<guess>'` predicate.

> ## ⚠️ Three misses on this one value
>
> `CODE IN ('SLB','ESP')` — abbreviations from a configuration *description*. Then
> `UPPER(CODE) = UPPER('LONDON')` — a plausible English name. The actual values are **`MADRID`** and
> **`LND BRANCH`**. Each guess was reasonable and each was wrong, because the value is not derivable from
> anything a reader would know; it has to be read.
>
> This table is an overloaded ~137-row registry, so the list is short enough to eyeball. **Enumerate and
> pick** rather than predicating on a string, and the failure mode disappears rather than being
> corrected a fourth time.

→ `Q-G1b-branch-registry.csv`

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
         'T_BOX_ERRORS_FE_S',
         'T_BOX_ENGDAYS_MATURED_S','T_BOX_ENGSETUP_S',
         'T_BOX_FIXING_ASSIGNMENT_S','T_BOX_BRPROCCAL_S')
ORDER  BY t.TABLE_NAME;

-- Views the walk depends on
SELECT VIEW_NAME FROM ALL_VIEWS
WHERE  OWNER = 'BOX_FE' AND VIEW_NAME = 'V_BOX_PROC_INSTR_S';
```

**Expect:** 15 table rows and 1 view row in a complete environment. (`T_BOX_ERRORS_FE_S` was added to
this list 2026-09-18 — it entered the walk as step 12 on 2026-09-17 and the gate query was not updated
with it, so the gate would have passed on an environment missing it.) A table present in Tier 1 and
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

### Q-G5 — Decode an environment suffix `Env: any` *(new 2026-09-18)*

**Purpose:** turn the auth-code suffix on any PK into a named environment. `[stated: Edouard,
2026-09-18]` The registry is `PGT_SYS.T_PGT_SOURCE_S`, column **`SIGOMID`**.

```sql
SELECT * FROM PGT_SYS.T_PGT_SOURCE_S ORDER BY SIGOMID;
```

`SELECT *`, deliberately — this is a discovery query and the fifth mechanism of hard rule 8 applies
(don't filter a diagnostic by its expected answer). Known anchors to check the result against: `4` =
global / all environments, `21` = Tier 1 Madrid.

**`PGT_SYS` is a shared schema**, so this returns the same rows from any environment — one run, reusable
everywhere, and it does not need `BOX_FE` access.

**What it should settle on first use:**

- **`.44`** — sighted twice (`12231.44` in NY's quote-reference array; earlier in
  `T_PGT_BRANCH_INST_S.FK_PARENT`) and never identified.
- **`.65`** — this repo calls it BOX-DEV on circumstantial evidence. Confirm or correct.
- **`.35`** — called NY Tier 2 on the same basis.

Record the full mapping in [`../confirmed-joins.md`](../confirmed-joins.md) under *Primary keys*, and
replace the repo's inferred suffix table with it. Until then the suffix model stays `[inferred]`.

→ `Q-G5-environment-registry.csv`

### Q-G7 — The declared object and field catalogue `Env: GOM_GLB_SYS` ⛔ **gate 0g** *(new 2026-09-18)*

**Purpose:** ask SIGOM what it declares, instead of inferring it. One query returns the identity
constants, every FK's declared target, and a completeness check on the walk. **Needs no `BOX_FE`
access** — `GOM_GLB_SYS` is readable today.

**Run this before the walk.** Every join defect in this project has been a relationship the database
states outright.

```sql
-- every declared field of every object the walk writes
SELECT o.PK_NAME          AS owning_screen,
       e.PK               AS fk_extension_value,
       e.FK_PARENT        AS fk_owner_obj_value,
       e.FIELD, e.FK_KIND,
       t.PK_NAME          AS target_object,
       t.BASIC_STORAGE    AS target_table
FROM        GOM_GLB_SYS.T__EXT_DEF_S e
JOIN        GOM_GLB_SYS.T__OBJ_DEF_S o ON o.PK = e.FK_PARENT
LEFT JOIN   GOM_GLB_SYS.T__OBJ_DEF_S t ON t.PK = e.FK_OBJECT
WHERE       e.FK_PARENT IN (35000126.65, 35000123.65,          -- Config, FixingCurve
                            35000128.65, 35000130.65, 35000131.65, 35000133.65,
                            35000135.65, 35000302.65, 35000289.65,
                            35000139.65, 35000153.65, 35000144.65, 35000145.65, 35000134.65)
ORDER  BY   e.FK_PARENT, e.PK;

-- and the objects themselves: storages, module, and what runs on save
SELECT PK, PK_NAME, BASIC_STORAGE, EXT_STORAGE, LANG_STORAGE,
       PRE_COMMIT_PROC, FK_PRECOMMIT, PSAVDLL, PSAVFUNC, NOT_SIGOM
FROM   GOM_GLB_SYS.T__OBJ_DEF_S
WHERE  FK_PARENT = 35000005.65          -- the BOX FE module
ORDER  BY PK;
```

**Expect:** 68 field rows and 80 objects for BOX FE as of 2026-09-18. Three things to read out of it:

1. **Identity constants** per target table — feeds Q-G6.
2. **The declared target of every FK** the walk writes. This supersedes every inferred join in the repo.
3. **A completeness diff.** Any extension with no walk step is a candidate missing step. This is how
   `T_BOX_ENGFIXDISC_S` was found; Allowed Errors went unnoticed for weeks without it.

**`FK_KIND`:** `2.1` scalar pointer · `3.1` owned collection (`am…`, child's own `_S`) · `4.1` link
array (`ap…`, an `_X` bridge) · `5.1` literal · `6.1` flag. Full decode, the three screens the walk
spans, and the distilled field catalogue are in
[`../sigom-metamodel.md`](../sigom-metamodel.md).

⚠️ **`T__OBJ_DEF_S.FK_PARENT` and `.FK_CONNECTION` do not point at `T__OBJ_DEF_S`.** Reading them as if
they did resolves `35000007.65` to "BOX - Colour Config" — a PK collision across tables, the same shape
as `6401.4` naming two different quote references. Only the `FK_OBJECT` join above is valid.

**Exclude `FK_KIND` `6.1` and `11.1` from any INSERT column list** — flags and screen filter parameters
respectively; `11.1` (`sql…`) is not a stored column at all.

*This catalogue is BOX FE only, so the module above is hard-coded to `35000005.65`. The
module-agnostic form of these queries lives in [`../sigom-metamodel.md`](../sigom-metamodel.md) §11 —
that is what another agent parameterises for its own module.*

→ `Q-G7-object-catalogue.csv`, `Q-G7b-field-catalogue.csv`

### Q-G6 — SIGOM identity constants for the target tables `Env: GOM_GLB_SYS` (or `BOX`) *(new 2026-09-18)*

**Purpose:** resolve `FK_OWNER_OBJ` and `FK_EXTENSION` for each INSERT. These belong to the
**destination** object, never to a GBO row — charter hard rule 9.

> **Revised 2026-09-18 — derivable from metadata, and off the deferred list.** This query originally
> read the constants from the target `BOX_FE` tables, which made it a deferred item. Q-G7 supplies them
> from `GOM_GLB_SYS` with no `BOX_FE` access, so the draft can bind real constants now.
>
> **Derivation** — base table (an object's `BASIC_STORAGE`): `FK_OWNER_OBJ` = the object's PK,
> `FK_EXTENSION` = NULL. Extension table: `FK_OWNER_OBJ` = the extension's `FK_PARENT`, `FK_EXTENSION` =
> the extension's own PK. Validated four for four against live Tier 1 rows —
> [`../sigom-metamodel.md`](../sigom-metamodel.md) §3.
>
> **These are not one constant across the walk.** The walk spans three screens: `35000126.65` Config,
> `35000123.65` FixingCurve, `35000289.65` Limit Error Assign. A single value applied everywhere is
> wrong for steps 3, 4 and 12 — the 2026-09-18 draft defect, in its second form.

The read below remains the **validation** of the derivation, and stays deferred with the other
`BOX_FE` reads. Derive from Q-G7; confirm here when access lands.

```sql
SELECT 'T_BOX_ENGCONF_S'     AS TAB, FK_OWNER_OBJ, FK_EXTENSION, COUNT(*) AS ROWS_FOUND
FROM   BOX_FE.T_BOX_ENGCONF_S       GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL
SELECT 'T_BOX_ENGCONF_X',           FK_OWNER_OBJ, FK_EXTENSION, COUNT(*)
FROM   BOX_FE.T_BOX_ENGCONF_X       GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL
SELECT 'T_BOX_ENGFCURVE_S',         FK_OWNER_OBJ, FK_EXTENSION, COUNT(*)
FROM   BOX_FE.T_BOX_ENGFCURVE_S     GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL
SELECT 'T_BOX_ENGLKFC_X',           FK_OWNER_OBJ, FK_EXTENSION, COUNT(*)
FROM   BOX_FE.T_BOX_ENGLKFC_X       GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL
SELECT 'T_BOX_ENGACCRCONF_S',       FK_OWNER_OBJ, FK_EXTENSION, COUNT(*)
FROM   BOX_FE.T_BOX_ENGACCRCONF_S   GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL
SELECT 'T_BOX_CONFIG_ACCRUAL_S',    FK_OWNER_OBJ, FK_EXTENSION, COUNT(*)
FROM   BOX_FE.T_BOX_CONFIG_ACCRUAL_S GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL
SELECT 'T_BOX_FIXING_BY_INSTR_S',   FK_OWNER_OBJ, FK_EXTENSION, COUNT(*)
FROM   BOX_FE.T_BOX_FIXING_BY_INSTR_S GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL
SELECT 'T_BOX_CONF_BY_BOOK_S',      FK_OWNER_OBJ, FK_EXTENSION, COUNT(*)
FROM   BOX_FE.T_BOX_CONF_BY_BOOK_S  GROUP BY FK_OWNER_OBJ, FK_EXTENSION
UNION ALL
SELECT 'T_BOX_ERRORS_FE_S',         FK_OWNER_OBJ, FK_EXTENSION, COUNT(*)
FROM   BOX_FE.T_BOX_ERRORS_FE_S     GROUP BY FK_OWNER_OBJ, FK_EXTENSION;
```

**Expect:** exactly **one row per table**. More than one means the column is *not* a constant for that
table and the model above is wrong for it — a finding, and a reason to stop rather than pick one.
Zero rows means the table is empty in the target — **use the Q-G7 derivation**, which needs no row;
that is not a blocker (see the step-12 note under the table).

**Tier 1 observed values, and the derivation that predicts them** `[confirmed: DB via Edouard,
2026-09-18]`:

| Table | `FK_OWNER_OBJ` | `FK_EXTENSION` | Derived from |
|---|---|---|---|
| `T_BOX_ENGCONF_S` | `35000126.65` | — | base storage of `BOX_ENG_Config` |
| `T_BOX_ENGCONF_X` | `35000126.65` | `35001566.65` | `apBranch` |
| `T_BOX_ENGACCRCONF_S` | `35000126.65` | `35001114.65` | `amAccrualConfig` |
| `T_BOX_ENGFCURVE_S` | **`35000123.65`** | — | base storage of `BOX_ENG_FixingCurve` |
| `T_BOX_ENGLKFC_X` | **`35000123.65`** | `35001101.65` | `apQuoteReference` |
| `T_BOX_ERRORS_FE_S` | **`35000289.65`** | — | base storage of `BOX - Limit Error Assign` |
| `T_BOX_CONFIG_ACCRUAL_S` | `35000126.65` | `35001120.65` | `BOX_ENG_Config_Accrual` — *from the BOX FE team's inserts, 2026-09-23* |
| `T_BOX_ENGDAYS_MATURED_S` | **`35000145.65`** | — | base storage of `BOX_ENG_Days_Matured` — *same source* |

> **Run 3 left step 12 unwritten because this read found `T_BOX_ERRORS_FE_S` empty in Tier 2.**
> `[2026-09-23]` An empty target table is **not** a missing identity: the constant is a property of the
> metamodel object, and **Q-G7's derivation gives it with no row at all** — base storage of `BOX - Limit
> Error Assign`, so `FK_OWNER_OBJ = <that object's PK>`, `FK_EXTENSION` = none (the table has no such
> column: the team's own insert writes `PK, FK_OWNER_OBJ, FK_BRANCH, FK_INSTRUMENT, LIMIT_ERRORS`).
> The BOX FE team's Tier 1 inserts write `35000289.65`. `.65` objects are allocated in BOX-DEV and
> promoted, so **Tier 2's derivation should return the same value**; if it does not, that is the
> finding. Same for Days Matured (`35000145.65`).

For contrast, the GBO side: `DEVENG.T_PGT_ENGCONF_S` carries `FK_OWNER_OBJ = 12198.4` on **every** row —
the GBO Financial Engine's own object. Copying it into a BOX row is the 2026-09-18 draft defect.

⚠️ **Derive per object, never hard-code, and never apply one value across the walk.** The last three
rows above are the ones a single-constant draft gets wrong.

→ `Q-G6-sigom-identity-constants.csv`

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

### Q-01c — The branch association row (walk **step 5**, the write) `Env: BOX` *(new 2026-09-18)*

**Purpose:** step 5 has no GBO twin to mine, which is why it had no query — and on 2026-09-18 a run
blocked it as "requires BOX-specific `FK_OWNER_OBJ` and `FK_EXTENSION` values not present in the supplied
GBO evidence." It has no query because **all four of its values are already resolved by other steps**,
not because it is unmineable.

| Column | Value | Source |
|---|---|---|
| `PK` | `F___SEQUENCE('T_BOX_ENGCONF_X','X')` | hard rule 3 |
| `FK_PARENT` | the step-2 header's declared variable | walk step 2 — **the owner**, `_X` convention |
| `FK_BS` | `&&BRANCH_PK` | Q-G1 — **the link**, `_X` convention |
| `FK_OWNER_OBJ` | `35000126.65` in Tier 1 | **Q-G6 against the target**, never GBO |
| `FK_EXTENSION` | `35001566.65` in Tier 1 | **Q-G6 against the target**, never GBO |

The BOX-side existence read for this step is Q-01 itself (`WHERE FK_BS = &&BRANCH_PK`), which is the
step-1 fork — so step 5 needs no new read, only the constants.

**Why this step cannot be skipped.** `T_BOX_ENGCONF_X` is what ties the configuration to the branch.
Steps 2–4 build a configuration and steps 6–12 populate it; without step 5 that configuration belongs
to no branch and the FE batch will never select it. A draft that emits every other step and blocks this
one has produced something worse than nothing, because it looks complete.

Uniqueness is `(FK_PARENT, FK_OWNER_OBJ, FK_EXTENSION, FK_BS)` — see
[`../branch-config/fe-branch-configuration.md`](../branch-config/fe-branch-configuration.md) §2.

→ no CSV; this step's evidence is Q-01 + Q-G6

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

**Confirmed columns — seven, but since 2026-09-23 only three are copied from GBO:** `DESCRIPTION`,
`FK_CALENDAR`, `FK_CURRENCY` are mined; `FK_CURVEMAN`, `FK_CURVEACC` are intra-config; `FK_SOURCE_FRONT`,
`FK_SOURCE_BACK` are **re-keyed** — see the correction below.

> ## ⚠️ `DESCRIPTION` is globally unique — new pre-flight, 2026-09-21
>
> `[confirmed: DDL via Devin]` `T_BOX_ENGCONF_S` carries a `CREATE UNIQUE INDEX` on `DESCRIPTION`
> alone — **across the whole table, not per branch.** So does `T_BOX_ENGFCURVE_S` (Q-03). A mined
> description that already exists in the target is a **hard INSERT failure**, not a silent one.
>
> ```sql
> -- run against the target before emitting steps 2 and 3
> SELECT PK, DESCRIPTION FROM BOX_FE.T_BOX_ENGCONF_S  WHERE DESCRIPTION = '<mined step-2 description>';
> SELECT PK, DESCRIPTION FROM BOX_FE.T_BOX_ENGFCURVE_S WHERE DESCRIPTION = '<mined step-3 description>';
> ```
>
> A hit is `SME_DECISION_REQUIRED` on naming — never a value to adjust quietly. Tier 1's convention
> carries a branch suffix (`Configuracion -SCH (ESP)` / `(SLB)`), so a config collision is unlikely;
> the **curve** description is the likelier one, since curve names tend to be generic. Part of the
> deferred C2 set.
>
> **`NOT NULL` on this table** `[confirmed: DDL]`: `PK`, `FK_OWNER_OBJ`, `DESCRIPTION`, `FK_CALENDAR`,
> `FK_CURRENCY`, `FK_CURVEMAN`, `FK_CURVEACC`, `FK_SOURCE_FRONT`, `FK_SOURCE_BACK`. `FK_PARENT` and
> `FK_EXTENSION` are **nullable** — exactly as the metamodel's base-table derivation predicts.

> ## ⛔ Corrected 2026-09-18 — the INSERT built from this query carried GBO's identity columns
>
> The generated draft was, in effect:
>
> ```sql
> INSERT INTO BOX_FE.T_BOX_ENGCONF_S (PK, FK_OWNER_OBJ, FK_PARENT, FK_EXTENSION, DESCRIPTION, …)
> SELECT v_pk, FK_OWNER_OBJ, FK_PARENT, FK_EXTENSION, DESCRIPTION, …
> FROM   DEVENG.T_PGT_ENGCONF_S WHERE PK = 64408.35;
> ```
>
> `FK_OWNER_OBJ` on **every** `DEVENG.T_PGT_ENGCONF_S` row is `12198.4` — the **GBO** Financial Engine
> module. On every `BOX_FE.T_BOX_ENGCONF_S` row it is `35000126.65` — the **BOX** one. The INSERT above
> writes a BOX row owned by the GBO module. `[confirmed: DB via Edouard, 2026-09-18]`
>
> **`FK_OWNER_OBJ`, `FK_EXTENSION` and `FK_PARENT` are not mined here.** The first two come from Q-G6
> against the target (charter hard rule 9); `FK_PARENT`'s meaning on this table is a separate open
> question and must not be copied across either. **The mining list is the columns above and
> nothing else** — and since 2026-09-23 the two source columns are not on it either.
>
> The tell was already in this catalogue: Q-05c's result note recorded `FK_OWNER_OBJ`/`FK_EXTENSION` as
> `.65` BOX-DEV values *while the same row's mined FKs were `.4` and `.21`* — written to corroborate the
> auth-code finding, never read as the rule it implies.
>
> **Structural fix: no `INSERT … SELECT * FROM DEVENG` anywhere in the walk.** Write an explicit column
> list and be able to say, per column, whether it is mined, allocated or structural.

**Sub-order for the findings:** currency + calendar first (they're the compatibility criteria), then
the two source systems, then the two curve references, then description. A Tier 1 caution worth
carrying: the ESP and SLB configurations share calendar, currency **and** both source systems, yet
use different curves. Shared scalars prove nothing about curves.

→ `Q-02-generic-gbo.csv`, `Q-02b-generic-box.csv`

> ## ⛔ Corrected 2026-09-23 — the two source columns are **not** mined from GBO
>
> `[stated: BOX FE expert via Edouard, 2026-09-23]` Run 3 copied NY's GBO values `9.4` / `11.4` into
> both columns. **Both are wrong for BOX**, and neither is a GBO→BOX copy at all:
>
> | Column | BOX value | Why | Kind |
> |---|---|---|---|
> | `FK_SOURCE_BACK` | **`586.4`, always** | *"BOX is always the SOURCE BACK"* | **Documented constant** — same for every branch |
> | `FK_SOURCE_FRONT` | the **Murex instance** the branch's trades come from | *"basically depends on which Murex instance/environment the trades from the branch will come from"* | **Stated decision**, per branch — input `SOURCE_FRONT` |
>
> Known Murex sources: **Murex 3 Latam = `513.4`** — *"NY should use that one"*; Murex 3 FXFI (Europe)
> = `413.4`. List them all with **Q-02c**, below.
>
> **So the mining list is now five columns, not seven:** `DESCRIPTION`, `FK_CALENDAR`, `FK_CURRENCY` are
> mined; `FK_CURVEMAN`/`FK_CURVEACC` are intra-config (the curve's variable, **allocated before the header** —
> both are `NOT NULL`); `FK_SOURCE_BACK`
> is the constant; `FK_SOURCE_FRONT` is the input. **These are re-keyed columns** (charter hard rule
> 13): GBO's values point at GBO's source systems, BOX's at BOX's. The GBO value is shown in the
> findings for comparison and never written.

### Q-02c — Murex source systems `Env: shared` (`PGT_SYS`) *(new 2026-09-23)*

**Purpose:** the candidates for `FK_SOURCE_FRONT`, and proof that `586.4` exists in the target.
`[stated: BOX FE expert via Edouard, 2026-09-23]` — the expert's query:

```sql
SELECT * FROM PGT_SYS.T_PGT_SOURCE_S
WHERE  FK_SYSTEM = '2.4';                      -- Murex source systems

SELECT * FROM PGT_SYS.T_PGT_SOURCE_S
WHERE  PK IN (586.4, &&SOURCE_FRONT);          -- the two values step 2 will write — expect 2 rows
```

**Expect:** the Murex list includes `513.4` (Murex 3 Latam) and `413.4` (Murex 3 FXFI Europe); the
second query returns **two** rows. A missing row is a stop — the header would point at nothing, and
nothing would reject it (hard rule 12). The value written to `SOURCE_FRONT` is a decision by a named
person; this query only shows the menu.

→ `Q-02c-murex-sources.csv` (two files: `-list`, `-check`)


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

**`NOT NULL` on `T_BOX_ENGFCURVE_S`** `[confirmed: DDL via Devin, 2026-09-21]`: `PK`, `FK_OWNER_OBJ`,
`DESCRIPTION`, `FK_CURRENCY`. And **`DESCRIPTION` carries a global `UNIQUE` index** — run the collision
pre-flight in Q-02 before emitting this step. Curve descriptions are more generic than configuration
descriptions, so this is the likelier of the two to collide.

→ `Q-03-curve-headers-gbo.csv`, `Q-03b-curve-headers-box.csv`

### Q-04 — Quote-reference array `Env: GBO` (linkage) + `shared` (references)

**Purpose:** the array of quotes behind **one curve**.

> ## ⛔ Corrected 2026-09-18 — this query had no curve filter, and the filter Devin invented was wrong
>
> The join below was `[confirmed: DB via BOX Lead, 2026-09-10]` and is still correct. But it was
> recorded **without any `WHERE` restricting it to a curve**, while step 4 needs exactly that. Faced
> with a query that returns every linkage row in the schema, the agent added the only `t1` column the
> query mentioned: `WHERE t1.FK_BS IN (<curve PK>)`.
>
> **That filter contradicts the query's own join.** Line 2 asserts `t1.FK_BS = t3.PK` where `t3` is
> `T_PGT_QUOTE_REFERENCE_S` — so `FK_BS` is a **quote-reference** FK. Filtering `FK_BS = <curve PK>`
> then asks "give me the linkage row whose *quote reference* happens to equal the curve's PK", which is
> a different question with a coincidental answer at best. One column cannot be both sides of the
> bridge.
>
> **The curve is `FK_PARENT`.** `[confirmed: DB via Edouard, 2026-09-18]` The filter is
> `WHERE t1.FK_PARENT = &&CURVE_PK`, where `&&CURVE_PK` is `DEVENG.T_PGT_ENGFCURVE_S.PK` — resolved by
> **Q-03**, never typed by hand.
>
> **This follows a convention the repo had already evidenced twice** — see *The `_X` bridge-table
> convention* below. It was findable, and it was not checked. Third join defect in this project.

```sql
SELECT t1.*, t3.*, t4.*, t5.*
FROM        DEVENG.T_PGT_ENGLKFC_X          t1
JOIN        PGT_MRK.T_PGT_QUOTE_REFERENCE_S t3 ON t1.FK_BS          = t3.PK
JOIN        PGT_MRK.T_PGT_QUOTE_SOURCE_S    t4 ON t3.FK_QUOTESOURCE = t4.PK
JOIN        PGT_SYS.PGT_DOMAINS             t5 ON t3.FK_QUOTETYPE   = t5.PK
WHERE       t1.FK_PARENT = &&CURVE_PK;        -- the CURVE. Never FK_BS.
```

**Expect:** one row per quote reference the curve carries — an array, so more than one. **Zero rows is
not an answer**: hard rule 8 applies, and the control is a curve you know is populated (a live
reference branch's). A curve header with no linkage rows is an incomplete curve, which is the specific
thing the steps 3/4 separation exists to catch.

### The `_X` bridge-table convention `[confirmed: DB, three tables]`

Tables ending `_X` are bridges, and they consistently use two FKs with **fixed roles**:

| Column | Role | Points |
|---|---|---|
| `FK_PARENT` | the **owner** | **up**, to the object the bridge belongs to |
| `FK_BS` | the **link** | **across**, to the object being linked |

Confirmed instances:

| Bridge | `FK_PARENT` → | `FK_BS` → |
|---|---|---|
| `T_BOX_ENGCONF_X` | FE configuration header `T_BOX_ENGCONF_S` | GBO branch `T_PGT_BRANCH_S` |
| `T_BOX_LINK_ARRAY_X` | `T_BOX_CONF_LO_PROP_S` | `T_BOX_CONDPAR_PROP_S` |
| `T_BOX_ENGLKFC_X` / `T_PGT_ENGLKFC_X` | fixing curve `T_*_ENGFCURVE_S` | quote reference `T_PGT_QUOTE_REFERENCE_S` |

**So on any `_X` table: filter on `FK_PARENT` to get one owner's array; join on `FK_BS` to resolve what
each row points at.** Doing it the other way round is the 2026-09-18 Q-04 defect.

`[inferred]` The convention is strongly evidenced but not stated by a developer. Treat a fourth `_X`
table as fitting the pattern **until checked**, not because it must.

Original comma-join form as recorded, and the BOX-side variant — **only the first table changes**,
because `PGT_MRK` and `PGT_SYS.PGT_DOMAINS` are shared by BOX and GBO. Note the curve predicate is an
**addition** to the form as originally recorded, which had none:

```sql
SELECT *
FROM   BOX_FE.T_BOX_ENGLKFC_X       T1,   -- DEVENG.T_PGT_ENGLKFC_X on the GBO side
       PGT_MRK.T_PGT_QUOTE_REFERENCE_S T3,
       PGT_MRK.T_PGT_QUOTE_SOURCE_S    T4,
       PGT_SYS.PGT_DOMAINS             T5
WHERE  T1.FK_PARENT      = &&CURVE_PK     -- added 2026-09-18; absent from the original
AND    T1.FK_BS          = T3.PK
AND    T3.FK_QUOTESOURCE = T4.PK
AND    T3.FK_QUOTETYPE   = T5.PK;
```

**Mining implication:** because the reference/source/domain tables are shared, there is no separate
"GBO version" of them to find. Only the `ENGLKFC_X` linkage rows are module- and curve-specific, and
they are the only part that needs mining per branch.

### Q-04b — Decode a quote reference `Env: GBO` or `BOX` *(new 2026-09-18)*

**Purpose: comprehension and review, not mining.** Q-04 returns the *PKs* of the quote references behind
a curve. `6401.4` is not reviewable; *"Santander NY spot closing prices, EUR/USD, mid"* is. Run this to
turn step 4's findings into something an SME can actually sign off.

> **This step never creates a quote reference.** Quote references are pre-existing market-data objects.
> Step 4 inserts into the **bridge** (`T_*_ENGLKFC_X`), pointing at references that already exist. If a
> required reference is absent in the target, that is a market-data provisioning finding to escalate —
> never a row for this agent to create.

```sql
SELECT T1.PK                AS QUOTE_REF_PK,
       T4.SHORTNAME         AS CURRENCY_PAIR,
       T3.DESCRIPTION       AS QUOTE_SOURCE,
       T2.DESCRIPTION       AS QUOTE_TYPE,
       T1.FK_QUOTEDIRECTION, T1.FK_MATURITY,
       T1.FK_PARENT, T1.FK_OWNER_OBJ
FROM   PGT_MRK.T_PGT_QUOTE_REFERENCE_S T1
JOIN   PGT_SYS.PGT_DOMAINS             T2 ON T1.FK_QUOTETYPE       = T2.PK
JOIN   PGT_MRK.T_PGT_QUOTE_SOURCE_S    T3 ON T1.FK_QUOTESOURCE     = T3.PK
JOIN   PGT_STC.T_PGT_CURR_PAIR_S       T4 ON T1.FK_QUOTEINSTRUMENT = T4.PK
WHERE  T1.PK IN (<the FK_BS values Q-04 returned>);
```

`[confirmed: DB via Edouard, 2026-09-18]` — all three joins confirmed. **`SELECT *` if you need the full
row:** the column list above is a useful subset, not the table's full shape, which is unconfirmed.

**What a quote reference turns out to be** — a tuple of:

| Component | Resolves to | Schema | Shared across environments? |
|---|---|---|---|
| Currency pair | `PGT_STC.T_PGT_CURR_PAIR_S.PK` (`SHORTNAME`) | `PGT_STC` | ✅ Yes |
| Quote type | `PGT_SYS.PGT_DOMAINS.PK` | `PGT_SYS` | ✅ Yes |
| **Quote source** | `PGT_MRK.T_PGT_QUOTE_SOURCE_S.PK` | `PGT_MRK` | ❌ **No — environment-specific** |
| Direction, maturity | `FK_QUOTEDIRECTION`, `FK_MATURITY` — targets **unconfirmed** `[open-question]`, `PGT_DOMAINS` is the obvious candidate | — | — |
| Owner | `FK_PARENT` — target **unconfirmed** `[open-question]` | — | — |

**This explains the `6401.4` collision.** Two of a quote reference's three identity components live in
shared schemas; the **quote source does not**. So the same PK naming a different market-data feed in two
environments is exactly what you would predict. **Cheap confirmation:** run this query for `6401.4` in
both environments and read which component diverges — currency pair and quote type should match, quote
source should differ. Worth doing once; record the result in
[`../confirmed-joins.md`](../confirmed-joins.md).

→ `Q-04b-quote-reference-decode.csv`

→ (Q-04's own outputs) `Q-04-quote-array-gbo.csv`, `Q-04b-quote-array-box.csv`

### Q-04c — Step 4's source set, decoded and export-ready `Env: GBO` *(revised 2026-09-24)*

> ## ✅ Settled 2026-09-24: the quote reference is `FK_BS`
>
> `[stated: operator, BOX Dev, 2026-09-24]` *"The link between `DEVENG.T_PGT_ENGLKFC_X` and
> `PGT_MRK.T_PGT_QUOTE_REFERENCE_S` is `FK_BS` = `PK`."* That is Q-04's join
> `[confirmed: DB via BOX Lead, 2026-09-10]` and the `_X` convention (`FK_PARENT` up, `FK_BS` across). The
> BOX FE expert's `SELECT DISTINCT PK …` is read as shorthand for the same set, not as a different
> column.
>
> **The version of this query that stopped run 4 is withdrawn, and the fault was in the query, not the
> agent.** It tested whether each bridge row's **`PK`** also matched a quote reference, and treated any
> match as evidence. One did (`87.35`), the outcome table said *mixed → stop*, and the run stopped. But
> a bridge row's PK and a quote reference's PK are drawn from sequences in the same environment, so a
> numeric match is a coincidence. **A PK is only meaningful with its table** — this catalogue's own rule
> ([`confirmed-joins.md`](../confirmed-joins.md)), broken by the query that was supposed to apply it.

**Purpose:** the file step 4's list is generated from, and a review aid in one pass. Based on the
operator's query, with **unique aliases** — the generator refuses a CSV with duplicate headers, and the
original selects four columns called `PK`:

```sql
-- (a) the set, decoded — one row per quote reference on NY's GBO curve
SELECT T1.PK            AS BRIDGE_PK,
       T1.FK_BS         AS FK_BS,               -- the quote reference: this column is copied
       T2.PK            AS QUOTE_REF_PK,
       T3.DESCRIPTION   AS QUOTE_TYPE,
       T4.DESCRIPTION   AS QUOTE_SOURCE,
       T5.SHORTNAME     AS CURRENCY_PAIR
FROM        DEVENG.T_PGT_ENGLKFC_X          T1
LEFT JOIN   PGT_MRK.T_PGT_QUOTE_REFERENCE_S T2 ON T1.FK_BS             = T2.PK
LEFT JOIN   PGT_SYS.PGT_DOMAINS             T3 ON T2.FK_QUOTETYPE       = T3.PK
LEFT JOIN   PGT_MRK.T_PGT_QUOTE_SOURCE_S    T4 ON T2.FK_QUOTESOURCE     = T4.PK
LEFT JOIN   PGT_STC.T_PGT_CURR_PAIR_S       T5 ON T2.FK_QUOTEINSTRUMENT = T5.PK
WHERE       T1.FK_PARENT = &&GBO_CURVE_PK        -- NY: 1.35, from Q-03. The CURVE.
ORDER  BY   T1.FK_BS;

-- (b) counts — hard rule 8: rows, distinct quote refs, and how many resolve
SELECT COUNT(*) AS n_rows, COUNT(DISTINCT T1.FK_BS) AS n_fk_bs, COUNT(T2.PK) AS n_resolved
FROM        DEVENG.T_PGT_ENGLKFC_X          T1
LEFT JOIN   PGT_MRK.T_PGT_QUOTE_REFERENCE_S T2 ON T1.FK_BS = T2.PK
WHERE       T1.FK_PARENT = &&GBO_CURVE_PK;
```

**`LEFT JOIN`s on purpose** (the operator's original is an inner join): a quote reference that does not
resolve must show up as a NULL row, not vanish. **Expect `n_resolved = n_rows`** — NY: 38. A gap is a
finding for `05-source-questions.md`, never a row to drop quietly. `n_fk_bs` is the count the config
script guards on.

**Then:** nothing to type. `scripts/render_sql.py` reads the FK_BS column of (a) and the counts of (b)
itself — save both CSVs under exactly these names. `values.json` states only `steps.4.expected_count`
(`N_FK_BS` from (b)), and the renderer refuses if the two disagree or if `N_RESOLVED <> N_ROWS`.

→ `Q-04c-quote-ref-column-gbo.csv` (a), `Q-04c-quote-ref-column-counts.csv` (b)

### Q-05 — Accrual defaults **— and the per-branch instrument set** `Env: GBO` + `BOX`

> ## ⛔ The values come from THIS branch's GBO row `[corrected 2026-09-22]`
>
> Gate 0c chooses **which** instruments; Q-05 supplies **their values**, mined from the branch's own
> `DEVENG.T_PGT_ENGACCRCONF_S` rows — `WHERE FK_PARENT = <the branch's GBO MIS header>`.
>
> **Run the reference branch alongside and put the two side by side**, so each findings row reads
> *this branch's GBO value · the reference branch's value · the decision*. Where they agree the SME
> confirms; **where they differ, the difference is the finding.** They do differ: SLB carries
> `INTERVAL = 370` for Forward Rate Agreement where NY's GBO has `377` `[confirmed: DB via Edouard,
> 2026-09-22]`.
>
> ⛔ **Never propose the reference branch's values when the branch's own row exists** — hard rule 6.
> The 2026-09-22 run did exactly that for five of six instruments with NY's rows already mined into its
> evidence folder. If the branch's own row is missing for an in-scope instrument, that is
> `SME_DECISION_REQUIRED` with the reference shown as an aid, not a licence to copy.
>
> *(Both queries use `LEFT JOIN` to `T_PGT_SUB_PRODUCT_S` for labels, plus the unjoined `COUNT(*)`.)*

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

### Q-05d — is there a GBO→BOX transformation for accrual values? `Env: GBO` + `BOX`, same tier `[new 2026-09-22]` ⛔ **OPEN**

**Purpose: eliminate a confound before any step-6 value is proposed.** The 2026-09-22 comparison that
exposed the step-6 defect compared **NY in GBO** against **SLB in BOX** — two variables at once, the
branch *and* the system:

| Deposit & Loan | `INTCOMMONBASIS` | `BYTRIGGER` | `BYRESIDUAL` | `INTERVAL` |
|---|---|---|---|---|
| **NY** — `DEVENG.T_PGT_ENGACCRCONF_S`, Tier 2 | 1 | 1 | 0 | 377 |
| **SLB** — `BOX_FE.T_BOX_ENGACCRCONF_S`, Tier 1 | 0 | 0 | *null* | *null* |

`[confirmed: DB via Edouard, 2026-09-22]` Four columns differ, two of them gate-0c `NOT NULL` values.
**But that difference has two possible causes and the data so far cannot separate them:** the branches
genuinely differ, **or** GBO and BOX hold these columns differently and the values are transformed when
a configuration is created in BOX.

**This query holds the branch constant and varies only the system.**

```sql
SELECT 'GBO' AS src, sp.DESCRIPTION AS instrument,
       a.FK_FEEFIRSTDAYSEL, a.FK_INTFIRSTDAYSEL, a.INTCOMMONBASIS,
       a.BYTRIGGER, a.BYRESIDUAL, a.INTERVAL, a.FK_MDRBASIS, a.FK_BASIS
FROM        DEVENG.T_PGT_ENGACCRCONF_S      a
LEFT JOIN   PGT_SYS.T_PGT_SUB_PRODUCT_S     sp ON sp.PK = a.FK_INSTRUMENT
WHERE       a.FK_PARENT = &&SLB_GBO_MIS_HEADER_PK      -- SLB's GBO header, Tier 1 (Q-G2 level 1)
UNION ALL
SELECT 'BOX', sp.DESCRIPTION,
       b.FK_FEEFIRSTDAYSEL, b.FK_INTFIRSTDAYSEL, b.INTCOMMONBASIS,
       b.BYTRIGGER, b.BYRESIDUAL, b.INTERVAL, b.FK_MDRBASIS, b.FK_BASIS
FROM        BOX_FE.T_BOX_ENGACCRCONF_S      b
LEFT JOIN   PGT_SYS.T_PGT_SUB_PRODUCT_S     sp ON sp.PK = b.FK_INSTRUMENT
WHERE       b.FK_PARENT = 333105.21                     -- SLB's BOX MIS configuration
ORDER  BY   2, 1;
```

**Both reads are Tier 1, so the tier is held constant too.** Three outcomes, and they lead to different
step-6 behaviour:

| Outcome | Meaning | What step 6 proposes |
|---|---|---|
| SLB's GBO row **equals** its BOX row | No transformation. The NY/SLB difference is a genuine branch difference | **NY's GBO values, copied straight.** `PROPOSED` |
| SLB's GBO row **differs from** its BOX row, in the same direction | GBO→BOX transforms these columns. The NY/SLB difference was mostly the system, not the branch | **NY's GBO values put through the same transformation**, tagged **`DERIVED`** with the rule written down |

> ## ⛔ A transformation is a rule to apply to NY's values — never a reason to use SLB's
>
> `[confirmed: run defect, 2026-09-22]` The 2026-09-22 run got this exactly backwards. Q-05d showed SLB
> GBO ≠ SLB BOX, and the run concluded: *"SLB **BOX** values with NY GBO fallback for absent/null
> values."*
>
> **That is the opposite of what the finding licenses.** A GBO→BOX difference tells you *how values
> change between the two systems*. It says nothing whatever about whether London's configuration suits
> New York. Using it to justify London's values is hard rule 6 wearing the evidence as a disguise — and
> the hybrid is worse than either source alone, because **a single row then carries two branches'
> decisions** with no way to tell which column came from where.
>
> **The rule, stated so it cannot be inverted:**
>
> 1. **The values are NY's, always.** Q-05d never changes whose values they are.
> 2. **Q-05d only supplies the transformation** to apply to them, if one exists.
> 3. **If the rule cannot be stated in one sentence, there is no rule** — the columns are
>    `EVIDENCE_REQUIRED` and go to the SME with both readings shown. "Fall back to the other branch" is
>    not a transformation.
> 4. **A null in NY's GBO row is a finding about NY**, not a hole to plug from London. It may be
>    correct — SLB's Deposit & Loan carries nulls in `INTERVAL` and `BYRESIDUAL` and is a live
>    configuration.
| **Mixed** — some columns transform, some don't | Per-column rules | Per-column, each stated. Any column that cannot be explained is `EVIDENCE_REQUIRED` |

⛔ **Until this runs, no step-6 value is `PROPOSED`.** It is one query, it needs only Tier 1, and
getting it wrong means every accrual row in the branch is wrong in the same way — silently, since
nothing rejects an out-of-range accrual flag.

→ `Q-05d-gbo-vs-box-same-branch.csv`

### Q-05c — a reference branch's instrument set `Env: BOX` *(new 2026-09-17)*

**Purpose:** turn gate 0c from an SME phrase into a concrete enumeration. Run against a named
reference branch (SLB is the working hypothesis for NY_SCH), put the resulting list in front of the
SME, and have them confirm or amend it **in writing**.

> ## ⛔ Corrected 2026-09-18 — the first version of this query joined the wrong table
>
> `[confirmed: DB via Edouard]` It joined `FK_INSTRUMENT` to **`BOX_FE.T_BOX_ENGINSTRUMENTS_S`**
> (Processed Instruments). That is wrong. `T_BOX_ENGACCRCONF_S.FK_INSTRUMENT` resolves to
> **`PGT_SYS.T_PGT_SUB_PRODUCT_S.PK`** — the Sub-Product level of the Family→Product→Sub-Product
> hierarchy. Observed `FK_INSTRUMENT` values for SLB are `20111.4`, `20.4`, `20092.4`, `20330.4`,
> `2.4`, `20314.4`, `20213.4`; Processed Instruments PKs are `1.65`, `2.65`, `3.65` — **different key
> spaces entirely**.
>
> **This repo already held the answer.** `T_BOX_CONF_BY_BOOK_S.FK_INSTRUMENT → T_PGT_SUB_PRODUCT_S.PK`
> was confirmed on 2026-09-11 and written into
> [`../box-data-model.md`](../box-data-model.md), which warns in as many words: *"an 'instrument' FK is
> not self-evidently pointing at the same table every time."* The correct join was one doc away and was
> not checked. Flagging a join as assumed is necessary; it is not a substitute for looking.

**Step 1 — count first, with no join at all.** This is the authoritative size of the branch's
instrument set:

```sql
SELECT COUNT(*) AS INSTRUMENT_COUNT
FROM   BOX_FE.T_BOX_ENGACCRCONF_S
WHERE  FK_PARENT = &&REFERENCE_FE_CONFIG_PK;
```

**Step 2 — label them, with a `LEFT JOIN` so nothing can vanish:**

```sql
SELECT a.FK_INSTRUMENT,
       sp.DESCRIPTION AS INSTRUMENT_NAME,
       CASE WHEN sp.PK IS NULL THEN 'UNRESOLVED' END AS FLAG
FROM   BOX_FE.T_BOX_ENGACCRCONF_S      a
LEFT   JOIN PGT_SYS.T_PGT_SUB_PRODUCT_S sp ON sp.PK = a.FK_INSTRUMENT
WHERE  a.FK_PARENT = &&REFERENCE_FE_CONFIG_PK
ORDER  BY sp.DESCRIPTION NULLS LAST;
```

**Expect:** step 2 returns **exactly as many rows as step 1**. If it returns fewer, the query is
broken; if any row is flagged `UNRESOLVED`, that instrument exists in the branch's configuration but
its Sub-Product row could not be found — a finding to report, never a row to drop.

> ### ⚠️ Two rows really do go missing for SLB — unresolved
>
> `[confirmed: DB via Edouard, 2026-09-18]` The SIGOM Accrual tab for SLB shows **nine** instruments.
> The `INNER JOIN` version above returned **seven** — everything except **Credit Derivatives** and
> **Bond Return Swap**. So an inner join to Sub-Product silently removed two instruments from a
> branch's configuration, which is precisely the class of error hard rule 8 exists to catch, arriving
> by a new route: not a join that returns nothing, but one that returns *almost* everything.
>
> It also explains the long-standing **7-vs-9 discrepancy**: this repo's Tier 1 calibration baseline
> records 7 Accrual rows for SLB, and 7 is what this join produces. The baseline was very likely
> measured the same way.
>
> **Run step 1 to settle it.** If `COUNT(*)` is 9, the join drops two and 9 is the real set size. If it
> is 7, the SIGOM screen is showing something wider than one `FK_PARENT` and *that* needs explaining.
> Either answer is worth having; do not proceed on the assumption that 7 is correct because a query
> said so.
>
> `[inferred]` A plausible cause: every resolved `FK_INSTRUMENT` carries the `.4` suffix — the global
> reference environment — so Credit Derivatives and Bond Return Swap may be newer instruments whose
> Sub-Product rows were allocated elsewhere, or do not exist in this environment. Bond Return Swap is a
> product still under development, which fits. Unconfirmed.

**Note the suffix mix in the result rows**, because it corroborates the auth-code finding: PKs are
`.21` (this Tier 1 environment), `FK_INSTRUMENT` is `.4` (global reference data), and `FK_OWNER_OBJ` /
`FK_EXTENSION` are `35000126.65` / `35001114.65` (BOX-DEV). One row legitimately carries three
different origin environments — which is exactly what "the suffix records where a row was allocated"
predicts.

**What this authorises and what it does not.** It authorises proposing a *set*. It does **not**
authorise copying the reference branch's accrual **values** — hard rule 6 is unchanged, and NY is
USD/New York where SLB is not. Read the set; get it confirmed; never inherit it.

> ## ⚠️ Four accrual **values** are `NOT NULL` — gate 0c needs more than an instrument list
>
> `[confirmed: DDL via Devin, 2026-09-21]` `T_BOX_ENGACCRCONF_S` requires `PK`, `FK_OWNER_OBJ`,
> `FK_INSTRUMENT`, **`FK_FEEFIRSTDAYSEL`, `FK_INTFIRSTDAYSEL`, `INTCOMMONBASIS`, `BYTRIGGER`**.
>
> Those last four are accrual *values*, not identities. They **cannot be left null pending an SME**, so
> gate 0c's sign-off is not "which instruments" — it is **"which instruments, and for each of them these
> four values."** That makes the SME conversation more demanding than this repo has been describing, and
> it should be put to them that way rather than discovered at SQL-generation time.
>
> The unique index is `(FK_PARENT, FK_INSTRUMENT)` — which **proves** what this repo has asserted since
> 2026-09-17: step 6 is exactly one row per instrument, so its row count *is* `PRODUCT_BOOK_SCOPE`.

→ `Q-05-accrual-gbo.csv`, `Q-05b-accrual-box.csv`, `Q-05c-reference-instrument-set.csv`

### Q-06 — Accrual exceptions `Env: GBO` + `BOX`

```sql
SELECT * FROM DEVENG.T_PGT_CONFIG_ACCRUAL_S WHERE FK_PARENT = <GBO config PK>;
SELECT * FROM BOX_FE.T_BOX_CONFIG_ACCRUAL_S WHERE FK_PARENT = &&FE_CONFIG_PK;
```

> ## ⛔ Corrected 2026-09-23 — one GBO configuration, several branches' exceptions
>
> `[stated: BOX FE expert via Edouard, 2026-09-23]` *"For the same `FK_PARENT = 64408.35` we had accrual
> exceptions for more than one branch."* NY's GBO MIS configuration is **shared**: `WHERE FK_PARENT`
> alone returns other branches' exceptions too. Run 3 then wrote the GBO `FK_BRANCH` (`141.35`) into
> BOX. **Two defects, one cause:** GBO's `FK_BRANCH` on this table is a **branch-configuration** PK, not
> a branch.
>
> | | GBO `T_PGT_CONFIG_ACCRUAL_S.FK_BRANCH` | BOX `T_BOX_CONFIG_ACCRUAL_S.FK_BRANCH` |
> |---|---|---|
> | Points into | `PGT_STC.T_PGT_BRANCH_CONFIG_S` → its `FK_BRANCH` → `T_PGT_BRANCH_S` | `PGT_STC.T_PGT_BRANCH_S` — the branch itself |
> | NY value | `141.35` (a branch config) | **`&&BRANCH_PK`** — `20007.4` |
> | Evidence | the expert's query, below | Q-G7 `pBranch` → `PGT - Branch`; and the BOX FE team's own inserts write `22.21` (Madrid) and `20087.4` (SLB) here |
>
> **So step 7 does three things, in this order:**
>
> 1. **Filter** GBO's exceptions to this branch — `T5.FK_BRANCH = &&BRANCH_PK` via the branch-config
>    join. Report the rows filtered out and **which branch each belongs to** (from `T6`), rather than
>    calling them "unrelated".
> 2. **Filter** to the approved instruments (gate 0c). Report those filtered out too.
> 3. **Write `FK_BRANCH = &&BRANCH_PK`** — a re-keyed column (hard rule 13), never the mined value.
>
> **`CRITERIAL` is mined** — it is `T1.CRITERIAL` on the same GBO row, which answers run 3's *"no
> provenance"*. Copy it per row; do not default it to `1` because the team's examples show `'1'`.

**The canonical GBO read** — the expert's query `[stated: BOX FE expert via Edouard, 2026-09-23]`,
with `T1.FK_INSTRTYPE` added to the select list and the duplicated `T1.PK` dropped:

```sql
SELECT T1.PK, T2.PK, T2.DESCRIPTION, T3.PK, T3.DESCRIPTION, T4.PK, T4.DESCRIPTION,
       T5.PK, T6.PK, T6.DESCRIPTION, T1.CRITERIAL, T1.FK_INSTRUMENT, T1.FK_STRATEGY, T1.FK_INSTRTYPE
FROM        DEVENG.T_PGT_CONFIG_ACCRUAL_S   T1
JOIN        PGT_SYS.T_PGT_SUB_PRODUCT_S     T2 ON T1.FK_INSTRUMENT = T2.PK
LEFT JOIN   PGT_SYS.T_PGT_INSTRUMENT_TYPE_S T3 ON T1.FK_INSTRTYPE  = T3.PK
JOIN        PGT_SYS.PGT_DOMAINS             T4 ON T1.FK_STRATEGY   = T4.PK
JOIN        PGT_STC.T_PGT_BRANCH_CONFIG_S   T5 ON T1.FK_BRANCH     = T5.PK
JOIN        PGT_STC.T_PGT_BRANCH_S          T6 ON T5.FK_BRANCH     = T6.PK
WHERE       T1.FK_PARENT = &&GBO_CONFIG_PK                 -- NY: 64408.35
ORDER  BY   T1.FK_INSTRUMENT, T1.FK_STRATEGY;

-- hard rule 8: the inner joins can drop rows. Count unjoined, and compare.
SELECT COUNT(*) FROM DEVENG.T_PGT_CONFIG_ACCRUAL_S WHERE FK_PARENT = &&GBO_CONFIG_PK;
```

The first query returns **every** branch's rows with `T6` naming the branch — the filter to NY
(`T6.PK = &&BRANCH_PK`) is applied by the agent in the findings, visibly, not in the `WHERE`. A
count mismatch between the two queries is a finding: some row's instrument, strategy or branch config
does not resolve.

⚠️ The 2026-09-18 note below says the mined `FK_BRANCH` "carries across environments unchanged". **That
is withdrawn** — it assumed GBO's column points at the branch master. It does not.


Grain: configuration × instrument × strategy × instrument-type × **branch**. This is one of the few
child tables carrying a branch column of its own — check whether it needs a row per branch even when
the parent configuration is shared. Tier 1: 6 rows (ESP), 5 (SLB).

> ## ⛔ Corrected 2026-09-18 — "`FK_BRANCH` semantics are not resolved for BOX" is not a blocker
>
> A run emitted `BLOCKED: Q-06 accrual-exception FK_BRANCH semantics are not resolved for BOX` and
> produced nothing for step 7. That conflates two different things:
>
> | | |
> |---|---|
> | **Can this step be mined?** | **Yes.** `WHERE FK_PARENT = 64408.35` returns NY's accrual exceptions from its own GBO configuration, exactly like every other child step |
> | **Is `FK_BRANCH` geographic or product-shaped on the BOX side?** | Open — the BOX-DEV `BOX CCS` / `BOX FX` / `BOX IRS` sighting |
>
> The second is a **verification item on the values**, not a reason to skip the mine. And the GBO
> evidence points the other way: `DEVENG.T_PGT_ERRORS_FE_S` — the other product-shaped-branch suspect —
> was confirmed on 2026-09-18 to key on a **geographic** `FK_BRANCH`. ~~`FK_BRANCH` also resolves into
> `PGT_STC.T_PGT_BRANCH_S`, a shared schema, so the mined value carries across environments
> unchanged.~~ **Withdrawn 2026-09-23** — on this table GBO's `FK_BRANCH` is a branch-*config* PK; see
> the correction above.
>
> **Correct behaviour:** mine it, propose the rows with `FK_BRANCH = &&BRANCH_PK`, status them
> `EVIDENCE_REQUIRED`, and let the SME sign off on a concrete row set. A blocker with no rows behind it
> gives the reviewer nothing to disagree with.
>
> ✅ **And the product-shaped-branch question is now closed, 2026-09-18.** `BOX_ENG_Config_Accrual`
> declares **`pBranch` → `PGT - Branch` → `PGT_STC.T_PGT_BRANCH_S`** — the geographic branch master.
> So does `BOX - Limit Error Assign`. The `BOX CCS` / `BOX FX` / `BOX IRS` values seen in BOX-DEV are
> rows *inside* that master, which this repo already records as overloaded (~137 rows: entities, SPVs,
> counterparties, test records). A dev environment with junk in the branch table, not a different data
> model. **The walk's grain is correct.** `[confirmed: DB, 2026-09-18]`
>
> Q-G7 also gives this object's full declared field list: `pBranch`, `pInstrType`
> (→ `T_PGT_INSTRUMENT_TYPE_*`), `pInstrument` (→ `T_PGT_SUB_PRODUCT_S`), `pStrategy` (→ `PGT_DOMAINS`),
> plus the literals `Criterial` and `Parent`. That matches the recorded grain exactly.
>
> If the mine genuinely returns zero rows for NY, hard rule 8 applies — control against Madrid or
> London, which have 6 and 5 — and a proven-empty result is `CONFIRMED_ABSENT`, a legitimate outcome
> for an *exceptions* table.

→ `Q-06-accrual-exceptions-gbo.csv`, `Q-06b-accrual-exceptions-box.csv`

### Q-06c — Step 7's rows, export-ready `Env: GBO` *(new 2026-09-23)*

**Purpose:** the file step 7's SQL is generated from. Q-06 is for reading (it names branches and
instruments); this is the same set with **unique, aliased columns**, because the generator refuses a CSV
with duplicate headers — and Q-06 has four columns called `PK`.

```sql
SELECT T1.FK_INSTRUMENT, T1.FK_STRATEGY, T1.FK_INSTRTYPE, T1.CRITERIAL,
       T6.PK AS BRANCH_PK, T6.DESCRIPTION AS BRANCH, T1.PK AS GBO_ROW_PK
FROM        DEVENG.T_PGT_CONFIG_ACCRUAL_S   T1
LEFT JOIN   PGT_STC.T_PGT_BRANCH_CONFIG_S   T5 ON T1.FK_BRANCH = T5.PK
LEFT JOIN   PGT_STC.T_PGT_BRANCH_S          T6 ON T5.FK_BRANCH = T6.PK
WHERE       T1.FK_PARENT = &&GBO_CONFIG_PK
ORDER  BY   T1.FK_INSTRUMENT, T1.FK_STRATEGY;
```

**All branches, unfiltered** — the filter is applied by `scripts/render_sql.py` (to `branch_pk` and the
approved instruments) and again by the validator, visibly: `03-sql/render-report.md` lists every row
dropped, with its `BRANCH` and `GBO_ROW_PK`, for the findings. `LEFT JOIN`s: a row whose branch
config does not resolve has a NULL `BRANCH_PK`, is dropped by the filter, and is **a finding to report**.

→ `Q-06c-accrual-exceptions-emit.csv`

### Q-07 — Fixing exceptions `Env: GBO` + `BOX`

**Purpose:** processed-instrument → curve override **for one configuration**. Two objects, joined
through a view.

> ## ⛔ Corrected 2026-09-18 — this query had no configuration filter. Same defect as Q-04.
>
> As recorded, the join returned **every fixing exception in the schema, for every branch**. Asked to
> mine NY's, a run kept the unfiltered join and narrowed it with a `MIN(PK)` subquery instead — which
> picks an arbitrary row, not NY's rows.
>
> **The filter is `FK_PARENT = &&GBO_CONFIG_PK`** `[stated: Edouard, 2026-09-18]` — the GBO MIS header
> from Q-G2 (`64408.35` for NY_SCH), the same predicate Q-06, Q-08 and Q-09 already use on their
> sibling child tables.
>
> This is the **second** instance of a catalogue join recorded without the predicate its walk step
> needs, and the second time a run filled the blank rather than reporting it. Hard rule 8's fourth
> mechanism covers both. Every remaining `SELECT *` in this catalogue with no `WHERE` has now been
> checked against its step.

```sql
-- GBO (the evidence) — NY's fixing exceptions, not everyone's
SELECT f.*, v.*
FROM   DEVENG.T_PGT_FIXING_BY_INSTR_S f
JOIN   DEVENG.V_PGT_PROC_INSTR_S      v ON f.FK_INSTRUMENT = v.PK
WHERE  f.FK_PARENT = &&GBO_CONFIG_PK;     -- the MIS header from Q-G2. Never omitted.

-- Count first, unjoined — hard rule 8's third mechanism
SELECT COUNT(*) FROM DEVENG.T_PGT_FIXING_BY_INSTR_S WHERE FK_PARENT = &&GBO_CONFIG_PK;

-- BOX (existing), deferred in a deferred-verification run
SELECT f.*, v.*
FROM   BOX_FE.T_BOX_FIXING_BY_INSTR_S f
JOIN   BOX_FE.V_BOX_PROC_INSTR_S      v ON f.FK_INSTRUMENT = v.PK
WHERE  f.FK_PARENT = &&FE_CONFIG_PK;
```

**Expect:** zero or more — this is an *exceptions* table, so a genuine zero is a legitimate finding,
but only against a control (Madrid's or London's configuration) proving the predicate works.

**`FK_INSTRUMENT` here resolves through the view, not to Sub-Product.** This is the third distinct
target for that column name in the walk — see [`../confirmed-joins.md`](../confirmed-joins.md).

> ## ⚠️ Step 2's pre-commit writes into this table — 2026-09-21
>
> `[confirmed: source via Devin]` `PKG_ENGPRECOMMIT.p_check_Val_Curves_precommit`, called with the
> **step-2 header PK**, UPDATEs `T_BOX_FIXING_BY_INSTR_S WHERE fk_parent = pk_in`, back-filling null
> `fk_fixingcurve_acc` / `fk_fixingcurve_man` from the header's defaults — **and COMMITs.**
>
> Two things follow for this step:
>
> 1. **Emit these rows with their curve values populated.** Where the GBO row is null, fill it from the
>    configuration header and tag the value `DERIVED`, citing `023-pkg_engprecommit_body.sql:413-438` as
>    the rule. That is what SIGOM would do anyway, done visibly and inside the transaction.
> 2. **Then call the procedure as a check.** If it updates nothing, it commits nothing — and its finding
>    nothing to do is positive evidence the INSERT set matched SIGOM. See charter hard rules 10 and 11.
>
> Also: `NOT NULL` is `PK`, `FK_OWNER_OBJ`, `FK_INSTRUMENT`; the unique index is
> `(FK_PARENT, FK_INSTRUMENT)` — **a fourth independent confirmation of the `FK_PARENT` correction
> above**, after the metamodel declaration, Edouard's correction and the procedure's own `WHERE` clause.

**Do not confuse with `T_BOX_FIXING_ASSIGNMENT_S`** (Q-11) — separate tables, separate roles. This
one is configured; that one is derived.

→ `Q-07-fixing-exceptions-gbo.csv`, `Q-07b-fixing-exceptions-box.csv`

### Q-08 — Yield curve `Env: GBO` + `BOX`

```sql
SELECT * FROM DEVENG.T_PGT_ENGZCCONF_S WHERE FK_PARENT = <GBO config PK>;
SELECT * FROM BOX_FE.T_BOX_ENGZCCONF_S WHERE FK_PARENT = &&FE_CONFIG_PK;
```

> ✅ **The `FK_PARENT` join is confirmed, 2026-09-18** — and so is Q-09's. Both were `[open-question]`
> because neither could be validated against a table that is empty in Tier 1 PRE. The metamodel settles
> it without data: `BOX_ENG_Config` declares **`amZeroCoupon`** (`FK_KIND 3.1`, an owned collection) →
> `T_BOX_ENGZCCONF_S`, and **`amCurrencyBasis`** → `T_BOX_ENGCURRENCYBASIS_S`. An owned collection's
> parent *is* the owning object, so `FK_PARENT = <GBO config PK>` is correct for both.
>
> An empty table cannot validate a join; a declaration does not need to. `[confirmed: DB, 2026-09-18]`
>
> **The steps stay parked** — for the separate reason that nobody has said whether the branch needs
> rows. Q-G7 also gives their declared fields: Yield Curve takes instrument (Sub-Product), currency and
> a yield curve from a new-to-this-repo `T_PGT_YIELDCURVE_*` master; Currency Basis takes maturity type,
> currency and a basis from `T_PGT_BASIS_S`.

> ## ✅ They are ordinary configuration — not derived, not batch-populated. 2026-09-21
>
> `[confirmed: source via Devin]` **Nothing in `cib-boxfin-dbboxfe` or `cib-boxacc-dbboxacc` writes to
> `T_BOX_ENGZCCONF_S`, `T_BOX_ENGCURRENCYBASIS_S` or `T_BOX_ENGFIXDISC_S`** — DDL, GRANT and SIGOM
> project-catalogue entries only. All three are registered as SIGOM configuration entities with
> edit-sheet metadata: the signature of tables maintained through the configuration UI.
>
> **So their status changes.** They were parked as *"empty, purpose unresolved, possibly derived."* They
> are ordinary configuration that **nobody has configured in Tier 1 PRE**. That makes the developer's
> "they probably don't matter" better founded — Madrid and London run without them — and it sharpens the
> question from *"what are these?"* to **"does NY need them?"**, which an SME can actually answer. If
> the answer is yes, they are INSERT targets like any other step.
>
> Caveat worth keeping: these repos hold DDL, packages and catalogue DML only. The SIGOM UI persistence
> layer is not in them, so *"nothing here writes them"* is strong evidence, not proof.

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

✅ **`FK_PARENT` confirmed 2026-09-18** — declared as `BOX_ENG_Config.amCurrencyBasis`, an owned
collection; see the Q-08 block above. The same **parked 2026-09-17** note still applies: the table is
empty in Tier 1 PRE, so a zero-row result remains ambiguous between "not configured for this branch"
and "not used at all". That is a purpose question, no longer a join question.

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

> ## ⛔ Corrected 2026-09-23 — two rows per instrument, not one
>
> `[stated: BOX FE expert via Edouard, 2026-09-23]` *"We should actually create 2 rows for each
> instrument: 1 row for each (book × instrument) combination; 1 additional row for (dummy book ×
> instrument) — dummy book used in Tier 1 is Label = `26391.4`."*
>
> **So step 11's row count is `(books + 1) × instruments`.** For NY with one book and six instruments:
> **12**, not the 6 run 3 wrote. The dummy row is not optional and not a placeholder for a missing book —
> it is emitted **in addition to** the real ones. This refines the 2026-09-17 guidance below that "rows
> with a `0 - EMPTY` Book/Label value exist": Q-10c establishes whether `26391.4` is that label.
>
> Input **`DUMMY_BOOK_LABEL`**, verified in the target by Q-10c — `26391.4` is the **Tier 1** value;
> `PGT_SYS` is shared, so it very likely holds in Tier 2, but *likely* is not evidence.



✅ **Both are now declared, not just observed** `[confirmed: DB, 2026-09-18]` — `BOX - MIS Config by
Book` (`35000302.65`) declares exactly three fields: `pBranch` → `T_PGT_BRANCH_S`, `pInstrument` →
`T_PGT_SUB_PRODUCT_S`, `pLabel` → `PGT_DOMAINS`. That is the whole INSERT. Its ownership link to the
configuration is `BOX_ENG_Config.amConfigByBook` (`FK_EXTENSION = 35006145.65`) — a late addition to the
Config screen, whose PK sits far above the contiguous `35001107–35001121` block, which fits Book being
new BOX functionality.

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

> ## ✅ What this table is *for* — resolved 2026-09-21
>
> `[stated: Edouard]` + `[confirmed: DB]` **It is a batch-partitioning table, not business
> configuration.** BOX FE runs processing by **(BOOK, INSTRUMENT, BRANCH)** to parallelise jobs, and a
> row here declares one unit of parallel work. The corroborating evidence sits on the ACC side and is
> recorded in [`../book-and-folder.md`](../book-and-folder.md) rather than here.
>
> That answers the standing question the developer himself couldn't ("the table's exact purpose is not
> fully understood"), and reframes his two rules: the `0 - EMPTY` row is a **partition placeholder** so
> an instrument gets processed at all, and a missing row is a **missing partition**, which is why the
> failure is silent — nothing errors, the work is simply never scheduled.
>
> **BOOK = the desk; FOLDER = an aggregation of Murex portfolios owned by GER.** Different dimensions.
> See [`../book-and-folder.md`](../book-and-folder.md).

> ## ⚠️ There is no way to verify book scope is complete — a named risk on this step
>
> `[confirmed: DB, 2026-09-21]` **No BOOK↔FOLDER mapping exists in BOX.** You cannot enumerate the
> folders under a book, so you cannot prove a branch's Book rows cover all of its trades. Gate 0c gets
> the *instrument* scope signed off; **there is no equivalent gate for book scope**, and none can be
> built from configuration alone.
>
> **But it is derivable from deal data**, which gives a coverage check for a *live* branch:
>
> ```sql
> SELECT lbl.CODE AS book_code, lbl.DESCRIPTION AS book, COUNT(*) AS deals
> FROM        BOX_FE.T_BOX_DATADEAL_S d
> JOIN        PGT_SYS.PGT_DOMAINS     lbl ON lbl.PK = d.FK_LABEL
> WHERE       d.FK_BRANCH = &&BRANCH_PK
> GROUP  BY   lbl.CODE, lbl.DESCRIPTION;
> ```
>
> Diff those books against this table for the same branch: **a book on deals with no partition row is a
> silent processing gap.** For a branch not yet live it can only be run against a reference branch — to
> size the problem and validate the method, not to produce the answer.

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

### Q-10c — The dummy book, and the two-row pattern on existing branches `Env: BOX` *(new 2026-09-23)*

**Purpose:** prove the dummy label exists in the target, and see the pattern on a branch that already
has it. The second query is the expert's `[stated: BOX FE expert via Edouard, 2026-09-23]`, written in
the original outer-join form:

```sql
-- (a) The dummy label — expect exactly 1 row
SELECT * FROM PGT_SYS.PGT_DOMAINS WHERE PK = &&DUMMY_BOOK_LABEL;       -- Tier 1: 26391.4

-- (b) The pattern on an existing branch (Madrid, 22.21, in Tier 1)
SELECT *
FROM   BOX_FE.T_BOX_CONF_BY_BOOK_S T1, PGT_STC.T_PGT_BRANCH_S T2,
       PGT_SYS.T_PGT_SUB_PRODUCT_S T3, PGT_SYS.PGT_DOMAINS T4
WHERE  T1.FK_BRANCH     = T2.PK(+)
AND    T1.FK_INSTRUMENT = T3.PK(+)
AND    T1.FK_LABEL      = T4.PK(+)
AND    T1.FK_LABEL      = &&DUMMY_BOOK_LABEL      -- the dummy-book rows
AND    T2.PK            = &&REFERENCE_BRANCH_PK;  -- a BRANCH PK: SLB 20087.4 (or Madrid 22.21) — never a label

-- (c) In the TARGET tier: which branches already carry dummy rows? Non-zero proves the label is live here.
SELECT FK_BRANCH, COUNT(*) FROM BOX_FE.T_BOX_CONF_BY_BOOK_S
WHERE  FK_LABEL = &&DUMMY_BOOK_LABEL GROUP BY FK_BRANCH;
```

**Expect:** (a) one row; (b) one dummy row per instrument the reference branch has; (c) at least one
branch in the target tier. **(a) empty or (c) zero in the target is a stop for step 11** — run
**Q-10d** and put the answer to the BOX FE team as a decision card; never reuse Tier 1's label on the
strength of `PGT_SYS` being shared. ⚠️ **Run 4: `26391.4` is absent in Tier 2.**

→ `Q-10c-dummy-book.csv` (three files: `-label`, `-pattern`, `-target`)

### Q-10d — Find the Tier 2 dummy-book label `Env: Tier 1` then `Env: BOX` (target) *(new 2026-09-24)*

**Why:** run 4 found **Tier 1's dummy label `26391.4` does not exist in Tier 2** — so `PGT_SYS` is *not*
identical across tiers for book labels, whatever `confirmed-joins.md` says about the schema in general.
The run then set `DUMMY_BOOK_LABEL` to the real book's label, which satisfied a check and skipped the
row. **Never again:** find candidates, then put a decision card to the BOX FE team.

```sql
-- (a) TIER 1: what the dummy is — its code, description and domain
SELECT PK, CODE, DESCRIPTION, FK_OWNER_OBJ FROM PGT_SYS.PGT_DOMAINS WHERE PK = 26391.4;

-- (b) TARGET: labels in the same domain whose CODE or DESCRIPTION matches (a) — enumerate, don't guess
SELECT PK, CODE, DESCRIPTION FROM PGT_SYS.PGT_DOMAINS
WHERE  FK_OWNER_OBJ = <FK_OWNER_OBJ from (a)>
AND   (CODE = '<CODE from (a)>' OR DESCRIPTION = '<DESCRIPTION from (a)>');

-- (c) TARGET: which labels existing branches use, and how widely. A dummy is used by many branches,
--     across every instrument each one has.
SELECT b.FK_LABEL, d.CODE, d.DESCRIPTION,
       COUNT(DISTINCT b.FK_BRANCH) AS branches, COUNT(DISTINCT b.FK_INSTRUMENT) AS instruments, COUNT(*) AS n
FROM        BOX_FE.T_BOX_CONF_BY_BOOK_S b
LEFT JOIN   PGT_SYS.PGT_DOMAINS         d ON d.PK = b.FK_LABEL
GROUP  BY   b.FK_LABEL, d.CODE, d.DESCRIPTION
ORDER  BY   branches DESC, n DESC;
```

**Read it:** a label that matches (a) in (b) **and** sits at the top of (c) is a strong candidate. Put
it as a card — *Authority: BOX FE team* — with options: use it · another label · the dummy must be
created in Tier 2 first. **The agent never creates a label and never picks one without an answer.** No
answer → step 11 `EVIDENCE_REQUIRED`, no SQL. **A real book's label is never the dummy.**

→ `Q-10d-dummy-tier1.csv`, `Q-10d-dummy-candidates.csv`, `Q-10d-labels-in-use.csv`

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

### Q-12 — Days Matured per instrument (step 14a) and EngSetup (14b) `Env: BOX` — **revised 2026-09-23**

> ## ⛔ Corrected 2026-09-23 — Days Matured is not branch-scoped, but it **is** instrument-scoped
>
> `[stated: BOX FE expert via Edouard, 2026-09-23]` *"We need to check what's configured in that table
> for the instruments/products our branch needs. If there is already a row for our instrument/product
> → that's fine. If an instrument/product is missing a line there → we should create the line (and
> configure it like our reference branch — SLB in this case)."* And: *"There should be nothing to
> configure for `BOX_FE.T_BOX_ENGSETUP_S`."*
>
> So step 14 splits:
>
> | Step | Table | Rule | Status when nothing to do |
> |---|---|---|---|
> | **14a** | `T_BOX_ENGDAYS_MATURED_S` | **Per approved instrument:** row present in the target → nothing. Missing → **insert**, `NUM_DAYS` as the reference branch's environment has it for that instrument | `CONFIRMED_PRESENT` |
> | **14b** | `T_BOX_ENGSETUP_S` | Nothing to configure, ever | `NOT_BRANCH_SCOPED` |
>
> **"Configure it like SLB" on a table with no branch column** means: take `NUM_DAYS` for that same
> instrument from the environment SLB is configured in (**Tier 1**). A proposal aid under hard rule 6,
> not a mined value — so it is **`PROPOSED`** and signed per instrument. If Tier 1 has no row for the
> instrument either, it is `SME_DECISION_REQUIRED` — never the value of the nearest-looking instrument.
>
> **Row shape** `[reference: BOX FE expert examples, 2026-09-23]` — `PK, FK_OWNER_OBJ, DDATE,
> FK_INSTRUMENT, NUM_DAYS`; no `FK_PARENT`, no `FK_EXTENSION`, no branch. The team's own insert writes
> `DDATE = SYSDATE`: **propose that and ask** — it is the one column whose meaning nobody has stated.
> `[2026-09-24]` If the existing rows carry no time of day (`ddate_time_part` = 0 in (a) and (b)), the
> card offers `TRUNC(SYSDATE)` too: a batch comparing `DDATE <= <process date at midnight>` would not see
> a row stamped `SYSDATE` until the next day. `values.json` accepts either.

**The step-14a queries** (they replace the `SELECT *` of `T_BOX_ENGDAYS_MATURED_S` below):

```sql
-- (a) TARGET tier: which approved instruments already have a row?
SELECT sp.PK AS instrument, sp.DESCRIPTION, dm.PK AS dm_pk, dm.NUM_DAYS, dm.DDATE,
       dm.DDATE - TRUNC(dm.DDATE) AS ddate_time_part            -- 0 on every row -> propose TRUNC(SYSDATE)
FROM        PGT_SYS.T_PGT_SUB_PRODUCT_S   sp
LEFT JOIN   BOX_FE.T_BOX_ENGDAYS_MATURED_S dm ON dm.FK_INSTRUMENT = sp.PK
WHERE       sp.PK IN (&&APPROVED_INSTRUMENTS)
ORDER  BY   sp.PK, dm.DDATE;

-- (b) TIER 1 (the reference branch's environment): the values to propose for the missing ones
SELECT FK_INSTRUMENT, NUM_DAYS, DDATE, DDATE - TRUNC(DDATE) AS ddate_time_part, PK
FROM   BOX_FE.T_BOX_ENGDAYS_MATURED_S
WHERE  FK_INSTRUMENT IN (<instruments (a) found missing>)
ORDER  BY FK_INSTRUMENT, DDATE;
```

**Read (a) carefully:** more than one row for an instrument means `DDATE` versions it — report all of
them, and propose from the latest in (b). A NULL `dm_pk` is a missing instrument. Hard rule 8's control
applies: (a) must return at least one present row for *some* instrument, or the join is suspect.

**The original column check, still run as evidence for 14b:**

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

> ✅ **Confirmed 2026-09-17**, ⚠️ **refined 2026-09-23.** `[stated: BOX FE Developer via Edouard]` Both tables are **global; a new
> branch needs nothing in them** — *as a branch*. Days Matured still needs a row per **instrument**, and
> an in-scope instrument without one is step 14a's insert (correction above). Run the query anyway as the evidence behind the status — the charter
> requires a status to trace to a result, not to a recollection — but the expected answer is now known
> rather than hypothesised.

→ `Q-12-not-branch-scoped.csv` (three files: `-columns`, `-days-matured`, `-engsetup`), `Q-12a-days-matured-target.csv`, `Q-12b-days-matured-tier1.csv`

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

-- (b) ★ THE SOURCE for this step, since 2026-09-21 (ADR 0004). Run in TIER 1 (SLB is configured there).
--     REFERENCE_BRANCH_PK = SLB = 20087.4 (PGT_STC.T_PGT_BRANCH_S, CODE 'LND BRANCH') — a BRANCH PK.
--     Never a book label (26391.4), a branch config (141.35) or a config header (333105.21).
--     LEFT JOIN for the label: an instrument that does not resolve is a finding, not a row to drop.
SELECT      e.PK, e.FK_BRANCH, br.CODE AS branch_code, e.FK_INSTRUMENT, sp.DESCRIPTION AS instrument,
            e.LIMIT_ERRORS
FROM        BOX_FE.T_BOX_ERRORS_FE_S    e
LEFT JOIN   PGT_STC.T_PGT_BRANCH_S      br ON br.PK = e.FK_BRANCH
LEFT JOIN   PGT_SYS.T_PGT_SUB_PRODUCT_S sp ON sp.PK = e.FK_INSTRUMENT
WHERE       e.FK_BRANCH = 20087.4                    -- REFERENCE_BRANCH_PK (SLB)
ORDER  BY   e.FK_INSTRUMENT;
SELECT COUNT(*) FROM BOX_FE.T_BOX_ERRORS_FE_S WHERE FK_BRANCH = 20087.4;  -- unjoined; expect > 0

-- (b0) If (b) returns nothing: confirm the PK is SLB's before concluding anything
SELECT PK, CODE, DESCRIPTION FROM PGT_STC.T_PGT_BRANCH_S WHERE PK = 20087.4;   -- expect LND BRANCH

-- (c) The GBO twin. EXISTS (confirmed 2026-09-18) but is NO LONGER MINED for this step — ADR 0004.
--     Kept for reference only; running it does not produce a value for the walk.
SELECT * FROM DEVENG.T_PGT_ERRORS_FE_S WHERE FK_BRANCH = &&BRANCH_PK;
```

> ## 🔄 Source changed 2026-09-21 — propose from the reference branch
>
> `[stated: Edouard, 2026-09-21]` **Query (b) is the source; query (c) is not.** For each in-scope
> instrument, propose the reference branch's `LIMIT_ERRORS` for **that same instrument**, tagged
> **`PROPOSED`** with the rule attached, for the SME to accept or change. Full reasoning and the
> boundary it must not cross:
> [ADR 0004](../../decisions/0004-step12-limits-from-reference-branch.md).
>
> **Three things this query must establish, not just return:**
>
> 1. **One row per in-scope instrument, or a stated gap.** A reference-branch instrument with no row is
>    `EVIDENCE_REQUIRED` — **not** a limit of zero, which is the dangerous default this step exists to
>    prevent.
> 2. **The instrument identity matches exactly.** Same instrument, not the nearest-looking one. No
>    similarity mapping — see the ADR's boundary section.
> 3. ✅ **Credit Derivatives exists** — `T_PGT_SUB_PRODUCT_S` PK `20313.4`, CODE `Credit`
>    `[confirmed: DB via Edouard, 2026-09-22]`. An earlier note here claimed it had no row; withdrawn.
>    Still check whether the reference branch has a step-12 row for it before proposing a limit — an
>    absent reference row is `EVIDENCE_REQUIRED`, never a limit of zero.

> ## ✅ Step 12 has a GBO source after all — confirmed 2026-09-18
>
> `[confirmed: DB via Edouard]` **`DEVENG.T_PGT_ERRORS_FE_S`**, keyed by **`FK_BRANCH`** (the
> geographic branch PK — `20007.4` for NY_SCH). The naming-rule prediction was right.
>
> **This changes step 12's character.** It was provisionally treated like step 11 — BOX-only, nothing
> to mine, values from a reference branch plus an SME. It is not: it is an ordinary mine-and-propose
> step like steps 2–10, with a real GBO row to read. The error limits come from **NY's own GBO
> configuration**, not from a reference branch and not from a guess.
>
> **A second, smaller finding.** The GBO column is `FK_BRANCH` and it holds a *geographic* branch PK.
> That was mild evidence against the product-shaped-branch worry on the GBO side; the BOX side is now
> settled too — see below.

> ## ✅ The BOX side is declared too — 2026-09-18
>
> `[confirmed: DB, 2026-09-18]` **`BOX - Limit Error Assign`** (`35000289.65`) is a **standalone
> object**, not a tab of the MIS Config — so its rows carry `FK_OWNER_OBJ = 35000289.65` and a NULL
> `FK_EXTENSION`, *not* Config's values. It declares exactly three fields:
>
> | Field | Kind | → |
> |---|---|---|
> | `LimitError` | `5.1` literal | the limit itself |
> | `pBranch` | `2.1` | **`PGT_STC.T_PGT_BRANCH_S`** — geographic |
> | `pInstrument` | `2.1` | `PGT_SYS.T_PGT_SUB_PRODUCT_S` |
>
> **That closes the product-shaped-branch question for this table**, and with the Accrual Exceptions
> result it closes it for the walk. It also gives the complete INSERT column list without needing (a).

> ## ⛔ A missing row means **zero tolerance**, not "no limit" — 2026-09-21
>
> `[confirmed: source via Devin]` `LIMIT_ERRORS` is read by `PKG_FE_DATADEAL_LOAD` and
> `PKG_FE_MTM_CALCULATION`, inside the `WHEN OTHERS` handler of **every per-instrument insert routine**,
> keyed by `(FK_BRANCH, FK_INSTRUMENT)` — **and it defaults to `0` when no row is found.**
>
> So a branch/instrument with no row here doesn't get a permissive default. It gets **zero**: the first
> failed deal aborts the whole load for that combination (`process_status` set, `-20001` raised). That is
> far harsher than this catalogue previously implied, and it makes **one row per in-scope instrument
> mandatory** — the same conclusion as step 11, reached for a completely different reason.
>
> **Semantics, for choosing a value.** It is a tolerance for *failed deals per load execution*, not a
> cumulative counter: `num_counterror` increments per failed insert and is compared against
> `LIMIT_ERRORS`; below the limit the process deletes/re-propagates the row and continues. Nothing
> writes back to the table, so it is static configuration. `100` therefore means "abort after 100 failed
> deals in one run" — still an SME decision, but now an informed one rather than a number inherited
> from another branch.
>
> `[open-question]` Whether `num_counterror` is procedure-local or package-level is unverified, so
> whether the count resets per instrument or spans a whole session is open. It changes what a given
> number means in practice.
>
> **`NOT NULL`:** `PK`, `FK_OWNER_OBJ`, `FK_INSTRUMENT`. **Unique index:** `(FK_BRANCH, FK_INSTRUMENT)`
> — confirming the grain exactly. `[confirmed: DDL]`

**Expect:** rows per (branch, instrument). The row count should track the instrument scope, like
steps 6 and 11. Run (a) anyway to map the declared field names onto the physical column names.

**Two open points, flagged rather than assumed:**
- **What is the default limit, and is it safe to copy?** An error threshold is a risk parameter, not a
  structural value. Reading a reference branch tells you the shape; the number needs an SME.
- ⚠️ **The product-shaped `Branch` column.** Allowed Errors is one of the two BOX-DEV screens where the
  `Branch` column showed values like `BOX CCS` / `BOX FX` / `BOX IRS` rather than geographic branches
  (see [`../branch-config/fe-branch-configuration.md`](../branch-config/fe-branch-configuration.md)
  §2). If that is real rather than a dev-environment convention, **this step's grain is wrong**.
  Query (a) settles it: look at what the branch column actually holds. Do this early.

> ## ✅ The row shape, from the BOX FE team's own inserts — 2026-09-23
>
> `[reference: BOX FE expert examples, Tier 1, product onboarding]` Two rows, Madrid and SLB, for one
> instrument:
>
> ```sql
> -- Madrid
> insert into BOX_FE.T_BOX_ERRORS_FE_S (PK, FK_OWNER_OBJ, FK_BRANCH, FK_INSTRUMENT, LIMIT_ERRORS)
>   values (<pk>, 35000289.65, 22.21,   20371.4, '100');
> -- SLB
> insert into BOX_FE.T_BOX_ERRORS_FE_S (PK, FK_OWNER_OBJ, FK_BRANCH, FK_INSTRUMENT, LIMIT_ERRORS)
>   values (<pk>, 35000289.65, 20087.4, 20371.4, '100');
> ```
>
> That settles three things query (a) was asked to learn: **the branch column is `FK_BRANCH`** and holds
> the **branch PK** (`T_PGT_BRANCH_S`, not a branch config); **the instrument column is
> `FK_INSTRUMENT`**; there is **no `FK_PARENT` and no `FK_EXTENSION`** — step 12 is not a child of the
> MIS configuration. Run (a) anyway as the evidence, but expect exactly these five.
>
> ⚠️ **Run 3 used NY's GBO `LIMIT_ERRORS`, which is `0` for all six instruments** — the operator's test
> decision, and it contradicts ADR 0004. Zero is the value the step exists to avoid: the first failed
> deal aborts the load. **Run 4 proposes SLB's per instrument**, as ADR 0004 says.

→ `Q-13-allowed-errors.csv` (three files: `-columns`, `-reference-branch`, `-gbo-twin-search`)

### Q-14 — Cross-environment reference check `Env: both` 📉 **spot check, not a per-run gate**

> ## 📉 Demoted 2026-09-18 (evening) — `PGT_STC` and `PGT_SYS` are shared
>
> `[stated: Edouard, 2026-09-18]` **Those two schemas hold identical rows in every environment.** That
> is most of what this query was checking, so running it per-run verifies a design guarantee rather than
> a risk — and it explains why the first run matched *exactly*: a shared schema, not lucky replication.
>
> | Mined FK | Schema | Check? |
> |---|---|---|
> | `FK_CALENDAR`, `FK_CURRENCY`, branch `FK_BS` | `PGT_STC` | ❌ Shared |
> | `FK_INSTRUMENT`, `FK_*DAYSEL`, `FK_LABEL`, other domain values | `PGT_SYS` | ❌ Shared |
> | **Quote references** (step 4) | `PGT_MRK` | ✅ **The one genuine item** `[open-question]` |
> | FKs to walk-created objects (`FK_CURVEMAN`, `FK_CURVEACC`) | `BOX_FE` / `DEVENG` | ❌ Apply-time |
>
> **Run this once per environment pair, then record the answer** — in
> [`../confirmed-joins.md`](../confirmed-joins.md), not just in a run folder. Do not spend a query round
> on it every run, and **never block a run on a `PGT_STC` or `PGT_SYS` value**: an out-of-sync shared
> schema is a platform escalation, not a finding about one branch onboarding.
>
> It is kept rather than deleted because "identical in every environment" is a stated design intent and
> real systems drift. One cheap check, not a gate.

**The part that still matters — quote references:**

```sql
-- Run in BOTH environments, compare. SELECT * deliberately: a comparison query must see
-- every column, or "same object" is a claim about the two columns you happened to pick.
SELECT *
FROM   PGT_MRK.T_PGT_QUOTE_REFERENCE_S qr
LEFT   JOIN PGT_MRK.T_PGT_QUOTE_SOURCE_S qs ON qs.PK = qr.FK_QUOTESOURCE
WHERE  qr.PK IN (<the FK_BS values Q-04 returned for this branch's curve>)
ORDER  BY qr.PK;
```

> ## 🔑 Answered 2026-09-18 — `PGT_MRK` is **environment-specific**, and step 4 is not rehearsable
>
> `[confirmed: DB via Edouard, 2026-09-18]` The first run of this check settles the open question, and
> the answer is **no, `PGT_MRK` is not replicated across environments.** NY_SCH's curve references **38
> quote references**; only **2** exist in BOX Tier 1 PRE.
>
> **The suffixes explain it completely.** Of the 38: **35 carry `.35`** — NY's own Tier 2 auth code —
> plus `6401.4`, `16309.4` (`.4`, global) and `12231.44` (`.44`). So thirty-five of NY's quote references
> were **allocated locally in Tier 2**. They are not shared reference data at all; they are NY's own
> market-data objects. Tier 1 has never had reason to hold Santander NY spot closing prices, and their
> absence there is correct behaviour, not a gap.
>
> **And one PK collides.** `6401.4` exists in both and resolves to **SANTANDER NY SPOT CLOSING PRICES**
> in GBO Tier 2 but **EUROPEAN CENTRAL BANK FIXING** in BOX Tier 1 PRE. Same PK, different object —
> the stop-and-escalate case. Note it carries the `.4` "global" suffix and still diverges, so **`.4` does
> not guarantee identity inside `PGT_MRK`** the way it does inside `PGT_STC`/`PGT_SYS`.
>
> **What this means — and it is good news for the real run.** `PGT_MRK` is confirmed **shared between
> BOX and GBO within one environment**. All 38 references were read from GBO Tier 2's `PGT_MRK`, so BOX
> Tier 2 sees the same 38 rows. **Step 4 will resolve natively in the real run; this blocker is an
> artifact of the substituted rehearsal target and provably does not occur in Tier 2.**
>
> **So step 4 is `EVIDENCE_REQUIRED — not rehearsable cross-environment`.** Record it, emit no SQL for
> it, and continue the other thirteen steps. Two things must **not** happen:
>
> | Tempting | Why not |
> |---|---|
> | Load NY's quote references into Tier 1 PRE to unblock the rehearsal | Polluting a shared pre-production environment with another branch's market data, to satisfy a test. The data has no business being there |
> | Substitute Tier 1 quote references so the curve "resolves" | **The worst available outcome.** It would configure NY to price off ECB fixings instead of Santander NY closes — hard rule 6 exactly, and the kind of error nothing downstream would catch until the numbers were wrong |
>
> A rehearsal that identifies precisely which step is environment-bound has done its job. That is a
> finding, not a failure.

**Expect:** every quote reference behind the branch's curve resolving identically in both — **and for a
split-tier rehearsal, expect that to fail for a branch whose market data is locally allocated**, per the
finding above. Absence in a *substituted* target is a statement about the substitution. Absence in the
*real* target would be a genuine provisioning finding.

---

**Original scope notes, retained** — they still govern *which kinds* of value are in scope at all:

### Q-14 (original framing) — what counts as a checkable value *(new 2026-09-18)*

**Purpose:** gate 0f. When `GBO_SOURCE` and `TARGET_ENV` are in **different tiers**, every FK value
mined from the source is a PK *in the source tier*. Before any `INSERT` carries one into the target,
prove it resolves there — and resolves to the **same object**.

Run **after** mining, once the findings table has a candidate value for each FK. Unlike the other
gates, this one cannot run before the walk: it tests values the walk produces.

> ## ⛔ MOVED 2026-09-22 — the three-kinds rule is now **hard rule 13**, and applies to every run
>
> The table below was written as a gate 0f scoping note. **It is not gate-specific**, and burying it
> inside a gate that is withdrawn for same-environment runs is how the 2026-09-22 run came to write
> `FK_CURVEMAN = 1.35` — a `DEVENG` curve PK — into a `BOX_FE` column, with this table naming that
> exact value as the example of what never to carry.
>
> **Read it in the charter's hard rule 13.** The copy below is retained because it is where the rule
> was first worked out, and because gate 0f's own scoping still needs it.

> ## ⛔ Scope correction, 2026-09-18 — this gate checks **reference FKs**, not source-object PKs
>
> The first run of this gate blocked on the wrong thing, and the wording below is why. Three kinds of
> value come out of mining, and **only one of them is a gate 0f item**:
>
> | Kind | Example | Gate 0f? |
> |---|---|---|
> | **Reference FK** — points at a pre-existing shared object the new rows will reference | `FK_CALENDAR = 83.4`, `FK_CURRENCY = 159.4`, `FK_INSTRUMENT = 20.4`, `FK_BS = <branch PK>` | ✅ **Yes.** Must resolve in the target |
> | **Source-object PK** — the identity of the GBO row being *read* | the GBO curve's own `PK = 1.35`, the GBO MIS header's `PK` | ❌ **No.** Never carried into the target |
> | **Intra-config FK** — points at another object *this walk creates* | curve → config header | ❌ **No.** Resolved at apply time from an `F___SEQUENCE` variable |
>
> **A source-object PK is expected to be absent from the target. That absence is the reason the walk
> exists.** If the GBO curve's PK already existed in the target, the branch would already be
> configured. Checking it against the target is a category error: it is not an FK the BOX row will
> carry, it is the identity of the thing being copied *from*. The new BOX row gets its own PK from
> `F___SEQUENCE`.
>
> **What happened.** On 2026-09-18 a run reported gate 0f blocked because GBO Tier 2's fixing curve
> `PK = 1.35` has no row at `PK = 1.35` in BOX Tier 1 PRE — while its own Q-14 output confirmed that
> calendars, currencies, branches and all sixteen Sub-Product descriptions matched exactly. **Those
> matches were the gate passing.** The curve was an absent *source PK*, which is step 3's normal
> `CONFIRMED_ABSENT` → create-it path, not a gate failure.
>
> The run's refusal to substitute a Tier 1 curve was **correct and should be preserved** — hard rule 6
> held exactly as intended. The error was in what it checked, not in how cautiously it behaved.

**Step 1 — list every **reference FK** that will appear in a statement.** From the findings table, not
from memory, and per the table above — reference FKs only. The set for this walk:
`FK_CALENDAR`, `FK_CURRENCY`, `FK_CURVEMAN`, `FK_CURVEACC`, `FK_SOURCE_FRONT`, `FK_SOURCE_BACK`
(step 2); quote references reached via `FK_BS` (step 4); the branch PK in `FK_BS` (step 5); each
`FK_INSTRUMENT` (steps 6, 11, 12); `FK_FEEFIRSTDAYSEL` / `FK_INTFIRSTDAYSEL` and other domain values
(step 6); `FK_LABEL` (step 11).

**Explicitly out of scope:** the PK of any GBO row being mined, and any FK pointing at an object this
walk itself creates. Record those as context in the findings table; do not gate on them.

**Step 2 — resolve each one in BOTH environments and compare the descriptions.**

```sql
-- Run the SAME query in GBO_SOURCE and in TARGET_ENV, save two CSVs, diff them.
-- Calendars
SELECT PK, DESCRIPTION FROM PGT_STC.T_PGT_CALENDAR_S   WHERE PK IN (<mined calendar FKs>);
-- Currencies
SELECT PK, DESCRIPTION FROM PGT_STC.T_PGT_CURRENCY_S   WHERE PK IN (<mined currency FKs>);
-- Sub-Product instruments
SELECT PK, DESCRIPTION FROM PGT_SYS.T_PGT_SUB_PRODUCT_S WHERE PK IN (<mined instrument FKs>);
-- Branch master
SELECT PK, <CODE_COLUMN> FROM PGT_STC.T_PGT_BRANCH_S    WHERE PK IN (<mined branch FKs>);
-- Domain values
SELECT PK, DESCRIPTION FROM PGT_SYS.PGT_DOMAINS         WHERE PK IN (<mined domain FKs>);
```

Table names for the calendar and currency masters are **not confirmed in this repo** — read them from
the branch master's FK columns on the first run and record them here.

**Interpreting it — three outcomes, and they are not equivalent:**

| Result | Meaning | Action |
|---|---|---|
| Present in both, **same description** | Global reference data, replicated. The common case for `.4` PKs | Use it. Tag the finding `CROSS_TIER_VERIFIED` |
| **Absent in the target** | The object does not exist there | `EVIDENCE_REQUIRED`. Emit no statement. A portability finding, not a value to substitute |
| Present in both, **different description** | Same PK, different object — the dangerous one | **Stop and escalate.** This is precisely the silent-wrong-value failure the agent exists to prevent |

**Expect, per the auth-code finding:** `.4` values (allocated in the global reference environment)
resolve identically in both tiers; tier-specific suffixes are the ones at risk. That is a **prior, not
a conclusion** — hard rule 8 applies, and "it's a `.4` so it must be fine" is exactly the reasoning
that rule forbids.

**This gate's answer has value past the rehearsal.** The proportion of mined FKs that are cross-tier
verified tells you how much of the eventual real run is a straight replay of these findings, and how
much has to be re-resolved against the real target.

**One reference FK in this walk deserves particular attention:** the **quote references** behind the
fixing curve (step 4, reached through `T_*_ENGLKFC_X.FK_BS` → `PGT_MRK.T_PGT_QUOTE_REFERENCE_S`).
`PGT_MRK` is documented as **shared between BOX and GBO** — but that is shared *within* a tier, and
whether it is also replicated *across* tiers is unrecorded. `[open-question]` If NY's quote references
do not exist in the target, step 4 is genuinely blocked there and that is a real gate 0f finding,
unlike the curve PK.

→ `Q-14-cross-tier-fk.csv` (two files, suffixed `-source`, `-target`)

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
| 4 | Q-04 | Join confirmed end to end — but it was recorded **with no curve filter**, and the one improvised in the first run used `FK_BS` (the quote-reference side) instead of `FK_PARENT`. Corrected 2026-09-18 |
| — | Q-04b | **New 2026-09-18** — decodes a quote reference into (currency pair, source, type). Three joins confirmed; `FK_QUOTEDIRECTION` / `FK_MATURITY` / `FK_PARENT` targets **unconfirmed** |
| 5 | Q-05 | Table confirmed; `FK_PARENT` assumed. **Also the per-branch instrument set** (2026-09-17) |
| — | Q-05c | **Join corrected 2026-09-18** — `FK_INSTRUMENT → PGT_SYS.T_PGT_SUB_PRODUCT_S.PK`, not Processed Instruments. Now `LEFT JOIN` with a count-first step: an inner join was silently dropping two of SLB's nine instruments |
| 6 | Q-06 | Table confirmed; `FK_PARENT` assumed |
| 7 | Q-07 | **Join confirmed** |
| 8 | Q-08 | Table confirmed; join `[open-question]`. **Empty in Tier 1 PRE (2026-09-17) — parked, not resolved** |
| 9 | Q-09 | Table confirmed; join `[open-question]`; rows never observed. **Confirmed empty in Tier 1 PRE (2026-09-17) — parked** |
| 10 | Q-10 | **Full join confirmed** (branch/sub-product/label); no GBO side exists — confirmed, not a gap (2026-09-11) |
| 11 | Q-11 | Relationships confirmed |
| 12 | Q-12 | Sound. **Answer now confirmed (2026-09-17): both tables global, no branch setup needed** |
| **2026-09-23** | Q-G3c | **New** — the target's auth code, read and recorded; feeds the config script's assertions and the verification script |
| **2026-09-23** | Q-02c | **New** — Murex source systems; `FK_SOURCE_BACK = 586.4` constant, `FK_SOURCE_FRONT` an input |
| **2026-09-24** | Q-04c | **Revised** — `FK_BS` settled; now the decoded, export-ready step-4 set. The PK-vs-FK_BS test that stopped run 4 is withdrawn |
| **2026-09-23** | Q-06 | **Corrected** — GBO `FK_BRANCH` is a branch-*config* PK; filter by branch via `T_PGT_BRANCH_CONFIG_S`, write `BRANCH_PK` |
| **2026-09-23** | Q-10c | **New** — dummy book label; step 11 is `(books + 1) × instruments` |
| **2026-09-24** | Q-10d | **New** — Tier 1's dummy is absent in Tier 2: find candidates, then a decision card to BOX FE |
| **2026-09-23** | Q-12 | **Revised** — Days Matured is instrument-scoped: insert missing instruments (step 14a); EngSetup nothing (14b) |
| — | Q-14 | **Demoted 2026-09-18 (evening)** — a one-time spot check, scoped to `PGT_MRK`. `PGT_STC` and `PGT_SYS` are shared and identical in every environment, so they need no cross-environment check |
| 13 | Q-13 | **New 2026-09-17** — Allowed Errors (`T_BOX_ERRORS_FE_S`). Table named by a BOX FE Developer; **column names, GBO twin and branch grain all unconfirmed** |

Three queries still rest on an assumed or unconfirmed join/column (Q-G1, Q-08, Q-09) — down from four
as of 2026-09-11, when Q-10's uncertainty was resolved the good way: not by finding the predicted GBO
table, but by a BOX FE Developer confirming none exists. Each remaining one is flagged inline above;
none should be allowed to produce a silent zero-row "absence" finding. Fix them on the first real run
and update this table — a zero-row result from a wrong join column is the most plausible way this
whole walk produces a confidently wrong answer.
