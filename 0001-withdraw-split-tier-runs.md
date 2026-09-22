# 0001 — Split-tier runs: withdrawn in favour of deferred-verification

**Status:** withdrawn 2026-09-18 · moved out of the charter 2026-09-21
**Context:** `sigom-box-fe-configs-agent`

## The decision

**A run never substitutes a different environment for its target.** When the target's `BOX_FE` cannot
be read, the run targets it anyway and defers the target-side reads — the *deferred-verification* shape,
which remains in the charter.

## What split-tier was

`GBO_SOURCE` and `TARGET_ENV` are separate inputs, so nothing structurally prevented mining one
environment and writing another. When Tier 2 had GBO access but no `BOX_FE` grants, that looked like the
way through: mine Tier 2 where NY_SCH is live, write Tier 1 where `BOX_FE` is reachable.

The reasoning was sound as far as it went — *mine the tier where the branch is real, write the tier you
can reach*, because a GBO read from the wrong tier is worthless whatever its shape, while a substituted
target can be verified and undone. Runs were recorded in their own folder, every output file headed with
**both** environments and marked a test artifact rather than a promotion candidate.

## Why it was withdrawn

`[stated: Edouard, 2026-09-18]` Substituting the target made **every mined FK a portability question**,
which is what gate 0f existed to answer. It blocked step 4 entirely — a branch's quote references live in
`PGT_MRK`, which is environment-specific, so NY's own curve references largely do not exist in Tier 1 —
and it produced SQL that was **never executable anywhere**: not in Tier 1 (wrong branch) and not in
Tier 2 (wrong PKs).

Deferred-verification is strictly better on every axis: the target is real, every FK is native, gate 0f
does not arise, and the output is the actual deliverable one verification pass from running.

## What was true about it, and is worth keeping

Two rules generalise beyond split-tier and were **kept in the charter**, not deleted with it:

1. **A step that cannot be evidenced is a finding, not a run-stopping blocker.** Mark it
   `EVIDENCE_REQUIRED`, annotate why, emit no SQL for it, and **continue the rest of the walk.**
2. **Never load source-environment data into the target, and never substitute the target's
   equivalents** to unblock anything. The second is hard rule 6, and for market data it would silently
   repoint a branch at the wrong pricing source.

The eval case retains failure conditions for both.

## If it is ever needed again

The shape works when — and only when — the branch is live in one environment and the writable `BOX_FE`
is in another, *and* someone accepts SQL that is a shape demonstration rather than a deliverable. It
requires **gate 0f** (ADR 0003) and an explicit statement in every output that the configuration is a
test artifact. Reinstating it means a new ADR superseding this one, not quietly re-adding the section.
