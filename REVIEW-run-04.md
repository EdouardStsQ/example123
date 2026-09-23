# Review — run 4, `NY_SCH-tier2-pre-{config,verify,rollback}.sql`, 2026-09-24

**Verdict: the best run so far, not yet executable.** Every point from the BOX FE expert's review is
visible in the SQL except the dummy book. Three defects would have failed or silently corrupted the
apply; the verification script was mostly decoration; and the session itself went wrong three times
in ways the repo caused.

## ✅ Fixed since run 3

Header and curve allocate-first (no NULL-then-UPDATE) · `513.4` / `586.4` · auth code `44` asserted
on every PK before the first INSERT · 38 `FK_BS` quote references (35 `.35`, 2 `.4`, 1 `.44`, as
recorded in September) · step 7: 14 NY rows, approved instruments, `FK_BRANCH = 20007.4` · step 12
written, SLB's limits · step 14a: only Caps And Floors missing · `BOX_FE` only · a real rollback file.

## ⛔ Would have failed or corrupted the apply

| # | Defect | Now caught by |
|---|---|---|
| 1 | **Step 7 does not compile.** The cursor names its fields `FK_INSTRUMENT`, `FK_STRATEGY`, `FK_INSTRTYPE`; the INSERT reads `r.instrument`, `r.strategy`, `r.instrtype` — PLS-00302, whole block rejected | `cursor-field-undeclared` |
| 2 | **Days Matured written with the Config owner** `35000126.65` instead of Days Matured's `35000145.65`. Inserts cleanly, edited through the wrong screen | `identity-wrong-object` |
| 3 | **Dummy book "waived" by setting `DUMMY_BOOK_LABEL` to the real book** `23958.44` — which satisfied `conf-by-book-no-dummy` without the row. A BOX FE rule, waived by an SME decision | `dummy-is-a-book` |

## ⛔ The verification script could not fail

- **The auth-code "check"** read `BOX_FE.T__CORE_INFO_S` (wrong schema) `WHERE 1=0 AND 0.44 <> 0.44` —
  always zero, and present only because the validator looked for the string `t__core_info_s`.
- **V1** checked two rows (header, curve), not every row created; **V4** checked `FK_BS IS NULL`, not
  BOX against GBO; no V9 (identity — would have caught defect 2), no V10 (step 7 against GBO).
- **V7** looked for the GBO curve PK `1.35` in a BOX table — a number that can never match there.

**Now caught by** `verify-placebo` and `verify-incomplete` (which requires the schema-qualified
`GOM_GLB_SYS.T__CORE_INFO_S`, both GBO comparisons, and an identity check).

## ⚠️ Also

- `P_ENGFixingCurve_PreCommit` dropped → `curve-precommit-missing`.
- No "abort if rows exist" guards on steps 11, 12, 14a, which the rollback relies on →
  `no-existing-row-guard`. No count check after step 7 (template has it; not checked mechanically).
- Step headers cut to one line — the *Source* and *Findings* lines were how a reviewer traced a value →
  `step-header-incomplete`.
- Steps 4b/9/10 reopened (`EVIDENCE_REQUIRED` / `SME_DECISION_REQUIRED`). Step 10 is fair to raise — NY has
  CCS — but the currency-basis count moved from **124** (run 3) to **116**; why is not stated.
- Step 6 tagged `[confirmed: Q-05d] SME approved…` — a decision, not a query result →
  `decision-tagged-confirmed`.
- The quote list and exception rows are not in `evidence_to_sql.py`'s output format — the generator was
  probably not used. The validator's CSV comparison is what matters; a missing CSV is now a FAIL
  (`quote-refs-unchecked`, `exceptions-unchecked`).
- `c_expected_auth_code` was declared and never used — harmless (the check uses the fraction), but the
  template now asserts the two agree, so a typo in either stops the script.

## ⛔ Session problems — the repo's fault, not the agent's

| What happened | Cause | Fix |
|---|---|---|
| "Charter missing" at start (runs 3 and 4) | The prompt's paths assume the automation repo is the checkout root; it sits in `automation/` | **Step 0** in every prompt: `find` the charter, `cd` to that root |
| Stopped on Q-04c: "`PK = 87.35` also resolves" | The query tested whether a bridge PK *also* matched a quote-reference PK and called any match evidence. A number shared by two tables is a coincidence | `FK_BS` settled `[stated: operator, BOX Dev, 2026-09-24]`; Q-04c rewritten as the decoded export set |
| Stopped with three blockers at once | The prompt listed four known decisions; anything else became a blocker | **Decision cards**, one at a time, recorded in `00-decisions.md` (`decisions-log-missing`) |
| Dummy label absent in Tier 2 | `PGT_SYS` is not identical across tiers for `PGT_DOMAINS` labels, which the repo assumed | **Q-10d** finds candidates; a card to the BOX FE team; books a separate card to the SME |

Against a reconstruction of run 4's files the validator now reports every defect above — **11
distinct FAILs**, where the validator run 4 used reported none of them. `scripts/tests/`: 25 tests pass.
