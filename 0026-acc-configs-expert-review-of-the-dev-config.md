# 0026. BOX ACC configs: the BOX ACC expert's review of the first DEV config — conditions left empty (never dropped), descriptions, Cross Account Config types, Conf Instru Type rows with a global or own instrument type

Date: 2026-11-10
Status: accepted — supersedes ADR 0024 point 2 (a condition value BOX does not hold dropped for that property), the
"Conf Instru Type: the reference's rows as they are" rule (ADR 0014, charter screen 12) as far as which rows are
copied, and the "`DESCRIPTION` as GBO's" rule of ADR 0020 (completed)

## Context

The first DEV config of the ACC agent (NY_SCH in DGBOUS, reference SLB) ran and committed: 54 portfolio
properties (15 `Valid`, 39 `InValid`), 5 local properties, 54 global topics, the Cross Account Config and Conf Instru
Type rows. The BOX ACC expert reviewed it in SIGOM: a very good result, with four changes asked.

## Decision

`[BOX ACC expert via operator, 2026-11-10]`

1. **Conf Instru Type (screen 12): only the reference's rows whose instrument type is global (GBO, PK fraction `.4`)
   or the target installation's own (fraction = the target's auth code) are copied** — whatever the row's own PK.
   `[BOX ACC expert via operator, 2026-11-12 — corrects the reading of 2026-11-10]`: "the agent should create it if
   the Conf Instru Type is global (auth code .4), so it should have created the 11071.4". SLB has two rows:
   FlexBlockTag → `INF_CVX_PD`, instrument type `11071.4` (row `42.21`) → **created**; FlexBlockTag → `#ALL`,
   instrument type `69.21` (row `107.65`) — a Tier 1 local instrument type, absent in DGBOUS → **not created**: one
   row, not two. ~~The rule was first read on the row's own PK (`.65` / auth code), 2026-11-10: it kept the `69.21`
   row and dropped the `11071.4` one — 0 rows in the re-run.~~ Each Conf Instru Type row in the values carries its
   reference PK (`ref_pk`, to trace it) and its `FK_INSTRUMENT_TYPE`; the renderer refuses another fraction
   (`itype-fraction`), a row without them (`itype-missing`, `ref-pk-missing`), and the precheck checks the
   instrument type exists in the target. `[operator, 2026-11-10]`: **this rule is for Conf Instru Type only** — the
   other reference rows are right as they are.
2. **Local properties (screen 2) have a description**: `Conditions Portfolio Properties - <product> <BRANCH>`, e.g.
   `Conditions Portfolio Properties - CCS NY_SCH` (it was empty). `<product>` is the instrument's **BOX product
   code** `[operator, 2026-11-10]` — side BOX of
   [`gbo-box-product-tables.csv`](../reference/gbo-box-product-tables.csv) (`irs` → `IR`, `depos` → `MM`, `ccs` →
   `CCS`, `otc` → `OTC`, `cap` → `CF`). The renderer refuses another shape (`lp-description`).
3. **Portfolio properties (screen 4)**:
   - (a) their `DESCRIPTION` is GBO's **followed by the GBO PK in parentheses** — e.g. `… (2485.35)` — to trace each
     BOX property to its GBO one (`gbo_pk`, required — `pp-gbo-pk`);
   - (b) **a condition is never dropped for some properties of an instrument**: the condition the local property has
     is on every portfolio property of that instrument (BOX generates it — `f_GenTopicCond`). A GBO value BOX does not
     hold (NY: `Touch2`, `Accrual`, `SWAP` where BOX `13.65` holds `CALL` / `PUT`) → the condition stays **with no
     value** and the property is **`InValid`** — for the operations / accounting user to complete or decide in SIGOM.
     Seen in NY's config: `327.44` had 5 conditions, without "Check if Option is Call or Put", `345.44` had 6;
     `327.44` should have had it, empty. In the values: `empty_conditions` (listed in the summary and the report,
     `EMPTY|` in the config's output), the property `expect_invalid`; `drop_conditions` is refused
     (`drop-not-allowed`). This answers ADR 0024's two open points (a re-save in SIGOM regenerating the empty row; a
     dropped condition widening the property): no condition is dropped any more.
4. **Cross Account Config (screen 3): only GBO rows with `TIPO` `0`, `1` or `2`** (BOX's `ACC_TYPE` `0` vencida /
   `1` viva / `2` balance viva). The others are listed as not carried, and **the accounts only they use are not
   created** `[operator, 2026-11-10]` (screen 10 creates the accounts the carried configuration uses — ADR 0023). The
   renderer refuses another `ACC_TYPE` (`acc-type`).

## Consequences

- `scripts/render_acc_sql.py`: the four refusals above plus `pp-empty-not-in-local`, `pp-empty-and-value`,
  `empty-condition-not-invalid`; the local property's `DESCRIPTION` written; the portfolio property's description
  ends with `(<GBO PK>)`; the precheck checks each description fits its column (`fits`, `ALL_TAB_COLUMNS`); the
  summary's column "Left empty (ADR 0026)" replaces "Dropped". Tests.
- The condition map records a GBO value BOX does not hold as **"empty on that property"**, not "drop"; the report
  and the matrix count those properties as created `InValid` (empty condition) — not OPEN, not dropped.
- An `InValid` property is now either in a clash group or has an empty condition (or both); the second status pass
  (ADR 0024) still checks the clash groups.
- NY's DEV config is rolled back (`NY_SCH-tier2-dev-acc-rollback.sql`, rendered from the config's output — it holds
  the `.65` topics too) and run again from re-derived values: one Conf Instru Type row, the local
  properties' descriptions, the GBO PK in each property's description, `13.65` empty on the `Touch2` / `Accrual` /
  `SWAP` properties (all `InValid`), the Cross Account Config rows of other `TIPO`s and their own accounts left out.
- **The re-run (2026-11-10)**: rollback (counts = the config's `CREATED|`; Cross Account Config 308 of 309 — `114.44`,
  account `9614600-982058` in no account table, was never created), precheck OK, rehearsal 0 problems, config
  committed, verify: 54 properties, **14 `Valid` / 40 `InValid`** (31 in clash groups, 9 with `13.65` empty — none
  both), no list row without an account, 5 local properties with their descriptions, 54 `.65` topics, 453 accounts /
  267 date rules, 163 Cross Account Config rows (146 of 309 excluded: `TIPO` 11 × 105, 9 × 7, 3–6 × 6 each, 7 and 8 × 5
  each), **0 Conf Instru Type rows** — the rule read on the row's PK kept the `69.21` row (which DGBOUS does not have;
  the first config had inserted it pointing to nothing) and dropped the `11071.4` one; corrected 2026-11-12 (point 1):
  the `11071.4` row is added on top of the re-run by a small config; the precheck now checks every row's
  `FK_INSTRUMENT_TYPE`. Lessons: an account is left out only when nothing carried uses it (the
  first re-derivation removed 129 accounts the lists used); an `expect_invalid` property's first status is not final
  (`STATUS-FIRST|`, renamed — read twice as final).

## Alternatives considered

- Keep dropping the condition on that property (ADR 0024 point 2): rejected by the expert — every property of an
  instrument has the local property's conditions; an empty one tells the user what is missing.
- Copy every reference row of every fraction for all screens: rejected for Conf Instru Type only (the other screens'
  reference rows are right, operator 2026-11-10).
- The LP description label from GBO's instrument name: rejected — the BOX product code (operator, 2026-11-10).
