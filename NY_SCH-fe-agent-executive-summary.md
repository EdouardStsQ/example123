# BOX FE configuration for a new branch — what the agent does, and what we need checked

**For review by a BOX FE developer.** First case: **NY_SCH**. Written 2026-09-17.

We have built an agent (`sigom-box-fe-configs-agent`) that produces the **reviewed, runnable SQL**
to configure a branch in BOX FE. It does not write to any database — a human runs the SQL after
sign-off. This page is the method in one read, and **section 4 is the actual ask**: eight points where
we are working from inference rather than confirmation, and where ten minutes of your time saves us
days.

---

## 1. Method in one paragraph

A branch that is live in GBO already has its configuration there. So for each BOX FE configuration
object we read the equivalent GBO (`DEVENG.T_PGT_*`) row, propose the BOX (`BOX_FE.T_BOX_*`)
equivalent, have a named SME confirm it, and only then generate the `INSERT`. Nothing is copied from
another branch, and nothing is invented. The one exception is **instrument scope**: which instruments
the branch gets is chosen from what is already live in BOX, by an SME — not read from the branch's GBO
instrument configuration.

---

## 2. The walk — 13 configuration objects, in dependency order

| # | Object | BOX FE table | GBO source |
|---|---|---|---|
| 1 | FE configuration association — **read**, reuse or new? | `T_BOX_ENGCONF_X` | — |
| 2 | MIS Generic header | `T_BOX_ENGCONF_S` | `T_PGT_ENGCONF_S` |
| 3 | Fixing Curve header | `T_BOX_ENGFCURVE_S` | `T_PGT_ENGFCURVE_S` |
| 4 | Curve → quote reference linkage | `T_BOX_ENGLKFC_X` | `T_PGT_ENGLKFC_X` |
| 5 | Branch association row — **write** | `T_BOX_ENGCONF_X` | (`T_PGT_BRANCH_S`) |
| 6 | Accrual defaults — **and the branch's instrument list** | `T_BOX_ENGACCRCONF_S` | `T_PGT_ENGACCRCONF_S` |
| 7 | Accrual Exceptions | `T_BOX_CONFIG_ACCRUAL_S` | `T_PGT_CONFIG_ACCRUAL_S` |
| 8 | Fixing Exceptions | `T_BOX_FIXING_BY_INSTR_S` + `V_BOX_PROC_INSTR_S` | `T_PGT_FIXING_BY_INSTR_S` |
| 9 | Yield Curve | `T_BOX_ENGZCCONF_S` | `T_PGT_ENGZCCONF_S` |
| 10 | Currency Basis | `T_BOX_ENGCURRENCYBASIS_S` | `T_PGT_ENGCURRENCYBASIS_S` |
| 11 | Book — FE batch execution registration | `T_BOX_CONF_BY_BOOK_S` | **none** — BOX-only |
| 12 | Derived — **verify, never INSERT** | `T_BOX_FIXING_ASSIGNMENT_S`, `T_BOX_BRPROCCAL_S` | — |
| 13 | Not branch-scoped — **rule out with evidence** | `T_BOX_ENGDAYS_MATURED_S`, `T_BOX_ENGSETUP_S` | — |

The order matters because the schema **declares no foreign-key constraints at all** — only primary-key
and check constraints. The dependency order above is therefore *derived*, not read from the data
dictionary. See question 1.

---

## 3. Five gates — no SQL is written until all pass

| Gate | Condition | Status for NY_SCH |
|---|---|---|
| 0a | Branch exists in GBO, `BRANCH_PK` resolved | ✅ Tier 2: `20007.4`, entity `31398.4`, currency `159.4`, calendar `83.4` |
| 0b | `FK_MISCONFIG` resolved to the branch's GBO MIS header | ✅ Tier 2: branch-config `141.35` → `FK_MISCONFIG 64408.35` → *"Configuracion -NY"* |
| 0c | Instrument scope, from a named SME, in writing | ⛔ **Open** — see question 3 |
| 0d | **PK generation mechanism known** | ⛔ **Open and blocking** — see question 2 |
| 0e | Target schema complete in the run environment | ⛔ Blocked on a Tier 2 account with `BOX_FE` grants |

A blocked run, honestly reported, is the correct outcome. The agent is built to stop rather than guess.

---

## 4. What we need your feedback on

Ordered by how much a wrong answer would cost us.

**1 — Is anything missing from the 13?** This is the most valuable question on the page. Is there a
table a newly onboarded branch needs in `BOX_FE` that is not in the walk above? An object that has to
exist before the branch's trades process correctly, that we would only discover when the batch fails?

**2 — How are primary keys actually allocated?** Gate 0d, and it blocks everything. We found ten target
PK columns with **no `DATA_DEFAULT`, no triggers**, and seven `BOX_FE` sequences we cannot map to any
walk table. Observed PKs look like `<integer>.<authcode>` — SLB's Accrual rows carry `24.095.416,21`,
`19.146.735,21`, `44.552,21`, `31.874.132,21` and so on, all with the same `,21` suffix. Three
sub-questions:

- Is there a **single sequence shared across many tables** rather than one per table?
- Is the `.21`-style suffix applied by **SIGOM application code**, and does it identify an owning
  authority or environment?
- **Can these rows be created by a raw `INSERT` at all**, or must they go through SIGOM so that
  allocation happens correctly? If it is the latter, our whole approach needs rethinking, and we would
  much rather know now.

**3 — Is the Accrual tab the right place to read a branch's instrument set?** We now treat
`T_BOX_ENGACCRCONF_S` (one row per instrument) as the authoritative answer to "which instruments does
this branch have," with `T_BOX_ENGINSTRUMENTS_S` as the global catalogue it is chosen from. SLB in
Tier 1 shows nine. Is that correct, and is there anywhere else a branch's instrument set is registered
that we would miss?

**4 — Two joins we are guessing at.** Queries for step 9 (`T_BOX_ENGZCCONF_S`, Yield Curve) and
step 10 (`T_BOX_ENGCURRENCYBASIS_S`, Currency Basis) rest on an assumed `FK_PARENT` relationship we
have never confirmed, and we have never observed rows in the Currency Basis table. What are the real
join columns, and is Currency Basis normally populated at all?

**5 — Book rows: all instruments, or some?** We understand `T_BOX_CONF_BY_BOOK_S` as BOX-only
functionality with no GBO twin, where a row for a `(branch, instrument)` pair is what registers that
combination for the FE batch to execute. Does a new branch need a row for **every** instrument in its
scope, or only for those with books in the Data Lake?

**6 — Is step 12 really derived?** We treat `T_BOX_FIXING_ASSIGNMENT_S` and `T_BOX_BRPROCCAL_S` as
populated by the system, never configured by hand, and the agent refuses to write to them. Correct?

**7 — Is step 13 really not branch-scoped?** We concluded `T_BOX_ENGDAYS_MATURED_S` and
`T_BOX_ENGSETUP_S` are global rather than per-branch, so a new branch needs nothing in them. Correct?

**8 — One oddity worth a sanity check.** In BOX-DEV screenshots, the `Branch` column on Accrual
Exceptions and Allowed Errors holds **product-shaped values** (`BOX CCS`, `BOX FX`, `BOX IRS`) rather
than geographic branches. Our entire model assumes FE configuration keys to a geographic branch. Is
that a dev-environment convention, or does "branch" genuinely mean something different on those
screens?

---

## 5. What the agent will never do

Worth stating, because it is what makes the output safe to review rather than safe to trust blindly.

It never invents a value. Every value is read from the database, given by a named SME, a documented
constant, or explicitly labelled `DERIVED` with its rule attached — and a `DERIVED` value is never
recorded as confirmed and needs its own sign-off. It never fabricates a primary key, and refuses to
emit any `INSERT` at all while gate 0d is open. It never writes DDL: if a table is missing, it locates
the authoritative `CREATE` statement in `cib-boxfin-dbboxfe` and cites the path rather than
reconstructing one, because a reverse-engineered table would silently lose the constraints, defaults
and triggers the PK mechanism may depend on. It never copies values from Madrid or London because the
shape matches — those two share calendar, currency and both source systems, yet use different fixing
curves, and NY is USD/New York, unlike either. It never writes to a database. And it treats a zero-row
result as a question rather than an answer: two "absences" in this project have already turned out to
be a broken join and a missing schema grant.

---

*Feedback of the form "that table is wrong," "that join is X not Y," or "you're missing Z" is exactly
what is useful. Corrections get recorded against the specific claim with attribution, not silently
absorbed.*
