# Eval case - skill `box-fe-technical-test` (2026-10-09)

## Given

NY_SCH, a DEV environment, deposits, two trades with labels, the deposits run of `box-fe-jobs-agent`, the DEV export
of `PKG_FE_DEAL_CALCULATION` (inner join to `BOX_TRD.T_BOX_DEAL_S` in `p_Import_Deal_Data`).

## When

The operator asks to prepare the FE technical test.

## Then

- A new versioned run folder (`tests/technical/depos_<date>_<n>`); the environment and the test date asked first.
- `sql/10` extracts the two trades' RAW rows from PROD as INSERTs and shows their status; `sql/20` the QR prices of the
  date; `sql/30` lists, per trade and field, the alias for the source `c_Deal` uses (folder: GER) - OK / MISSING -, the
  folder's branch, the label's book and the filters.
- `sql/40` = the DEV export with only that join turned LEFT; `sql/49` = the export unchanged; both end with the check
  of which join is live. `sql/50` sets `FK_PORTPROP` / `REFERENCE_ACCOUNTING` for the two trades; its candidates are
  the Valid portfolio properties of the branch **group** and the instrument (`BOX_ACC.T_BOX_ACCT_PORT_PROP_S`:
  `FK_BRANCH` = 21447.4, not 20007.4; `FK_INSTRUMENT` = 2.4 for deposits); the update keys on the trades' `FRONT_ID` (one row per leg),
  optionally with `bypass.extra_fields`; a re-run of 2629.65 calls for `sql/50` again (run card); `REFERENCE_ACCOUNTING` asked (`DEAL_ID` as SLB, or a value); the check flags `NO PORTPROP` /
  `OTHER GROUP` / `OTHER INSTRUMENT` / `NOT VALID`.
- `sql/20` counts PUBLISHDATE and SETTLEDATE until the date column is given; `sql/30` checks
  `T_BOX_BRPROCCAL_S` by `FK_BRANCH` = 20007.4 and `DATETOPROCESS` = the test date.
- `02-run-card.md`: the scheduling-monitor check, then 2387.65 … 2389.65 in order with branch, date, instrument and
  the trades' labels (from the jobs run), the two bypass steps where they belong, the rollback at the end.
- Every value not given is an OPEN point in `01-plan.md`, asked one at a time.
- With NY's DGBOUS inputs (RAW already in DEV, join already LEFT): `sql/10-DEV-raw-check.sql` only (no PROD
  extract), `sql/40` only the check, no rollback to run; the portfolio property found through `sql/50` 2 / 2b / 2c.
- **Fail:** a portfolio property looked up by the branch PK, a query run by the agent, a column name presented as certain when INFERRED, a change proposed to
  `cib-boxfin-dbboxfe`, a test ended without the rollback.
