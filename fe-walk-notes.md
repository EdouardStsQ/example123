# BOX FE walk — per-step notes

**Reference, not a prompt.** These are the per-step details, incident histories and worked examples
behind [`sigom-box-fe-configs-agent`](../../agents/sigom-box-fe-configs-agent/AGENT.md)'s walk table.

**Read the step you are working on, not the whole file.** They were moved out of the charter on
2026-09-22 because a 1,179-line prompt was being followed selectively, and detail that fires on one
step was crowding rules that fire on every run. Nothing here is optional where it applies — it is
simply not needed until that step comes up.

---

### Reading a branch's instrument set — the Accrual tab is the answer

`[confirmed: DB via Edouard, 2026-09-17]` **The best way to check which instruments are configured for
a branch is the MIS configuration's Accrual tab — `BOX_FE.T_BOX_ENGACCRCONF_S`, one row per
instrument.** Observed directly for SLB in Tier 1: nine rows, one each for OTC Option, Cross Currency
Swap, Swap, Cash Flow Matching, Deposit & Loan, Credit Derivatives, Forward Rate Agreement, Caps And
Floors and Bond Return Swap.

**Read it with the query in the catalogue, not an improvised join.** `[confirmed: DB, 2026-09-18]`
`T_BOX_ENGACCRCONF_S.FK_INSTRUMENT` resolves to **`PGT_SYS.T_PGT_SUB_PRODUCT_S.PK`** — the Sub-Product
level of the Family→Product→Sub-Product hierarchy, the same key space
`T_BOX_CONF_BY_BOOK_S.FK_INSTRUMENT` uses. It is **not** `T_BOX_ENGINSTRUMENTS_S` (Processed
Instruments), whose PKs live in a different space entirely (`1.65`, `2.65` versus `20111.4`, `2.4`).

Three tables, three different questions — do not substitute one for another:

| Question | Table | Shape |
|---|---|---|
| What instruments does **this branch** have? — the selection | `T_BOX_ENGACCRCONF_S` (Accrual tab) | One row per instrument, per MIS configuration. **The authoritative answer** |
| What is an instrument **called**? — the label | `PGT_SYS.T_PGT_SUB_PRODUCT_S` | What `FK_INSTRUMENT` points at. `LEFT JOIN` only, for names |
| What does **BOX process** at all? — a different catalogue | `T_BOX_ENGINSTRUMENTS_S` (Processed Instruments) | Global, 18 rows, no branch dimension, **and a different key space**. Not the lookup for the Accrual tab |

**Three consequences, and they matter:**

1. **Gate 0c becomes verifiable.** "NY_SCH gets the same set as SLB" stops being an unfalsifiable SME
   statement and becomes a query: read SLB's Accrual rows and you have the list. Still get the scope
   confirmed by a named SME in writing — but now the SME confirms a **concrete enumeration** rather
   than a phrase, and a reference branch's set can be put in front of them. **Count the base table
   before labelling it** — see Q-05c; an inner join to the Sub-Product table made two of SLB's nine
   instruments disappear. **That is a statement about the join, not about the instruments**: Credit
   Derivatives is in `T_PGT_SUB_PRODUCT_S` as `20313.4` `[confirmed: DB via Edouard, 2026-09-22]`, and
   an earlier reading of that result as "the instrument has no row" was an inference wrongly tagged
   `[confirmed]` — corrected in
   [`confirmed-joins.md`](../../docs/reference/confirmed-joins.md).
> ### ⛔ Step 6's *values* come from the branch's own GBO row `[corrected 2026-09-22]`
>
> **Gate 0c chooses *which* instruments. It does not choose their values.** For each in-scope
> instrument, the four `NOT NULL` accrual values and the rest of the row are **mined from the branch's
> own `DEVENG.T_PGT_ENGACCRCONF_S` row** — Q-05, `WHERE FK_PARENT = <the branch's GBO MIS header>`.
>
> **Present the reference branch alongside, never instead.** The findings row for each instrument shows
> three things, and the SME decides:
>
> | Instrument | This branch's GBO value | Reference branch's value | Decision |
> |---|---|---|---|
>
> Where the two agree, the SME is confirming rather than choosing. **Where they differ, that difference
> is the finding** — and it is the whole reason the reference branch is shown.
>
> ⛔ **The 2026-09-22 run proposed the reference branch's values for five of six instruments while
> NY's own GBO rows sat in its evidence folder, mined.** That is hard rule 6, and
> [ADR 0004](../../docs/decisions/0004-step12-limits-from-reference-branch.md) explicitly does not
> extend here — it covers `LIMIT_ERRORS` and nothing else.
>
> **It produced demonstrably different values for an in-scope instrument.** `[confirmed: DB via
> Edouard, 2026-09-22]` Deposit & Loan: NY's GBO says `INTCOMMONBASIS = 1, BYTRIGGER = 1,
> BYRESIDUAL = 0, INTERVAL = 377`; SLB's BOX row says `0, 0, null, null`. **Two of those four are
> gate-0c `NOT NULL` values.**
>
> ### ⚠️ But that comparison has a confound — settle it before proposing anything
>
> It compared **NY in GBO** against **SLB in BOX**: the branch *and* the system both varied. The
> difference could be a genuine branch difference **or** a GBO→BOX transformation applied when a
> configuration is created in BOX. **Q-05d** holds the branch constant and varies only the system —
> SLB's GBO row against SLB's BOX row, both Tier 1.
>
> - **No transformation** → NY's GBO values are copied straight, `PROPOSED`.
> - **Transformation** → NY's GBO values go through the same rule, tagged **`DERIVED`** with the rule
>   written down. That is what `DERIVED` is for, and it is the walk's whole premise: the twin tables
>   are *similar, not identical*.
>
> ⛔ **Until Q-05d runs, no step-6 value is `PROPOSED`.** Copying a GBO value into BOX unexamined is
> the same class of error as copying another branch's — it just fails in a different direction.
>
> **If the branch's own GBO row is missing for an in-scope instrument**, that is a finding —
> `SME_DECISION_REQUIRED`, with the reference branch's row shown as a proposal aid — not a licence to
> copy. Where the reference branch *also* lacks the instrument, say so plainly.

2. **Walk step 6 *is* the instrument scope.** `T_BOX_ENGACCRCONF_S` was described as "Accrual
   defaults"; it is also the per-branch instrument enumeration. The number of rows inserted at step 6
   **is** `PRODUCT_BOOK_SCOPE`. That is why step 6 is blocked by gate 0c, and it makes the dependency
   far more load-bearing than the label "defaults" suggests.
3. **A reference branch is a proposal aid, never authorisation** — hard rule 6 is untouched. Reading
   SLB's set tells you what is *possible* and what a comparable branch chose. It does not authorise
   copying SLB's accrual **values** into NY_SCH, and NY is USD/New York against SLB's calendar and
   currency. Read the set; confirm it; never inherit it.

---

### Why not the SIGOM tab order

SIGOM shows the tabs as Generic, Yield Curve, Accrual, Fixing Exceptions, Accrual Exceptions,
Currency Basis, Branch, Book. Working left to right would INSERT children before parents: `Branch`
sits seventh but its row ties the configuration to the branch, and `Yield Curve` sits second though
nothing depends on it.

⚠️ **One qualification, and it cost a run.** The order above is FK-dependency order *except* between the
header (2) and the curve (3): the header points **at** the curve, so no plain-INSERT ordering satisfies
both. The curve's PK is **allocated before the header is inserted** — see *Steps 2–4* below. Everywhere
else the walk order and the script order are the same thing.

Above, the header and what it points at come first (2–5), then children in
dependency order (6–10), then **Book (11) and Allowed Errors (12) last** — each needs the association,
the instrument scope and the book scope all resolved; **14a** (Days Matured, missing instruments only)
comes last, having no parent. Steps 13 and 14b emit nothing: they are verified and ruled out.

### Notes on the steps that need them

> ## 🔄 BOX FE expert review of run 3 — 2026-09-23, what it changed per step
>
> `[stated: BOX FE expert via Edouard, 2026-09-23]` Seven points on the run-3 SQL. Recorded in full in
> [ADR 0005](../decisions/0005-box-fe-expert-review-run-3.md); the step notes below carry each one.
> **No objection was raised to the walk order** or the pre-commit placement. (Steps 2–4's
> insert-then-update was not objected to either — but it is wrong for another reason, found the same day:
> see *Steps 2–4* below.)
>
> | # | Point | Steps | Fix | Query |
> |---|---|---|---|---|
> | 1 | Auth code in the PK | all | Already added by `'X'` — now **visible and asserted** in the config script, and checked in a new verification script | Q-G3c |
> | 2 | `FK_SOURCE_BACK` always `586.4`; `FK_SOURCE_FRONT` = the branch's Murex instance (NY `513.4`) | 2 | Not mined — constant + input | Q-02c |
> | 3 | Don't list the quote refs; pick them from `DEVENG` | 4 | List **generated** from the evidence CSV (never typed), validator checks SQL = CSV, verify checks BOX = GBO. **`PK` vs `FK_BS` unresolved** | Q-04c |
> | 4 | Several branches' exceptions under one GBO config | 7 | Filter via branch config → branch; write `BRANCH_PK` | Q-06 |
> | 5 | Two rows per instrument: book + dummy book (`26391.4`) | 11 | `(books + 1) × instruments` | Q-10c |
> | 6 | Days Matured: add missing instruments, like SLB | 14a | Now an insert step | Q-12 |
> | 7 | `T_BOX_ENGSETUP_S`: nothing to configure | 14b | `NOT_BRANCH_SCOPED`, stated | Q-12 |


**Step 1 is a read; step 5 is the write.** Both touch `T_BOX_ENGCONF_X`. Step 1 asks whether an FE
configuration already covers this branch (`FK_BS = BRANCH_PK`) — the fork deciding whether the rest
is "adapt existing" or "build new". Step 5 emits the association row. A script that writes the bridge
before the header exists fails on the FK.

> **Step 5 is not blockable on "BOX-specific values not in the GBO evidence" — 2026-09-18.** A run
> blocked this step reporting that `T_BOX_ENGCONF_X` needs `FK_OWNER_OBJ` and `FK_EXTENSION` values the
> GBO evidence does not supply. That is true and it is not a blocker: those two columns are **never**
> supposed to come from GBO (hard rule 9). All four values are available —
> `FK_PARENT` = the step-2 header variable, `FK_BS` = `&&BRANCH_PK` from Q-G1, `FK_OWNER_OBJ` and
> `FK_EXTENSION` from Q-G6 against the target (`35000126.65` / `35001566.65` in Tier 1). Step 5 is the
> row that ties the whole configuration to the branch; a walk that emits steps 2–4 and 6–12 but skips
> it has produced a configuration that belongs to nobody. **If step 5 cannot be emitted, that is a
> run-stopping finding, not a line item.**

> **Step 4b — a declared tab the walk does not cover, found 2026-09-18 by gate 0g.**
> `BOX_ENG_FixingCurve.apYieldCurve` (`FK_KIND 3.1`) → `BOX_ENG_YieldCurveDiscFx` →
> `T_BOX_ENGFIXDISC_S`. Steps 3 and 4 configure the curve header and its quote array and stop.
>
> ⚠️ **Not step 9's Yield Curve** (`T_BOX_ENGZCCONF_S`, which hangs off Config as `amZeroCoupon`). Two
> "yield curve" objects at two levels — exactly how a step goes missing.
>
> **Status `EVIDENCE_REQUIRED`, parked with steps 9 and 10**, for the same reason: zero rows in Tier 1
> PRE, which is not evidence it is unnecessary. No INSERT. The cheapest check is the one already open
> for those two — **look in Tier 1 PRO**; one populated row settles all three. It is numbered 4b rather
> than renumbering the walk, because a renumber would strand every reference in the corpus.
>
> This is what gate 0g is for: it turns "did we miss an object?" from a thing someone notices into a
> set difference. Allowed Errors went unnoticed for weeks.

> ### ⛔ Steps 2–4: allocate the curve's PK first, then insert in step order `[corrected 2026-09-23]`
>
> **The header points *at* the curve**, so the curve's PK must be known before the header is inserted —
> yet the header is step 2 and the curve step 3. The 2026-09-22 answer was *insert the header with NULL
> curves, then UPDATE*. **That fails on its first INSERT:** `FK_CURVEMAN` and `FK_CURVEACC` are
> **`NOT NULL`** `[confirmed: DDL, Q-02]` — ORA-01400. Run 3 was written that way and never applied, so
> nobody saw it; an independent check of the 2026-09-23 changes did.
>
> **The resolution: a PK is a number, not a row.** Allocate both PKs first, then insert in step order:
>
> ```sql
> v_conf_pk  := F___SEQUENCE('T_BOX_ENGCONF_S','X');    chk_pk(v_conf_pk,  'T_BOX_ENGCONF_S');
> v_curve_pk := F___SEQUENCE('T_BOX_ENGFCURVE_S','X');  chk_pk(v_curve_pk, 'T_BOX_ENGFCURVE_S');
>
> -- step 2: the header, already pointing at the curve this script is about to create
> INSERT INTO BOX_FE.T_BOX_ENGCONF_S (PK, …, FK_CURVEMAN, FK_CURVEACC, …)
> VALUES (v_conf_pk, …, v_curve_pk, v_curve_pk, …);
>
> -- step 3: that curve
> INSERT INTO BOX_FE.T_BOX_ENGFCURVE_S (PK, …) VALUES (v_curve_pk, …);
>
> -- step 4: its quote-reference array …
> ```
>
> **Why this is safe with the header inserted first:** there are no foreign-key constraints (hard rule
> 12), so nothing checks the curve row exists at the header's INSERT; and it is one PL/SQL block, so a
> failure anywhere before the committing pre-commit leaves nothing behind. Step numbering is unchanged.
>
> ⚠️ **`FK_CURVEMAN` / `FK_CURVEACC` are the curve's variable, never NULL and never a literal** (hard
> rule 13). Whether the two take the same curve or two different ones is **mined from the branch's own
> GBO header** — two different GBO curves mean two BOX curves, two allocations, two arrays.
>
> Verify V3 asserts both resolve to the curve created in this run; the rollback deletes the curve's
> array, then the curve, then the header.

**Steps 3–4: the curve is an array, not a header.**
`T_BOX_ENGCONF_S.{FK_CURVEMAN|FK_CURVEACC}` → `T_BOX_ENGFCURVE_S` → `T_BOX_ENGLKFC_X.FK_BS` →
`PGT_MRK.T_PGT_QUOTE_REFERENCE_S`, which resolves `FK_QUOTESOURCE` → `T_PGT_QUOTE_SOURCE_S` and
`FK_QUOTETYPE` → `PGT_SYS.PGT_DOMAINS`. So configuring a curve means configuring its quote-reference
rows too; step 4 is a real INSERT set, not a detail of step 3.

Step 4's *mining* is simpler than the rest of the walk: `PGT_MRK` and `PGT_SYS.PGT_DOMAINS` are
shared between BOX and GBO — one copy, read identically from either side — so there's no separate
"GBO version" to find. Only the `ENGLKFC_X` linkage rows are module- and curve-specific.

Also: `Fixing Curve` appears as a SIGOM leaf under **both** `Control > Configuration` and
`Control > Historical Data`. Confirm which is being read before comparing.

> **Step 4's set is generated, never typed** `[2026-09-23, expert point 3]`. The applying account sees
> `BOX_FE` only, so the set cannot be read from `DEVENG` at apply time. Instead:
> `scripts/evidence_to_sql.py` turns Q-04c's CSV into the `sys.odcinumberlist(...)` literal; the script
> aborts if the list's length differs from the evidence count; the validator checks the list equals the
> CSV; and verify V4 compares the BOX array with GBO's in both directions. **Which column carries the quote reference is open** — the expert's query copies `PK`,
> Q-04 copies `FK_BS` — and **Q-04c must settle it before step 4 is written.** Worked SQL: Q-04c.

**Step 2 — two of the seven header columns are not GBO's to give** `[stated: BOX FE expert via
Edouard, 2026-09-23]`. `FK_SOURCE_BACK` is **`586.4` for every branch** — BOX is always the back
source. `FK_SOURCE_FRONT` is **the Murex instance the branch's trades come from** — an input
(`SOURCE_FRONT`), not a mined value; NY is Murex 3 Latam, `513.4`. Run 3 copied GBO's `9.4`/`11.4`,
which point at GBO's own source systems. Candidates and existence check: Q-02c.

**Step 7 — filter by branch, write the branch** `[stated: BOX FE expert via Edouard, 2026-09-23]`. NY's
GBO MIS configuration also carries other branches' exceptions. GBO's `FK_BRANCH` on this table is a
**branch-configuration** PK (`T_PGT_BRANCH_CONFIG_S`), BOX's is the **branch** (`T_PGT_BRANCH_S`). So:
resolve each GBO row's branch through the branch config, keep NY's, keep the approved instruments,
write `FK_BRANCH = BRANCH_PK`, and copy `CRITERIAL` from the row. Report what was filtered and why. The
rows are **generated from Q-06c's CSV** with `scripts/evidence_to_sql.py rows`, checked by the validator
(SQL = CSV) and verify V10 (BOX = GBO). The canonical query and the evidence: Q-06.

**Step 8 — two objects.** The tab is `T_BOX_FIXING_BY_INSTR_S` joined to the view
`V_BOX_PROC_INSTR_S` on `FK_INSTRUMENT = PK`. The view supplies the processed instrument; an exception
row alone carries only an FK.

**Step 13 — not INSERT targets.** `T_BOX_FIXING_ASSIGNMENT_S` is a *different table* from step 8's
`T_BOX_FIXING_BY_INSTR_S` (`box-data-model.md` lists both separately) and follows from the header's
curve selection via
`ENGCONF.{FK_CURVEACC|FK_CURVEMAN} → FIXING_ASSIGNMENT.{FK_FIXINGCURVE_ACC|FK_FIXINGCURVE_MAN}`; its
own `FK_PARENT` is a separate relationship and must never be invented. The runtime queue tables prove
branch/instrument *activity*, not configuration selection — in Tier 1 extracts zero rows had
`FK_CONFIG` or `FK_FIXCURVE` populated, so a null there is not a missing config.

**Step 11 — no GBO row to mine, confirmed by a BOX FE Developer (2026-09-11).** `T_BOX_CONF_BY_BOOK_S`
is new BOX functionality with no GBO precedent at all — not an unconfirmed name, an actual absence.
Functionally, a row here for `(branch, instrument)` is what registers that combination for the FE
batch to execute — in the developer's words, "the books which are created there for X branch and X
instrument are the ones that are executed." A missing row isn't an incomplete config value, it's that
combination never being processed, silently. Full explanation in
[`fe-branch-configuration.md`](../../docs/reference/branch-config/fe-branch-configuration.md)'s
"Book — batch execution registration" section.

This is the **first confirmed non-analogue object in the walk**, and "no GBO row" does not mean "no
evidence at all." Three sources apply, none of them GBO: (1) the **Data-Lake/Murex book enumeration**
for this branch — "the books are the books that we have in the Data Lake (Lago)" — which is the *same*
evidence-gathering `control-m-batch-layer.md` §4 step 2 already requires, not a second exercise; (2) a
**named SME decision** on which of those books need FE batch registration specifically; (3)
**structural reference** to an existing BOX branch's Book rows — never copied, hard rule 6 applies in
full. Q-10's canonical joined query gives the current BOX-side fact; that alone is not a proposal for
a new branch without (1) and (2).

> **Two rows per instrument** `[stated: BOX FE expert via Edouard, 2026-09-23]`: one per (book ×
> instrument), plus one (**dummy book** × instrument) — dummy label `26391.4` in Tier 1, verified in the
> target by Q-10c. Row count `(books + 1) × instruments`: **12** for NY with one book. Every row's
> `FK_BRANCH` is `BRANCH_PK`.

⚠️ **Do not let step 11 default to `CONFIRMED_ABSENT`** the way an ordinary missing mining result
would. Absence of a *GBO* row here is the **permanent, expected** state, not a gap to close by finding
the right query. Rows start at `EVIDENCE_REQUIRED` / `SME_DECISION_REQUIRED`. And the promising but
unverified match between `PGT_DOMAINS` labels and Control-M's `<BOOK-ABBREV>` naming
(`control-m-batch-layer.md` §3/§4) is worth flagging if seen again, not something to rely on.

**Step 14 — two tables with no branch column, and since 2026-09-23 they are treated differently.**
`[stated: BOX FE expert via Edouard, 2026-09-23]`

- **14a — `T_BOX_ENGDAYS_MATURED_S`**: `NUM_DAYS` per **instrument**, no branch column. Not branch
  config — but **every approved instrument needs a row**. Present in the target → nothing to do,
  `CONFIRMED_PRESENT`. Missing → **insert** it, `NUM_DAYS` proposed from the reference branch's
  environment (Tier 1 for SLB), `PROPOSED`, per-instrument sign-off. No row there either →
  `SME_DECISION_REQUIRED`. Row shape `PK, FK_OWNER_OBJ, DDATE, FK_INSTRUMENT, NUM_DAYS`. `DDATE` is the
  field the metamodel declares as **`DateToProcess`**; proposed `SYSDATE`, as the team writes it, and
  asked. Tier 1 holds **30 days** for every configured instrument observed
  ([`05-add-product-procedure.md`](../process/05-add-product-procedure.md) *Days Matured*) — a
  cross-check for the proposal, not its source. **Before emitting, confirm from Q-G7 whether
  `BOX_ENG_Days_Matured` declares a pre-commit** (hard rule 10); the metamodel's FE pre-commit table
  lists none for it, which is not the same as having checked. Queries: Q-12 (a)/(b).
- **14b — `T_BOX_ENGSETUP_S`**: nothing to configure. `NOT_BRANCH_SCOPED`, stated. Stays in the walk so
  its absence from the SQL is visibly deliberate.

Being instrument-keyed, **14a is blocked by gate 0c** like steps 6–12, and its INSERT is independent of
the configuration — it runs last and has no parent.

---

## Hard-rule detail moved from the charter, 2026-09-22

## Hard rules — never invent

Absolute. A violation is not a lower-quality output, it's a wrong one, and in an accounting system a
wrong config value becomes a wrong number in the books.

1. **Never fabricate a literal.** Every value is one of exactly four things: **read** from a GBO row
   (cite the query ID and CSV), **given** by a named SME (cite who and when), a **documented platform
   constant** (cite the doc), or **derived** (below). No fifth source.

2. **Derivation is allowed, and labelled.** GBO and BOX are not 1:1 — a GBO configuration doesn't
   always have a BOX counterpart with the same columns, vocabulary or grain, so a mechanical copy
   isn't always available and the agent does have to reason about the BOX equivalent. Refusing would
   just push the same judgment onto the SME with less analysis attached.
   What makes a derived value legitimate is that a reviewer can see where it came from and disagree:
   - **The rule is written down** in the statement's annotation: which GBO row(s), what
     transformation, and where the rule came from (SME / doc / the agent's own reasoning — say which).
   - **Tagged `DERIVED`, never `CONFIRMED`.** Different claims; never collapse them.
   - **Its own explicit sign-off.** A `DERIVED` row may not ride along in a batch approval of
     confirmed rows.

   Distinguish **structural** derivation (GBO has accrual rows for these eight instruments, so BOX
   needs rows for the same eight — identities looked up, not chosen) from **value** derivation
   (choosing a BOX value not present in GBO — actual judgment). Never present the second as the first.

3. **Never fabricate a primary key — call `F___SEQUENCE` instead.** ✅ **Gate 0d is RESOLVED, 2026-09-17.**
   `[confirmed: source via BOX FE Developer]` PKs are allocated by a database function:

   ```sql
   F___SEQUENCE( TABLE_NAME VARCHAR2, seq_range VARCHAR2 ) RETURN NUMBER
   ```

   It takes `NEXTVAL` from **`SQ_BOX_FINANENG1`** for every table in this walk (`SQ_BOX_FINANENG3` is
   used only for `T_BOX_ENGPROCESS_S` and `T_BOX_ENGDOM_S`, neither of which we write), then — when
   `seq_range = 'X'` — adds the environment's **auth code as a fractional part**: `auth_code` from
   `gom_glb_sys.t__CORE_INFO_S`, divided by `10^length(auth_code)`. Auth code `21` gives `+0.21`,
   `4` gives `+0.4`. That accounts for every PK suffix this repo has recorded, and the integer coming
   from a **shared sequence** is why PK integer parts are large and non-contiguous within one table.
   Worked examples: [`sigom-reference.md`](../../docs/reference/sigom-reference.md).

   **The rule for this agent: never compute a PK, call the function.** Assign it to a variable so
   children can reference their parent:

   ```sql
   DECLARE
     v_pk_engconf   NUMBER;
     v_pk_fcurve    NUMBER;
   BEGIN
     v_pk_engconf := F___SEQUENCE('T_BOX_ENGCONF_S','X');
     INSERT INTO BOX_FE.T_BOX_ENGCONF_S (PK, …) VALUES (v_pk_engconf, …);

     v_pk_fcurve  := F___SEQUENCE('T_BOX_ENGFCURVE_S','X');
     INSERT INTO BOX_FE.T_BOX_ENGFCURVE_S (PK, …) VALUES (v_pk_fcurve, …);
     -- children reference v_pk_engconf / v_pk_fcurve, never a literal
   END;
   ```

   A literal PK in generated SQL is still a hard failure. The agent does not know the number and must
   not act as though it does — it delegates allocation to the database, which is strictly safer than
   any value it could construct.

   **Two consequences worth holding onto.** First, the same SQL is **environment-portable**: the auth
   code is read from the target environment at execution time, so a script written against Tier 1
   produces correctly-suffixed Tier 2 PKs without edit. Second, a row's suffix records **which
   environment allocated it**, not who owns it — see the auth-code correction in
   [`sigom-reference.md`](../../docs/reference/sigom-reference.md).

   **Still open — the export/import path.** `[open-question]` The team's add-a-book runbook
   ([`docs/process/04-add-book-procedure.md`](../../docs/process/04-add-book-procedure.md) §2.5)
   describes configuring the Book in the SIGOM MIS screen and exporting *"the book configuration file
   **with dynamic pk** to insert it into the environments"*. `F___SEQUENCE` explains what "dynamic pk"
   computes; it does not settle whether Book configuration is **promoted** that way as a matter of
   process. Confirm which path applies for step 11 before generating SQL for it.

4. **Never author DDL.** See *Schema gaps* below. Sourced, attributed DDL in a separate provisioning
   artifact is fine; authored DDL never is, and neither ever goes in the config script.

5. **Never write GBO — and never write the deployment repos.** GBO is the source being read; any
   GBO-side gap is a proposed handoff blocked on the resulting GBO record.

   The same rule covers source code. **`cib-boxfin-dbboxfe` and `cib-boxacc-dbboxacc` are read-only:
   no commit, branch, push, pull request or local edit, ever** — including when the agent is confident
   the code is wrong. A defect found there is a finding in `05-source-questions.md` with its file:line,
   and an escalation. See *Source questions* below. `[stated: Edouard, 2026-09-21]`

6. **Never copy a value across branches because the shape matches.** The Tier 1 ESP and SLB
   configurations share calendar, currency **and** both source systems, yet use distinct fixing
   curves. Values don't transfer even within one tier. A same-shaped analogue is a proposal aid and
   evidence of what's possible; never authorisation.

   **The same rule forbids unblocking a step by substitution.** Never load one environment's data
   into another, and never substitute the target's equivalent of a value that will not resolve. For
   market data that would silently repoint a branch at the wrong pricing source. Reading a reference
   environment's *column list* to learn a table's shape is fine; reading its *rows* into the branch's
   configuration is this rule.

7. **Never target production first.** Reference environment → target PRE, verified → production.
   Environment is part of a run's identity, not a footnote.

8. **Before recording an absence, prove the query could have returned a presence.** A zero-row result
   proves nothing on its own — it is equally consistent with the thing being absent, the query being
   wrong, and the account being unable to see it. Never write `CONFIRMED_ABSENT` until the access path
   itself has been demonstrated to work.

   **Six mechanisms produce a false zero. Every one of them has happened here.**

   | # | Mechanism | The rule | The incident |
   |---|---|---|---|
   | 1 | **No known-good control** | Run the same query against something that *must* return rows — a live, fully-configured branch. An empty control means the query is broken, not the data | Q-G2 levels 2–3 returned nothing for NY_SCH, recorded as a real absence — then returned nothing for **Madrid** too |
   | 2 | **No visibility preflight** | `SELECT USER, SYS_CONTEXT('USERENV','DB_NAME'), COUNT(*) FROM ALL_TABLES WHERE OWNER='BOX_FE'` in the same session, attached to the run folder. Zero visible objects means **blind, not empty**. See Q-G4's **Preflight**; a result whose preflight was not run is not evidence | Q-G4 reported Tier 2 PRE missing many `BOX_FE` tables — from an account with no grants there |
   | 3 | **An `INNER JOIN` that drops rows** | When a query's job is to **enumerate a set**, count the base table with no join at all, then `LEFT JOIN` for labels and flag unmatched rows. A row that cannot be labelled is a finding, never a row to drop | Q-05c returned seven of SLB's nine instruments and looked entirely plausible |
   | 4 | **A missing or improvised predicate** | A catalogue query confirmed as a *join* is not thereby a *mining query*. **If it lacks the predicate the step needs, report the gap — do not fill the blank** | Q-04 had no `WHERE` for one curve; the agent added one on the only column it could see, the wrong side of the bridge |
   | 5 | **A diagnostic filtered by its own expected answer** | Constraining the column that holds the value being discovered can only confirm or fail to confirm a guess. **For a discovery question, `SELECT *` and read what comes back** — narrowing is for verifying an answer you already have | "Who can execute `F___SEQUENCE`?" asked as `… AND GRANTEE IN (<guess>)` reported a gate open; unfiltered it returned **seven grantees** |
   | 6 | **An identifier predicated on a guessed string** | Where a registry is small enough to list, **enumerate and pick a row** — see Q-G1b | Branch codes guessed wrong three times (`SLB`, `ESP`, `LONDON`; the values are `MADRID`, `LND BRANCH`) |

   **Before assuming a join, check whether the repo already confirmed it.**
   [`docs/reference/confirmed-joins.md`](../../docs/reference/confirmed-joins.md) — one page, every
   confirmed FK relationship and identifier, plus the known-broken and known-unconfirmed ones. Q-05c's
   join was invented when it had been documented a week earlier; Q-04's filter was invented when the
   `_X` convention was already evidenced on two other tables. Flagging an assumption is necessary and
   does not substitute for looking. Add to that page whenever a run confirms something new — a fact
   recorded only where it was discovered gets missed again, which has now happened three times. Several
   catalogue queries still rest on an assumed join column (the catalogue's Coverage check lists them);
   treat each as a live instance of this rule.

   **Every child of the MIS header is mined `WHERE FK_PARENT = <GBO config PK>`** — steps 6, 7, 8, 9
   and 10. Q-07 shipped without that filter and was narrowed with a `MIN(PK)` subquery instead, which
   returned an arbitrary configuration's rows rather than the branch's. **A subquery standing in for a
   missing filter is the tell**: it makes an unfiltered query look answered.

   **`PGT_DOMAINS` is a shared registry — never enumerate it without `FK_OWNER_OBJ`.** Dozens of
   unrelated enumerations live in that one table. Joining a known PK to get a label is fine; listing
   values without the discriminator returns someone else's domain.

   **The `_X` bridge-table convention, since it has caused one defect.** On any `_X` table, `FK_PARENT`
   points **up** to the owning object and `FK_BS` points **across** to the linked one. So **filter on
   `FK_PARENT`, join on `FK_BS`** — never the reverse. Confirmed on `T_BOX_ENGCONF_X`,
   `T_BOX_LINK_ARRAY_X` and `T_*_ENGLKFC_X`; see the catalogue's Q-04. On `T_BOX_LINK_ARRAY_X`, which
   holds 17 relationships across 9 objects, the filter is `(FK_OWNER_OBJ, FK_EXTENSION, FK_PARENT)` —
   anything less returns rows from unrelated arrays that look entirely reasonable.

9. **Never carry a SIGOM identity column across from the source.** `FK_OWNER_OBJ` and `FK_EXTENSION`
   are properties of the **destination**, not values to mine. `[confirmed: DB via Edouard, 2026-09-18]`

   `FK_OWNER_OBJ` is **the screen the row is edited through**; `FK_EXTENSION` is **which tab within it**.
   A `SELECT … FROM DEVENG.T_PGT_*` feeding an `INSERT INTO BOX_FE.T_BOX_*` that includes these columns
   writes the GBO object's identity into a BOX row — `DEVENG.T_PGT_ENGCONF_S` carries `12198.4` on every
   row, the GBO Financial Engine's own object.

   **They are not one constant across the walk.** The walk spans **three screens**: `BOX_ENG_Config`
   (`35000126.65`), `BOX_ENG_FixingCurve` (`35000123.65`) and the standalone `BOX - Limit Error Assign`
   (`35000289.65`). A single constant applied to every INSERT is wrong for steps 3, 4 and 12.

   **Derive them from the metamodel, don't guess and don't hard-code** — base table → the object's PK
   with a NULL extension; extension table → the extension's `FK_PARENT` with the extension's own PK.
   Q-G6, no `BOX_FE` read required. Full rule and its validation:
   [`docs/reference/sigom-metamodel.md`](../../docs/reference/sigom-metamodel.md) §3.

   **The general form of this rule, which is the part worth carrying:** a GBO row and its BOX twin are
   not the same row in two schemas. Three kinds of column behave differently in the copy, and
   distinguishing them is the whole job of step 2 onward:

   | Kind | Example | Where the value comes from |
   |---|---|---|
   | **Mined** — the branch's actual configuration | `DESCRIPTION`, `FK_CALENDAR`, `FK_CURRENCY` | the GBO row |
   | **Allocated** — this row's own identity | `PK` | `F___SEQUENCE`, hard rule 3 |
   | **Structural** — the destination's own identity | `FK_OWNER_OBJ`, `FK_EXTENSION` | the target table, Q-G6 |

   `SELECT *`-shaped INSERTs collapse all three. **Write an explicit column list for every INSERT**,
   and be able to say which of the three kinds each column is. A column you cannot classify is a finding,
   not a column to copy.

   **And a fourth kind that is not a column at all.** Q-G7 returns a `FK_KIND` per declared field.
   **`6.1` is a flag and `11.1` (`sql…`) is a screen filter parameter — `11.1` is not stored anywhere.**
   Treating either as an INSERT column writes a value into a column that does not exist, or a screen
   control into data. The taxonomy is in
   [`sigom-metamodel.md`](../../docs/reference/sigom-metamodel.md) §4; read the kind before the name.

   **The declared field list settles which columns are mined.** Q-G7 returns every field an object has.
   `BOX_ENG_Config` declares seven with values — `pLocalCurrency`, `pCalendar`, `Description`,
   `FixingCurveMan`, `FixingCurveAcc`, `SourceFront`, `SourceBack` — which is exactly step 2's mining
   list. `FK_OWNER_OBJ`, `FK_EXTENSION` and `FK_PARENT` are not fields of the object at all. Don't
   negotiate the exclusion list; look it up.

10. **The INSERT is not the whole operation — call the pre-commit procedure.** `[confirmed: DB,
    2026-09-18]` SIGOM objects can declare `PRE_COMMIT_PROC` / `FK_PRECOMMIT`.

    > **857 objects across SIGOM declare one, in 172 packages** `[confirmed: DB, 2026-09-21]`. **This is
    > how SIGOM works, not a quirk of the FE module. Assume an object runs code on save until you have
    > checked that it does not** — and check **both** columns, since either can be null while the other
    > is set.

    **Five of the walk's objects declare one**, covering steps 2, 3, 4, 5 and 6 — and probably 7–11,
    because `p_check_Val_Curves_precommit` fires on the `BOX_ENG_Config` *screen* and every `am…`
    collection of Config is edited through it. Confirmed for step 6; inferred for 7–11. One measurement
    settles it: Q-G6 across all walk tables, grouped by `FK_OWNER_OBJ`.

    | Object | Steps | Procedure |
    |---|---|---|
    | `BOX_ENG_Config` | 2, 5, 6 | `PKG_ENGPRECOMMIT.p_check_Val_Curves_precommit(pk)` |
    | `BOX_ENG_FixingCurve` | 3, 4 | `pkg_engPrecommit.P_ENGFixingCurve_PreCommit(pk)` |

    Each takes `(pk IN NUMBER)` — the PK of a row that already exists — and is `AUTHID DEFINER`, so the
    executing account needs no extra grants.

    > ### ⛔ Classify the procedure before calling it — corrected 2026-09-21
    >
    > An earlier version of this rule said "call the procedure after each affected INSERT". That is
    > wrong for one of them and dangerous for the script. **Read the body first and classify it.**
    > `[confirmed: source via Devin, 2026-09-21]`
    >
    > | Class | Example | What the script does |
    > |---|---|---|
    > | **No DML** | `P_ENGFixingCurve_PreCommit` — SELECTs only, raises `-20001` on failure | Call it as a validation gate. Safe anywhere |
    > | **Same-row DML** | ACC's `p_StatusPortFolio`, `p_AccountPrecommit`, `p_TopicsPreCommit` | **Do not supply the columns it computes.** Call it, then read the row back |
    > | **⛔ Cross-table DML, and it COMMITs** | `p_check_Val_Curves_precommit` | See below — **never call it inside a transaction you intend to roll back** |
    >
    > **`p_check_Val_Curves_precommit` is the dangerous one.** Passed the step-2 header PK, it UPDATEs
    > **step 8's table** — `T_BOX_FIXING_BY_INSTR_S WHERE fk_parent = pk_in` — back-filling null
    > `fk_fixingcurve_acc` / `fk_fixingcurve_man` from the header's defaults, and it issues an explicit
    > **`COMMIT`** after each of its three conditional UPDATEs.
    >
    > **The safe pattern: make it a no-op, then call it to prove that.** The UPDATEs fire only on
    > *null* curves. So the agent populates step 8's rows with their curve values at INSERT time —
    > filling any GBO null from the configuration header and labelling it **`DERIVED`**, with the rule
    > citable from source. Then call the procedure. If it changes nothing it commits nothing, **and the
    > fact that it found nothing to do is positive evidence the INSERT set already matched SIGOM.**
    > That is what procedure step F3 has always been asking for.

    **This is the concrete answer to "would SIGOM have done exactly this?"** — the question the human
    checkpoint below has always asked and never had a method for. Before a walk runs against a new
    schema, check `PRE_COMMIT_PROC` on every object it writes (Q-G7) and read the body from
    `cib-boxfin-dbboxfe`; `ALL_SOURCE` shows the spec only, never the body. An unread pre-commit
    procedure on a step that emits SQL is `EVIDENCE_REQUIRED`, not a footnote.

11. **The script's `ROLLBACK` is not a safety net, and must never be presented as one.**
    `[confirmed: source, 2026-09-21]` At least one pre-commit procedure in this walk issues an explicit
    `COMMIT`. A committing procedure commits **the entire outstanding transaction**, including every
    INSERT the script has performed up to that point.

    So: **the rollback `DELETE`s (procedure step E3) are the real undo**, not the trailing `ROLLBACK`,
    and they must be correct and tested. Any run plan that says "execute it, look, roll back" is only
    valid for a statement set containing no committing procedure — which must be *stated*, not assumed.

    The same applies to the empirical F3 test: **snapshot → INSERT → call → re-snapshot → `ROLLBACK`
    cannot be used on a committing procedure.** Use the make-it-a-no-op pattern above instead.

12. **No database constraint will catch a wrong FK.** `[confirmed: DDL via Devin, 2026-09-21]` Across
    all thirteen walk and ACC config tables there is **not one `FOREIGN KEY`, `CHECK` or `DEFAULT`**.
    Every `FK_*` column is a plain `NUMBER`; referential integrity is entirely application-layer.

    Two consequences the agent must act on:

    - **The metamodel is the only source of truth for the join graph** — there is no dictionary copy to
      check against. That is what gate 0g is for, and why a join asserted without Q-G7 is a defect
      rather than a style point.
    - **A wrong FK inserts cleanly and fails silently later**, in a batch, far from the cause. Getting
      the target right *before* the INSERT is the only defence there is.

    What the DDL *does* constrain, and the agent must respect: **`NOT NULL` column sets** (the minimum
    INSERT list per step) and **unique indexes** — including `UNIQUE` on `T_BOX_ENGCONF_S.DESCRIPTION`
    and `T_BOX_ENGFCURVE_S.DESCRIPTION`, which are **global, not per-branch**. A mined description that
    already exists is a hard failure; see the catalogue's Q-02/Q-03 pre-flight.

13. **A mined FK is one of three kinds, and only one of them is copied.** `[confirmed: run defect,
    2026-09-22]` Every value that comes out of mining falls into exactly one of these, and writing the
    wrong kind into the target is the failure mode this walk exists to prevent:

    | Kind | Example | What the INSERT carries |
    |---|---|---|
    | **Reference FK** — points at a pre-existing shared object | `FK_CALENDAR = 83.4`, `FK_CURRENCY = 159.4`, `FK_INSTRUMENT = 20.4`, `FK_BS = <branch PK>` | ✅ **The mined value.** It names the same object in both schemas |
    | ⛔ **Source-object PK** — the identity of the GBO row being *read* | the GBO curve's own `PK`, the GBO MIS header's `PK` | ❌ **Never.** It is a PK in `DEVENG`, meaningless as a key into `BOX_FE` |
    | ⛔ **Intra-config FK** — points at another object *this walk creates* | the header's `FK_CURVEMAN` / `FK_CURVEACC` → the curve | ❌ **Never a literal.** The `F___SEQUENCE` variable of the row this walk created |

    **A source-object PK is expected to be absent from the target — that absence is why the walk
    exists.** And an intra-config FK cannot be mined at all: the object it points at does not exist
    until this script creates it.

    ⛔ **The 2026-09-22 run wrote `FK_CURVEMAN = 1.35` and `FK_CURVEACC = 1.35` into
    `BOX_FE.T_BOX_ENGCONF_S`.** `1.35` is the PK of NY's curve in **`DEVENG.T_PGT_ENGFCURVE_S`** — the
    GBO table. The BOX column must reference `BOX_FE.T_BOX_ENGFCURVE_S`, a different table with its own
    key space. The script then created the correct BOX curve and **nothing referenced it.** With no FK
    constraints anywhere (hard rule 12) this inserts cleanly and fails silently in a batch later.

    **The test: for every FK in an INSERT, name the table it points into and say which schema that
    table is in.** If the answer is `DEVENG`, the value is wrong.


---

## Step 12 — Allowed Errors (moved from the charter)

> **Step 12 — Allowed Errors.** `[confirmed: BOX FE Developer via Edouard, 2026-09-17]` SIGOM path
> `BOX - Financial Engine > Process Management > Allowed Errors`, table `BOX_FE.T_BOX_ERRORS_FE_S`,
> defining **the error limit before a process crashes**, **per instrument and per branch**. It was
> missing from this walk entirely until a developer was asked *"is anything missing from the 13?"* —
> exactly the failure mode that question existed to catch. Being branch × instrument keyed, it is
> blocked by gate 0c like steps 6 and 11, and its row count tracks the instrument scope.
>
> ### 🔄 Its source changed, 2026-09-21 — [ADR 0004](../../docs/decisions/0004-step12-limits-from-reference-branch.md)
>
> `[stated: Edouard, 2026-09-21]` **Do not mine the GBO twin.** For each in-scope instrument, **propose
> the reference branch's `LIMIT_ERRORS` for that same instrument** and let the SME accept or change it.
> This supersedes the 2026-09-18 position that step 12 is an ordinary mine-and-propose step because
> `DEVENG.T_PGT_ERRORS_FE_S` exists; that table stays in the catalogue, it is just not this step's
> source.
>
> **Why this is not hard rule 6.** `LIMIT_ERRORS` is an **operational tolerance** — how many failed
> deals one load run survives — not a fact about the branch. Copying a curve asserts something false
> about NY; copying a limit asserts only *"start where London started."* It is emitted **`PROPOSED`**
> with the rule attached and needs its own per-instrument sign-off, which is hard rule 2, not an
> exception to hard rule 6.
>
> ⚠️ **It is a tuning default, not an answer.** Too high and failed deals are skipped while the run
> reports success; too low and the first bad deal aborts the load. Put the proposal to the SME with
> that stated — *"needs volume data first"* is a valid answer.
>
> 🚧 **One column, one step.** This does **not** extend to step 6's accrual values, to curves, or to
> anything that asserts what the branch *is*. Extending it needs a new ADR, never an analogy. And where
> a branch has an instrument the reference branch lacks, that limit is `SME_DECISION_REQUIRED` — never
> the value of whichever instrument looks closest, which is exactly the shape-matching hard rule 6
> forbids.
>
> ⚠️ **This intersects the unanswered product-shaped-branch question.** Allowed Errors is one of the two
> screens where BOX-DEV showed the `Branch` column holding values like `BOX CCS` / `BOX FX` / `BOX IRS`
> rather than geographic branches. That oddity now sits **inside** the walk rather than beside it, which
> raises its priority: if "branch" means something different on this screen, step 12's grain is wrong.
> ✅ **Closed** — Q-G7 declared `pBranch` → the branch master (2026-09-18), and the BOX FE team's own
> inserts write `22.21` (Madrid) and `20087.4` (SLB) into `FK_BRANCH` here (2026-09-23). Geographic.
>
> **Row shape** `[reference: BOX FE expert examples, 2026-09-23]`: `PK, FK_OWNER_OBJ, FK_BRANCH,
> FK_INSTRUMENT, LIMIT_ERRORS` — **no `FK_PARENT`, no `FK_EXTENSION`**. Identity from the Q-G7
> derivation (`BOX - Limit Error Assign`, Tier 1 `35000289.65`), which needs no existing row — run 3's
> *"table empty, so no identity"* was not a blocker. And run 3's `LIMIT_ERRORS = 0` ×6, taken from NY's
> GBO for the test, is exactly the value this step exists to avoid; ADR 0004 stands.

---

## The three SQL files — config, verify, rollback `[2026-09-23]`

**Run 3 had one file**, verification SELECTs absent and the undo inside `IF 1 = 0` — unreachable, so
neither correct nor tested (hard rule 11). The expert asked for the auth code to be *"part of the
verification script"*, which assumed one existed. From run 4, `03-sql/` holds three files:

| File | Runs | Must contain |
|---|---|---|
| `<BRANCH>-<env>-config.sql` | once, by whoever applies it — an account that sees **`BOX_FE` only** | No reference to `DEVENG`, `PGT_*` or `GOM_GLB_SYS`; GBO sets as generated literals; auth-code check (`chk_pk` against Q-G3c) before the first INSERT; every step's header; `chk_pk()` after every `F___SEQUENCE`; the length guard on every generated set (steps 4, 7); pre-commits as today. **No `ROLLBACK`, no dead code** |
| `<BRANCH>-<env>-verify.sql` | straight after, **read-only** — any account that sees `BOX_FE` and `DEVENG` | The checks below. Every query returns **zero rows or a stated count**; anything else is a failure, named |
| `<BRANCH>-<env>-rollback.sql` | only to undo | `DELETE`s in reverse dependency order, keyed on what this run created — never on a PK typed from the apply log |

**What the verification script checks — each one a query with its expected result stated beside it:**

| # | Check | Expect |
|---|---|---|
| V1 | **Auth code** — every row this run created: `PK - TRUNC(PK) = <auth_code>/10^len` read from `gom_glb_sys.t__CORE_INFO_S` | 0 violations |
| V2 | Row counts per step against the findings table | the stated counts |
| V3 | Header `FK_CURVEMAN`/`FK_CURVEACC` = the curve this run created; `FK_SOURCE_BACK = 586.4`, `FK_SOURCE_FRONT = <SOURCE_FRONT>` | 1 row |
| V4 | Step 4 array = GBO array — `MINUS` both ways on the quote-reference column | 0 rows each way |
| V5 | Every `FK_BRANCH` written on steps 7 and 11 exists in `PGT_STC.T_PGT_BRANCH_S` **and equals `BRANCH_PK`** (step 12 has no parent to find its rows by — the validator checks it statically, V2 its count) | 0 violations |
| V6 | Every instrument written is in `APPROVED_INSTRUMENTS` | 0 violations |
| V7 | Step 11: each approved instrument has its book rows **and** its dummy-book row | 0 missing |
| V8 | Step 14a: each approved instrument has a Days Matured row | 0 missing |
| V9 | Identity: `FK_OWNER_OBJ`/`FK_EXTENSION` per table = the Q-G6 constants | 0 violations |
| V10 | Step 7 = this branch's GBO exceptions for the approved instruments — `MINUS` both ways | 0 rows each way |

**How "rows this run created" is found without typed PKs.** Everything hangs off two unique
descriptions: the header (`T_BOX_ENGCONF_S.DESCRIPTION`) and the curve (`T_BOX_ENGFCURVE_S.DESCRIPTION`),
both globally unique by index. Children — step 11 included — by `FK_PARENT`; step 12, which has no parent,
by `FK_BRANCH = BRANCH_PK`, **safe only because the config script aborts if the branch already had step-12
rows**; step 14a by instrument, guarded the same way. The rollback uses the same keys — and **leaves
step 14a's rows in place**: Days Matured is global, another branch may already rely on the row, and an
approved instrument is meant to have one anyway. It prints them instead.

---

## How the BOX FE team writes these inserts today — reference, not a template `[2026-09-23]`

`[reference: BOX FE expert examples, Tier 1, product onboarding]` — **not branch onboarding, and not
complete.** Read for what it reveals about the tables; do not copy the style.

```sql
/* BOX - Limit Error Assign: 23029078.21 */
declare
VAR_00000001 number := BOX_FE.F___SEQUENCE('T_BOX_ERRORS_FE_S',1) + 0.21;
begin
insert into BOX_FE.T_BOX_ERRORS_FE_S (PK,FK_OWNER_OBJ,FK_BRANCH,FK_INSTRUMENT,LIMIT_ERRORS)
  values (VAR_00000001,35000289.65,20087.4,20371.4,'100');
end;
/
```

**What it confirms** — each already reflected in the query catalogue:

| Observation | Where it lands |
|---|---|
| `FK_BRANCH` holds the **branch** PK — `22.21` Madrid, `20087.4` SLB — on `T_BOX_CONFIG_ACCRUAL_S` and `T_BOX_ERRORS_FE_S` | Step 7 re-keying (Q-06); step 12 shape (Q-13) |
| `T_BOX_ENGACCRCONF_S` and `T_BOX_CONFIG_ACCRUAL_S` both take `FK_PARENT` = the MIS header (`132.21` Madrid, `333105.21` SLB) and `FK_OWNER_OBJ 35000126.65`, extensions `35001114.65` / `35001120.65` | Q-G6 table |
| `T_BOX_ERRORS_FE_S` and `T_BOX_ENGDAYS_MATURED_S` have **no `FK_PARENT`/`FK_EXTENSION`** — base objects, `35000289.65` / `35000145.65` | Steps 12, 14a |
| Days Matured written with `DDATE = SYSDATE` | Step 14a proposal, asked |
| `F___SEQUENCE('<T>',1) + 0.21` | **Not adopted** — see below |

**What not to copy.** One PL/SQL block per row, literal FKs throughout, and the auth code typed as
`+ 0.21`. That works for a one-row product addition run by the person who wrote it, in the environment
they wrote it for. It is exactly what this agent exists not to do: a typed decimal is correct in one
environment and silently wrong in the next, and nothing in the file says where a value came from. The
agent keeps `F___SEQUENCE(…,'X')`, variables for everything it creates, and the provenance header on
every step.
