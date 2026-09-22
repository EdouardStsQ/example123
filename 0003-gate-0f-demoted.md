# 0003 — Gate 0f: demoted to a one-time spot check, then moved out of the charter

**Status:** demoted 2026-09-18 · moved out of the charter 2026-09-21 · **not applicable to any current
run**
**Context:** `sigom-box-fe-configs-agent` · applies only to split-environment runs (ADR 0001, withdrawn)

## What the gate was for

Every value mined from GBO is a PK **in the source tier**. An `INSERT` into a *different* tier carrying
`FK_CALENDAR = 83.4` is only correct if `83.4` names the same calendar there. Three outcomes, not
equivalent:

| Outcome | Meaning | Action |
|---|---|---|
| Resolves, same object | replicated reference data | use it |
| **Does not resolve** | absent in the target | `EVIDENCE_REQUIRED`, no statement — a portability finding, not a value to substitute |
| **Resolves to a *different* object** | same PK, different meaning | ⛔ **stop.** A silently wrong FK is the failure the whole agent exists to prevent |

It was the one gate evaluated **after** mining, since it tests values the walk produces.

## Why it was demoted

`[stated: Edouard, 2026-09-18]` **`PGT_STC` and `PGT_SYS` hold identical rows in every environment.**
That is most of the reference data this walk touches, so checking it across environments verifies a
design guarantee rather than a risk — and it explains why the first Q-14 run matched *exactly*.

| Mined FK | Schema | Check? |
|---|---|---|
| `FK_CALENDAR`, `FK_CURRENCY`, branch `FK_BS` | `PGT_STC` | ❌ shared |
| `FK_INSTRUMENT`, `FK_*DAYSEL`, `FK_LABEL`, domain values | `PGT_SYS` | ❌ shared |
| **Quote references** (step 4) | `PGT_MRK` | ✅ the one genuine item — shared BOX↔GBO *within* an environment, **not** across |
| `FK_CURVEMAN` / `FK_CURVEACC`, any FK to a walk-created object | `BOX_FE` / `DEVENG` | ❌ resolved at apply time |

So: one check per environment *pair*, not a gate on every walk.

## Why it left the charter

ADR 0001 withdrew split-tier runs, and gate 0f applies to nothing else. A same-environment run — every
current and planned run — has no portability question to answer. Sixty lines of charter describing a
gate that never fires is sixty lines competing for attention with rules that do.

## The two things kept in the charter

1. **A run is never blocked on a `PGT_STC` or `PGT_SYS` value.** If one looks divergent that is a
   **platform escalation** — a shared schema out of sync is far bigger than one branch onboarding — not
   a finding about this walk. Retained in *Escalation rules*.
2. **Same PK, different object is the dangerous case.** That lesson outlived the gate: `6401.4` names a
   different quote reference in two environments, and `35000007.65` is both an object PK and a module
   PK in different registries. It now lives where it is more generally useful — `confirmed-joins.md`
   and `sigom-metamodel.md` §7 — as *a PK is only meaningful with its table*.

## The prior that still holds

A `.4` suffix means the row was allocated in the global reference environment, so `.4` FKs are the ones
most likely to be valid in two environments; a tier-specific suffix is the least likely to travel. **Use
that to predict, never to conclude.** Q-14 remains in the query catalogue for whoever needs it.
