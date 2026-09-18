# Devin kickoff — NY_SCH BOX FE SIGOM config

Paste this as the task prompt to Devin. For a future branch, copy this file to
`kickoff-<branch>.md` and change **only the input block** — everything below it is branch-agnostic by
design, and if you find yourself editing the instructions instead of the inputs, something has leaked
into the wrong file and should be fixed there.

---

You are running as this repo's `sigom-box-fe-configs-agent`
(`agents/sigom-box-fe-configs-agent/AGENT.md`). Read that charter first, in full, before doing
anything. Then read, in this order:

1. `docs/process/03-fe-sigom-config-procedure.md` — the stage-by-stage sequence you follow
2. `docs/reference/queries/fe-config-mining.md` — the exact queries, with their IDs, target databases
   and output filenames
3. `docs/reference/branch-config/fe-branch-configuration.md` — the evidence base, §2 especially

**Your goal: produce the reviewed SQL that configures branch NY_SCH in BOX FE.** Not an analysis of
what's needed — the runnable statements, with an evidence trail behind every value.

**The shape of the job, so no gate misreads it.** NY_SCH is live in GBO Tier 2 and its Financial Engine
configuration exists there as real rows — MIS header `DEVENG.T_PGT_ENGCONF_S` `PK = 64408.35`, fixing
curve `DEVENG.T_PGT_ENGFCURVE_S` `PK = 1.35`, and so on. **You read those rows and create the equivalent
rows in `BOX_FE`.** Finding nothing for NY_SCH in `BOX_FE` is the **precondition** for the job, not a
problem — if the BOX row already existed there would be nothing to do. Every step expects
`CONFIRMED_ABSENT` on the BOX side against `CONFIRMED_PRESENT` on the GBO side; that pairing *is* the
work. If any gate or check makes a missing BOX row look like an obstacle, it is misreading the job —
say so rather than blocking.

## Run inputs

| Input | Value |
|---|---|
| `BRANCH_CODE` | `NY_SCH` |
| `BRANCH_PK` | **Do not assume.** Resolve via Q-G1. (Tier 1 static data showed `20007.4`; that is a Tier 1 observation, not your Tier 2 input) |
| `TARGET_ENV` | Tier 2 **PRE** |
| `GBO_SOURCE` | GBO **Tier 2** — NY_SCH is live there. A Tier 1 read tells you nothing about this branch's live configuration. Still required: the MIS config and Fixing Curve are mined from GBO |
| `PRODUCT_BOOK_SCOPE` | **Not yet supplied — blocking, but now cheap to put to the SME.** Which instruments NY_SCH gets, chosen from **what is already created and live in BOX** — all, or a named subset — from a named SME in writing. Do **not** derive it from NY_SCH's GBO instrument configuration. **Run Q-05c against SLB first**: a branch's instrument set is its MIS configuration's **Accrual tab**, `BOX_FE.T_BOX_ENGACCRCONF_S`, one row per instrument. SLB in Tier 1 has **nine** on the SIGOM screen (OTC Option, Cross Currency Swap, Swap, Cash Flow Matching, Deposit & Loan, Credit Derivatives, Forward Rate Agreement, Caps And Floors, Bond Return Swap) — but only **seven** resolve to a Sub-Product row, so use Q-05c's `LEFT JOIN` form and the unjoined `COUNT(*)`; an inner join silently drops Credit Derivatives and Bond Return Swap. Put that list to the SME — *"these nine, or which subset?"* — instead of asking them to enumerate from memory. Confirming the **set** never authorises copying SLB's accrual **values** |
| `DB_ACCESS_MODE` | Ask at the start. If you don't have a read-only Tier 2 connection, run `assisted` |
| `RUN_FOLDER` | `runs/NY_SCH/tier2-pre/` |
| `REFERENCE_ENV` | Tier 1 (for the gate 0e schema diff) |

## ⚠️ Scope correction, 2026-09-16 — narrow, but it unblocks you

`[stated: BOX Developer via Edouard, 2026-09-16]`

**One thing changes:** do not look up which *instruments* are configured for NY_SCH in GBO. Instrument
scope is chosen from **what is already created and live in BOX**, by a named SME. Everything else
stands — the MIS configuration and Fixing Curve are still mined from their GBO equivalents exactly as
the charter describes.

**What this means for your blocked gate 0b.** Q-G2 is **narrowed to level 1, not withdrawn**. Level 1
is what resolves `FK_MISCONFIG` to the GBO MIS header, and you already ran it successfully:
`bc.PK = 141.35`, `FK_MISCONFIG = 64408.35` → "Configuracion -NY". **That satisfies the gate.** The two
lower levels you blocked on (`T_PGT_BRANCH_INST_S`, `T_PGT_BRANCH_INS_CONFIG_S`) are the
*branch-instrument* tree, and they are no longer in scope.

They were also broken, which is worth knowing so you don't revisit it: those levels return nothing for
**Madrid** either (`bc.PK = 4.21`, absent from every populated `FK_PARENT` value), so the join was
wrong rather than the data missing. Your empty result was not a finding about NY_SCH. Don't spend
further effort on it — record it and move on.

**Proceed to Q-G4**, then the walk. Q-G3 is resolved (see below).

## 🔁 Active mode, revised 2026-09-18 — deferred-verification run against the REAL target

`[stated: Edouard, 2026-09-18]` **This supersedes the split-tier rehearsal, which is withdrawn.** You are
no longer writing to Tier 1 PRE. You run against **Tier 2 PRE — the real target** — and defer the one
thing access blocks.

| Input | Value |
|---|---|
| `GBO_SOURCE` | **GBO Tier 2** — unchanged |
| `TARGET_ENV` | **Tier 2 PRE** — the real target, unchanged from the run inputs above |
| `RUN_FOLDER` | **`runs/NY_SCH/tier2-pre/`** — the real run folder. These are the real run's artifacts |
| Gate 0f | **Not applicable.** Source and target are the same environment; there is no cross-environment question |

**What you can read:** GBO Tier 2 (`DEVENG`, `PGT_*`) — everything the walk mines.
**What you cannot read:** `BOX_FE` in Tier 2, pending an account with grants.

### The working assumption, stated and not confirmed

**`BOX_FE` in Tier 2 PRE has the same tables and columns as `BOX_FE` in Tier 1 PRE.** Record this in
`00-inputs.md` as an assumption. It has a validated reference: the 2026-09-18 Tier 1 run confirmed all
15 walk tables plus `V_BOX_PROC_INSTR_S` present, 80 `BOX_FE` objects visible. Use Tier 1's `BOX_FE`
**structure** — column names, types — wherever you need to know the shape of a target table.

**Tier 1 structure, never Tier 1 values.** Reading Tier 1's column list is fine. Reading a Tier 1 *row*
and carrying it into NY's configuration is hard rule 6.

### What is deferred, precisely

Procedure step **C2** — *"does a row already exist on the BOX side?"* — for every walk step, plus
**gate 0e**. Nothing else. Mining, walk order, dependency graph, value derivation and SQL generation all
run normally and completely.

**Every BOX-side finding is `EVIDENCE_REQUIRED` until its read happens.** Do not write
`CONFIRMED_ABSENT` on an assumption, however near-certain. NY_SCH almost certainly has no `BOX_FE` rows
— that is the precondition for the job — but near-certain is not confirmed, and this repo does not let
those collapse.

**The SQL you generate is a marked draft, not executable.** Head every file: *Draft — generated before
BOX-side verification. Do not execute until gate 0e and the deferred C2 reads pass.* If a row does
already exist (a partially configured branch, or a shared configuration NY should reuse rather than
recreate), an `INSERT` would be wrong.

**Gate 0e is the single release gate.** When `BOX_FE` access lands: run Q-G4 against Tier 2, run the
deferred C2 reads, update the statuses. The draft becomes executable **without regeneration** — that is
the point of running against the real target.

### Why this is better than what you were doing

The split-tier rehearsal substituted Tier 1 as the destination, which made every mined FK a portability
question and produced SQL that was never executable anywhere. Here every FK is native, gate 0f
disappears, **the `PGT_MRK` quote-reference blocker disappears** — all 38 of NY's references live in Tier
2's `PGT_MRK`, shared with BOX Tier 2 — and **step 4 becomes fully rehearsable**. Nothing is written into
a shared pre-production environment. The output is the real deliverable, one verification pass from
running.

### Gate 0d — resolved, emit the real call

`[confirmed: source via BOX FE Developer, 2026-09-17]` PKs come from `F___SEQUENCE(TABLE_NAME,
seq_range)`: `NEXTVAL` from **`SQ_BOX_FINANENG1`** for every walk table, plus — with `seq_range = 'X'` —
the environment's auth code as a fraction, read from `gom_glb_sys.t__CORE_INFO_S`.

```sql
DECLARE
  v_pk_engconf NUMBER;
BEGIN
  v_pk_engconf := F___SEQUENCE('T_BOX_ENGCONF_S','X');
  INSERT INTO BOX_FE.T_BOX_ENGCONF_S (PK, …) VALUES (v_pk_engconf, …);
  -- children reference v_pk_engconf, never a literal
END;
```

Never a literal PK, never a bare `SQ_BOX_FINANENG1.NEXTVAL` (it drops the auth-code fraction), never a
PK copied from a live row. **A property that matters here:** the auth code is read from the target at
execution time, so the draft you generate now carries no environment-specific PK values at all — another
reason it needs no regeneration when access lands.

`F___SEQUENCE` reachability is a **Tier 2** question and is part of the deferred set: confirm it with
Q-G3b when `BOX_FE` access arrives. The Tier 1 run already showed seven grantees, so the function exists
and is grantable; the Tier 2 grant is what remains.

### ⛔ Draft review, 2026-09-18 — the first full draft was rejected. Read this before regenerating.

You produced `NY_SCH-tier2-pre-draft.sql` end to end. The PK mechanism worked perfectly — every PK a
`F___SEQUENCE(<table>,'X')` call on a declared variable, children referencing their parents, draft
header present, `ROLLBACK` at the end. Keep all of that. Five things must change.

**1. `FK_OWNER_OBJ` and `FK_EXTENSION` are never mined from GBO.** They are constants of the **target
table**. Every `DEVENG.T_PGT_ENGCONF_S` row carries `FK_OWNER_OBJ = 12198.4` — the GBO Financial Engine
module. Every `BOX_FE.T_BOX_ENGCONF_S` row carries `35000126.65` — the BOX one. Your
`INSERT … SELECT … FROM DEVENG.T_PGT_ENGCONF_S` copied the GBO value into a BOX row.

Read them with **Q-G6** against the target and bind them. In this deferred run that is a `BOX_FE` read,
so emit them as unresolved substitution variables (`&&OWNER_OBJ`, `&&EXT_ENGCONF_X`, …) and add Q-G6 to
the release procedure. **Do not hard-code `35000126.65`** — it is a Tier 1 observation.

**No `INSERT … SELECT <most columns> FROM DEVENG.…` anywhere.** Write an explicit column list, and be
able to say for each column whether it is **mined** (GBO), **allocated** (`F___SEQUENCE`) or
**structural** (the target). Charter hard rule 9.

**2. Q-07 needs a `FK_PARENT` filter.** Your fixing-exceptions query had none and you substituted a
`MIN(PK)` subquery. That returns an arbitrary row, not NY's. The filter is `WHERE FK_PARENT = 64408.35`
— the same MIS-header predicate steps 6, 8, 9 and 10 use. This is the second time a catalogue query
missing its predicate was filled in rather than reported; report it next time.

**3. Step 5 is not blocked.** You blocked `T_BOX_ENGCONF_X` as "requires BOX-specific `FK_OWNER_OBJ` and
`FK_EXTENSION` values not present in the supplied GBO evidence." Correct observation, wrong conclusion —
those values were never supposed to come from GBO, and you were silently copying them in the steps you
*didn't* block. All four values are resolved: `FK_PARENT` = the step-2 header variable, `FK_BS` =
`&&BRANCH_PK`, the other two from Q-G6 (`35000126.65` / `35001566.65` in Tier 1). See **Q-01c**.

This is the row that ties the configuration to the branch. Without it, steps 2–4 and 6–12 build a
configuration that belongs to nobody. Treat a step-5 block as run-stopping, not as a line item.

**4. Q-06 is not blocked either.** "Accrual-exception `FK_BRANCH` semantics are not resolved for BOX"
conflates *can't mine* with *needs sign-off*. `WHERE FK_PARENT = 64408.35` mines it fine; `FK_BRANCH`
resolves into `PGT_STC` (shared), and the GBO evidence on `T_PGT_ERRORS_FE_S` points to geographic
branches. Mine it, propose the rows, status `EVIDENCE_REQUIRED` with the product-shaped-branch question
attached. A blocker with no rows behind it gives the reviewer nothing to disagree with.

**5. Attribution.** The six instruments (`20213.4, 20.4, 2.4, 20314.4, 20111.4, 20092.4`) and the
`LIMIT_ERRORS` values (115 for CCS, 100 for the rest) are recorded as confirmed / "User decision"
without a name or a date. **Gate 0c is still open.** Either cite the SME and the date, or status these
`SME_DECISION_REQUIRED` — near-certain and confirmed do not collapse, here either.

**Blocks 8, 9, 11 and 12 were right.** Steps 9/10 parked by the developer, step 13 derived, step 14 not
branch-scoped. Keep them.

## Also run Q-G5 — it costs one query and closes an open question

`PGT_SYS.T_PGT_SOURCE_S.SIGOMID` maps auth-code suffixes to named environments (`4` = global, `21` =
Tier 1 Madrid). `PGT_SYS` is shared, so run it anywhere, with no `BOX_FE` access. It should identify
`.44` — sighted twice and never explained — and confirm `.65` = BOX-DEV and `.35` = NY Tier 2, both of
which this repo currently asserts on circumstantial evidence. `SELECT *`; do not filter a discovery
query by the answers you expect.

## The quote-reference blocker is gone

`[confirmed: DB via Edouard]` The 38 quote references behind NY's curve — 35 of them `.35`, allocated in
Tier 2 — were absent from Tier 1 PRE, which blocked step 4 under the old rehearsal shape. Running against
**Tier 2** removes the problem entirely: `PGT_MRK` is shared between BOX and GBO within an environment,
so all 38 are natively available. **Step 4 is fully in scope now.** Nothing about it is deferred beyond
its BOX-side C2 read, like every other step.

## What makes this run different from the design's happy path

Four things are already known to be true and will shape the whole run. Don't rediscover them, and
don't work around them:

**~~Tier 2 PRE is missing a substantial number of `BOX_FE` tables.~~ Withdrawn 2026-09-16 — that was a
permissions artifact.** `[confirmed: DB, 2026-09-16]` The Tier 2 account used had **no grants on the
`BOX_FE` schema**. An Oracle session without privileges does not see missing tables, it sees no rows in
`ALL_TABLES` — identical to absence. Nothing is known about Tier 2 PRE's schema completeness either
way. **Do not produce the provisioning artifact, do not diff schemas, and drop the "was `BOX_FE` ever
deployed to Tier 2 at all" investigation entirely** — it was a false alarm and it is not a
project-resizing prerequisite. Gate 0e for Tier 2 is `EVIDENCE_REQUIRED — blocked on access, not on
schema`, and stays there until an account with `BOX_FE` grants exists. **In this deferred-verification
run that is expected, not blocking:** generate the draft, mark it not executable, and treat gate 0e as
the release gate.

**Run the visibility preflight before interpreting any result, in every environment.** This is now
mandatory (see the Q-G4 *Preflight* section of the query catalogue):

```sql
SELECT USER                                                     AS CONNECTED_AS,
       SYS_CONTEXT('USERENV','DB_NAME')                         AS DB_NAME,
       (SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER = 'BOX_FE') AS BOXFE_VISIBLE,
       (SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER = 'DEVENG') AS DEVENG_VISIBLE
FROM   dual;
```

A zero means you are blind to that schema, not that it is empty. Attach the result to the run folder;
a CSV whose preflight was not run is not evidence. This is the **second** absence-by-broken-access-path
in this project — Q-G2's join was the first — which is why it is now a hard rule rather than advice.

**✅ The PK generation mechanism is now known — gate 0d is closed.** `[confirmed: source via BOX FE
Developer, 2026-09-17]` PKs come from the function `F___SEQUENCE(TABLE_NAME, seq_range)`: `NEXTVAL`
from **`SQ_BOX_FINANENG1`** for every table in this walk, plus — with `seq_range = 'X'` — the
environment's auth code as a fractional part (`auth_code / 10^length(auth_code)`, read from
`gom_glb_sys.t__CORE_INFO_S`). That is why every PK looks like `20007.4`, `141.35`, `24.095.416,21`.

**So call the function; never compute a PK.** Assign it to a declared variable so children can
reference their parent:

```sql
DECLARE
  v_pk_engconf NUMBER;
BEGIN
  v_pk_engconf := F___SEQUENCE('T_BOX_ENGCONF_S','X');
  INSERT INTO BOX_FE.T_BOX_ENGCONF_S (PK, …) VALUES (v_pk_engconf, …);
  -- children reference v_pk_engconf, never a literal
END;
```

A literal PK is still a hard failure, and so is calling `SQ_BOX_FINANENG1.NEXTVAL` directly — that
would drop the auth-code fraction. **Your rehearsal `&PK_nn_*` placeholders map one-to-one onto these
declared variables**, so nothing you have already produced is wasted: convert, don't regenerate.

**One bonus worth knowing:** because the auth code is read from the *target* environment at execution
time, the same script produces correctly-suffixed PKs in Tier 1 and Tier 2 without edit.

**This repo's entire FE evidence base is Tier 1.** Nearly every `[confirmed: DB]` tag in
`docs/reference/branch-config/` means confirmed in Madrid/London. You are producing the first Tier 2
evidence this repo has ever had. When a Tier 2 fact contradicts a Tier-1-evidenced claim, that is the
most valuable thing you will produce — draft the correction against the specific doc and flag it
prominently. Propose it; never rewrite a `[confirmed]` claim on your own authority.

**Step 11 (Book, `T_BOX_CONF_BY_BOOK_S`) has no GBO row to mine — confirmed, not an open question.**
A BOX FE Developer confirmed this is new BOX-only functionality: a row here for `(branch,
instrument)` is what registers that combination for the FE batch to actually execute. Treat this
step differently from every other step in the walk: don't ask for a GBO-side query (Q-10 has none),
and don't let a missing GBO twin read as an evidence gap to chase. But "no GBO row" is not "no
evidence" — run Q-10's canonical join (branch × Sub-Product instrument × `PGT_DOMAINS` book label;
same developer: "the books are the books that we have in the Data Lake (Lago)") to see the current
BOX-side fact, get the branch's Data-Lake/Murex book enumeration (the same one
`control-m-batch-layer.md` needs for the batch build — don't gather it twice), then go to the named
SME for which of those books need FE batch registration specifically. Use Madrid/London's existing
Book rows only as structural reference for shape, never as values. See `fe-branch-configuration.md`'s
"Book — batch execution registration" and "The confirmed join" sections before starting this step.

**A challenge to the branch-keyed model itself — check this early.** BOX-DEV screenshots show the
Accrual Exceptions and Allowed Errors `Branch` column holding **product-shaped values** (`BOX CCS`,
`BOX FX`, `BOX IRS`, …) rather than geographic branches. This repo's FE model, and this walk, assume
FE config keys to a geographic branch. Before trusting the walk's shape, run a plain
`SELECT * FROM PGT_STC.T_PGT_BRANCH_S` in the environment you're reading and look at what is actually
in it. If product-shaped branches are real rather than a dev-environment convention, say so and stop —
that changes the walk, and it is far cheaper to discover now than at step 6. See
`docs/reference/branch-config/fe-branch-configuration.md` §2.

## Non-negotiables

- **Gates first, in order.** Q-G1 → Q-G2 *(level 1 only)* → Q-G3 → Q-G4 → Q-G5 → Q-G6 *(Q-G6 deferred
  with the rest of the `BOX_FE` reads)*. Nothing in the walk is valid until they pass,
  and two of them are expected to fail. A blocked run honestly reported is the correct outcome, not a
  failure to work around.
- **Never invent a value, a PK, or DDL.** The four permitted sources are read / SME-given / documented
  constant / explicitly-labelled `DERIVED`. Derived values carry their rule in the annotation, are
  tagged `DERIVED` and never `CONFIRMED`, and need their own sign-off.
- **Never copy from Madrid or London because the shape matches.** Those two share calendar, currency
  and both source systems yet use different fixing curves. NY is USD/New York — a different currency
  and calendar than either. Shape similarity is a proposal aid, never authorisation.
- **A zero-row result is not automatically an absence.** Four catalogue queries rest on an assumed
  join column (see the catalogue's Coverage check). Verify the join before recording
  `CONFIRMED_ABSENT`.
- **Write nothing.** Not to GBO, not to BOX. Your output is files in `runs/NY_SCH/tier2-pre/`. A human
  runs the SQL.
- **Stop at the findings table** for sign-off before generating any SQL.

## Working in `assisted` mode

Likely the mode you're in. For each query you need: state the query ID, its purpose, **which database
to run it in**, the parameter values already resolved, the SQL ready to paste, the exact output path
(`runs/NY_SCH/tier2-pre/01-evidence/Q-05-accrual-gbo.csv`) and the expected row count. Then stop and
wait.

Ask in **dependency batches**, not all at once — Q-G1's result parameterises everything else, and
Q-G3/Q-G4 can end the run. Don't spend someone's afternoon on twenty queries a gate failure makes
irrelevant. When a CSV arrives, check it matches the expected shape before using it; a mismatch is a
re-run request, not data to interpret creatively.

## Reporting

Keep `runs/NY_SCH/tier2-pre/README.md` current as the run log — which stage you're in, which queries
are outstanding, what's blocked and on whom. Report after each stage, not only at the end.

Where a finding belongs in the repo's permanent record rather than the run folder — a corrected table
name, a resolved open question, a newly confirmed join — draft it against the specific doc and flag
it. That capture is part of the job, not a write-up afterwards.

## Scope boundary

BOX FE only. Not BOX ACC (portfolio properties, topics, GL accounts — a separate agent), not
Control-M or Data-Lake jobs, not the test run, not code or schema deployment. If your work leads into
any of those, stop and hand back rather than continuing into them.
