# BOX FE run modes

**Reference, not a prompt.** Run shapes for
[`sigom-box-fe-configs-agent`](../../agents/sigom-box-fe-configs-agent/AGENT.md), read when a run uses
one. A normal run against a readable target uses none of them.

Moved out of the charter 2026-09-22: a mode nobody is using is weight on every run that isn't.

---

### Dry-run mode — the agent explains the walk instead of executing it `[added 2026-09-21]`

**Purpose: let a BOX FE expert review the agent's *reasoning* without anyone running a query.**
`RUN_MODE = dry-run` produces the complete plan — every query stated, every decision made explicit with
its rule and its source — and runs nothing.

It exists because the thing an expert can usefully check is the **plan**, not the data. Asking them to
sit through forty queries wastes the one resource that is genuinely scarce. Worked prompt:
[`../../agents/sigom-box-fe-configs-agent/prompts/dryrun-ny-sch.md`](../../agents/sigom-box-fe-configs-agent/prompts/dryrun-ny-sch.md).

| | Normal run | Dry-run |
|---|---|---|
| Queries | run, or handed over and awaited | **stated, never run, never awaited** |
| Findings | statused from evidence | every row `EVIDENCE_REQUIRED`, with *what the query would decide* |
| SQL | generated for signed-off rows | **generated as an illustrative skeleton, marked `DRY-RUN — NOT EXECUTABLE`** |
| Gates | must pass | evaluated on paper; a failing gate is described, not blocking |
| Duration | days | one sitting |

**The deliverable is organised by decision, not by query** — a query log is unreviewable by someone who
doesn't know the catalogue. Per walk step, in this order: (1) **what it will insert** — target table,
expected row count, why that count; (2) **where each value comes from** — **mined** (name the GBO row),
**allocated** (`F___SEQUENCE`), **structural** (from the target object) or **`DERIVED`** (the rule *and*
its source); (3) **what it is uncertain about**, in the reviewer's language; (4) **what it needs from
the reviewer** — a specific question, or "nothing".

**Extra obligations, because nothing downstream will catch a mistake here.** Every claim carries its
evidence tag — a dry-run is the one output with no CSV behind it, so an unsourced assertion is
indistinguishable from a guess. State what **cannot be verified at all** prominently rather than in a
footnote: book scope has no completeness check, and gate 0c's four accrual values are an SME decision.
**Never present a gate as passing because the plan is sound** — gate 0c is unsigned, and saying so is
the point of the exercise. Answer in the reviewer's terms: they will ask *what happens if we get this
wrong*, so have the consequence ready (a missing step-12 row means the first failed deal aborts the
load; a missing step-11 row means that work is never scheduled).

Writes to `RUN_FOLDER/` as normal, so the dry-run and its eventual real run sit side by side and can be
diffed. `scripts/validate_run_output.py` still applies — the skeleton SQL must pass the mechanical
checks even though it will never execute.

**A dry-run is a review, not a test.** It catches what the reviewer notices on the day and nothing
afterwards. The repeatable check is fixtures plus the validator; run both.

### Deferred-verification runs — the preferred shape when the target is read-blocked

**When you can read the source but not yet the target, run against the *real* target anyway and defer
the target-side reads.** Do not substitute a different environment.

This is the better of the two answers to missing target access, and the reason the other one —
substituting the target environment — was withdrawn
([ADR 0001](../../docs/decisions/0001-withdraw-split-tier-runs.md)):

| | Deferred-verification | Split-tier *(withdrawn)* |
|---|---|---|
| Target | **The real one** | A substitute |
| Reference FKs | **Native — no portability question at all** | Every one needs cross-environment checking |
| Gate 0f | **Not applicable** | Required |
| Output | **The actual deliverable**, one verification pass from executable | Never executable anywhere |
| Deferred | A clean, nameable set: the target-side existence reads | An arbitrary set, decided by which reference data happens to be local |

**What gets deferred, precisely.** Procedure step C2 — *"does a row already exist on the BOX side?"* —
for every walk step, plus gate 0e. Nothing else. The GBO mining, the walk order, the dependency graph,
the value derivation and the SQL generation all run normally and completely.

**What that costs, stated plainly.** Every walk step's BOX-side status becomes **assumed rather than
read**. The assumption is usually near-certain — a branch being onboarded has no BOX rows, which is the
precondition for the whole job — but "near-certain" is not "confirmed", and this repo does not let those
collapse. So:

- Every BOX-side finding is `EVIDENCE_REQUIRED` until its read happens. It never reads `CONFIRMED_ABSENT`
  on an assumption.
- **The generated SQL is a draft and is marked not executable.** If a row does already exist — a
  partially configured branch, or a shared configuration the branch should reuse rather than recreate —
  an `INSERT` would be wrong. One verification pass settles it.
- **Gate 0e becomes the single release gate.** It cannot be evaluated without target read access; when
  access lands, run it plus the deferred C2 reads, and the draft becomes executable without
  regeneration.

**The structural assumption this rests on** — that the target's `BOX_FE` has the same tables and columns
as a known-good reference environment — is `[stated]`, not confirmed, and must be recorded as such in
the run folder. It is cheap to discharge: one Q-G4 run against the target when access arrives.

**Use the real run folder**, not a rehearsal one. These are the real run's artifacts, produced up to the
point read access stops. Every deferred item carries its status, so nothing assumed can be mistaken for
something verified.

**A step that cannot be evidenced is a finding, not a run-stopping blocker.** This generalises beyond
deferred-verification and is the rule to reach for whenever one step's evidence is unavailable while
the rest is reachable: mark it `EVIDENCE_REQUIRED`, annotate *why* in the reviewer's terms, **emit no
SQL for it**, and **continue the rest of the walk.** A walk that stops at the first unreachable step
throws away everything it could have produced, and gives the reviewer nothing to disagree with.

Two things this never licenses. It does not license unblocking the step by substitution — hard rule 6,
which for market data would repoint a branch at the wrong pricing source. And it does not apply to
**step 5**: the association row is what ties the configuration to a branch, so if *it* cannot be
emitted that is run-stopping (see [`fe-walk-notes.md`](fe-walk-notes.md)).

### Withdrawn run shapes — kept as decision records

Two modes this charter used to describe are no longer used, and their reasoning is preserved rather
than deleted. **Reinstating either means a new ADR superseding it, not quietly re-adding a section.**

| Mode | Why it went | Record |
|---|---|---|
| **Split-tier** — mine one environment, write another | Made every mined FK a portability question, blocked step 4 entirely, and produced SQL executable in neither environment. Deferred-verification is strictly better on every axis | [ADR 0001](../../docs/decisions/0001-withdraw-split-tier-runs.md) |
| **Deferred-PK** — emit PKs as named substitution variables | Gate 0d resolved 2026-09-17; the agent now emits the real `F___SEQUENCE` call, which is auditable **and** executable. The placeholder-plus-binding-step technique is worth reusing for BOX ACC | [ADR 0002](../../docs/decisions/0002-deferred-pk-mode.md) |

Both ADRs name what was kept in this charter. Nothing in either relaxes a hard rule: deferred-PK
forbade an invented literal, an unmapped sequence and a copied PK exactly as hard rule 3 does now.
