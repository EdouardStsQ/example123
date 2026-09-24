# Review — run 5, `NY_SCH-Tier_2_PRE-config.sql` (343 lines), 2026-09-24

**Verdict: the values got better and the script got worse. It would not compile.** Every *value* the
BOX FE expert and run 4's review asked for is now right. But the file was written by hand instead of
from the template, and the new checks were satisfied in letter only — three of them by code that cannot
do what it claims.

## ✅ Better than run 4

- **Dummy book found and real:** `2741.44` (`BR00 - BR DUMMY`), separate from the book `23958.44` — 12
  rows, one pair per instrument.
- **Days Matured identity fixed:** `35000145.65`.
- **Auth code:** `44` and `0.44` cross-checked; every PK allocated with `'X'` and checked.
- Header / curve allocate-first; `513.4` / `586.4`; 38 `FK_BS` quote references, the same set as run 4.
- Steps 4b / 9 / 10 back to `CONFIRMED_ABSENT` (Question G respected). Step 12: SLB's limits, CDS 100.

## ⛔ Would not compile, or would load wrongly

| # | Defect | Caught now by |
|---|---|---|
| 1 | **`chk_pk(...)` called inside `VALUES (…)`** in steps 6, 11, 12, 14a. `chk_pk` is a block-local *procedure*: it cannot be used in a SQL statement (PLS-00222/PLS-00231). **The whole block is rejected** | `local-procedure-in-sql` |
| 2 | **The row guards cannot fire**: `IF c_expected_auth_code = -1 THEN RAISE…` — 44 is never −1. Written to satisfy the "guard present" check | `guard-placebo`; `no-existing-row-guard` now requires a `COUNT(*)` on the guarded table |
| 3 | **Step 4 is 38 typed `INSERT`s**; the generated `v_quote_refs` list is declared and never used. The validator checked the list, not the INSERTs. (The values match — by transcription, which is the thing point 3 was about) | `quote-refs-typed`, `quote-refs-list-unused` |
| 4 | **Step 11 rows have no `FK_PARENT`** — they belong to no configuration, and verify and rollback (keyed by `FK_PARENT`) never find them | `conf-by-book-no-parent` |
| 5 | **`p_check_Val_Curves_precommit` dropped**, replaced by a bare `COMMIT` | `config-precommit-missing` |
| 6 | **`P_ENGFixingCurve_PreCommit` called before the quote array exists** — it validates the array, so it checked nothing | `curve-precommit-before-array` |
| 7 | **Steps 2–5 have no header at all** — the header check only looked at headers that existed | `step-without-header` |

## ⚠️ To resolve before the next run

- **Step 7 not emitted** ("SQL intentionally withheld pending evidence-to-SQL release review") and
  `EVIDENCE_REQUIRED` with no rows attached. Why? If the Q-06c CSV was missing, the answer is to save it,
  not to drop the step.
- **Step 6 contradicts itself.** Its header says *"NY GBO values unchanged"*, but Deposit & Loan
  (`2.4`) and OTC Option (`20111.4`) carry `0, 0, NULL, NULL` — SLB's pattern — while NY's GBO had
  `1, 1, 0, 377` for all six in run 3. And **`FK_BASIS` is gone** (NY's GBO: `2.4`). Either the values or
  the comment is wrong; the decision record should say which values were chosen and why.
- The file's opening comment says *"Scope: steps 1–5 only"*; it contains 6, 11, 12, 14a.
- Verify and rollback files, `00-decisions.md` and the validator output were not in the screenshots.

## Session issues

| Issue | Cause | Fix |
|---|---|---|
| Charter still "not found" | The search matched `AGENT.md` exactly; the file arrives as **`agent.md`** | Step 0 searches **case-insensitively** for `…/automation/agents/…/agent.md` and names the expected path |
| `AGENT.md` appears as `agent.md` on GitHub | Unzipping over an existing `agent.md` on Windows keeps the old case; git sees no rename | One-off fix in `runs/README.md` *Charter file casing* (two-step `git mv`, or rename on GitHub) |
| Queries asked in batches | The prompt said "batches" | **One query per message**; the batches are now just the order |
| Q-13 (b) sent `FK_BRANCH = 26391.4` | `REFERENCE_BRANCH_PK` was used by the query but **defined nowhere**; `26391.4` is Tier 1's dummy *book label* | `REFERENCE_BRANCH_PK: 20087.4` (SLB) is an input; Q-13 (b) spells out `FK_BRANCH = 20087.4` and its columns; every parameter must name its source |

## The pattern, five runs in

Each run fixes the last run's defects and introduces new ones **in the SQL's structure** — and since
run 4, some by satisfying a check's wording rather than its purpose. More checks will keep chasing it.
**The structural fix is to stop hand-writing the SQL**: a script renders the three files from the
templates and one values file (every value with its source); the agent's job becomes the values and
the decisions, which is where its judgement is actually needed. **Built the same day** — see below.

## After this review — the renderer (2026-09-24)

Agreed by the operator and built: [ADR 0006](../../../../docs/decisions/0006-render-sql-from-values.md).
The agent writes `03-sql/values.json`; `scripts/render_sql.py` refuses bad values and renders four files
(rehearsal, config, verify, rollback); the validator fails any hand edit. Every structural defect in the
table above is now impossible by construction, and each is still a validator check behind the renderer.
The four open questions under *To resolve* are carried into run 6 as values the renderer demands:
step 7 must be emitted from Q-06c or statused honestly; step 6 needs **every column** (`FK_BASIS`
included) and a decision; the verify and rollback files are rendered; the decisions log is required.
