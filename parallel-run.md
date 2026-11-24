# Kickoff — parallel run: GBO's file vs BOX's, until no difference is unexplained

Agent: [`box-report-migration-agent`](../AGENT.md). Starts when the BOX file of one date passes
`check_fixed_width.py` ([`build.md`](build.md)).

## For each process date of `report-inputs.json` `dates`

1. The operator puts both files in `local/`: GBO's own output for the date and the BOX spool. Id files only if the
   two files print different trade ids (a D1 answer other than GBO's id): `local/box-ids.csv` mapping BOX's id to the
   GBO `DEAL_ID` × 100 through the AUKI migration crosswalk (R-B6, ADR 0029) — never through `FRONT_ID`.
   **Steps 2 and 3 run on the operator's PC** (standard-library Python): the agent writes the exact commands and
   receives the reports, never the files (hard rule 6).
2. Both checked: `check_fixed_width.py` → `05-compare/<date>-gbo-check.md`, `05-compare/<date>-box-check.md`.
3. Compared:
   `python3 scripts/compare_fixed_width.py local/<gbo file> local/<box file> --layout <report folder>/layout.csv
   --gbo-ids local/gbo-ids.csv --only <the scope filter> --expect 05-compare/expected-differences.csv
   --out 05-compare/<date>.md --detail <a path outside the repository>`
4. Every difference reported is one of:
   - **expected** — a row in `05-compare/expected-differences.csv` (`field,gbo_value,box_value,class`) whose class is
     a decision or deviation id (`D1`, `DV7`…), added with the reason in the comparison's notes;
   - **a defect of the SELECT** — fixed in `04-sql/`, the date run and compared again;
   - **new** — a decision or deviation proposed (status `default`), never an `--expect` row without one.
   GBO-only / BOX-only records: a product out of scope belongs in the `--only` filter; a portfolio property that
   picks other accounts in BOX (a clash group, a consolidated property) is named with its property.
5. The date is done when its comparison ends `UNEXPLAINED|0`.

## The dates

At least: a normal day, a month-end, a day with maturities, a day with a cancellation or early termination. One date
`UNEXPLAINED|0` is not enough for go-live (`check_report_run.py --go-live` asks for one; the operator asks for the
others).

## When every date is done

`python3 scripts/check_report_run.py <run>` → `REPORT RUN OK`; `--go-live` lists what is still pending (decisions,
deviations, OPEN rows). The packaging for production (procedure, batch, directory — D7) is a separate step after the
owners' answers.
