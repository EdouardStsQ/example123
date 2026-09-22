# 0004 — Step 12 `LIMIT_ERRORS`: proposed from the reference branch, not mined from GBO

**Status:** adopted 2026-09-21 · **narrow, and it does not generalise**
**Context:** `sigom-box-fe-configs-agent`, walk step 12 (`BOX_FE.T_BOX_ERRORS_FE_S`)

## The decision

`[stated: Edouard, 2026-09-21]` **Do not mine the GBO twin for step 12.** For each in-scope instrument,
**propose SLB's `LIMIT_ERRORS` value for that same instrument**, and let the SME accept or change it.

This **supersedes** the 2026-09-18 position that step 12 is an ordinary mine-and-propose step because
`DEVENG.T_PGT_ERRORS_FE_S` exists.

## Why this does not breach hard rule 6

Hard rule 6 forbids copying a value across branches **because the shape matches** — an unattributed
value presented as though it were derived. The rejected September draft did exactly that: it carried
115 for Cross Currency Swap and 100 for the rest, taken from London, with no attribution and no
decision behind it.

What makes this different is not the source, it is the **status**:

| The rejected draft | This decision |
|---|---|
| Value appeared in SQL as though mined | Value is tagged **`PROPOSED`**, never `CONFIRMED` |
| No stated rule | The rule is stated: *SLB's limit for the same instrument* |
| No attribution | `[stated: Edouard, 2026-09-21]` as the instruction; the SME's acceptance is its own sign-off |
| Rode along in a batch approval | Needs **explicit per-instrument sign-off** before any SQL is emitted |

That is hard rule 2 — derivation is allowed, and labelled — applied to a value whose source is a
reference branch. **A `PROPOSED` value that is never signed off never becomes SQL.**

## Why a reference branch is the right source *for this column specifically*

`LIMIT_ERRORS` is not a correctness value. It is an **operational tolerance**: how many failed deals a
single load run survives before it aborts. It does not describe what the branch *is*, the way a
calendar, currency or curve does. There is no fact about NY_SCH that determines it — only a judgement
about how much failure to absorb before stopping, and SLB's judgement on the same instrument is the
best available starting point.

Contrast a fixing curve, where copying London's value asserts something false about NY. Copying
London's error tolerance asserts only *"start where London started."*

## ⚠️ What it is, and what it is not

**It is a tuning default, not an answer.** SLB's limits reflect SLB's volumes and data quality. NY_SCH's
are unknown. Both directions of error are real and neither announces itself:

| Too high | Failed deals are skipped and the run reports success. **Missing deals, no alarm** |
| Too low | The first bad deal aborts the whole load for that instrument |

So the proposal is put to the SME **with that stated**, and *"needs volume data first"* stays a valid
answer. A limit accepted without anyone considering NY's volumes is a decision that has been made by
default rather than taken.

## The mapping is exact — there is no "similar product" judgement

All six of NY_SCH's confirmed instruments are in SLB's nine. **Six for six, same instrument, direct
match.** Nobody has to decide what counts as "similar", and nobody should: if a future branch has an
instrument SLB does not, that instrument's limit is `SME_DECISION_REQUIRED` — **not** the value of
whichever instrument looks closest. Picking a near-neighbour is the shape-matching hard rule 6 forbids.

**CDS resolves.** `[confirmed: DB via Edouard, 2026-09-22]` Credit Derivatives is
`PGT_SYS.T_PGT_SUB_PRODUCT_S` PK **`20313.4`**, CODE `Credit`. *(An earlier version of this ADR said it
had no row and was therefore blocked — withdrawn; that was inferred from an inner join that failed to
match.)* Still confirm SLB has a step-12 row for it before proposing a limit: an absent **reference**
row is `EVIDENCE_REQUIRED`, never zero.

## 🚧 The boundary — this covers one column, on one step

**It does not extend to step 6's accrual values**, and that boundary is the whole reason this is written
down. Those four `NOT NULL` columns are genuine configuration: they describe how the branch accrues, NY
is USD/New York where SLB is not, and the eval case still fails a run that copies them. The same applies
to curves, calendars, currencies and every other mined value.

The test for extending this to any other column: **is it an operational tolerance, or does it assert
something about the branch?** Only the first kind may be proposed from a reference branch, and only as
`PROPOSED`. Extending it means a new ADR, not an analogy to this one.

## What this changes in the walk

- Step 12's source is **the reference branch (Q-13), not the GBO twin**. The GBO twin is not mined.
- Step 12 rows start `PROPOSED` with the rule attached, and need SME sign-off like any `DERIVED` value.
- Step 12 remains **mandatory per in-scope instrument**: a missing row means `LIMIT_ERRORS = 0`, so the
  first failed deal aborts the load. Absence is never the safe default.
- `DEVENG.T_PGT_ERRORS_FE_S` stays recorded in the catalogue as a known table. It is simply not this
  step's source any more.
