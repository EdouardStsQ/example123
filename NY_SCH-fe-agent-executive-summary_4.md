# BOX FE configuration for a new branch — what the agent does, and what's still open

**For review by a BOX FE developer.** First case: **NY_SCH**. Rev. 3 — 2026-09-18.

We have built an agent (`sigom-box-fe-configs-agent`) that produces the **reviewed, runnable SQL** to
configure a branch in BOX FE. It does not write to any database — a human runs the SQL after sign-off.

> **What changed in rev. 3.** The first rehearsal run found a defect in our own query catalogue: we
> had the Accrual tab's instrument join pointing at the wrong table, and an inner join was silently
> dropping two of SLB's nine instruments. Corrected, and question F below is rewritten around it.
>
> **What changed in rev. 2.** A BOX FE developer answered six of the eight questions in rev. 1. Two
> answers changed the design materially: the walk gained a missing step (**Allowed Errors**), and the
> PK-allocation gate is **closed** (`F___SEQUENCE`). Section 4 carries what is still open, including
> two questions from rev. 1 that were not answered and one the developer flagged as not fully
> understood on the BOX side either.

---

## 1. Method in one paragraph

A branch that is live in GBO already has its configuration there. So for each BOX FE configuration
object we read the equivalent GBO (`DEVENG.T_PGT_*`) row, propose the BOX (`BOX_FE.T_BOX_*`)
equivalent, have a named SME confirm it, and only then generate the `INSERT`. Nothing is copied from
another branch, and nothing is invented. The one exception is **instrument scope**: which instruments
the branch gets is chosen from what is already live in BOX, by an SME — not read from the branch's GBO
instrument configuration. A branch's current instrument set is read from its **Accrual tab**
(`T_BOX_ENGACCRCONF_S`, one row per instrument) — confirmed 2026-09-17.

---

## 2. The walk — 14 configuration objects, in dependency order

| # | Object | BOX FE table | GBO source |
|---|---|---|---|
| 1 | FE configuration association — **read**, reuse or new? | `T_BOX_ENGCONF_X` | — |
| 2 | MIS Generic header | `T_BOX_ENGCONF_S` | `T_PGT_ENGCONF_S` |
| 3 | Fixing Curve header | `T_BOX_ENGFCURVE_S` | `T_PGT_ENGFCURVE_S` |
| 4 | Curve → quote reference linkage | `T_BOX_ENGLKFC_X` | `T_PGT_ENGLKFC_X` |
| 5 | Branch association row — **write** | `T_BOX_ENGCONF_X` | (`T_PGT_BRANCH_S`) |
| 6 | Accrual defaults — **and the branch's instrument list** (`FK_INSTRUMENT` → `T_PGT_SUB_PRODUCT_S`) | `T_BOX_ENGACCRCONF_S` | `T_PGT_ENGACCRCONF_S` |
| 7 | Accrual Exceptions | `T_BOX_CONFIG_ACCRUAL_S` | `T_PGT_CONFIG_ACCRUAL_S` |
| 8 | Fixing Exceptions | `T_BOX_FIXING_BY_INSTR_S` + `V_BOX_PROC_INSTR_S` | `T_PGT_FIXING_BY_INSTR_S` |
| 9 | Yield Curve — *empty in Tier 1 PRE, parked* | `T_BOX_ENGZCCONF_S` | `T_PGT_ENGZCCONF_S` |
| 10 | Currency Basis — *empty in Tier 1 PRE, parked* | `T_BOX_ENGCURRENCYBASIS_S` | `T_PGT_ENGCURRENCYBASIS_S` |
| 11 | Book — FE batch execution registration | `T_BOX_CONF_BY_BOOK_S` | **none** — BOX-only |
| 12 | **Allowed Errors** — error limit per branch × instrument · *added 2026-09-17* | `T_BOX_ERRORS_FE_S` | unknown |
| 13 | Derived — **verify, never INSERT** | `T_BOX_FIXING_ASSIGNMENT_S`, `T_BOX_BRPROCCAL_S` | — |
| 14 | Not branch-scoped — **confirmed global, nothing to do** | `T_BOX_ENGDAYS_MATURED_S`, `T_BOX_ENGSETUP_S` | — |

Order matters because the schema **declares no foreign-key constraints at all** — only primary-key and
check constraints. The dependency order above is therefore *derived*, not read from the data
dictionary. Steps 6, 11 and 12 are all keyed by instrument, so their row counts should agree with each
other and with the confirmed scope.

---

## 3. Five gates — no SQL is written until all pass

| Gate | Condition | Status for NY_SCH |
|---|---|---|
| 0a | Branch exists in GBO, `BRANCH_PK` resolved | ✅ Tier 2: `20007.4`, entity `31398.4`, currency `159.4`, calendar `83.4` |
| 0b | `FK_MISCONFIG` resolved to the branch's GBO MIS header | ✅ Tier 2: branch-config `141.35` → `FK_MISCONFIG 64408.35` → *"Configuracion -NY"* |
| 0c | Instrument scope, from a named SME, in writing | ⛔ **Open** — the question is now concrete: SLB has nine instruments; does NY_SCH get those nine or a subset? |
| 0d | PK generation mechanism known | ✅ **RESOLVED 2026-09-17** — `F___SEQUENCE` |
| 0e | Target schema complete in the run environment | ⛔ Blocked on a Tier 2 account with `BOX_FE` grants |

### How PKs are allocated — for the record, since it shapes every statement we emit

`F___SEQUENCE(TABLE_NAME, seq_range)` takes `NEXTVAL` from **`SQ_BOX_FINANENG1`** for every table in
this walk, then — with `seq_range = 'X'` — adds the environment's auth code as a fractional part
(`auth_code / 10^length(auth_code)`, read from `gom_glb_sys.t__CORE_INFO_S`). So the agent emits:

```sql
DECLARE
  v_pk_engconf NUMBER;
BEGIN
  v_pk_engconf := F___SEQUENCE('T_BOX_ENGCONF_S','X');
  INSERT INTO BOX_FE.T_BOX_ENGCONF_S (PK, …) VALUES (v_pk_engconf, …);
  -- child rows reference v_pk_engconf, never a literal
END;
```

Never a literal PK, and never a bare `SQ_BOX_FINANENG1.NEXTVAL` — that would drop the auth-code
fraction. A useful side effect: because the auth code is read from the target at execution time, the
same script produces correctly-suffixed PKs in Tier 1 and Tier 2 without editing.

---

## 4. What's still open

**A — Not answered in rev. 1, and now more urgent.** In BOX-DEV screenshots, the `Branch` column on
**Accrual Exceptions and Allowed Errors** holds **product-shaped values** (`BOX CCS`, `BOX FX`,
`BOX IRS`) rather than geographic branches. Our whole model assumes FE configuration keys to a
geographic branch. This mattered before; now that Allowed Errors is **walk step 12**, it sits inside the
walk rather than beside it — if "branch" means a product on that screen, step 12's grain is wrong. It
is also not only a config-screen quirk: the FE Process Calendar (`T_BOX_BRPROCCAL_S`) shows a row
scheduled against Branch `BOX COMMODITIES` for instrument `COMM_SWAP`. **Is this a dev-environment
convention, or does "branch" genuinely mean something different here?**

**B — Allowed Errors, the new step.** Three things we don't know: does a **GBO counterpart** exist (the
naming rule would predict `T_PGT_ERRORS_FE_S`, but that's a guess)? What are the **branch and instrument
column names**? And what is a **safe default limit** — an error threshold is a risk parameter, so we'd
rather have it from you than infer it from a reference branch.

**C — Book (`T_BOX_CONF_BY_BOOK_S`).** You told us at least one row per instrument is needed (hence the
`0 - EMPTY` rows), and that the safest approach is to mirror a branch that trades the same instrument,
confirming Book/Label values. We've built both rules in. You also said the table's exact purpose isn't
fully clear — we've recorded that honestly rather than smoothing it over, and the agent treats
proposals here as requiring an SME decision rather than deriving them. **If anyone can explain what a
row in this table actually causes at runtime, that's the single best thing that could happen to this
step.**

**D — Yield Curve and Currency Basis (steps 9, 10), parked.** Both empty in Tier 1 PRE. We've taken
"they probably don't matter" as the working read but *not* recorded them as unnecessary, because
nobody has said so and because an assumed `FK_PARENT` join can't be validated against an empty table.
The agent emits no INSERT for them and flags them. **Cheapest check: are they populated in Tier 1 PRO?**
One populated row would settle both the join and the purpose.

**E — `T_BOX_FIXING_ASSIGNMENT_S`.** You confirmed `T_BOX_BRPROCCAL_S` is derived; this one was left as
to-be-confirmed. We write to neither, so nothing is at risk — but the status matters for the findings
table. **Is it derived too?**

**F — Two of SLB's nine instruments don't resolve to a Sub-Product row.** Mostly self-answered, but
worth a sanity check. `T_BOX_ENGACCRCONF_S.FK_INSTRUMENT` resolves to `PGT_SYS.T_PGT_SUB_PRODUCT_S.PK`
— we had this wrong initially and have corrected it. Joining that way, SLB returns **seven** rows;
the SIGOM Accrual tab shows **nine**. The two that disappear are **Credit Derivatives** and **Bond
Return Swap**, whose `FK_INSTRUMENT` values find no Sub-Product row (every resolved one carries the
`.4` global-reference suffix). **Is that expected for newer products, and where should their
Sub-Product rows live?** It also explains our old 7-vs-9 discrepancy: the 7 in our baseline was almost
certainly measured with the same inner join.

---

## 5. What the agent will never do

It never invents a value. Every value is read from the database, given by a named SME, a documented
constant, or explicitly labelled `DERIVED` with its rule attached — and a `DERIVED` value is never
recorded as confirmed and needs its own sign-off. It never fabricates a primary key: it calls
`F___SEQUENCE` and lets the database allocate. It never writes DDL — if a table is missing it locates
the authoritative `CREATE` in `cib-boxfin-dbboxfe` and cites the path, because a reverse-engineered
table would silently lose the constraints and defaults the system depends on. It never copies values
from Madrid or London because the shape matches — those two share calendar, currency and both source
systems yet use different fixing curves, and NY is USD/New York, unlike either. It never writes to a
database. And it treats a zero-row result as a question rather than an answer: two "absences" in this
project have already turned out to be a broken join and a missing schema grant, so every query now
carries a visibility preflight and no absence is recorded without one.

---

*Feedback of the form "that table is wrong," "that join is X not Y," or "you're missing Z" is exactly
what is useful — rev. 1 produced a missing table and a closed gate from precisely that. Corrections get
recorded against the specific claim with attribution, not silently absorbed.*
