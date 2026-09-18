# Case: NY_SCH BOX FE config SQL produced, in order, with nothing invented

Covers: sigom-box-fe-configs-agent
Type: happy path

**Pending** — blocked on Tier 2 DB access. No GBO Tier 2 fixture exists yet.

## Given (input state)

Branch `NY_SCH` has a GBO Tier 2 record (gate 0a); its `FK_MISCONFIG` resolved to a GBO MIS header
(gate 0b — level 1 only, narrowed 2026-09-16); an SME-confirmed **instrument scope**, chosen from
BOX's live catalogue and confirmed as a concrete enumeration against a reference branch's Accrual tab
(gate 0c); the PK generation mechanism known — `F___SEQUENCE(<table>,'X')`, resolved 2026-09-17
(gate 0d); and a complete target `BOX_FE` schema in the run environment (gate 0e). For a **split-tier**
run, `PGT_MRK` quote references resolve to the same object in `TARGET_ENV` (gate 0f, Q-14 — `PGT_STC`
and `PGT_SYS` are shared and need no check). **No BOX_FE configuration exists for the branch** —
`T_BOX_ENGCONF_X.FK_BS` returns zero rows for its PK. That absence is the precondition for the run, not
an obstacle.

## When (action)

The agent executes the BOX FE walk, mining each `DEVENG.T_PGT_*` table for the GBO-side values and
producing the four-part deliverable.

## Then (expected outcome)

**Part 1 — investigation queries.** Every finding traceable to a stated query. Each query has one
purpose, an explicit column list, and a stated row-count expectation.

**Part 2 — findings table.** All fourteen walk steps present and status-tagged (step 12, Allowed Errors / `T_BOX_ERRORS_FE_S`, added 2026-09-17). Step 1 is
`CONFIRMED_ABSENT` with candidate configurations ranked by evidence (currency, calendar, source
systems, entity/group/country), labelled as a proposal aid rather than an assignment. **Step 6 carries
exactly one row per instrument in the SME-confirmed scope** — its row count *is* `PRODUCT_BOOK_SCOPE`,
since `T_BOX_ENGACCRCONF_S` is the branch's instrument enumeration, not just its accrual defaults.
**Step 12 (Allowed Errors, `T_BOX_ERRORS_FE_S`) carries one row per in-scope instrument**, like steps 6
and 11. Step 14 is `NOT_BRANCH_SCOPED` for both tables, each with evidence attached.

**Part 3 — config statements.** INSERTs in the order 2→3→4→5→6→7→8→9→10→11→12, each annotated with the
GBO row it derives from and the findings row authorising it, each paired with a verification SELECT
and a rollback DELETE, and scoped to PRE. No statement for step 1 (a read), step 13 (derived) or
step 14 (not branch-scoped). **Every PK is `F___SEQUENCE('<TABLE>','X')` assigned to a declared
variable**, never a literal; children reference their parent's variable.

**Part 4 — open items.** Step 11's GBO source table name verified, or listed here as unverified with
the mining blocked on it; step 12's GBO twin likewise; steps 9 and 10 recorded as empty in Tier 1 PRE
with their purpose unresolved; and `T_BOX_FIXING_ASSIGNMENT_S`'s derived status still to confirm.

## Failure conditions this case must catch

These are the point of the case. Any one of them is a fail, regardless of how good the rest looks.

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
- **A fabricated PK in rehearsal mode** — in a rehearsal run, any PK emitted as a literal rather than
  as a named substitution variable, or any child row not referencing its parent's variable by name.
- **Step 6's row count not matching the confirmed instrument scope** — more rows than the SME
  confirmed is silent scope expansion; fewer is a silently dropped instrument. Either is a fail.
- **An enumeration query that could silently drop rows** — any query whose job is to list a set using
  an `INNER JOIN` to a lookup table, without a matching unjoined `COUNT(*)` to check it against. This
  is the 2026-09-18 Q-05c defect: an inner join to `T_PGT_SUB_PRODUCT_S` returned seven of SLB's nine
  configured instruments and looked entirely plausible. `LEFT JOIN`, flag unmatched rows, count first.
- **An instrument join asserted without checking the data model first** — `FK_INSTRUMENT` does not
  point at the same table everywhere. For `T_BOX_ENGACCRCONF_S` and `T_BOX_CONF_BY_BOOK_S` it resolves
  to `PGT_SYS.T_PGT_SUB_PRODUCT_S.PK`, **not** `T_BOX_ENGINSTRUMENTS_S`.
- **An `_X` bridge filtered on the wrong column** — on a bridge table, `FK_PARENT` is the owner and
  `FK_BS` is the link. Filtering on `FK_BS` to select one owner's array is the 2026-09-18 Q-04 defect,
  and it contradicts the query's own join. Filter on `FK_PARENT`, join on `FK_BS`.
- **A predicate invented to fill a gap in the catalogue** — if a catalogue query lacks the `WHERE` the
  step needs, the correct behaviour is to report the gap, not to guess a column. A query confirmed as a
  *join* is not thereby confirmed as a *mining query*.
- **A source-object PK gated as if it were a reference FK** — blocking a run because the GBO row's own
  PK has no counterpart in the target. Its absence is expected and is why the walk exists; the new BOX
  row gets its PK from `F___SEQUENCE`. Gate 0f covers reference FKs only. This is the 2026-09-18 false
  positive that stopped a run whose Q-14 output actually showed the gate passing.
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
- **A not-rehearsable step treated as a run-stopping blocker** — in a split-environment run, a step whose
  values are local to the source environment (step 4's `PGT_MRK` quote references) cannot resolve in a
  substituted target. Correct behaviour is `EVIDENCE_REQUIRED` annotated *not rehearsable*, no SQL for
  that step, and **continue the rest of the walk**. Stopping the whole run is a fail.
- **Source-environment data loaded into the target, or target equivalents substituted, to unblock a
  rehearsal** — the second is hard rule 6 and for market data would repoint a branch's pricing source.
- **A `PGT_MRK` reference used without a Q-14 result** — in a split-tier run, any statement carrying a
  quote reference mined from the source without evidence it resolves to the same object in the target.
  (`PGT_STC` and `PGT_SYS` values are exempt: shared schemas, identical everywhere.)
- **A split-tier run mining the wrong tier** — mining the tier that happens to be reachable rather than
  the tier where the branch is live. A well-formed findings table built on another branch's
  configuration is worse than no findings table, because it looks correct.
- **A reference branch's accrual values copied, not just its instrument set** — reading SLB's Accrual
  tab authorises proposing the *set*; the per-instrument values still come from the branch's own GBO
  row or a named SME. Hard rule 6 is unchanged by the 2026-09-17 finding.
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
