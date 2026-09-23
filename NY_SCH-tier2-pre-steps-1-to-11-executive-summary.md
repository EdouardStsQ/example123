# NY_SCH — BOX FE configuration, Tier 2 PRE: reviewer's guide to the SQL

**Accompanies:** `NY_SCH-tier2-pre-steps-1-to-11.sql` (306 lines) · **Run:** 3 of the agent ·
**Produced:** 2026-09-22 · **Target:** Tier 2 PRE

> ✅ **Reviewed with a BOX FE expert, 2026-09-23.** Seven points came back and all are adopted — see
> [ADR 0005](../../../../docs/decisions/0005-box-fe-expert-review-run-3.md). This guide is kept as sent;
> where it is now wrong (step 2's sources, step 7's branch, step 11's row count, step 14) the ADR says so.

> ⚠️ **Test output — please do not execute it.** The file was produced to test the agent end to end.
> Several scope decisions in it were taken by the person running the test rather than by the
> product-scope SME (§6), and our own review has already found defects (§7, listed so you don't spend
> time on them). **What we'd value from you is a review of the approach:** is the order right, is any
> value wrong, is anything missing.

---

## 1. In one minute

**What the agent is for.** Configuring a new branch in BOX FE by hand means recreating in `BOX_FE` the
Financial Engine configuration the branch already has in GBO — in the right order, without a single
wrong reference. These tables carry no foreign-key constraints, so a wrong reference inserts cleanly
and fails later, silently, in a batch. The agent does that derivation and records where every value
came from.

**How it works.** It reads the branch's GBO configuration in `DEVENG`, checks what already exists in
`BOX_FE`, and writes the SQL that creates the equivalent BOX rows in dependency order. Every value is
one of four things: **read** from a GBO row, **given** by a named person, a **documented constant**, or
**derived** with the rule written down.

**What it never does.** It never connects to a database — in this run a person executed every query on
a read-only account and returned the results. It never writes DDL, never invents a primary key (every
PK comes from `F___SEQUENCE`), and never commits to or raises a pull request against
`cib-boxfin-dbboxfe`. The output is a file a human reviews and then runs.

**What we'd like from you:** the seven questions in §8, ranked. *"That's wrong"* is the most useful
answer you can give.

---

## 2. How a run proceeds

| Phase | What happens | Result in this run |
|---|---|---|
| **1. Preflight** | Confirm the account can actually see both schemas, so a zero-row result means *absent* rather than *invisible* | 62 `BOX_FE` and 525 `DEVENG` tables visible |
| **2. Release gates** | Branch resolved · GBO MIS header resolved · `F___SEQUENCE` callable · target schema complete · SIGOM metamodel read for identity columns | Branch `20007.4` · MIS header `64408.35` · all passed |
| **3. Mining** | For each object: read NY's GBO rows, and check whether BOX already has any | No existing NY configuration in `BOX_FE` — a new build |
| **4. Decisions** | Scope choices that no query can answer are put to a person | See §6 |
| **5. SQL** | Statements written in dependency order; each step headed with its row count and *"If wrong:"* — what failure to look for | 73 INSERTs + 1 UPDATE + 2 procedure calls |
| **6. Checks** | A mechanical validator, then an independent review | §7 lists what the review found |

---

## 3. The walk — 15 configuration objects, in the order the SQL executes them

| # | Object | `BOX_FE` table | GBO source (`DEVENG`) | In the SQL | Rows |
|---|---|---|---|---|---|
| 1 | Does an FE configuration already cover NY? | `T_BOX_ENGCONF_X` | — | **read only** — none found, so build new | — |
| 2 | MIS configuration header | `T_BOX_ENGCONF_S` | `T_PGT_ENGCONF_S` | INSERT, **curve columns left NULL** | 1 |
| 3 | Fixing curve header | `T_BOX_ENGFCURVE_S` | `T_PGT_ENGFCURVE_S` | INSERT | 1 |
| 4 | Curve → quote references | `T_BOX_ENGLKFC_X` | `T_PGT_ENGLKFC_X` | loop | **38** |
| — | *Link header to curve* | `T_BOX_ENGCONF_S` | — | **UPDATE** `FK_CURVEMAN`, `FK_CURVEACC` | — |
| — | *Curve validation* | `pkg_engPrecommit.P_ENGFixingCurve_PreCommit` | — | call — read-only check | — |
| 4b | Curve yield-curve collection | `T_BOX_ENGFIXDISC_S` | — | not emitted — judged not needed | 0 |
| 5 | Branch association | `T_BOX_ENGCONF_X` | branch `20007.4` | INSERT | 1 |
| 6 | Accrual tab — one row per instrument | `T_BOX_ENGACCRCONF_S` | `T_PGT_ENGACCRCONF_S` | 6 INSERTs | **6** |
| 7 | Accrual exceptions | `T_BOX_CONFIG_ACCRUAL_S` | `T_PGT_CONFIG_ACCRUAL_S` | loop | **20** |
| 8 | Fixing exceptions | `T_BOX_FIXING_BY_INSTR_S` | `T_PGT_FIXING_BY_INSTR_S` | none — NY's GBO has no rows | 0 |
| 9 | Yield curve | `T_BOX_ENGZCCONF_S` | `T_PGT_ENGZCCONF_S` | not emitted — NY's GBO has no rows | 0 |
| 10 | Currency basis | `T_BOX_ENGCURRENCYBASIS_S` | `T_PGT_ENGCURRENCYBASIS_S` | not emitted — ⚠️ **NY's GBO has 124 rows**, see question E | 0 |
| 11 | Book — batch registration | `T_BOX_CONF_BY_BOOK_S` | **no GBO equivalent** | loop, one per instrument | **6** |
| 12 | Allowed errors | `T_BOX_ERRORS_FE_S` | `T_PGT_ERRORS_FE_S` | not emitted — identity unresolved, see §7 | 0 |
| — | *Configuration pre-commit* | `PKG_ENGPRECOMMIT.p_check_Val_Curves_precommit` | — | call — **writes and COMMITs** | — |
| 13 | Derived — fixing assignment, process calendar | `T_BOX_FIXING_ASSIGNMENT_S`, `T_BOX_BRPROCCAL_S` | — | verify only, never inserted | — |
| 14 | Not branch-scoped | `T_BOX_ENGDAYS_MATURED_S`, `T_BOX_ENGSETUP_S` | — | verify only — no branch column | — |

The end of the file holds a cleanup template (`DELETE`s in reverse order) — see §7, item 7. Each step in the SQL opens with a comment header naming the step number, so the table maps directly onto the file.

### The values, and where each came from

| Step | Column | Value | Source |
|---|---|---|---|
| 2 | `DESCRIPTION` | `'Configuracion -NY'` | NY's GBO MIS header `64408.35` |
| 2 | `FK_CALENDAR` · `FK_CURRENCY` | `83.4` · `159.4` | same |
| 2 | `FK_SOURCE_FRONT` · `FK_SOURCE_BACK` | `9.4` · `11.4` | same |
| 2 | `FK_CURVEMAN` · `FK_CURVEACC` | `NULL`, then the new curve's PK | set by the UPDATE after step 4 |
| 3 | `DESCRIPTION` · `FK_CURRENCY` | `'NY Configuration Suc'` · `159.4` | NY's GBO curve. **Its GBO PK `1.35` is deliberately not copied** |
| 4 | `FK_BS` × 38 | quote-reference PKs | NY's GBO curve's quote array (`PGT_MRK`, shared) |
| 5 | `FK_BS` | `20007.4` | the NY branch |
| 6 | per instrument | `FK_FEEFIRSTDAYSEL 3.4` · `FK_INTFIRSTDAYSEL 3.4` · `INTCOMMONBASIS 1` · `BYTRIGGER 1` · `BYRESIDUAL 0` · `INTERVAL 377` · `FK_MDRBASIS NULL` · `FK_BASIS 2.4` | NY's GBO accrual rows — identical for all six instruments |
| 7 | 20 × (instrument, strategy, instrument type) | from NY's GBO exceptions | `FK_BRANCH 141.35` · `CRITERIAL 1` — **see question B** |
| 11 | `FK_LABEL` · `FK_BRANCH` | `23958.44` (book `NY001`) · `20007.4` | book chosen in the test (§6) |

**Identity columns** (`FK_OWNER_OBJ`, `FK_EXTENSION`) are supplied as seven substitution variables,
`&&QG6_*`, declared at the top of the file. SQL\*Plus or SQL Developer will prompt for them; the values come from the
SIGOM metamodel read. Base tables take `FK_EXTENSION = NULL`.

---

## 4. Order of operations — three things worth checking

**1. Header first, then curve, then UPDATE.** `T_BOX_ENGCONF_S.FK_CURVEMAN` points *at* the curve, but
the curve does not exist yet when the header is inserted. So the header goes in with those columns
NULL, the curve and its 38 quote references follow, and an UPDATE links them. The alternative is to
create the curve first. **Question A.**

**2. Two pre-commit procedures, placed by what they do.**
`P_ENGFixingCurve_PreCommit` only reads — it checks that if any currency has a yield curve, every
currency in the quote reference has one — so it runs straight after the curve is built.
`p_check_Val_Curves_precommit` back-fills null curve columns on the fixing-exception rows (step 8) and
**issues a COMMIT**, so it runs last. Step 8 has no rows here, so we expect it to find nothing to do.
**Once it runs, nothing before it can be rolled back.** **Question F.**

**3. Primary keys.** Every PK is `F___SEQUENCE('<table>','X')`, allocated immediately before its
INSERT; every child references its parent's variable, never a literal.

---

## 5. Files the run produces

| File | What it holds | Sent to you? |
|---|---|---|
| `00-inputs.md` | The run's inputs, and the preflight result | on request |
| `01-evidence/` | One CSV per query, named by query ID — the evidence behind every value | on request |
| `02-findings.md` | One row per walk object: its status, and the evidence for it | on request |
| **`03-sql/NY_SCH-tier2-pre-steps-1-to-11.sql`** | **The configuration script** | ✅ attached |
| `05-source-questions.md` | Questions the data could not answer | on request |
| `99-open-items.md` | What is unresolved, and who it is waiting on | on request |
| `00-gate-0c-signoff-request.md` | The sign-off form for the product-scope SME | on request |

**Status words used in the findings:** `CONFIRMED_ABSENT` — checked, not there · `PROPOSED` — ready for
sign-off · `EVIDENCE_REQUIRED` — cannot be established yet · `SME_DECISION_REQUIRED` — needs a person's
decision · `NOT_BRANCH_SCOPED` — the table has no branch dimension.

---

## 6. Decisions — who took them in this run, and what still needs the SME

| Decision | In this run | Needs |
|---|---|---|
| **Instrument scope** — Swap `20092.4`, Deposit & Loan `2.4`, Cross Currency Swap `20.4`, OTC Option `20111.4`, Caps And Floors `20213.4`, CDS `20313.4` | ✅ **product-scope SME**, 2026-09-21 | — |
| **Accrual values** — 4 mandatory values × 6 instruments | test decision: take NY's GBO values | ⛔ SME sign-off, and **question C** |
| **Error limits** (`LIMIT_ERRORS`) | test decision: NY's GBO value where one exists, London's otherwise. **NY's GBO holds `0` for all six** | ⛔ SME sign-off, and **question D** |
| **Book scope** | test decision: one book, `NY001`, for all six instruments | ⛔ SME sign-off. **No query can prove a book list complete** — BOX holds no book-to-folder mapping |
| **Accrual exceptions scope** (step 7) | not decided — the run emitted every GBO exception, including out-of-scope instruments | ⛔ SME: which exceptions NY carries |
| **Steps 4b, 9, 10 not needed** | test decision | ⚠️ confirm — **question E** |
| **Exceptions under branches `1651.44` / `1662.44`** excluded from step 7 as unrelated | stated in the test | ⚠️ confirm |

---

## 7. What we have already found wrong — no need to report these

1. **Step 7 includes six instruments outside the approved scope** — `8.4`, `11.4`, `13.4`, `10022.4`,
   `20134.4`, `20173.4`: six of its twenty rows. Deposit & Loan, which is in scope, has none.
2. **Step 12 is not emitted.** The agent could not resolve the identity columns for
   `T_BOX_ERRORS_FE_S` because the table is empty in Tier 2. We believe they should come from the SIGOM
   metamodel (the *Limit Error Assign* object) rather than from existing rows — see question D.
3. **Step 8 is labelled "confirmed absent"** in the findings, but NY's count and London's control count
   were both zero, which does not prove the query could have found a row.
4. **`CRITERIAL = 1`** in step 7 has no stated source.
5. **The identity values are left as substitution variables** although they were resolved, so you
   cannot check them from the file itself.
6. **No verification queries** follow the INSERTs.
7. **The cleanup `DELETE`s sit inside `IF 1 = 0`** — a template that never runs. Because the last
   procedure commits, those `DELETE`s are the only undo there is; they will become a separate, runnable
   file.
8. **Step 6's values were emitted while question C is open.**

---

## 8. Questions for you — ranked

> **A — Order.** Header with NULL curves → curve → 38 quote references → UPDATE the header. Is that
> right, or should the curve come first? Does SIGOM do something on save that this bypasses?

> **B — Step 7's `FK_BRANCH`.** *Our strongest suspicion.* The file writes `141.35` — the GBO
> branch-configuration key under which NY's exceptions are filed in `DEVENG`. Step 11 in the same file
> writes `20007.4`, the branch itself. **Which does `T_BOX_CONFIG_ACCRUAL_S.FK_BRANCH` reference?** If it
> is the branch, all twenty rows point at the wrong thing — and nothing would reject them.

> **C — Step 6's values.** Do accrual values copy straight from `T_PGT_ENGACCRCONF_S` to
> `T_BOX_ENGACCRCONF_S`, or are some columns transformed? When we compared London's GBO rows against
> London's BOX rows for the same instruments, some differed. We need to know whether that is by design.

> **D — Step 12.** NY's GBO holds `LIMIT_ERRORS = 0` for all six instruments. As we understand it, zero
> means the **first failed deal aborts the whole load** for that instrument. Is that intended for NY? And
> should the identity columns for `T_BOX_ERRORS_FE_S` come from the *Limit Error Assign* object?

> **E — Step 10, currency basis.** We judged steps 4b, 9 and 10 unnecessary, because Madrid and London
> run without them. But **NY's GBO holds 124 currency-basis rows**, and NY has Cross Currency Swap in
> scope. Does NY need currency basis configured in BOX?

> **F — Pre-commit placement.** Is calling `P_ENGFixingCurve_PreCommit` after the curve, and
> `p_check_Val_Curves_precommit` last, the sanctioned pattern for a script? Does SIGOM do anything else
> on save — audit columns, other procedures — that a script would miss?

> **G — Anything missing.** Is there anything a new branch needs in BOX FE that is not one of these
> fifteen objects? And what does `CRITERIAL` control?

---

*Corrections are the most useful thing you can give us. Each one is recorded against the specific
claim it corrects and changes the agent before the next run.*
