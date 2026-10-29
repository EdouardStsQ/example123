# Devin kickoff — `sigom-box-acc-configs-agent` — NY_SCH BOX ACC **SQL step** (phase 2)

> **How to start — nothing to paste.** Open a Devin session with this repo attached and type:
> **`Run automation/agents/sigom-box-acc-configs-agent/prompts/tier2-sql.md`**
> Devin reads this file and asks you for anything it needs, one question at a time.

**What this run produces:** in the gap run's folder, `03-sql/acc-values.json` (every value with its source) and, from
`scripts/render_acc_sql.py`, the SQL files you run in SQL Developer — precheck, rehearsal, config, verify — then the
rollback files from the config's output. ([ADR 0022](../../../docs/decisions/0022-acc-configs-sql-step.md))

| | |
|---|---|
| **Repos** | this automation repo `cib-box-aukinbranch` (**read/write**); optional read-only `cib-boxacc-dbboxacc` |
| ⛔ **Write protection** | No commit, branch, push, PR or edit on any repo except this automation repo. Devin never runs SQL |
| **Starts from** | a **finished gap run** of the same environment under ADR 0020 (`acc-configs/gap_<date>_<n>/`: evidence, `02-acc-gap-matrix.md`, `03-portfolio-properties-report.md`, the condition map, the clash choices answered, the multi-account answers) — none → stop: run [`tier2-gap-run.md`](tier2-gap-run.md) first |
| ✏️ **Devin asks** | which gap run; the `.65` start per global table — DEV: `next-free` allowed; PRE / PROD: the range the BOX team agreed (open item 4zx); a value the evidence does not give (e.g. a column of the column map with no source) |
| 🔒 **Never** | a value without its source; an open (`<…>`) or masked (`H…`) value; SQL written by hand; a PK typed by hand |

---

**If you were pointed at this file**, it is your task prompt. You are the `sigom-box-acc-configs-agent`, **phase 2**.

**Step 1 — read:** `agents/sigom-box-acc-configs-agent/AGENT.md` (Phase 2, hard rules), ADR 0018, 0020, 0022, 0023, the
header of `scripts/render_acc_sql.py`, `agents/sigom-box-acc-configs-agent/templates/acc-values.example.json`.

**Step 2 — the run.** Ask which gap run (list `runs/NY_SCH/<tier>-<env>/acc-configs/RUNS.md`); the SQL step works in
that run's folder (a run on a PR branch: merge the default branch into it first; files already in `03-sql/` are
re-rendered, the CSVs in `01-evidence/` never asked again — ADR 0023). Check it is finished: matrix and report
written, `decisions.pp_clash_mode` filled, the condition map with no pair `to confirm`. **Clash mode (a) with no
`pp_clash_choices` is not a stop** `[operator, 2026-10-29 — ADR 0023]`: the groups are held and not carried. Stop
only for what a **carried** row needs: an `ask` unanswered that it depends on, a multi-account case unanswered on a
carried property. Everything held, OPEN (a condition value with no BOX value, an account no source has) or out of
scope is **not carried** — listed with its reason and source under `_not_carried` in `acc-values.json` (a comment
key: the renderer ignores it), never as a row. A lookup
the evidence does not hold (e.g. A-10e) is the catalogue's query, named as such.

**Step 3 — `03-sql/acc-values.json`**, from the template, every entry with `source` (file:line or decision + date):
- `auth_code` (A-P5 b), `group_pk` (A-G1), `branch_pk`; `owners` for the tables the template asks (A-P2);
- `global_topics` / `standard_historics`: the matrix's *Global objects — to review* section, rows through the column
  map; `global_pk`: asked (Step 4);
- `accounts`: screen 10's `create` rows (+ date rule, A-10d), columns through the column map (A-P7) — only the
  accounts the carried rows use; type and direction by `CODE` (A-10a codes → A-10e PKs); the Net CCS accounts from
  the reference's BOX row (A-13a), the others from A-10a; **never** a column BOX sets itself (`LOC_CODE`,
  `HOSTINTERFIND`, `STATUS`… — the renderer refuses them, `column-computed`);
- `local_properties`: per instrument in scope, ADR 0020 — the in-scope GBO properties' topics by `CODE` in their GBO
  list (A-04e) and their conditions **with a BOX twin**, as the target's PKs (condition map + A-01-TGT); start
  `1900-01-01`;
- `portfolio_properties`: one per `Valid` in-scope GBO property (clash mode a: the chosen one of each group only;
  mode b: all, the clashing ones `expect_invalid: true`); `description` = GBO's; `inivalpcdate` = the decision;
  `conditions` = its GBO values translated (condition map); `accounts` per list = its own GBO rows (topics by `CODE`;
  `multi_account_topics` applied; internal list → the internal account);
- `rows`: Cross Account Config (A-03a through the column map), Conf Instru Type (A-12), Net CCS PlanBS (if it applies).

**Step 4 — render and refuse.** `python3 scripts/render_acc_sql.py <run> --precheck`. Each `REFUSED <code>` names the
field: fix it from the evidence or ask the operator **that one** question; never weaken a value to pass. Then hand the
operator `03-sql/<base>-precheck.sql`:

> *Run it in SQL Developer (F5) with your BOX_ACC account on <env>. Save the whole Script Output as
> `03-sql/<base>-precheck-output.txt` and commit it.*

`ACC PRECHECK PROBLEM` → show each `PROBLEM` line: a sequence behind → its proposal to the BOX team; a signature that
differs → stop, report it (the renderer must be changed); a code / condition missing → back to the values. Run the
precheck again until OK.

**Step 5 — the files.** `python3 scripts/render_acc_sql.py <run>` → `<base>-rehearsal.sql`, `-config.sql`,
`-verify.sql`, `render-report.md`. Tell the operator, in this order:
1. rehearsal (it ends with ROLLBACK) — `SUMMARY|problems|0` expected; any `PROBLEM|` → back to the values;
2. config — save the whole output as `03-sql/<base>-config-output.txt` and commit it;
3. verify — each query says its expected result;
4. then `python3 scripts/render_acc_sql.py <run> --rollback` → `<base>-rollback.sql` and `global_pk_rollback.sql`
   (only to undo the config).

**Step 6 — finish:** the render report, `_not_carried` (what and why), the `STATUS|` lines of the config output (every property `Valid` except
`expect_invalid`), what was skipped as `PRESENT|`, the global objects created (to review). Commit the run folder.
