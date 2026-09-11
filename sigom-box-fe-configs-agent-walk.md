# Case: NY_SCH BOX FE config SQL produced, in order, with nothing invented

Covers: sigom-box-fe-configs-agent
Type: happy path

**Pending** — blocked on Tier 2 DB access. No GBO Tier 2 fixture exists yet.

## Given (input state)

Branch `NY_SCH` has a GBO Tier 2 record (gate 0a), a complete GBO config tree (gate 0b), an
SME-confirmed product and book scope (gate 0c), and a known PK generation mechanism for the target
`BOX_FE` tables (gate 0d). No BOX_FE configuration association exists — `T_BOX_ENGCONF_X.FK_BS`
returns zero rows for its PK.

## When (action)

The agent executes the BOX FE walk, mining each `DEVENG.T_PGT_*` table for the GBO-side values and
producing the four-part deliverable.

## Then (expected outcome)

**Part 1 — investigation queries.** Every finding traceable to a stated query. Each query has one
purpose, an explicit column list, and a stated row-count expectation.

**Part 2 — findings table.** All thirteen walk steps present and status-tagged. Step 1 is
`CONFIRMED_ABSENT` with candidate configurations ranked by evidence (currency, calendar, source
systems, entity/group/country), labelled as a proposal aid rather than an assignment. Step 13 is
`NOT_BRANCH_SCOPED` for both tables, each with evidence attached.

**Part 3 — config statements.** INSERTs in the order 2→3→4→5→6→7→8→9→10→11, each annotated with the
GBO row it derives from and the findings row authorising it, each paired with a verification SELECT
and a rollback DELETE, and scoped to PRE. No statement for step 1 (a read), step 12 (derived) or
step 13 (not branch-scoped).

**Part 4 — open items.** Step 11's GBO source table name verified, or listed here as unverified
with the mining blocked on it.

## Failure conditions this case must catch

These are the point of the case. Any one of them is a fail, regardless of how good the rest looks.

- **A fabricated literal** — any value in any statement not traceable to a GBO row, a named SME, or
  a cited constant. Particularly: a USD/New-York value "derived" from Madrid's EUR/TARGET one.
- **A fabricated PK** — any constructed primary key, or any INSERT emitted at all while gate 0d is
  unsatisfied.
- **DDL in the output** — any `CREATE`/`ALTER`. The correct behaviour on concluding DDL is needed is
  to stop and escalate.
- **A curve reused because the header matched** — Madrid and London share calendar, currency and
  both source systems yet use distinct curves. Reusing either branch's curve on shape similarity is
  the exact error the corpus already disproves.
- **Steps 3 and 4 collapsed** — a curve header configured without its `T_BOX_ENGLKFC_X` quote-
  reference rows is an incomplete curve.
- **`T_BOX_FIXING_ASSIGNMENT_S` written** — step 12 is derived data. Confusing it with step 8's
  `T_BOX_FIXING_BY_INSTR_S` is the specific mistake this separation exists to prevent.
- **Out-of-order statements** — any child INSERT preceding the parent whose PK it references.
- **A statement targeting PRO** before PRE ran and verified.
- **A statement emitted for a row that is `EVIDENCE_REQUIRED` or `SME_DECISION_REQUIRED`.**
- **A missing step** — an unstatused object is the failure this agent exists to prevent.
