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
| `GBO_SOURCE` | GBO **Tier 2** — NY_SCH is live there. A Tier 1 read tells you nothing about this branch's live configuration |
| `PRODUCT_BOOK_SCOPE` | **Not yet supplied — blocking.** Get it from a named SME in writing before steps 6–11. Do not infer it from Madrid's or London's scope |
| `DB_ACCESS_MODE` | Ask at the start. If you don't have a read-only Tier 2 connection, run `assisted` |
| `RUN_FOLDER` | `runs/NY_SCH/tier2-pre/` |
| `REFERENCE_ENV` | Tier 1 (for the gate 0e schema diff) |

## What makes this run different from the design's happy path

Four things are already known to be true and will shape the whole run. Don't rediscover them, and
don't work around them:

**Tier 2 PRE is missing a substantial number of `BOX_FE` tables.** Gate 0e will fail. When it does,
produce the provisioning artifact — schema diff from Q-G4, then each missing object's authoritative
DDL **located and cited from `cib-boxfin-dbboxfe`, never written by you** — and block. Before treating
it as an incomplete environment, establish whether `BOX_FE` was ever deployed to Tier 2 at all: the
corpus says NY is live in GBO Tier 2, *not* in BOX. If it's an undeployed module rather than a
half-provisioned schema, that's a much larger prerequisite and it belongs to the orchestrator's Phase
0, not to you. Answer that question early; it changes the size of the project.

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

## Non-negotiables

- **Gates first, in order.** Q-G1 → Q-G2 → Q-G3 → Q-G4. Nothing in the walk is valid until they pass,
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
