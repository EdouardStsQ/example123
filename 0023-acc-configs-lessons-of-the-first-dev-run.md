# 0023. BOX ACC configs: what NY's first DEV run taught — duplicates, OPEN rules, accounts, the SQL step in clash mode (a), queries, continuing a run

Date: 2026-10-29
Status: accepted — completes ADR 0020 (portfolio properties) and ADR 0022 (the SQL step); nothing they decided is
reversed. **Partly superseded by [ADR 0024](0024-acc-configs-expert-review-of-the-dev-run.md) (2026-10-30)**: point 3's
first case (a condition value with no BOX value → OPEN) is now "dropped for that property"; point 5 (the SQL step in
clash mode (a)) is gone — clash groups are always created `InValid`. **And by
[ADR 0025](0025-acc-configs-net-ccs-left-to-operations.md)**: point 4's Net CCS accounts are no longer taken from the
reference — the operations user defines them at UAT.

## Context

`sigom-box-acc-configs-agent` ran its first gap run under ADR 0020 end to end, for NY_SCH in **DGBOUS** (Tier 2 DEV),
GBO source **PRE PARALELO**: `runs/NY_SCH/tier2-dev/acc-configs/gap_20261029_1/` (Devin's PR #111), then its SQL step
up to the precheck. The operator reviewed every Devin proposal and relayed the answers. The run worked, but showed
gaps the charter did not close:

- the matrix recorded **"keep the `.44`"** for `.35` / `.44` property pairs as an operator decision, and applied it to
  pairs that were not identical in GBO (a proposal written as a decision);
- three queries named tables that do not exist (`PGT_NY.T_PGT_ACCT_PORT_PROP_S`, A-P7's
  `PGT_SYS.T_MAD_REVAL_ACCOUNTS`, an improvised A-04i on `PGT_ACT.T_PGT_TOPICS_S`), and A-P5 reported a GLTA collision
  by comparing across PK fractions (the second time, after `T_BOX_ACCT_PARENT_DATE_S` in October);
- property counts were inconsistent until the overlap of "held in a clash" and "OPEN" was shown;
- screen 10 proposed every GBO account read (486) instead of those the carried configuration uses;
- the Net CCS accounts and `FFM` had no stated source;
- a kept condition whose GBO value has no BOX value (`SWAP` / `Accrual` / `Touch2` on BOX's call/put condition), and an
  account referenced by a list but present in no table (`9614600-982058`), had no rule;
- the SQL kickoff (`tier2-sql.md` Step 2) stopped when the clash choices were empty — which is exactly clash mode (a)
  before the accounting user answers;
- the precheck read `PGT_STC.T_PGT_BRANCH_GROUP_S`, which `BOX_ACC` cannot read in DGBOUS (ORA-00942);
- the 14 multi-account cases of 2026-10-28 were found in GBO **PRE**; PRE PARALELO has none;
- the operator asked whether a run can be continued after the repo is updated, without running its queries again.

## Decision

`[operator, 2026-10-29 — the review of gap_20261029_1, relayed to the agent run by run]`

1. **Duplicates are proven, a rule to keep one is asked.** Two GBO portfolio properties are duplicates only when every
   GBO condition value (hashes included) and every topic → account row are identical — the report shows that evidence
   per pair. A rule that keeps one (e.g. "keep the `.44`") is a **proposal for the BOX expert** in the questions,
   applied only once the operator answers it; until then the clash group is held (mode a). NY: no pair is identical.
2. **A proposal is never written as a decision.** The matrix's *Decisions* table holds only the operator's answers
   (value, date); *Fixed by the BOX ACC expert* only the expert's rulings (with the ADR). The agent's proposals are in
   *Questions for the BOX team* until answered.
3. **OPEN — a property is not carried when BOX cannot hold it as GBO has it:**
   - a kept condition whose GBO value has no BOX value (no translation) → the property is **OPEN** on that condition,
     a question with the values; the condition is not dropped for it alone and no value is invented;
   - an account its lists use that no source has (neither the target's GBO nor, for a BOX-side technical account, the
     reference's BOX) → **OPEN**, a question; the property is not carried (it would be `InValid`).
   The report counts every property once: **created + held only + OPEN only + held and OPEN = in scope**.
4. **Screen 10 creates only the accounts the carried configuration uses**: the in-scope properties' lists ∪ the Cross
   Account Config rows ∪ the Net CCS rows (when screen 13 applies), minus those in BOX. The Net CCS accounts are the
   **reference's BOX rows** (BOX-side technical accounts with no GBO row; source A-13a). GBO accounts used only by
   properties out of scope or not carried are listed, not created. Account type and direction: translated by
   `CODE` (A-10a with the codes, A-10e); a code with no BOX twin is asked. Columns BOX sets itself on save
   (`LOC_CODE`, `HOSTINTERFIND`, `STATUS`…) are mapped "computed — not supplied".
5. **The SQL step in clash mode (a)**: empty clash choices mean the groups are **held** — not a stop. Phase 2 renders
   everything that is neither held nor OPEN, and its render report lists what was not carried and why (held, OPEN,
   out of scope). The kickoff stops only for what it needs: an `ask` unanswered that a carried row depends on, a
   condition pair `to confirm`, a multi-account case unanswered on a carried property.
6. **Queries**: every `schema.table` is checked against the catalogue's *Where each table lives* before a query is
   handed over; an improvised query says why the catalogue's does not do and is written from A-P8's columns. A-P5 is
   read per fraction — an (a) warning is never reported before (d). In DGBOUS `BOX_ACC` cannot read
   `PGT_STC.T_PGT_BRANCH_GROUP_S`: target queries run as `BOX_ACC` use `FK_BRANCH` as the group (A-02c, A-04c), A-G1 /
   A-L1 run in the GBO account, and the renderer's precheck proves the group by its branch (`FK_LOCALGROUP`).
   A condition function's owner and package are read from `NOM_FUNC` and its source (A-04h) is read **before** a pair
   is proposed.
7. **A finding names its GBO source.** The multi-account cases, the scope counts and the clashes depend on the GBO
   copy read (NY: 14 cases in GBO PRE, 0 in PRE PARALELO); a decision recorded from another source is shown with it
   and confirmed again, never applied blindly. A-04i (b) checks by topic `CODE` and rows without an account.
8. **Continuing a run.** A run folder that is not frozen is continued, not restarted: the kickoff (gap run or SQL step)
   asked for an existing run reads its `RUN.md`, inputs file and `01-evidence/`; a CSV already there is **never asked
   again** unless the catalogue's text of that query changed since it was run (then only that query, saying what
   changed); the matrix, the report and `acc-values.json` are re-derived from the evidence under the current rules.
   A repo update reaches a run that lives on a PR branch by merging the default branch into that branch first. A new
   version (`new_run.py`) is for a new GBO source, a new environment, or a rerun the operator asks for; `--from` carries
   the answers, not the evidence.

## Consequences

- Catalogue (`acc-config-mining.md`): rule 4 and *Where each table lives*, the grants seen, A-P2 / A-P7 owners, A-P5
  reading, A-02c / A-04c written for the target, A-04i (b), A-04h, the condition-value rule (A-01), duplicates (§4),
  which accounts (§10), A-10a codes, A-10e, Net CCS accounts (§13).
- Charter: hard rules 21–24, checkpoint 2b, the inputs table; kickoffs `tier2-gap-run.md` (continue a run; schemas;
  `NOM_FUNC` / A-04h first; duplicates; OPEN; accounts) and `tier2-sql.md` (Step 2 in mode a; continue; what is not
  carried); templates (matrix: decisions vs proposals, the count line, computed columns; report: duplicates evidence,
  OPEN; values: account sources and computed columns).
- `scripts/render_acc_sql.py`: the precheck no longer reads `T_PGT_BRANCH_GROUP_S` (test updated).
- NY's facts of the run: `box-acc-model.md` §9.8; open items 4zz (the BOX expert's questions) and the updates of 4zb,
  4ze, 4zw, 4zx, 4zy; ADR 0020 point 6 (the GBO source of the 14 cases).
- The eval case gains the run's failures as guard rails.

## Alternatives considered

- Apply "keep the `.44`" as a default: rejected — no pair was identical, and the choice is the accounting user's.
- Drop a condition on the properties whose value has no BOX translation: rejected — it changes the property and can
  create new clashes silently.
- Create every GBO account of the branch's group: rejected — the charter's rule is the accounts the configuration uses.
- Re-run every query of a run after a repo update: rejected — the evidence is the run's, and only a changed query
  needs its CSV again.
