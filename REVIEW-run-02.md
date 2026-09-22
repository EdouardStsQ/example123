# Draft review — run 2, `ny_sch_steps_1_to_5.sql`, 2026-09-22

**Verdict: rejected — regenerate.** Every defect I made *mechanical* after run 1 was fixed. Three new
ones appeared that were prose-only. That is the whole lesson of this run.

---

## ✅ What the run-1 fixes bought

| Run 1 defect | Run 2 |
|---|---|
| `FK_CURVEMAN = 1.35`, a GBO PK in a BOX column | ✅ **Fixed.** Emitted `NULL`, then `UPDATE … SET FK_CURVEMAN = v_curve_pk` |
| Curve created and orphaned | ✅ **Fixed.** Insert-then-update implemented exactly as specified |
| Identity via `WHERE ROWNUM = 1` | 🟡 **Changed, not fixed** — now `GROUP BY … HAVING`, still sampled from data |
| Step 14 `CONFIRMED_PRESENT` | ✅ **Fixed** — `NOT_BRANCH_SCOPED` |
| No pre-commit call | 🟡 **Called, wrong name** — see below |
| `[stated: user]` | 🟡 **Now `[stated: Edouard Sintes, BOX Dev, 2026-09-22]`** — properly formed |

**Best single line in the run**, step 8: *"NY count and SLB control count were both zero; no non-zero
control proves the absence"* → `EVIDENCE_REQUIRED`. It ran the control, the control came back empty, and
it **refused to conclude absence**. That is hard rule 8 applied correctly and unprompted.

---

## ⛔ Blocking

### 1. 37 of 38 quote-reference rows were dropped

Run 1 emitted **38** `T_BOX_ENGLKFC_X` rows. Run 2 emits **one** (`FK_BS = 16309.4`). The repo records
all 38 as read from Tier 2's `PGT_MRK`.

Open item 5 names it without recognising it: *"Q-04 evidence is a normalized projection of the wide
returned join."* **Normalising a result set down to one row is not a projection, it is a silent
enumeration loss** — the exact defect class hard rule 8 exists for, and the same shape as the Q-05c
inner join that dropped two instruments in September.

A curve with 1 of its 38 quote references is not a partially configured curve. It is a wrong one.

### 2. Q-05d's answer was inverted

Q-05d showed **SLB GBO ≠ SLB BOX**. The run concluded: *"SLB **BOX** values with NY GBO fallback for
absent/null values."*

**Backwards.** A GBO→BOX difference tells you how values change **between systems**. It says nothing
about whether London's configuration suits New York. Using it to justify London's values is hard rule 6
wearing the evidence as a disguise — and the hybrid is worse than either source alone, because one row
now carries two branches' decisions with no way to tell which column came from where.

The values are **NY's**, always. Q-05d supplies only the transformation to apply to them. If the rule
cannot be stated in one sentence there is no rule, and the columns are `EVIDENCE_REQUIRED`. **A null in
NY's GBO row is a finding about NY**, not a hole to plug from London — SLB's own Deposit & Loan carries
nulls in `INTERVAL` and `BYRESIDUAL` and is a live configuration.

### 3. `PGT_MRK.P_ENGFixingCurve_PreCommit` — invented qualifier

The recorded package is **`PKG_ENGPRECOMMIT`**. `PGT_MRK` is the market-data schema and holds no such
procedure. The call fails at runtime, and an invented schema qualifier is a fabricated literal
(hard rule 1). The instruction to call the procedure landed; the name was not checked against the repo
that records it.

### 4. Gate 0c closed on "same as SLB"

The sign-off pack says in its own opening: *"A verbal 'same as London' is not usable — the walk needs
the list."* The run took that phrase and interpreted it into a value rule. Interpreting an
unusable answer does not make it usable.

Attribution is now properly formed, which is real progress. But the recorded role is **BOX Dev**, and
the decisions taken — accrual values, error limits, book scope — are the **product-scope SME's**. That
is the second of the three gate-closure tests, and it is still open.

---

## ⚠️ Also

- **Gate 0c closed but steps 6, 11, 12 emit no SQL.** If the gate is closed they are releasable; if they
  are not releasable the gate is not closed. The run is internally inconsistent, and open item 1 asks
  for a C2 read on a configuration that does not exist yet.
- **Identity columns still sampled** — `GROUP BY FK_OWNER_OBJ HAVING COUNT(DISTINCT FK_OWNER_OBJ) = 1`
  is a tautology; the `HAVING` never excludes anything. It happens to be safe because `SELECT … INTO`
  raises on multiple rows, but the predicate does no work and the identity still is not the metamodel's.
- **Step 7 `CONFIRMED_ABSENT`** with Q-06 mined — if NY's GBO *has* exceptions, absent on the BOX side
  is the reason to write them, not to skip. The finding does not say what Q-06 returned.

---

## What this run changed in the repo

**Three checks, because all three defects were prose-only rules:**

| Check | Catches |
|---|---|
| `sql-no-step-headers` | the missing step annotations — requested, never enforced |
| `identity-sampled-from-target` | `ROWNUM = 1`, `GROUP BY/HAVING`, `MIN()` — any runtime sampling of `FK_OWNER_OBJ`/`FK_EXTENSION` |
| `precommit-wrong-package` | a pre-commit called under any package but `PKG_ENGPRECOMMIT` |

All three fire on this file. Plus Q-05d now carries an explicit prohibition on inverting its result.

**The pattern across two runs is unambiguous.** Everything converted to a validator check was fixed.
Everything left as prose — however emphatic, however recently written — was not. The step headers were
asked for in the charter *and* the prompt, in bold, with a rationale, and did not appear.
