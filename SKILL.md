---
name: box-fe-parallel-test
description: Prepares and follows the BOX FE parallel test of a new branch - GBO and BOX running side by side in the PRE Paralelo environment over a period, the whole branch reconciled every day with the breaks followed from day to day until sign-off. Use when the operator wants to run or follow the parallel (full) test.
---

# BOX FE parallel test (full test)

`[operator, 2026-10-09]` The third of three tests of a new branch's BOX FE (after the
[technical test](../box-fe-technical-test/SKILL.md) and the [Y test](../box-fe-y-test/SKILL.md)): **the whole branch,
every day of a period, GBO and BOX give the same results**. Basics only, to be completed after the Y test
`[operator, 2026-10-09]`. Same mechanics as the Y test - the same script and field map - on the whole population
(no trade list: the branch's filter per side) and several dates, with the breaks followed day to day.

**Script:** `scripts/fe_reconcile.py` (folder: `scripts/new_run.py`). **Where to look:** [`box-fe-test-lookups.md`](../../docs/reference/box-fe-test-lookups.md) - a break that is a trade
missing in BOX is traced and diagnosed as in the Y test. **Reference:**
[`gbo-box-fe-field-map.csv`](../../docs/reference/gbo-box-fe-field-map.csv).

## The rules

| Rule | Source |
|---|---|
| NY_SCH: BOX in the PRE Paralelo environment **IGBOUSIB**; the GBO environment and the period are asked | operator, 2026-10-09 |
| The products the operator chooses (`products`); the population is the branch's, by a filter per side (`gbo_filter`, `box_filter`, also per product), never a trade list | basics / operator, 2026-10-13 |
| Each date's CSVs in `01-evidence/<YYYY-MM-DD>/` (`gbo-<product>-<area>.csv`, `box-<product>-<area>.csv`); `compare` reconciles every date present | basics |
| `04-breaks.csv`: each break (key, area, field) with first / last date seen, days, state `NEW` (today only), `OPEN` (still there), `RESOLVED` (gone) | basics |
| **The trade key is the GBO `DEAL_ID`**: BOX's `DEAL_ID` through the AUKI migration crosswalk `BOX_MIG.T_BOX_AUKI_MIG_DEALS_S` (`FK_AUKI_ID` → `REGISTRY`) for the branch (input `gbo_branch`); never `FRONT_ID` (it differs between the systems). `sql/05-crosswalk-checks.sql` runs first - a GBO deal with no crosswalk row can only be ONLY_GBO, and that is reported as such, not as a BOX defect | operator, 2026-11-24 - [ADR 0029](../../docs/decisions/0029-gbo-box-trade-key-auki-migration-crosswalk.md) |
| `03-results.md` counts duplicate keys per side (a key twice in one CSV: only its first row compared) - a duplicate means the key misses a column (e.g. the leg) | ADR 0029 |
| Sign-off criteria (no `OPEN` break? a threshold? days in a row?) - asked, OPEN until the operator decides | OPEN |

## How to run

```bash
python3 scripts/new_run.py --branch NY_SCH --tier tier2 --env preparalelo --area tests/parallel --name depos
cp runs/NY_SCH/tier2-preparalelo/tests/parallel/parallel-test-inputs.NY_SCH.json <run>/parallel-test-inputs.json
python3 scripts/fe_reconcile.py pack <run>/
# first: sql/05-crosswalk-checks.sql (counts) - then every day: the operator returns 01-evidence/<YYYY-MM-DD>/gbo-<product>-<area>.csv and box-<product>-<area>.csv
python3 scripts/fe_reconcile.py compare <run>/     # 03-recon/, 03-results.md, 04-breaks.csv
python3 scripts/fe_reconcile.py compare <run>/ --date <YYYY-MM-DD>   # one day only
```

## Failure modes

| Symptom | Code | Meaning |
|---|---|---|
| refused before writing | `inputs-missing` | no `parallel-test-inputs.json` in the run folder |
| refused before writing | `run-frozen` | the period is closed - a new version |
| refused | `map-missing` | the field map file is not where the inputs say |
| `compare` refused | `evidence-missing` | no `01-evidence/<YYYY-MM-DD>/` folder |
| `compare` refused | `key-missing` | the key column of the map is not in a CSV (or still OPEN) |

## Never

- Run anything on a database. Close a break without its explanation in `03-results.md`.

## Eval cases

[`evals/cases/box-fe-parallel-test.md`](../../evals/cases/box-fe-parallel-test.md).
