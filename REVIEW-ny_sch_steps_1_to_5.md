# Draft review — `ny_sch_steps_1_to_5.sql`, 2026-09-22

**First end-to-end run of the agent against a real target.** Reviewed by Edouard and this repo.

**Verdict: rejected — regenerate.** Three blocking defects, four to fix, and one genuinely excellent
piece of work. **All the mechanical rules held**; every defect is semantic, which is the finding that
matters most about the agent itself.

---

## ⛔ Blocking

### 1. `FK_CURVEMAN` / `FK_CURVEACC` = `1.35` — a GBO PK in a BOX column

The header INSERT carries `1.35`, which is NY's curve PK in **`DEVENG.T_PGT_ENGFCURVE_S`**. The column
must reference **`BOX_FE.T_BOX_ENGFCURVE_S`** — a different table with its own key space. The script
then created the correct BOX curve, `'NY Configuration Suc'`, with 38 quote references, and **nothing
referenced it.**

With no FK constraints anywhere (hard rule 12) this inserts cleanly and fails silently in a batch later.

> **The rule already existed** — the query catalogue's three-kinds table names *"the GBO curve's own
> `PK = 1.35`"* as its worked example of a value never to carry. It was buried inside the **gate 0f**
> section, and gate 0f is not applicable to a same-environment run. Promoted to **hard rule 13**.

**And the charter was wrong too.** The walk put the header at step 2 and the curve at step 3 while
claiming FK-dependency order — but the header points *at* the curve, so no plain-INSERT ordering
satisfies both. The run hit a real contradiction and resolved it the only way its ordering allowed.
Fixed as **insert-then-update**: header with NULL curves → curve → quote array → `UPDATE` the header.

### 2. Step 6 proposed London's accrual values with NY's own rows already mined

`Q-05-accrual-gbo.csv` is cited in the run's own evidence. NY has 18 accrual rows in
`DEVENG.T_PGT_ENGACCRCONF_S` under `FK_PARENT = 64408.35`. The run used London's values for five of
six instruments anyway — hard rule 6, and ADR 0004 explicitly does not extend past `LIMIT_ERRORS`.

**⛔ Confirmed against an in-scope instrument.** `[confirmed: DB via Edouard, 2026-09-22]`

| Deposit & Loan | `FK_FEEFIRSTDAYSEL` | `FK_INTFIRSTDAYSEL` | `INTCOMMONBASIS` | `BYTRIGGER` | `BYRESIDUAL` | `INTERVAL` |
|---|---|---|---|---|---|---|
| NY — GBO Tier 2 | 3.4 | 3.4 | **1** | **1** | **0** | **377** |
| SLB — BOX Tier 1 | 3.4 | 3.4 | **0** | **0** | *null* | *null* |

Four columns differ, and **`INTCOMMONBASIS` and `BYTRIGGER` are two of the four gate-0c `NOT NULL`
values**. This is no longer "nothing checked" — the run proposed values that differ from the branch's
own configuration on an instrument in scope.

### ⚠️ And the fix is not simply "use NY's GBO values"

That comparison varied **two** things: the branch *and* the system (NY in **GBO** vs SLB in **BOX**).
The difference could be a real branch difference, or a **GBO→BOX transformation** applied when a
configuration is created in BOX — in which case NY's GBO values must be transformed too, not copied.

**Q-05d** (new) holds the branch constant and varies only the system: SLB's GBO row against SLB's BOX
row, both Tier 1. One query, Tier 1 only. **No step-6 value is `PROPOSED` until it runs.**

### 3. Gate 0c marked `CONFIRMED_PRESENT` on the operator's in-session acceptance

Evidence reads `[stated: user, 2026-09-22]`. The gate requires **a named SME in writing** — that is
what the sign-off pack exists for. The instrument list came from the SME; the four accrual values,
`LIMIT_ERRORS` and book scope did not. Steps 6, 11 and 12 are all `PROPOSED` on that basis.

*Acceptable as a test input if labelled as one. Not acceptable as gate closure.*

---

## ⚠️ Fix before the rerun

| # | Defect | Fix |
|---|---|---|
| 4 | Identity columns read with `WHERE ROWNUM = 1` — an arbitrary row, while `Q-G6-identities.csv` sat unused. `v_owner_curve` is also assigned twice, the second overwriting the first, so the curve header takes the bridge table's owner | Emit the Q-G6 constants |
| 5 | Step 8 `CONFIRMED_ABSENT` reasoning from **Tier 1** emptiness, with `Q-07` absent from its evidence | Mine NY's own GBO fixing exceptions |
| 6 | Step 7 blocked on `FK_BRANCH` semantics — the known over-blocking pattern; the step mines on `FK_PARENT` regardless | Mine it, status the values |
| 7 | No pre-commit calls. `P_ENGFixingCurve_PreCommit` does no DML and belongs as a gate for steps 3/4. No `DESCRIPTION` uniqueness pre-check, and that index is global | Add both |

Minor: step 14 should be `NOT_BRANCH_SCOPED`, not `CONFIRMED_PRESENT`.

---

## ✅ What the run got right

**The discrepancy investigation is the best work in it.** It established that SLB's accrual table has
7 rows that all join cleanly, that the reference set holds `20314.4 = Forward Rate Agreement` and no
Credit Derivatives row at all, and it **explicitly disproved** this repo's typo hypothesis about
`20313.4`/`20314.4`. That closes the 2026-09-18 finding completely.

Preflight ran first and is quoted (`BOXFE_VISIBLE = 62`). Every PK is `F___SEQUENCE` on a declared
variable — no literal PKs. Explicit column lists throughout. No `INSERT … SELECT FROM DEVENG`. Draft
header, rollback `DELETE`s child-first, verification `SELECT`s. Steps 4b, 9, 10 correctly parked. Step
12 correctly applied ADR 0004. **CDS was sourced from NY's own GBO row** — the right source, for the
right stated reason.

---

## What this run changed in the repo

The most valuable output of the test was not the SQL.

- **Hard rule 13** — the three kinds of mined value, promoted out of gate 0f where it was unreachable.
- **Steps 2–4 are insert-then-update** — a charter defect the run exposed by colliding with it.
- **Step 6's values come from the branch's own GBO row**, reference branch shown alongside.
- **Three new validator checks** — `curve-fk-literal`, `orphan-curve`, `identity-from-rownum`. All
  three fire on this file; all three pass on the corrected form.
- **Four new eval failure conditions.**

**The validator passed this file before those checks existed.** That is the honest measure of what
mechanical checking was worth here — and the reason three of these defects are now mechanical.
