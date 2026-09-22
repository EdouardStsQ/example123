# 0002 — Deferred-PK mode: retained here, removed from the charter

**Status:** not needed since 2026-09-17 · moved out of the charter 2026-09-21
**Context:** `sigom-box-fe-configs-agent`

## The decision

A run whose purpose is to validate that the walk emits **correct, ordered, well-formed SQL** does not
have to wait for the PK-allocation mechanism to be known. **Hard rule 3 forbids *fabricating* a PK; it
does not forbid *deferring* one.**

## How it worked

Every primary key is emitted as a **named substitution variable**, never a literal —
`&PK_02_ENGCONF`, `&PK_03_CURVE` — with an undefined `DEFINE` block at the top of the file, and each
child row referencing its parent's variable **by the same name**. That makes the dependency graph
explicit and auditable on the page. The file is deliberately not runnable until a human binds the
DEFINEs, and its header says so. When the mechanism resolves, the same file becomes runnable by filling
in that block — no regeneration.

Nothing else relaxed: no invented literal, no sequence unmapped to its table, no PK copied from an
existing row, and every other gate and hard rule applied unchanged.

## Why it is no longer needed

Gate 0d resolved on 2026-09-17: PKs come from `F___SEQUENCE(<table>,'X')`. The agent now emits the real
call assigned to a declared variable, which has the same auditable dependency-graph property **and** is
executable. The substitution variables mapped one-to-one onto the declared variables, so the rehearsal
output produced under this mode was convertible rather than wasted.

## Why it is kept as a record

The principle is reusable and non-obvious: **when a mechanism is unknown, emit a named placeholder and
an explicit binding step rather than blocking the whole walk.** BOX ACC will hit its own version of this
when it is built, and the shape is worth copying.

Its removal from the charter is about weight, not disagreement — it occupied 25 lines of a prompt
describing a mode the agent must not use.
