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

## Case 2 - the standard assessment (2026-11-25, ADR 0030)

**Given** the pack's exports for a date (financial, deal, flows). **When** the operator asks whether BOX matches GBO.
**Then** `fe_assess.py` runs first; the answer gives the funnel, the headline and the Issues table with examples;
only `DIFF - unexplained` rows are investigated, each from BOX's code (`cib-boxfin-dbboxfe`, file:line) or on GBO's
data, and a confirmed cause is proposed as a rule.
**Fail:** an improvised query where the pack has one; a deal with missing data counted as a calculation difference;
a difference explained without code or data; an id, amount or the xlsx committed outside `local/`.
