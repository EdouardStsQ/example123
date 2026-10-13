# Eval case - skill `box-fe-y-test` (2026-10-09, basics)

## Given

NY_SCH, the products the operator chose (e.g. deposits, or deposits + IRS), their trades and one date, a field map with the deposits key, date column and two fields
(an amount with a tolerance, a date), the GBO and BOX CSVs returned by the operator.

## When

The operator asks to run the Y test.

## Then

- A new versioned run folder (`tests/y/<products>_<date>_<n>`); the products asked (never assumed), then environments,
  dates and each product's trades.
- `pack` writes one GBO and one BOX query per area from the map, filtered by the dates and the trades; every map
  value still `<ask>` is an OPEN point in `01-plan.md`.
- `compare` writes `03-recon/<date>-<product>-<area>.csv` per key and field: `OK` within the tolerance, `DIFF` beyond it,
  `ONLY_GBO` / `ONLY_BOX` for a trade on one side; `03-results.md` counts them and keeps the operator's explanations.
- With the deposits financial rows of the map (link to the deal tables, key `FRONT_ID`, date `DDATE`, no field rows):
  the queries join each financial table to its deal table and every common column is compared (auto); a trade
  `ONLY_GBO` sends the agent to `sql/30-BOX-trace.sql` / `sql/70-BOX-diagnose.sql` before calling it a difference.
- For CCS the GBO query reads `DEVENG.T_PGT_SWFINANCST_S` (GBO code SW), the BOX one `T_BOX_CCSFINANCST_S`; for OTC
  there are five GBO queries (OB, OE, OF, OI, OS), read together against `T_BOX_OTCFINANCST_S`.
- **Fail:** a GBO table name built from the BOX code (`T_PGT_CCSFINANCST_S`); a query run by the agent; a map column guessed; a difference called expected without the operator.
