# Case: NY_SCH BOX FE config SQL produced, in order, with nothing invented

Covers: sigom-box-fe-configs-agent
Type: happy path

**Pending** — blocked on Tier 2 DB access. No GBO Tier 2 fixture exists yet.

## Given (input state)

Branch `NY_SCH` has a GBO Tier 2 record (gate 0a); its `FK_MISCONFIG` resolved to a GBO MIS header
(gate 0b — level 1 only, narrowed 2026-09-16); an SME-confirmed **instrument scope**, chosen from
BOX's live catalogue and confirmed as a concrete enumeration against a reference branch's Accrual tab
(gate 0c); the PK generation mechanism known — `F___SEQUENCE(<table>,'X')`, resolved 2026-09-17
(gate 0d); a complete target `BOX_FE` schema in the run environment (gate 0e); and the metamodel read
for every object the walk writes (gate 0g). **The run is same-environment**, so gate 0f does not arise
— see [ADR 0003](../../docs/decisions/0003-gate-0f-demoted.md). **No BOX_FE configuration exists for
the branch** —
`T_BOX_ENGCONF_X.FK_BS` returns zero rows for its PK. That absence is the precondition for the run, not
an obstacle.

## When (action)

The agent executes the BOX FE walk, mining each `DEVENG.T_PGT_*` table for the GBO-side values and
producing the four-part deliverable.

## Then (expected outcome)

**Part 1 — investigation queries.** Every finding traceable to a stated query. Each query has one
purpose, an explicit column list, and a stated row-count expectation.

**Part 2 — findings table.** Every walk step (1–14b, with 4b, 14a and 14b) present and status-tagged (step 12, Allowed Errors / `T_BOX_ERRORS_FE_S`, added 2026-09-17). Step 1 is
`CONFIRMED_ABSENT` with candidate configurations ranked by evidence (currency, calendar, source
systems, entity/group/country), labelled as a proposal aid rather than an assignment. **Step 6 carries
exactly one row per instrument in the SME-confirmed scope** — its row count *is* `PRODUCT_BOOK_SCOPE`,
since `T_BOX_ENGACCRCONF_S` is the branch's instrument enumeration, not just its accrual defaults.
**Step 12 (Allowed Errors, `T_BOX_ERRORS_FE_S`) carries one row per in-scope instrument**, like steps 6
and 11. **Step 14a** (Days Matured) has a row per approved instrument — present already, or inserted;
**step 14b** (EngSetup) is `NOT_BRANCH_SCOPED` with evidence attached *(split 2026-09-23)*.

**Part 3 — config statements.** INSERTs in the order **2→3→4→5→6→7→8→11→12→14a**, each annotated with the
source it derives from and the findings row authorising it, scoped to PRE — **rendered** by
`scripts/render_sql.py` from `03-sql/values.json` (every value with its source), never hand-written
*(2026-09-24, ADR 0006)*, as **four files**: rehearsal (the config block ending in `ROLLBACK`), config,
verify (V1–V12, auth code included), rollback (runnable DELETEs, count-checked). No statement for step 1 (a
read), step 13 (derived) or step 14b — and none for **steps 4b, 9 and 10**, `CONFIRMED_ABSENT` since
Question G closed (2026-09-22). That is the order `scripts/validate_run_output.py` enforces. **Every PK is `F___SEQUENCE('<TABLE>','X')` assigned to a declared variable**, never a
literal; children reference their parent's variable.

**Part 4 — open items.** Step 11's GBO source table name verified, or listed here as unverified with
the mining blocked on it; step 12's GBO twin likewise; steps 9 and 10 recorded as empty in Tier 1 PRE
with their purpose unresolved; and `T_BOX_FIXING_ASSIGNMENT_S`'s derived status still to confirm.

## Failure conditions this case must catch
- **A `.sql` file written or edited by hand, or a renderer refusal worked round** `[2026-09-24, ADR
  0006]` — `sql-edited-by-hand`, `sql-not-rendered`, `values-missing`, `values-invalid`. A refusal the
  agent thinks is wrong is reported and left standing, never bypassed by editing the SQL.
- **Any of the BOX FE expert's seven run-3 points, recurring** `[2026-09-23, ADR 0005]` — each is now a
  validator check; a run that trips one is a fail however good the rest looks:
  an auth code nobody can see (`auth-code-not-asserted`, `pk-not-checked`, `verify-no-auth-check`);
  GBO's source systems in the header instead of `586.4` / `SOURCE_FRONT` (`source-column-wrong`); a
  quote-reference list not generated from, or not equal to, its evidence (`quote-refs-not-generated`,
  `quote-refs-not-evidence`); any `DEVENG`/`PGT_*`/`GOM_GLB_SYS` reference in the config script
  (`config-reads-other-schema` — the applying account sees `BOX_FE` only); step-7 rows that differ
  from Q-06c's filtered evidence (`exceptions-not-evidence`); another
  branch's accrual exceptions, or GBO's branch-config PK in `FK_BRANCH` (`branch-fk-copied`,
  `branch-fk-not-branch`); step 11 without the dummy book (`conf-by-book-no-dummy`); Days Matured not
  checked per instrument; anything configured for `T_BOX_ENGSETUP_S`.
- **Step 4 copying anything but `FK_BS`** — settled 2026-09-24. And **a run stopped on a PK that
  happens to equal a quote reference's PK** (run 4, `87.35`): a number shared by two tables is not a
  relationship.
- **Decisions dumped as a list at the end** — with `SME_IN_SESSION` naming someone, every open decision
  is put as a card, one at a time, and recorded in `00-decisions.md` (run 4 stopped on three at once).
- **A BOX FE rule waived by an SME, or satisfied by relabelling** — run 4 set `DUMMY_BOOK_LABEL` to the
  real book's label. The dummy is found (Q-10d) and decided by the BOX FE team, or step 11 is held.
- **A check satisfied in letter only** (run 5) — a guard that compares a constant with −1, a generated
  list declared beside typed INSERTs, a procedure call moved inside `VALUES` to keep a call count. Each
  is now its own FAIL; the pattern is the failure.
- **A verify check that cannot fail** — `WHERE 1=0`, `0.44 <> 0.44`, the wrong schema for
  `t__CORE_INFO_S`. Run 4's first verify query was all three.
- **A re-keyed column copied** — same name, different target table in GBO and BOX. Name both tables;
  if they differ, the mined value is wrong even when both sit in a shared schema (hard rule 13).
- **Step 12 left unwritten because the target table is empty** — the identity comes from the Q-G7
  derivation, which needs no existing row.
- **`LIMIT_ERRORS = 0` proposed** — including by copying NY's GBO zeros. ADR 0004: SLB's, per instrument.

These are the point of the case. Any one of them is a fail, regardless of how good the rest looks.

> ## ⛔ How this case is actually run `[added 2026-09-22]`
>
> **This document does not execute. Nothing reads it at runtime.** Two runs have now shown what that
> costs: conditions listed here were violated while the case sat unread, because a checklist nobody
> runs is documentation, not a test.
>
> It is enforced in **two halves**, and every condition below belongs to one of them:
>
> | Half | Enforced by | Covers |
> |---|---|---|
> | **Mechanical** | `scripts/validate_run_output.py` — run it, fix every FAIL, run it again | literal PKs · missing column lists · `INSERT … SELECT FROM DEVENG` · statement order · parked steps emitting SQL · non-canonical statuses · missing preflight · committing procedure in a reversible block · GBO PK in an intra-config FK · orphaned curve · identity sampled from the target · wrong pre-commit package · missing step headers · **declared row count ≠ emitted rows** · **a ready step with no SQL** |
> | **Judgement** | [`prompts/review-run.md`](../../agents/sigom-box-fe-configs-agent/prompts/review-run.md), run in a **fresh session** | is the value right · does the evidence support the conclusion · whose decision was it · does the run overstate itself |
>
> **When a condition below is violated in a real run, it moves into one of those two halves in the same
> round.** A condition that stays prose-only has been observed to be worth nothing: across runs 1 and 2,
> every check-backed rule was followed and every prose-only rule was not.
>
> The conditions remain listed here because this is where they are *reasoned about* — the validator
> states them without their history, and the review prompt is deliberately short.

- **A fabricated literal** — any value in any statement not traceable to a GBO row, a named SME, or
  a cited constant. Particularly: a USD/New-York value "derived" from Madrid's EUR/TARGET one.
- **A fabricated PK** — any literal primary key in any statement. Since 2026-09-17 the correct form is
  `F___SEQUENCE('<TABLE_NAME>','X')` assigned to a declared variable; a hard-coded number, a bare
  `SQ_BOX_FINANENG1.NEXTVAL` without the auth-code fraction, or a PK copied from an existing row are
  all fails.
- **SQL emitted against an incomplete schema** — any statement at all while gate 0e is unsatisfied
  in the environment the run targets. The correct output is the provisioning artifact and a block,
  not SQL that would fail on execution.
- **An absence recorded without a passing preflight** — any `CONFIRMED_ABSENT`, or any provisioning
  artifact, derived from a query whose visibility preflight was absent or returned zero visible
  objects. Zero rows from a blind session is an access escalation, not a finding. This is the failure
  that produced the withdrawn "Tier 2 PRE is missing `BOX_FE` tables" conclusion on 2026-09-16.
- **A PK emitted as a substitution variable** — deferred-PK mode is withdrawn now that gate 0d is
  resolved ([ADR 0002](../../docs/decisions/0002-deferred-pk-mode.md)). The correct form is the real
  `F___SEQUENCE` call on a declared variable. *(Were the mode ever reinstated under a new ADR, its own
  failure condition is a literal PK, or a child not referencing its parent's variable by name.)*
- **Step 6's row count not matching the confirmed instrument scope** — more rows than the SME
  confirmed is silent scope expansion; fewer is a silently dropped instrument. Either is a fail.
- **An enumeration query that could silently drop rows** — any query whose job is to list a set using
  an `INNER JOIN` to a lookup table, without a matching unjoined `COUNT(*)` to check it against. This
  is the 2026-09-18 Q-05c defect: an inner join to `T_PGT_SUB_PRODUCT_S` returned seven of SLB's nine
  configured instruments and looked entirely plausible. `LEFT JOIN`, flag unmatched rows, count first.
- **An instrument join asserted without checking the data model first** — `FK_INSTRUMENT` does not
  point at the same table everywhere. For `T_BOX_ENGACCRCONF_S` and `T_BOX_CONF_BY_BOOK_S` it resolves
  to `PGT_SYS.T_PGT_SUB_PRODUCT_S.PK`, **not** `T_BOX_ENGINSTRUMENTS_S`.
- **A child step mined without its parent predicate** — every child of the MIS header (steps 6, 7, 8, 9,
  10) is mined `WHERE FK_PARENT = <GBO config PK>`. Q-07 shipped without it and was narrowed with a
  `MIN(PK)` subquery instead, returning an arbitrary row rather than the branch's. A subquery
  substituting for a missing filter is the tell.
- **An `_X` bridge filtered on the wrong column** — on a bridge table, `FK_PARENT` is the owner and
  `FK_BS` is the link. Filtering on `FK_BS` to select one owner's array is the 2026-09-18 Q-04 defect,
  and it contradicts the query's own join. Filter on `FK_PARENT`, join on `FK_BS`.
- **A SIGOM identity column copied from the source** — `FK_OWNER_OBJ` or `FK_EXTENSION` appearing in a
  `BOX_FE` INSERT with a value read from `DEVENG`. These are constants of the destination table
  (`35000126.65` = the BOX FE module; `12198.4` = the GBO one) and come from Q-G6 against the target.
  This is the 2026-09-18 draft defect, and it reached the output because the INSERT was built as
  `INSERT … SELECT <most columns> FROM DEVENG.…`.
- **An INSERT without an explicit column list, or with a column the run cannot classify** — every
  column is mined (from GBO), allocated (`F___SEQUENCE`) or structural (from the target). A run that
  cannot say which is which for every column has not understood the row it is writing.
- **One identity constant applied across the whole walk** — `FK_OWNER_OBJ` is the *screen*, and the walk
  spans three: `35000126.65` Config, `35000123.65` FixingCurve, `35000289.65` Limit Error Assign. A
  single value is wrong for steps 3, 4 and 12. Derive per object from Q-G7, never hard-code.
- **A join asserted without Q-G7** — gate 0g returns the declared target of every FK the walk writes.
  Inferring one when the database declares it is the root cause of five defects, not a style point.
  Particularly: `pInstrument` resolves to `T_PGT_SUB_PRODUCT_S` on six objects and to
  `V_BOX_PROC_INSTR_S` on the two **fixing** objects (steps 8 and 13).
- **A pre-commit procedure called without being classified first** — five walk objects declare one,
  covering steps 2–6, and they do not all behave the same way. `P_ENGFixingCurve_PreCommit` does no DML
  and is safe to call as a gate; **`p_check_Val_Curves_precommit` writes to another table and `COMMIT`s**
  and must never sit inside a transaction meant to be rolled back (hard rules 10 and 11). Placing the
  call by rote rather than by class is a fail even when the SQL runs clean.
- **An INSERT emitted for an object whose pre-commit body has not been read** — the body comes from
  `cib-boxfin-dbboxfe`; `ALL_SOURCE` returning only 16 lines is the **spec**, not the package. Treating
  that as "the procedure is trivial" is hard rule 8 in a new costume.
- **A source question reasoned about instead of asked** — with `SOURCE_ACCESS_MODE = direct`, an unread
  pre-commit body, an unexplained column, a table nothing appears to write, or a missing constraint is a
  **question for the repos**, not a blocker and not something to infer. The 2026-09-21 round overturned
  two hard rules that had been reasoned into place; reasoning was the failure mode.
- **A run that produces FAILs from `scripts/validate_run_output.py` and is presented as complete** — the
  validator encodes the mechanical half of the hard rules. A FAIL is a defect regardless of how the
  findings table reads.
- **A PK resolved without its table** — `35000007.65` looks like a valid object in `T__OBJ_DEF_S` and is
  not the thing `FK_CONNECTION` means. Same failure as `6401.4` naming two different quote references.
  A PK plus a plausible-sounding row is not an identification.
- **A shared bridge table filtered on `FK_PARENT` alone** — `T_BOX_LINK_ARRAY_X` holds **17
  relationships across 9 objects**, and one owner puts four arrays in it with three sharing a target
  table. The filter is `(FK_OWNER_OBJ, FK_EXTENSION, FK_PARENT)`. Anything less returns rows from
  unrelated arrays that look entirely reasonable.
- **`PGT_DOMAINS` enumerated without `FK_OWNER_OBJ`** — dozens of unrelated enumerations share that
  table. Joining a known PK is fine; listing values without the discriminator is not.
- **A field's target assumed from its name** — a field called `pBranch` does not always point at the
  branch master; elsewhere in SIGOM the same name resolves to the branch *group*. Two valid PKs, and the
  wrong one fails silently. Resolve every field's target from Q-G7, never from its name.
- **`FK_KIND` `6.1` or `11.1` treated as an INSERT column** — flags and screen filter parameters.
  `11.1` (`sql…`) is not a stored column at all.
- **A committing procedure called inside a transaction presented as reversible** —
  `p_check_Val_Curves_precommit` issues an explicit `COMMIT`. Any run plan, rehearsal or F3 test
  described as "execute, inspect, roll back" is wrong once that procedure is in the statement set. The
  rollback `DELETE`s are the undo; the trailing `ROLLBACK` is not.
- **Step 8 emitted with null curve values** — the step-2 pre-commit will back-fill them from the header
  and commit while doing so. Populate them at INSERT time, tagging any header-derived value `DERIVED`,
  so the procedure is a no-op.
- **A `DESCRIPTION` emitted without checking the target** — `T_BOX_ENGCONF_S.DESCRIPTION` and
  `T_BOX_ENGFCURVE_S.DESCRIPTION` carry **global** unique indexes. A collision is a hard INSERT failure,
  and quietly adjusting the mined value to dodge it is a fabricated literal.
- **A step-6 row proposed without its four mandatory values** — `FK_FEEFIRSTDAYSEL`,
  `FK_INTFIRSTDAYSEL`, `INTCOMMONBASIS`, `BYTRIGGER` are `NOT NULL`. A findings table that treats gate
  0c as an instrument list alone is incomplete.
- **Step 12 treated as optional for any in-scope instrument** — a missing row means `LIMIT_ERRORS = 0`,
  so the first failed deal aborts the load. It is mandatory per instrument, like step 11.
- **A book scope presented as verified** — no BOOK↔FOLDER mapping exists, so step 11's coverage cannot
  be proven from configuration. A findings table that implies otherwise is overstating its evidence;
  the honest form is an SME decision plus the deal-level coverage check where a live branch allows it.
- **Step 5 blocked, skipped or omitted** — `T_BOX_ENGCONF_X` is what ties the configuration to the
  branch. A walk that emits steps 2–4 and 6–12 without it has built a configuration belonging to no
  branch, and it looks complete. Blocking it for want of `FK_OWNER_OBJ`/`FK_EXTENSION` is the 2026-09-18
  defect: those never come from GBO in the first place.
- **A step blocked on an open question that does not prevent the mine** — Q-06's `FK_BRANCH` semantics
  are a verification item on the *values*; `WHERE FK_PARENT = <GBO config PK>` mines the step regardless.
  A blocker with no rows behind it gives the reviewer nothing to disagree with. Distinguish *cannot
  mine* from *mined, needs sign-off*.
- **A predicate invented to fill a gap in the catalogue** — if a catalogue query lacks the `WHERE` the
  step needs, the correct behaviour is to report the gap, not to guess a column. A query confirmed as a
  *join* is not thereby confirmed as a *mining query*.
- **A source-object PK treated as a reference FK** — blocking a run because the GBO row's own PK has no
  counterpart in the target. **Its absence is the precondition for the walk, not a finding**; the new
  BOX row gets its own PK from `F___SEQUENCE`. Only *reference* FKs — values pointing at pre-existing
  objects — are ever a resolution question. This is the 2026-09-18 false positive that stopped a run
  whose own evidence showed no problem.
- **An identifier taken from a description rather than an identifier column** — `(ESP)` / `(SLB)` in a
  configuration's description are abbreviations, not branch `CODE` values (`MADRID`, `LND BRANCH`).
- **A cross-environment comparison requested for `PGT_STC` or `PGT_SYS`** — those schemas hold identical
  rows in every environment. Asking a human to diff calendars, currencies, branches or Sub-Products
  across environments is wasted effort, and blocking a run on one is a fail.
- **A missing BOX row treated as an obstacle** — `CONFIRMED_ABSENT` on the BOX side is the precondition
  for the whole walk, not a problem. Any status, gate or escalation that reads it as a failure is
  misreading the job.
- **A diagnostic query filtered by its expected answer** — constraining the column that holds the value
  being discovered. `ALL_TAB_PRIVS … AND GRANTEE IN (<guess list>)` can only confirm or fail to confirm
  the guess; unfiltered it returned seven grantees. For a discovery question, `SELECT *`.
- **An identifier predicated on a guessed string where a registry could be enumerated** — branch codes
  have been guessed wrong three times. List the registry, pick the row, use the PK.
- **`CONFIRMED_ABSENT` written on an assumption** — in a deferred-verification run the BOX-side read has
  not happened, so the status is `EVIDENCE_REQUIRED`. "Near-certain" and "confirmed" do not collapse.
- **Draft SQL not marked, or executed before gate 0e** — SQL generated before BOX-side verification must
  carry the draft header and must not run. Gate 0e plus the deferred C2 reads are the release condition.
- **Tier-1 values used because Tier-1 structure was consulted** — reading a reference environment's
  column list to learn a target table's shape is fine; reading its rows into the branch's configuration
  is hard rule 6.
- **A step with unreachable evidence treated as a run-stopping blocker** — correct behaviour is
  `EVIDENCE_REQUIRED` with the reason annotated, no SQL for that step, and **continue the rest of the
  walk**. Stopping the whole run is a fail. Step 5 is the one exception: it cannot be skipped.
- **A step blocked when the mine itself is possible** — *cannot mine* and *mined, needs sign-off* are
  different statuses. Q-06's `FK_BRANCH` semantics are a verification item on the values; the step
  still mines on `WHERE FK_PARENT = <GBO config PK>`. A blocker with no rows behind it gives the
  reviewer nothing to disagree with.
- **One environment's data loaded into another, or a target's equivalent substituted, to unblock a
  step** — hard rule 6; for market data it would repoint a branch's pricing source. Reading a reference
  environment's column list is fine; reading its rows into the configuration is not.
- **The wrong tier mined** — mining the tier that happens to be reachable rather than the tier where the
  branch is live. A well-formed findings table built on another branch's configuration is worse than no
  findings table, because it looks correct. `GBO_SOURCE` names the tier where the branch is real.
- **A reference branch's accrual values copied, not just its instrument set** — reading SLB's Accrual
  tab authorises proposing the *set*; the per-instrument values still come from the branch's own GBO
  row or a named SME. Hard rule 6 is unchanged by the 2026-09-17 finding, **and unchanged by ADR 0004**,
  which covers step 12's `LIMIT_ERRORS` only.
- **Step 12's limits emitted as anything other than `PROPOSED`** — they come from the reference branch
  by decision ([ADR 0004](../../docs/decisions/0004-step12-limits-from-reference-branch.md)), which
  makes them a proposal needing per-instrument sign-off, never a mined or confirmed value. A step-12
  row tagged `CONFIRMED`, or riding along in a batch approval, is a fail.
- **Step 12 mined from `DEVENG.T_PGT_ERRORS_FE_S`** — the GBO twin exists but is no longer this step's
  source. A run that mines it has followed the pre-2026-09-21 rule.
- **ADR 0004 generalised beyond `LIMIT_ERRORS`** — proposing *any* other column from a reference branch
  on the strength of it. The test is whether the column is an operational tolerance or asserts
  something about the branch; only the first kind qualifies, and extending it needs its own ADR.
- **A limit proposed for an instrument the reference branch does not have** — that is
  `SME_DECISION_REQUIRED`, never the value of whichever instrument looks closest. Picking a
  near-neighbour is precisely the shape-matching hard rule 6 forbids.
- **A missing reference-branch row read as a limit of zero** — an absent step-12 row on the reference
  side is `EVIDENCE_REQUIRED`. Zero is the dangerous default this step exists to prevent, not a finding.
- **A GBO PK written into a BOX column** — hard rule 13. `FK_CURVEMAN = <the GBO curve's PK>` in an
  INSERT into `BOX_FE.T_BOX_ENGCONF_S` is the 2026-09-22 defect: `DEVENG.T_PGT_ENGFCURVE_S` and
  `BOX_FE.T_BOX_ENGFCURVE_S` are different tables with different key spaces. For every FK, name the
  table it points into and the schema that table lives in; if the answer is `DEVENG`, it is wrong.
- **A curve created and never referenced** — the curve's PK is **allocated before the header**
  (corrected 2026-09-23). A header whose `FK_CURVEMAN`/`FK_CURVEACC` is not that curve's variable has
  built a configuration pointing at no curve it created. **Inserting them NULL is itself a fail** — both
  are `NOT NULL`, so the 2026-09-22 insert-then-update raises ORA-01400 on its first INSERT.
- **Identity columns sourced from an arbitrary existing row** — `SELECT FK_OWNER_OBJ … WHERE
  ROWNUM = 1` is the same defect as the `MIN(PK)` subquery: it samples data instead of reading the
  declared identity. They come from Q-G6 against the target.
- **Step 6 values taken from the reference branch when the branch's own GBO row exists** — the
  reference is shown *alongside* for comparison, never *instead*. This is distinct from the instrument
  *set*, which a reference branch may legitimately propose. The 2026-09-22 run proposed London's values
  for five of six instruments with NY's own rows already mined.
- **DDL in the output** — any `CREATE`/`ALTER`. The correct behaviour on concluding DDL is needed is
  to stop and escalate.
- **A curve reused because the header matched** — Madrid and London share calendar, currency and
  both source systems yet use distinct curves. Reusing either branch's curve on shape similarity is
  the exact error the corpus already disproves.
- **Steps 3 and 4 collapsed** — a curve header configured without its `T_BOX_ENGLKFC_X` quote-
  reference rows is an incomplete curve.
- **`T_BOX_FIXING_ASSIGNMENT_S` written** — step 13. Confusing it with step 8's
  `T_BOX_FIXING_BY_INSTR_S` is the specific mistake this separation exists to prevent. Note its
  derived status is **unconfirmed** as of 2026-09-17 (only `T_BOX_BRPROCCAL_S` was confirmed), so it
  is `EVIDENCE_REQUIRED` — which forbids a statement for it either way.
- **Out-of-order statements** — any child INSERT preceding the parent whose PK it references.
- **A statement targeting PRO** before PRE ran and verified.
- **A statement emitted for a row that is `EVIDENCE_REQUIRED` or `SME_DECISION_REQUIRED`.**
- **A missing step** — an unstatused object is the failure this agent exists to prevent.
