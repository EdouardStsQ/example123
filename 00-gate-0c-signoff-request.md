# Gate 0c — scope sign-off request for NY_SCH

**To:** the named SME for NY_SCH product scope · **From:** the BOX FE onboarding run ·
**Run folder:** `runs/NY_SCH/tier2-pre/`

> **Status 2026-09-21: Question 1 answered, Questions 2 and 3 still open.** Gate 0c remains **blocked**
> — the instrument list alone does not release it, because steps 6, 11 and 12 each need values this
> document has not yet received. See the answer block under Question 1.
>
> ⚠️ **The SME's name must be written into this file before it is filed.** The attribution placeholder
> `<SME_NAME>` is not a valid evidence tag: gate 0c requires a **named** SME in writing, and an
> unnamed sign-off does not satisfy it.

**What this is.** Three decisions that only you can make. Everything else in the NY_SCH BOX FE
configuration is read from the branch's existing GBO configuration; these three are choices, and the
automated walk is blocked until they are made in writing.

**Why it is written this way.** You are asked to confirm **concrete lists**, not to enumerate from
memory. Each question carries a proposed answer taken from a comparable live branch, and your job is to
accept it, amend it, or reject it. A verbal "same as London" is not usable — the walk needs the list.

---

## Question 1 — Which instruments does NY_SCH get? ✅ **ANSWERED 2026-09-21**

> ### ✅ Answered — six instruments
>
> `[stated: <SME_NAME — insert before this file is filed>, via Edouard, 2026-09-21]`
>
> | # | Instrument | In SLB's set? | Resolves to a Sub-Product row? |
> |---|---|---|---|
> | 1 | Swap | ✅ | ✅ |
> | 2 | Deposit & Loan | ✅ | ✅ |
> | 3 | Cross Currency Swap | ✅ | ✅ |
> | 4 | OTC Option | ✅ | ✅ |
> | 5 | Caps And Floors | ✅ | ✅ |
> | 6 | **CDS (Credit Derivatives)** | ✅ | ✅ **`20313.4`** — see the correction below |
>
> **Not in scope**, though SLB has them: Cash Flow Matching, Forward Rate Agreement, Bond Return Swap.
>
> **The "same set as SLB" hypothesis is disproven.** NY_SCH gets **six of SLB's nine**. Had the walk
> run on the working assumption, it would have created **three instruments nobody asked for** — silent
> scope expansion, and exactly what this gate exists to prevent. Record the delta, not just the list.
>
> ### ✅ Correction, 2026-09-22 — the "CDS is blocked" warning is withdrawn
>
> An earlier version of this block said Credit Derivatives had no `PGT_SYS.T_PGT_SUB_PRODUCT_S` row
> `[confirmed: DB, 2026-09-18]`, that picking it turned a known gap into a blocker, and that it would
> block steps 6, 11 and 12. **All of that is withdrawn.**
>
> `[confirmed: DB via Edouard, 2026-09-22]` **Credit Derivatives is PK `20313.4`, CODE `Credit`.** The
> 2026-09-18 evidence was an `INNER JOIN` that returned seven of nine rows — which shows **the join did
> not match**, not that the instrument is absent. Recording that as a confirmed absence was an
> inference, and the `[confirmed]` tag made it unfalsifiable downstream. Hard rule 8, applied to
> everyone's queries except this repo's own reasoning.
>
> **Nothing is blocked. All six instruments resolve.**
>
> **What remains open** is only why the join missed: read SLB's Credit Derivatives accrual row and
> compare its `FK_INSTRUMENT` against `20313.4`. A different value is a question about that row; a
> different key space would be a data-model finding. Either way, use Q-05c's **`LEFT JOIN`** form plus
> the unjoined `COUNT(*)` — and never map "CDS" to a Sub-Product row by name similarity.

### The question as it was put

The instrument set *is* the configuration: BOX FE creates one Accrual row per instrument, and the number
of rows **is** the scope. An instrument not on this list is never configured and never processed.

**Chosen from what is already live in BOX** — not from what NY_SCH has in GBO. The proposed set was the
nine SLB (London) has configured in Tier 1: OTC Option, Cross Currency Swap, Swap, Cash Flow Matching,
Deposit & Loan, Credit Derivatives, Forward Rate Agreement, Caps And Floors, Bond Return Swap.

---

## Question 2 — Four accrual values, per instrument

**This is new as of 2026-09-21 and it is the part most likely to be missed.** The Accrual table has
four columns that are **`NOT NULL` at the database level**, so they cannot be left blank pending a later
decision. Every instrument you choose in Question 1 needs all four.

| Column | Screen label *(mapping unconfirmed — see below)* | Kind |
|---|---|---|
| `FK_FEEFIRSTDAYSEL` | `FeeCalcInterval`? | a value from the Accrue Interval list |
| `FK_INTFIRSTDAYSEL` | `InterestCalcInterval`? | a value from the Accrue Interval list |
| `INTCOMMONBASIS` | `InCommonBasis`? | a literal |
| `BYTRIGGER` | one of the `ByTrigger` flags? | a flag |

⚠️ **Honest caveat, and it needs closing before the meeting.** The metamodel declares the *screen field*
names (`FeeCalcInterval`, `InterestCalcInterval`, `InCommonBasis`) and the DDL gives the *physical
column* names above. The mapping between them is **plausible but unconfirmed** — `FEEFIRSTDAYSEL` reads
like "fee first day selection", not obviously "fee calculation interval". **Do not ask an SME to sign
values whose meaning we cannot state.**

**Run this first, and bring the output to the meeting.** It shows the four values as a live branch
actually has them, with the domain values resolved, which both confirms the mapping and gives the SME
something concrete to react to:

```sql
SELECT sp.DESCRIPTION                       AS instrument,
       a.FK_FEEFIRSTDAYSEL, d1.DESCRIPTION  AS fee_value,
       a.FK_INTFIRSTDAYSEL, d2.DESCRIPTION  AS int_value,
       a.INTCOMMONBASIS,
       a.BYTRIGGER
FROM        BOX_FE.T_BOX_ENGACCRCONF_S      a
LEFT JOIN   PGT_SYS.T_PGT_SUB_PRODUCT_S     sp ON sp.PK = a.FK_INSTRUMENT
LEFT JOIN   BOX_FE.T_BOX_ENGDOM_S           d1 ON d1.PK = a.FK_FEEFIRSTDAYSEL
LEFT JOIN   BOX_FE.T_BOX_ENGDOM_S           d2 ON d2.PK = a.FK_INTFIRSTDAYSEL
WHERE       a.FK_PARENT = &&REFERENCE_CONFIG_PK      -- SLB's MIS configuration
ORDER  BY   sp.DESCRIPTION;
```

> ### 🔄 Corrected 2026-09-22 — NY's own values are the proposal
>
> **NY_SCH has its own accrual configuration in GBO** — `DEVENG.T_PGT_ENGACCRCONF_S` under
> `FK_PARENT = 64408.35`, 18 instruments. Those are the proposed values. **London is shown beside them
> for comparison, not as the source.**
>
> | Instrument | NY's GBO value | London's value | Same? | Decision |
> |---|---|---|---|---|
> | Swap | | | | ☐ accept NY ☐ use ____ |
> | **Deposit & Loan** | `INTCOMMONBASIS 1`, `BYTRIGGER 1`, `BYRESIDUAL 0`, `INTERVAL 377` | `0`, `0`, *null*, *null* | ⛔ **No — 4 columns** | ☐ accept NY ☐ use ____ |
> | Cross Currency Swap | | | | ☐ accept NY ☐ use ____ |
> | OTC Option | | | | ☐ accept NY ☐ use ____ |
> | Caps And Floors | | | | ☐ accept NY ☐ use ____ |
> | CDS (Credit Derivatives) | | *(London has no row)* | — | ☐ accept NY ☐ use ____ |
>
> **Where the two agree you are confirming, not choosing. Where they differ, that is the question** —
> and they do differ, on an instrument in scope. Deposit & Loan is filled in above as the worked
> example: four columns apart, two of them among the four mandatory values on this very form.
>
> ⚠️ **One check outstanding before these are proposals rather than observations.** NY's figures are
> read from **GBO** and London's from **BOX**, so the difference might be the two systems rather than
> the two branches. **Q-05d** settles it in one Tier 1 query — London's GBO row against London's BOX
> row. If the systems transform these columns, NY's figures will be transformed the same way and
> labelled `DERIVED` before they reach you. **Do not sign this section until that column is settled.**

**Then the question to the SME is:** *"These are NY's own values from GBO, with London's beside them.
Do you accept NY's, and where they differ from London, is that difference intended?"*

⚠️ **NY is USD / New York; SLB is not.** Confirming the instrument *set* from a reference branch is
legitimate (question 1). Copying its accrual *values* is not — that is the repo's hard rule 6, and it
exists because Madrid and London share calendar, currency and both source systems yet use different
curves. These four values need the SME's explicit agreement per instrument, even where the answer turns
out to be "same as London".

**Sign-off:** ☐ values as shown for all instruments  ☐ values as amended (attach)  ☐ needs a working session

> **Now scoped to six instruments, not nine** (Question 1, answered 2026-09-21) — so this is
> **24 values**, not 36. Still `NOT NULL`, still per instrument, still blocking step 6.

---

## Question 3 — Error limit per instrument, and book scope

### 3a. `LIMIT_ERRORS` — a risk parameter, and the default is dangerous

`[confirmed: source, 2026-09-21]` Each (branch, instrument) needs a row giving the number of **failed
deals tolerated in a single load run**. Above it, the load aborts; below it, the failed deal is skipped
and the run continues.

⛔ **If the row is missing, the limit defaults to `0` — the first failed deal aborts the entire load for
that instrument.** So a row is **mandatory** for every instrument chosen in Question 1; this is not an
optional tuning parameter.

It is a **per-run** tolerance, not cumulative across days.

> ### 🔄 How we now propose these — changed 2026-09-21
>
> `[stated: Edouard, 2026-09-21]` **We propose London's (SLB's) limit for each of your six instruments**
> — the same instrument, one for one — and you accept or change it. We are **not** deriving these from
> NY_SCH's GBO configuration. [ADR 0004](../../../docs/decisions/0004-step12-limits-from-reference-branch.md)
> records why that is legitimate for this column and for no other.
>
> ⚠️ **Please read these as a starting point, not a recommendation.** London's limits reflect London's
> volumes and data quality; nobody has looked at NY's. Both ways of being wrong are quiet:
>
> | Set too high | Failed deals are skipped and the run **reports success** — missing deals, no alarm |
> | Set too low | The **first** bad deal aborts the entire load for that instrument |
>
> **"Needs volume data first" is a perfectly good answer** and we would rather have it than a number
> nobody examined.
>
> | Instrument | London's limit | NY_SCH | |
> |---|---|---|---|
> | Swap | *(to fill from Q-13)* | | ☐ accept ☐ change to ____ |
> | Deposit & Loan | *(to fill from Q-13)* | | ☐ accept ☐ change to ____ |
> | Cross Currency Swap | *(to fill from Q-13)* | | ☐ accept ☐ change to ____ |
> | OTC Option | *(to fill from Q-13)* | | ☐ accept ☐ change to ____ |
> | Caps And Floors | *(to fill from Q-13)* | | ☐ accept ☐ change to ____ |
> | CDS (Credit Derivatives) | ⛔ *may not exist — check* | | ☐ accept ☐ change to ____ |
>
> *An earlier draft used 115 for Cross Currency Swap and 100 for the others, also from London, but
> unattributed and never decided. Run Q-13 and fill the column above from the data rather than reusing
> those numbers.*

**Sign-off:** ☐ as proposed  ☐ as amended above  ☐ needs volume data first

### 3b. Book scope — and what we cannot check

BOX FE runs processing partitioned by **(book, instrument, branch)**, and a row is needed per
combination. A missing row means that combination is **silently never scheduled** — no error, no
warning.

⚠️ **We cannot verify this answer is complete.** There is no mapping in BOX between books and folders,
so there is no query that proves a branch's book list covers all of its trades. Question 1's instrument
scope can be checked; **this one cannot.** It rests entirely on your judgement, which is why it is
called out rather than buried.

**Sign-off:** ☐ the book list attached  ☐ same books as the reference branch, per instrument  ☐ needs a working session

---

## Signature

| | |
|---|---|
| **Name** | |
| **Role** | |
| **Date** | |

Returned answers are recorded in `02-findings.md` as `[stated: <name>, <date>]` against each affected
walk step. Anything left unanswered stays `SME_DECISION_REQUIRED` and **no SQL is generated for it** —
the walk does not proceed on an assumed scope.

---

### For the run, not the SME

| | |
|---|---|
| Blocks | walk steps **6** (Accrual), **11** (Book), **12** (Allowed Errors) — and therefore the findings table as a whole |
| Prepared from | Q-05c against a reference branch; the DDL `NOT NULL` sets (2026-09-21); `PKG_FE_DATADEAL_LOAD`'s `LIMIT_ERRORS` read |
| Before sending | run the Question 2 query and paste its output in; without it the SME is being asked to sign column names, not values |
| Related | [`book-and-folder.md`](../../../docs/reference/book-and-folder.md) for why 3b cannot be verified · charter *Human checkpoints* |
