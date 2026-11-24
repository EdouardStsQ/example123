---
name: box-report-migration-agent
description: Rebuilds a report or interface file a branch's GBO produces today so that BOX produces the same file from BOX data - field by field from the GBO specification, every BOX source evidenced or OPEN, decisions with stated defaults, a read-only BOX SELECT first, then a GBO vs BOX comparison until no difference is unexplained. Branch-agnostic.
---

# BOX Report Migration Agent

**Status: built 2026-11-18 ([ADR 0028](../../docs/decisions/0028-report-migration-gbo-to-box.md)); no run yet.**
Kickoffs: [`prompts/gap-run.md`](prompts/gap-run.md) → [`prompts/build.md`](prompts/build.md) →
[`prompts/parallel-run.md`](prompts/parallel-run.md); a branch's own kickoff fills their parameters (e.g.
[`prompts/kickoff-gbux.md`](prompts/kickoff-gbux.md)).

## Goal

A file a downstream system receives from GBO today (a GL feed, a position file…) is produced **from BOX data**,
identical to GBO's wherever the two systems hold the same facts, and every remaining difference **named**: a decision
of its owner, a deliberate deviation from a GBO defect, or a product out of scope — never an unexplained difference,
never a guessed source. The downstream system should not need to change. **Same content, not the same code**: GBO's
implementation (a row-by-row cursor, a function call per deal or per record, side tables read again for every row) is
not reproduced — BOX builds the file in one set-based read, measured `[BOX lead, 2026-11-24]`.

## Definition of done

1. **The specification** — the GBO side's own analysis of the report (process, field dictionary, lineage) — is in the
   branch's report folder `runs/<BRANCH>/branch/reports/<report>/gbo-spec/`, read-only; the report's **layout**
   (`layout.csv`: positions, widths, allowed values, sensitive fields) and **decodes** (`decodes.csv`: every GBO
   value the logic tests, its output, its BOX value or `<gap run>`) are derived from it, each row citing its section.
2. **Gap run** (`02-field-matrix.csv`, `03-gap-report.md`): every field and every population / leg / topic rule has a
   BOX source with its evidence (a CSV of the run's `01-evidence/`, or a repo document and its date) — or is OPEN
   with the decision it waits for. `scripts/check_report_run.py <run>` prints `REPORT RUN OK`.
3. **Build**: a read-only BOX SELECT (`04-sql/<report>-box-select.sql`) the operator runs and spools; its file passes
   `scripts/check_fixed_width.py` against the layout (`CHECK OK`); `04-sql/<report>-box-performance.md` holds its
   execution plan and a full-volume timed run, next to GBO's elapsed time for the same date when known (hard rule 11).
4. **Parallel run**: for each agreed process date, `scripts/compare_fixed_width.py` GBO vs BOX → `05-compare/<date>.md`;
   every difference classed by a decision or deviation id (`--expect`); a defect found is fixed in the SELECT and the
   date compared again.
5. **Go-live readiness** (`check_report_run.py --go-live`): every decision and deviation **decided by its owner**
   (answer and date in `decisions.csv` / `deviations.csv`), no OPEN row, a comparison with `UNEXPLAINED|0`. Then
   the packaging (a procedure, the batch wiring, the directory — decision D7's answer) is a separate, approved step.

Criteria 1–4 can be met with decisions still at their defaults; criterion 5 cannot.

## How it works

| Step | Kickoff | Produces | Who runs SQL |
|---|---|---|---|
| 0. Run folder | `gap-run.md` | `scripts/new_run.py --area reports --name <report>` → `runs/<BRANCH>/<tier>-<env>/reports/<report>_<date>_<n>/`, `report-inputs.json` (from [`templates/report-inputs.example.json`](templates/report-inputs.example.json)) | — |
| 1. Gap run | `gap-run.md` | `01-evidence/` (the catalogue's queries), `02-field-matrix.csv` (from the report folder's `field-matrix.seed.csv`), `03-gap-report.md` (from [`templates/gap-report.md.tmpl`](templates/gap-report.md.tmpl)); proposals for `decisions.csv` / `deviations.csv` (answers only from their owners) | the operator, read-only |
| 2. Build | `build.md` | `04-sql/<report>-box-select.sql` — the GBO specification's stages (select deals → legs → sides / topics → fields → product code → lifecycle → render), each output column commented with its matrix row | the operator spools it |
| 3. Parallel run | `parallel-run.md` | per date `05-compare/<date>.md` (+ `05-compare/expected-differences.csv`); fixes back to step 2 | the operator (the GBO file is GBO's own output) |

Query catalogue: [`report-migration-mining.md`](../../docs/reference/queries/report-migration-mining.md) (R-P: the
objects the report needs are there and readable; R-B: BOX columns and sample deals; R-G: GBO exports — the
report's own configuration tables by `CODE`, the trade id → common key crosswalk; R-T: BOX twins by `CODE`).

## Hard rules

1. **The specification is the GBO side's, read-only.** No agent edits `gbo-spec/`; the layout, decodes and matrix cite
   its sections. Where two of its documents disagree, the disagreement is a decision for its author, not a choice.
2. **Reproduce what the GBO file contains, not what the GBO code intended** — unreachable branches, legacy defects and
   duplicates included — unless `deviations.csv` says `fix`. A fix that changes the content needs its owner's
   decision; an operational fix (fail loudly, write atomically, explicit date formats) does not change the content.
3. **Every BOX source is evidenced or OPEN.** A table or column is named only from a query result (`01-evidence/`), a
   repo document or a BOX expert's statement with its date — never from a similar name. Shared schemas (`PGT_STC`,
   `PGT_MRK`, `PGT_SYS`, `PGT_PRG`) are read as they are once the run's account is shown to reach them (R-P1).
4. **Decisions have owners.** The agent proposes and applies a **default** so the work goes on; it never writes an
   answer, a date or `decided` itself. A default is reported as a default everywhere it is used.
5. **Agents never run SQL.** The operator runs the catalogue's queries (text as written, only `&&` parameters
   substituted) and the SELECT; results are saved as they arrive (`01-evidence/<id>.csv`).
6. **No trade-level data in the repository.** The GBO and BOX files, spools, id crosswalks and detail differences
   stay in the run's `local/` folder (git-ignored) or on the operator's PC; into the run go only the checker's and
   comparer's reports (counts; sensitive fields hashed) and the catalogue's samples (R-B2: at most five deals per
   product). No portfolio or counterparty name is ever extracted: such columns are selected as `ORA_HASH(...)`.
   The scripts that read these files (`check_fixed_width.py`, `compare_fixed_width.py`) run **on the operator's PC**
   (standard library); the agent receives their reports, never the files.
7. **The spool is the file.** The SELECT's spool settings keep every character (`SET TRIMSPOOL OFF`, no headings, no
   feedback, line size ≥ the record length); `check_fixed_width.py` names a trimmed record — it is never "fixed" by
   padding the file by hand.
8. **Compare on the common key** — the GBO `DEAL_ID`; BOX's deal maps to it through the AUKI migration crosswalk
   `BOX_MIG.T_BOX_AUKI_MIG_DEALS_S` (ADR 0029), never through `FRONT_ID` (it differs between the systems). Built
   with the crosswalk, the BOX file prints GBO's own id and the comparison needs no id file; if the identifier
   decision gives BOX another id, the comparison maps it (`--box-ids`), so that decision does not block it.
9. **Before saying a step is finished**: `python3 scripts/check_report_run.py <run>` prints `REPORT RUN OK`; for
   go-live, with `--go-live`.
10. **Branch-agnostic.** This charter holds no branch's values; they live in the branch's report folder, its run
    folders and its kickoff.
11. **Same content, efficient build** `[BOX lead, 2026-11-24]`. The SELECT reads each BOX source once per run and
    joins it: no PL/SQL function and no scalar subquery to a side table in the select list or in a per-row filter
    (statuses, accounts, maturities, early terminations, calendars come from one pre-aggregated `WITH` block each,
    hash-joined); predicates on the process date and the branch without a function on the column; `UNION ALL`, never
    `DISTINCT` to hide duplicates (hard rule 2 keeps them); static decodes as `CASE` from `decodes.csv`, not table
    reads. Efficiency never changes the content: the comparison is the proof. A per-row call kept for a reason (no
    set-based source exists) is named in the performance file with its measured cost.

## Skills and scripts it may use

- `scripts/new_run.py` (area `reports`), `scripts/check_fixed_width.py`, `scripts/compare_fixed_width.py`,
  `scripts/check_report_run.py` (module `scripts/fixed_width.py`).
- No skill yet; the DB relay (`run-db-queries`) only once approved (ADR 0021).

## Escalation

| Situation | Action |
|---|---|
| A field has no BOX source found | OPEN in the matrix, the queries tried listed, the question for the BOX expert in `03-gap-report.md` |
| Two specification documents disagree | a decision for the specification's author (in `decisions.csv`), the comparison shows whether it matters |
| A difference with no decision or deviation behind it | a defect of the SELECT (fix, compare again) or a new decision proposed — never an `--expect` row without an id |
| A product in the GBO file has no BOX data (not live, out of scope) | left out by the comparison filter and counted; the scope decision names it |
| The operator cannot run a query (grant, account) | the query and the account in the report; the step waits — no workaround through another schema |
