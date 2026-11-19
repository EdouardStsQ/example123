# Kickoff — build: the report as a read-only BOX SELECT

Agent: [`box-report-migration-agent`](../AGENT.md). Starts from a gap run whose `check_report_run.py` printed
`REPORT RUN OK` and whose matrix the operator reviewed. Decisions may still be defaults — each one used is named in
the SQL's header.

## Step 1 — the SELECT

Write `04-sql/<report>-box-select.sql` (one statement; read-only — `SELECT` / `WITH` only) following the stages of the
GBO specification, in this order:

1. **Deals** — the population rules of the matrix (`P*` rows) for the slice's products, one process date
   (`&&process_date`, `DD-MON-YYYY`).
2. **Legs** — one row per product leg where the product has legs (`L*` rows).
3. **Sides and topics** — the buy and sale topic rows from the report's topic table copy (`T*` rows) joined to the
   deal's portfolio-property account list; the extra records the specification adds (e.g. a deposit's opposite
   record). Duplicates stay (hard rule 2).
4. **Fields** — each column from its matrix row, decoded with `decodes.csv`; a comment above each one:
   `-- F<n> <name>: <matrix box_source> [<decision / deviation id>]`.
5. **Derived fields** — built from the others in the specification's effective order (not its intended one).
6. **Lifecycle** — the status, early-termination and maturity fields.
7. **Render** — one column, the record: each field `RPAD(NVL(<value>, ' '), <width>, ' ')` with the widths of
   `layout.csv`, concatenated in field order; `SUBSTR(..., 1, <width>)` where a value could be longer.

The header of the file: the run, the layout's record length, the decisions and deviations it applies with their
status (`default` / `decided`), and the spool settings the operator uses:

```sql
SET TERMOUT OFF FEEDBACK OFF HEADING OFF PAGESIZE 0 VERIFY OFF ECHO OFF
SET LINESIZE 32767 TRIMSPOOL OFF TRIMOUT OFF TAB OFF
SPOOL local/<REPORT><YYMMDD>.box
-- the SELECT
SPOOL OFF
```

`TRIMSPOOL OFF` matters: with `ON` the trailing spaces of the last field are lost and every record is short.

## Step 2 — the operator runs it, the checker reads the file

The operator runs it in the target with the run's BOX account for one date and keeps the spool in `local/`. Then:
`python3 scripts/check_fixed_width.py local/<file> --layout <report folder>/layout.csv --out 05-compare/<date>-box-check.md`.
`CHECK FAIL` → fix the SELECT (never the file), run again. The GBO file of the same date is checked the same way
(`<date>-gbo-check.md`): the layout must fit GBO's own output first.

## Step 3 — then the parallel run

[`parallel-run.md`](parallel-run.md).
