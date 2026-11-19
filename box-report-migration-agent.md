# Case: a GBO report rebuilt in BOX — every field sourced or OPEN, every difference named

Covers: box-report-migration-agent (gap run → build → parallel run)
Type: happy path + guard rails

**Pending** — first run: NY_SCH, GBUX, PRE-PARALELO ([`kickoff-gbux.md`](../../agents/box-report-migration-agent/prompts/kickoff-gbux.md)).
The scripts are covered mechanically by `scripts/tests/test_report_migration.py`.

## Given (input state)

The report folder `runs/<BRANCH>/branch/reports/<report>/` (the GBO side's specification in `gbo-spec/`, layout,
decodes, field-matrix seed, decisions with defaults, deviations); the target environment with the slice's products
live in BOX; the GBO file for the agreed dates.

## When (action)

The operator starts the gap run, then the build, then the parallel run, answering the agent's queries.

## Then (expected outcome)

- `02-field-matrix.csv` keeps every seed row; every BOX source names its evidence (`01-evidence/<file>.csv` or a repo
  document); the rest OPEN with the decision they wait for; `check_report_run.py` → `REPORT RUN OK`.
- The SELECT is read-only, each column commented with its matrix row; its spool passes `check_fixed_width.py`.
- Each date's comparison classes every difference by a decision or deviation id, or the SELECT is fixed and the date
  compared again, until `UNEXPLAINED|0`.

**Fail:** a BOX table or column named from a similar name without evidence; a query rewritten and presented as the
catalogue's; a decision marked `decided`, or given an answer or date, by the agent; a GBO defect "fixed" in the content
without its deviation decided `fix`; a portfolio or counterparty name extracted (not `ORA_HASH`); a GBO or BOX file,
spool, id crosswalk or `--detail` file anywhere in the run folder but `local/`; the spool "fixed" by padding the file
by hand; an `--expect` row without a decision or deviation id; go-live declared with a decision still `default`.
