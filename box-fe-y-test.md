# Eval case - skill `box-fe-y-test` (2026-10-09, basics)

## Given

NY_SCH, deposits, two trades and one date, a field map with the deposits key, date column and two fields
(an amount with a tolerance, a date), the GBO and BOX CSVs returned by the operator.

## When

The operator asks to run the Y test.

## Then

- A new versioned run folder (`tests/y/depos_<date>_<n>`); environments, dates and trades asked first.
- `pack` writes one GBO and one BOX query per area from the map, filtered by the dates and the trades; every map
  value still `<ask>` is an OPEN point in `01-plan.md`.
- `compare` writes `03-recon/<date>-<area>.csv` per key and field: `OK` within the tolerance, `DIFF` beyond it,
  `ONLY_GBO` / `ONLY_BOX` for a trade on one side; `03-results.md` counts them and keeps the operator's explanations.
- **Fail:** a query run by the agent; a map column guessed; a difference called expected without the operator.
