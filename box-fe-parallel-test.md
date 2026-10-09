# Eval case - skill `box-fe-parallel-test` (2026-10-09, basics)

## Given

NY_SCH in IGBOUSIB, deposits, the branch filter per side, three days of CSVs.

## When

The operator returns a new day's CSVs and asks for the status.

## Then

- `compare` reconciles every date present; `04-breaks.csv` lists each break with its first / last date, days open and
  state: `NEW` (only the last day), `OPEN` (since an earlier day, still there), `RESOLVED` (no longer there).
- The answer lists the `NEW` and `OPEN` breaks first, with what each needs (map fix, known difference, defect).
- **Fail:** a break closed without its explanation; the sign-off declared without the operator's criteria.
