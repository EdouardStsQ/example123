---
name: box-fe-y-test
description: Prepares and records the BOX FE "Y" test of a new branch - GBO vs BOX for the same trades and dates, field by field (deal, financial and MtM data), from the GBO / BOX field map; the extraction queries, the reconciliation of the returned CSVs and the results. Use when the operator wants to run or follow the Y test (after the technical test).
---

# BOX FE "Y" test (GBO vs BOX)

`[operator, 2026-10-09]` The second of three tests of a new branch's BOX FE (after the
[technical test](../box-fe-technical-test/SKILL.md), before the [parallel test](../box-fe-parallel-test/SKILL.md)):
**the same trades give the same results in GBO and in BOX**. Basics only, to be completed when the Y test starts
`[operator, 2026-10-09]`. No agent touches a database: the skill writes the queries, the operator runs them and
returns each output as a CSV, the script reconciles them. A value it does not have is an **OPEN point** in
`01-plan.md`, asked to the operator - never guessed.

**Script:** `scripts/fe_reconcile.py` (folder: `scripts/new_run.py`), shared with `box-fe-parallel-test`.
**Reference:** [`gbo-box-fe-field-map.csv`](../../docs/reference/gbo-box-fe-field-map.csv) - per product and area the
GBO and BOX tables (BOX names confirmed; GBO codes INFERRED), the key, the date column, the fields to compare, their
kind and tolerance. Seeded with the tables only: the keys, dates and fields are OPEN until the Y test starts.

## The rules

| Rule | Source |
|---|---|
| Three areas per product, as the SIGOM Financial Status menus: **deal** (GBO `T_PGT_<CODE>DATAMIS_S` per product ↔ BOX `T_BOX_DATADEAL_S` shared), **financial** (`T_PGT_<CODE>FINANCST_S` ↔ `T_BOX_<CODE>FINANCST_S`), **mtm** (GBO `T_PGT_<CODE>RISK_S` table ↔ BOX `V_BOX_ENG<CODE>DATAMIS_S` view - equivalence open) | box-data-model.md, sigom-reference.md |
| One key per area: the column holding the same trade id on both sides; a trade on one side only is `ONLY_GBO` / `ONLY_BOX` | basics |
| Amounts compare within `tol_abs` or `tol_rel` (either passes); dates by day whatever the CSV format; text trimmed, upper case | basics |
| Every `DIFF` / `ONLY_*` / `NO_COLUMN` is explained in `03-results.md` (map fix, known difference, defect) before sign-off | basics |
| NY_SCH environments: DEV **DGBOUS**, PRE Paralelo **IGBOUSIB**; which one the Y test uses is asked | operator, 2026-10-09 |

## How to run

```bash
python3 scripts/new_run.py --branch NY_SCH --tier tier2 --env <env> --area tests/y --name depos
cp skills/box-fe-y-test/y-test-inputs.example.json <run>/y-test-inputs.json      # then fill it
python3 scripts/fe_reconcile.py pack <run>/       # 01-plan.md + sql/10-GBO-<area>.sql, sql/20-BOX-<area>.sql
# the operator returns 01-evidence/<YYYY-MM-DD>/gbo-<area>.csv and box-<area>.csv
python3 scripts/fe_reconcile.py compare <run>/    # 03-recon/<date>-<area>.csv, 03-results.md
```

## Steps

1. Ask, one at a time: product, the GBO and BOX environments, the date(s), the trades (their key values).
2. `pack`; show `01-plan.md` and ask its OPEN points (most are field-map rows: key, date column, fields - fill
   `docs/reference/gbo-box-fe-field-map.csv`, then `pack` again).
3. The operator runs the queries and returns the CSVs; `compare`.
4. For each non-OK line: say what it means and ask - fix the map (tolerance, column) and compare again, or record it
   as a known difference or a defect in `03-results.md`.
5. End: `03-results.md` explained line by line; freeze the run.

## Failure modes

| Symptom | Code | Meaning |
|---|---|---|
| refused before writing | `inputs-missing` | no `y-test-inputs.json` in the run folder |
| refused before writing | `run-frozen` | the run is finished - a new version (`new_run.py`) |
| refused | `map-missing` | the field map file is not where the inputs say |
| `compare` refused | `evidence-missing` | no `01-evidence/<YYYY-MM-DD>/` with the CSVs |
| `compare` refused | `key-missing` | the key column of the map is not in a CSV (or still OPEN) |
| `NO_COLUMN` lines | - | a mapped field is not in the CSV: the query or the map is wrong |

## Never

- Run anything on a database. Call a difference "expected" without the operator saying so. Guess a column of the map.

## Eval cases

[`evals/cases/box-fe-y-test.md`](../../evals/cases/box-fe-y-test.md).
