# Case: the BOX ACC gap run — only branch-dependent rows in scope proposed, each from a stated source

> **Phase 2 (the SQL, ADR 0022)** `[2026-10-28]` — mechanically covered by `scripts/tests/test_render_acc_sql.py`.
> **Then:** `03-sql/acc-values.json` written from the gap run's evidence, every entry with its source; the precheck
> run and its output `ACC PRECHECK OK` saved before any other file; rehearsal before config; the config's output saved;
> the rollback rendered from it. **Fail:** SQL written or edited by hand; a PK typed; a `.65` PK in PRE / PROD outside
> the BOX team's range (`next-free` only in DEV); an open or masked value forced through; a clashing property kept
> without the operator's choice (mode a) or `expect_invalid` (mode b).

Covers: sigom-box-acc-configs-agent (phase 1, gap run)
Type: happy path + guard rails

**Pending** — first run (NY_SCH, Tier 2, reference SLB Tier 1). Guard rails of 2026-10-14 added
([ADR 0013](../../docs/decisions/0013-acc-prechecks-and-sigom-routines.md)).

## Given

The target branch and its group (A-G1); the reference branch's BOX ACC rows for the approved instruments (local
properties with their four arrays, portfolio properties with their generated lists, cross account config, ACC event
groups from its MBJ rows); the target's GBO rows (cross account config, portfolio properties and their accounts) and
its GBO configuration in scope (`Valid` portfolio properties of its branch, full lists) in the run's GBO source; the global catalogues in both tiers (topics, conditions, standard
historic, event groups and events, accounts).

## When

`Run automation/agents/sigom-box-acc-configs-agent/prompts/tier2-gap-run.md`, the operator returning each CSV.

## Then

- **Run folder:** a new versioned folder (`new_run.py --area acc-configs`); an earlier run is never written over.
- **Pre-checks first:** A-P1–A-P7 before any screen query; a failure (unreadable table, unknown owner / extension
  pair, `PKG_ACCTPROP` older than r0.0.8) **stops** the run with the finding; a sequence below its table's max PK
  (A-P5) is a finding with a proposal, blocking that table in phase 2 (2026-10-23).
- **GBO source and scope** `[ADR 0015]`: the GBO source asked once at the start; **no usage window**; A-U1 (a), (f)
  (g) and A-U7 (a), (b) only (the windowed queries not run unless the BOX team asks); no "configured but unused" question;
  `&&ACCOUNT_CODES` = A-U7b + A-03a; every target GBO query in the GBO source, every target BOX query in the target
  environment; an approved instrument with no in-scope GBO property → asked.
- **Global screens** (topics, conditions, standard historic, event groups, event config): `present`, or a finding
  when missing in the target — never `create`, **never a question** (conditions and event groups as BOX has them,
  ADR 0014) — except a GBO → BOX condition pair the agent is not sure of, asked once (ADR 0020). **No event-group question** and no branch copy.
- **Local properties** `[ADR 0020, 2026-10-28]`: `create` per instrument from **the target's GBO** — the topics of its
  in-scope `Valid` properties (by `CODE`, each in its GBO list) and their conditions with a BOX twin; arrays listed by
  `FK_EXTENSION`; **`INIVALPCDATE` 01/01/1900** (not asked); nothing if the target's group already has them; a GBO
  property whose topics or conditions differ from the instrument's set → a finding; the reference's local property
  shown for comparison only.
- **Cross account config:** `create` from the target's **`<GBO schema>.T_MAD_REVAL_ACCOUNTS`** rows (A-03a), never
  from `T_PGT_CROSS_ACCTCONF_S`; the column map from A-P7 and the reference's GBO vs BOX rows (A-03b, `TIPO` →
  `ACC_TYPE` only if they agree); account by code; no rows for the target → asked.
- **Portfolio properties** `[ADR 0020, 2026-10-28]`: **one BOX property per `Valid` in-scope GBO property** (e.g. 3 GBO
  Swap properties → 3 BOX ones), description as GBO's, its own topic → account rows (topics **by `CODE`**, ADR 0018;
  internal-list topics → the internal account); its conditions through the **condition map** — paired automatically
  only on the same field domain or description, otherwise proposed from both functions (A-04h) with the value
  translation and asked **once per pair**, written to `runs/<BRANCH>/branch/acc-configs/condition-map.csv`; a GBO
  condition with no BOX twin dropped and listed. **Clash mode asked** before the report ((a) default: clashing
  properties held for the user's choice; (b) all created, the clashing ones `InValid`); each clash group with its
  shared BOX values, every property's GBO conditions, the dropped conditions that told them apart, the topic →
  account rows that differ — **no recommendation**; `pp_clash_choices` from an earlier run applied. A portfolio /
  counterparty / entity value → its hash only (A-04f). **A topic with several accounts in one GBO property** (A-04i,
  2026-10-28): asked — one question for every `INTERNAL` + one real account case (real proposed), once per identical
  case otherwise; shown with both accounts; never chosen by the agent; unanswered → OPEN.
  **`03-portfolio-properties-report.md`**: the condition map, per GBO property its BOX property, the clashes, what is
  not carried. **Fail:** the reference's number of properties or its conditions used; GBO properties merged; a
  condition pair assumed from a similar name without the operator's confirmation; a BOX condition created or added; a
  clash resolved by the agent; the clash mode not asked; a pair already in the condition map asked again.
- **Conf Instru Type (screen 12):** `create` = the reference's BOX rows per instrument, as they are (A-12); nothing
  read from GBO.
- **Column maps (A-P7):** every BOX column of a copied table has a source (GBO column, fixed value, reference pattern)
  or is asked; GBO-only columns reported.
- **Global accounts:** the target's GBO accounts **in scope** missing in BOX → `create` (copied from GBO); none from the
  reference; a value longer than BOX's column → a finding.
- **Net CCS PlanBS (screen 13)** `[2026-10-26]`: asked every run whether the CCS end-of-month netting applies; no →
  `N/A`; yes → the reference's rows as they are (instrument types, strategies, `EOM_CCS_ACTIVE`, accounts by code),
  the events `5210.65` / `5211.65`, the netting standard historics, internal topics, `FFM` / `INTERNAL` verified;
  each account shown with whether the target's CCS portfolio properties use it. **Fail:** rows proposed without the
  question; the load PL's `.21` PKs or branch reused.
- **Label aliases for MIC (screen 14)** `[2026-10-27]`: one per book label with ACC jobs (excluded books none), code
  from `runs/<BRANCH>/branch/books/label-aliases.csv`, source from `label_aliases.source`; no code → `OPEN` + the book list for the GL
  team. **Fail:** a code derived or copied from the reference; an alias proposed for an excluded book.
- **Net contract:** `N/A` (not Madrid real). **MBJ:** not in the matrix (other agent).
- An instrument the reference has no ACC rows for (e.g. CDS) → `N/A — no reference`.
- **Find before asking** `[2026-10-23]`: a PK met in a CSV (e.g. a second `FK_BRANCH` on the reference's rows) is
  resolved with A-L1 and reported, not asked; every branch-condition value is classified in / out from A-U1 (g)
  (function source, the group's branches, family size) and confirmed in one answer; only a blank or unexplained value
  is asked, with the evidence.
- **Queries as written** `[2026-10-23]`: the catalogue's text with `&&` values only; GBO schemas from the inputs file
  (SLB `PGT_ES`); GBO vs BOX comparisons (A-03b, A-10c) as two CSVs; a failing query → A-P8, then only the named
  column changed. **A-P5** shows the auth code, the `F_GetPK` mode and the max PK of this fraction; a table behind is
  a finding with a proposal for the BOX team, not a stop.
- **NY's first DEV run** `[2026-10-29, ADR 0023]`: every `schema.table` matches the catalogue's *Where each table
  lives*; A-P5 (d) read before a collision is reported; a duplicate claimed only with every condition value and
  topic → account row shown identical, and a rule keeping one of them (e.g. "keep the `.44`") in the questions, not in
  *Decisions*; a kept condition value with no BOX value, or a list account no source has → the property OPEN, not
  carried; the counts add up (create + held only + OPEN only + held and OPEN = in scope); screen 10 = the accounts the
  carried configuration uses, Net CCS accounts from the reference's BOX rows; computed columns not supplied; the SQL
  step in mode (a) proceeds with the groups held and lists `_not_carried`; an existing run continued without asking
  its CSVs again. **Fail:** `PGT_NY.T_PGT_ACCT_…`, `PGT_SYS.T_MAD_REVAL_ACCOUNTS` or `T_PGT_TOPICS_S` in a query; a
  GLTA / date-rule collision reported from A-P5 (a) across fractions; "keep the `.44`" recorded as the operator's
  decision or applied before the answer; a value invented for `SWAP` / `Accrual` / `Touch2`, or the condition dropped
  for those properties; a property carried with an account in no table; every GBO account of the group proposed;
  `LOC_CODE` / `HOSTINTERFIND` supplied; the SQL step stopped for empty clash choices in mode (a); a CSV already in
  the run asked again.
- **Fail:** any SQL written or run by the agent; **a column, table or schema not in the catalogue (e.g. `PGT_SLB`,
  `T_BOX_ACCT_PORT_PROP_S.NAME`)**; **one statement reading a GBO accounting schema and `BOX_ACC`**; **a question on
  what a PK is, or on a branch value before A-U1 (g)**; any GBO topic as a BOX value; any account taken from the reference
  branch; a condition, event group or event marked `create`; **a topic or standard historic created without the
  global `.65` PK and the *global — to review* flag, or missing from the global section**; **a topic mapped by
  description, or the mapping asked**; **a property with a blank branch condition carried or asked**; a query run in
  the wrong tier; **a list read without its owner and
  extension** (lists mixed); **a negative-owner row compared or copied**; **`NUM_ROWS` used as a count**; a screen
  query run before the pre-checks; **a portfolio, counterparty or entity name or value extracted from GBO
  production**; **a usage window asked, or a row dropped because it was not used in a period** (ADR 0015); **a question on conditions (other than a GBO → BOX pair
not yet in the condition map and not sure), event groups or the local properties' start date; an `InValid` GBO portfolio property read; an internal-list topic left without an
account; Cross Account Config read from `T_PGT_CROSS_ACCTCONF_S`; a BOX column filled from a GBO column of another
name without the reference showing it** (ADR 0014).
