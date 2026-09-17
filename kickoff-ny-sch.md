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

## 🔁 Active mode, revised 2026-09-18 — split-tier: mine GBO Tier 2, write BOX Tier 1 PRE

`[stated: Edouard, 2026-09-18]` **Access is asymmetric, and the run is shaped around that:**

| Environment | What we have |
|---|---|
| **Tier 2 PRE** | GBO access only (`DEVENG`, `PGT_*`). **No `BOX_FE`.** This is where NY_SCH is actually live |
| **Tier 1 PRE** | Full access **including `BOX_FE`**. NY_SCH is not configured here |

So this run **mines Tier 2 and writes Tier 1**. Read the charter's *Split-tier runs* section and
*Gate 0f* before starting.

| Override | Value |
|---|---|
| `GBO_SOURCE` | **GBO Tier 2 — unchanged from the real run.** NY_SCH's real configuration lives there and nowhere else |
| `TARGET_ENV` | **Tier 1 PRE**, for this run only. Tier 2 PRE remains the real target |
| `RUN_FOLDER` | `runs/NY_SCH/tier1-pre-rehearsal/` — **not** the Tier 2 folder |
| Gate 0e | Evaluated **against Tier 1 PRE**, where `BOX_FE` access exists. It can pass there normally |
| Gate 0d | ✅ **RESOLVED 2026-09-17** — `F___SEQUENCE(<table>,'X')`. Emit real function calls |
| **Gate 0f** | ✅ **PASSING, and demoted to a spot check** — `PGT_STC` and `PGT_SYS` are shared and identical in every environment, so only `PGT_MRK` quote references need checking. See below |

**Correcting an earlier instruction.** A previous version of this section told you to set
`GBO_SOURCE = Tier 1`. That was wrong and is withdrawn: NY_SCH is live in GBO **Tier 2**, so a Tier 1
GBO read yields either nothing or another branch's configuration. Mining the wrong tier produces a
worthless findings table however well-formed the SQL is. **Mine where the branch is real; substitute
only the target.**

**What this buys you.** Every mined value is NY_SCH's *actual* configuration — the real MIS header, the
real Fixing Curve. Only the destination is a stand-in. So the findings table this run produces is the
one that goes to the SME for the real run, not a throwaway.

**Gate 0f, correctly sized.** `[stated: Edouard, 2026-09-18]` `PGT_STC` and `PGT_SYS` hold **identical
rows in every environment**, so calendars, currencies, the branch master, Sub-Product instruments and
`PGT_DOMAINS` values are the same in Tier 1 and Tier 2 by design. They need no cross-environment check —
which is why your first Q-14 run matched exactly. The only reference values worth comparing are
`PGT_MRK` quote references; see below.

**One working assumption remains, stated and unconfirmed:** that `BOX_FE` table structures are identical
across tiers and differ only in content. Record it as an assumption; it stays untested until someone
with Tier 2 `BOX_FE` grants runs the Q-G4 diff. (The second assumption — that `.4` reference data is
genuinely replicated — is **answered**: those are shared schemas.)

**Gate 0d — ✅ resolved, and your finding was correct.** Ten PK columns with empty `DATA_DEFAULT`, no
triggers, seven sequences unmapped: that was right, and it pointed exactly where it should have —
allocation lives in a **function**, not the dictionary. A BOX FE Developer supplied it on 2026-09-17:
`F___SEQUENCE(TABLE_NAME, seq_range)` takes `NEXTVAL` from **`SQ_BOX_FINANENG1`** (that is the one of
the seven that matters for this walk) and, with `seq_range = 'X'`, adds the environment's auth code as
a fraction — which is why PKs look like `20007.4` and `24.095.416,21`.

**Stop emitting symbolic placeholders and emit the real call.** Your `&PK_nn_*` variables map
one-to-one onto declared PL/SQL variables, so convert rather than regenerate:

```sql
DECLARE
  v_pk_engconf NUMBER;
BEGIN
  v_pk_engconf := F___SEQUENCE('T_BOX_ENGCONF_S','X');
  INSERT INTO BOX_FE.T_BOX_ENGCONF_S (PK, …) VALUES (v_pk_engconf, …);
END;
```

Never a literal, never `SQ_BOX_FINANENG1.NEXTVAL` on its own (it would drop the auth-code fraction),
never a PK copied from a live row. The file is now genuinely runnable once its values are signed off.

**One thing still worth checking while you have Tier 1 access:** confirm `F___SEQUENCE` exists and is
valid in whichever environment you target (`SELECT object_name, status FROM all_objects WHERE
object_name = 'F___SEQUENCE'`), and note which schema owns it, since your INSERT script has to
reference it correctly. Also record `SELECT auth_code FROM gom_glb_sys.t__CORE_INFO_S` per environment
— not to use in a PK, but so a reviewer can tell at a glance which environment a row was allocated in.

**Why the SLB `InternalID` values look the way they do — now fully explained.** `24.095.416,21`,
`44.552,21`, `31.874.132,21` and the rest are `SQ_BOX_FINANENG1.NEXTVAL + 0.21`. The shared sequence is
why integer parts are large, scattered and non-contiguous within one table; the constant `.21` is the
Tier 1 environment's auth code, not an ownership marker. Nothing here needs testing any more.

## ✅ Gate 0f — you are NOT blocked. Read this before re-running.

`[confirmed: DB via Edouard, 2026-09-18]` The 2026-09-18 run reported gate 0f blocked because GBO
Tier 2's fixing curve `PK = 1.35` has no row at `PK = 1.35` in BOX Tier 1 PRE. **That is not a gate 0f
failure, and the gate's wording was at fault — it has been corrected.**

**Why.** `1.35` is the **source object's own PK** — the identity of the GBO row you are *reading*. It
is not an FK your `INSERT` will carry. The BOX curve does not exist yet; creating it is step 3's whole
purpose, and its PK will come from `F___SEQUENCE`. **A source PK is expected to be absent from the
target.** If it were present, the branch would already be configured.

Gate 0f checks **reference FKs only** — pre-existing shared objects the new rows point at:

| Kind | Gate 0f? |
|---|---|
| Reference FK (`FK_CALENDAR`, `FK_CURRENCY`, `FK_INSTRUMENT`, branch `FK_BS`, domain values, quote references) | ✅ Yes |
| Source-object PK (the GBO curve's `PK`, the GBO MIS header's `PK`) | ❌ No — absence expected |
| FK pointing at something this walk creates | ❌ No — resolved at apply time |

**Your own Q-14 output shows the gate PASSING:** calendars, currencies, branches and all sixteen
Sub-Product descriptions matched exactly across GBO Tier 2 and BOX Tier 1 PRE. That is the result the
gate wanted.

**What to do instead.** Step 3 (Fixing Curve header) is `CONFIRMED_ABSENT` in the target → **propose
creating it**, from GBO's `1.35` row: description *"NY Configuration Suc"*, `FK_CURRENCY = 159.4`, and
the rest of its attributes. Check that `159.4` resolves in Tier 1 — per your Q-14 result, currencies
match — and proceed. **Your refusal to substitute SLB's or Madrid's curve was exactly right and stands:**
both are `FK_CURRENCY = 160.4` against NY's `159.4`, so they are not merely different PKs, they are a
different currency. Hard rule 6 unchanged; never copy them.

**Stop asking for `PGT_SYS` / `PGT_STC` comparisons.** `[stated: Edouard, 2026-09-18]` Those two schemas
hold **identical rows in every environment**. Calendars, currencies, the branch master, Sub-Product
instruments and all `PGT_DOMAINS` values are therefore the same in Tier 1 and Tier 2 by design — which
is why your Q-14 run matched *exactly*. Do not request those comparisons again; a run must never be
blocked on one, and an apparent divergence there is a platform escalation, not a walk finding.

**The one reference check that still earns its keep:** the **quote references** behind the curve
(step 4, via `T_PGT_ENGLKFC_X.FK_BS` → `PGT_MRK.T_PGT_QUOTE_REFERENCE_S`). `PGT_MRK` is shared between
BOX and GBO *within* an environment; whether it is replicated *across* environments is unrecorded. If
NY's quote references are absent in Tier 1 PRE, **that** is a real finding — unlike the curve PK, and
unlike anything in `PGT_STC`/`PGT_SYS`. Run it once and record the answer in
[`docs/reference/confirmed-joins.md`](../../../docs/reference/confirmed-joins.md).

## Two other corrections from the 2026-09-18 run

**Branch lookup — `SLB` and `ESP` are not branch codes.** They are abbreviations inside *configuration
descriptions*. The `PGT_STC.T_PGT_BRANCH_S.CODE` values are **`MADRID`** (`PK 22.21`) and **`LND
BRANCH`** (`PK 20087.4`). The column is confirmed to be `CODE`, with `DESCRIPTION` alongside it.

**Step 12 has a GBO source after all.** `DEVENG.T_PGT_ERRORS_FE_S`, keyed by `FK_BRANCH` — so
`WHERE FK_BRANCH = 20007.4` for NY_SCH. Allowed Errors is an **ordinary mine-and-propose step**, not a
BOX-only one like step 11: mine NY's own error limits rather than taking them from a reference branch.

**Before writing any further join, read
[`docs/reference/confirmed-joins.md`](../../../docs/reference/confirmed-joins.md).** Three of the four
query defects so far asserted a relationship this repo had already confirmed somewhere else.

**Two traps in this mode.**

**You are writing into a shared pre-production environment.** NY_SCH does not exist in Tier 1 PRE and
this run creates it there. That is a real configuration other people's testing could notice. Get an
owner's OK before applying anything, keep the rollback `DELETE`s with each statement as the charter
requires, and label the configuration so nobody mistakes it for a real Tier 1 onboarding.

**Cross-tier values need re-checking, not re-using blindly.** Head every output file with: *Rehearsal —
mined from GBO Tier 2, written to BOX Tier 1 PRE. Values are NY_SCH's real GBO configuration; FK
resolution is verified per gate 0f and holds for Tier 1 only.* When Tier 2 `BOX_FE` access lands,
**re-run gate 0f against Tier 2** and regenerate — the findings carry over, the FK verification does
not.

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
schema`, and stays there until an account with `BOX_FE` grants exists.

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

- **Gates first, in order.** Q-G1 → Q-G2 *(level 1 only)* → Q-G3 → Q-G4. Nothing in the walk is valid until they pass,
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
