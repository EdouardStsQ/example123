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
7. **Render** — one column, the record, aliased `rec`: each field `RPAD(NVL(<value>, ' '), <width>, ' ')` with the widths of
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

## Step 1b — efficient by design (hard rule 11)

The GBO specification describes **what** each field holds and **how** GBO computes it; only the what is reproduced.
GBO's how — a cursor over the deals, a procedure per deal for the status, the early termination or the maturity, a
function per record for the GL account code, the same financial table or MTM view queried again for every deal — is
listed in the gap report's *GBO implementation* section and replaced by:

| GBO pattern | In the BOX SELECT |
|---|---|
| a cursor, then one query per deal | one `WITH` block per source, filtered to the process date and branch, joined to the deals |
| a function call per record (account code, account number) | a join to the account table on its key |
| a status / early-termination / maturity procedure per deal | one block that aggregates the source once (e.g. a `COUNT` per deal, the latest row with `ROW_NUMBER()`), joined |
| a view queried per deal | the view (or its base table, when the view adds nothing the field needs) read once for the date |
| a calendar function per deal | one block of the calendar dates the run needs |
| decodes read from a table | `CASE` from `decodes.csv` |
| `DISTINCT` / `UNION` | `UNION ALL` — duplicates are content (hard rule 2) |

Predicates keep the column bare (`DDATE >= :d AND DDATE < :d + 1`, not `TRUNC(DDATE) = :d`) so an index or a
partition can serve them. Hints only with a measured reason, written in the performance file.

## Step 1c — measure (the operator, read-only)

`04-sql/<report>-box-performance.md`, for the same date as the spool:

1. **The plan**: `EXPLAIN PLAN FOR <the SELECT>;` then
   `SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY(NULL, NULL, 'TYPICAL'));` — pasted as it is. The agent reads it for
   `FILTER` steps over subqueries and repeated scans of the same table, and says which line of the SELECT each comes
   from.
2. **A timed full run without the spool** (timing lines would corrupt the file):
   `SET TIMING ON` then `SELECT COUNT(*) n, SUM(LENGTH(rec)) chars FROM (<the SELECT>);` — `SUM(LENGTH(...))` forces
   every column to be computed; `n` must equal the spool's record count and `chars` = `n` × the record length.
3. **GBO's baseline**: the elapsed time of the GBO job that wrote the file for that date (its batch log or the
   scheduler's run time), when the operator can get it; otherwise `unknown` — never estimated.

A first version that is correct but slow is still a correct first version: the comparison comes first, then the
plan's worst step is fixed and measured again, and the date compared again (the content must not move).

## Step 2 — the operator runs it, the checker reads the file

The operator runs it in the target with the run's BOX account for one date and keeps the spool in `local/`. Then:
`python3 scripts/check_fixed_width.py local/<file> --layout <report folder>/layout.csv --out 05-compare/<date>-box-check.md`.
`CHECK FAIL` → fix the SELECT (never the file), run again. The GBO file of the same date is checked the same way
(`<date>-gbo-check.md`): the layout must fit GBO's own output first.

## Step 3 — then the parallel run

[`parallel-run.md`](parallel-run.md).
