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

## Run inputs

| Input | Value |
|---|---|
| `BRANCH_CODE` | `NY_SCH` |
| `BRANCH_PK` | **Do not assume.** Resolve via Q-G1. (Tier 1 static data showed `20007.4`; that is a Tier 1 observation, not your Tier 2 input) |
| `TARGET_ENV` | Tier 2 **PRE** |
| `GBO_SOURCE` | GBO **Tier 2** — NY_SCH is live there. A Tier 1 read tells you nothing about this branch's live configuration. Still required: the MIS config and Fixing Curve are mined from GBO |
| `PRODUCT_BOOK_SCOPE` | **Not yet supplied — blocking.** Which instruments NY_SCH gets, chosen from **what is already created and live in BOX** — all, or a named subset — from a named SME in writing. The working hypothesis is "the same set as SLB"; confirm it, never assume it. Do **not** derive it from NY_SCH's GBO instrument configuration |
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

**Proceed to Q-G3 and Q-G4.** Those are the real remaining blockers.

## 🔁 Active mode, 2026-09-16 — Tier 1 rehearsal, symbolic PKs

`[stated: Edouard, 2026-09-16]` Tier 2 `BOX_FE` access does not exist yet. Rather than sit blocked,
this run switches to a **Tier 1 rehearsal** whose purpose is to prove the walk emits correct, ordered,
well-formed SQL. Read the charter's *Rehearsal mode* section before starting.

| Override | Value |
|---|---|
| `RUN_FOLDER` | `runs/NY_SCH/tier1-rehearsal/` — **not** the Tier 2 folder |
| `TARGET_ENV` | Tier 1, for this run only. Tier 2 PRE remains the real target |
| Gate 0e | Evaluated **against Tier 1**, where access exists. It can pass there normally |
| Gate 0d | **Unresolved — proceed in symbolic-PK mode.** See below |

**The working assumption, stated and not confirmed:** `BOX_FE` table structures are identical between
Tier 1 and Tier 2 and differ only in content. That is what makes a Tier 1 rehearsal meaningful. It is
an assumption, not a finding — record it as one, and it stays untested until someone with Tier 2
grants runs the Q-G4 diff.

**Gate 0d — your finding stands, and does not block you.** Ten PK columns with empty `DATA_DEFAULT`,
no triggers, seven sequences with no mapping to the walk tables: record that as the result of Q-G3.
Then emit every PK as a named substitution variable (`&PK_02_ENGCONF`, `&PK_03_CURVE`, …) with an
undefined `DEFINE` block at the top of each SQL file, children referencing their parent's variable by
the same name. Never a literal, never an unmapped sequence, never a PK copied from a live row. The
file is deliberately not runnable until a human binds the DEFINEs — say so in its header.

**Finish the 0d diagnostic while you have Tier 1 access** — it is cheap here and impossible in Tier 2
right now. Pull `ALL_SEQUENCES` for `BOX_FE` (`sequence_name`, `last_number`, `increment_by`), then
`MAX(<pk>)` and `TRUNC(MAX(<pk>))` for each of the ten walk tables, then `data_precision`/`data_scale`
for each PK column from `ALL_TAB_COLUMNS`. One question to answer: **does any sequence's `LAST_NUMBER`
track the integer part of any table's `MAX(PK)`?** Every observed PK in this system has the form
`<integer>.<authcode>` — `141.35`, `20007.4`, `4.21`, `64408.35` — and a bare sequence cannot produce
that suffix. If `DATA_SCALE` is 2 and a sequence tracks the integer part, the mechanism is *sequence
for the integer, application or import tooling for the auth-code suffix*, which resolves 0d and
establishes that the suffix is a stated rule or an SME input, never yours to choose.

**The trap in this mode.** Every value in the rehearsal SQL is a Tier 1 value — Tier 1 calendar and
currency FKs, NY_SCH's *Tier 1* branch PK `20007.4` rather than whatever Tier 2 holds. A rehearsal
produces a validated **shape**, never a draft to promote. Head every output file with: *Tier 1
rehearsal — structure validated; values are Tier 1 and must not be carried to Tier 2.* When Tier 2
access lands, regenerate; do not edit this run's files into Tier 2 ones.

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

**The PK generation mechanism is unknown.** Gate 0d. Run Q-G3 early. If it comes back empty — no
sequence, no trigger, no column default — that is a *significant finding*, not an inconclusive one:
it points at SIGOM-side allocation in application code, which would mean a raw `INSERT` is not a safe
way to create these rows at all. Report that rather than proceeding.

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
