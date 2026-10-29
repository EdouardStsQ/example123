---
name: run-db-queries
description: How an agent gets the results of its read-only queries - DB access mode "relay" (the operator's PC runs them through scripts/db_relay.py and the CSVs come back through git, one call of scripts/relay_ask.py per batch) or "manual" (the operator runs them and returns the CSVs, as before). PROPOSED (ADR 0021) - used only once the operator has approved the relay; until then every agent stays in manual mode.
---

# Run an agent's read-only queries — relay or manual

**Status: proposed** ([ADR 0021](../../docs/decisions/0021-db-relay-read-only-queries.md)). Until the operator approves
the relay after its test on DGBOUS, **no kickoff points here and every agent stays in manual mode**.

**Scripts:** `scripts/relay_ask.py` (the agent's side, in the cloud) · `scripts/db_relay.py` (the operator's side, on
their PC: guard, SQL\*Plus, passwords). **Routes and accounts:** `docs/reference/db-routes.csv`.

## The rules

1. **The mode is asked once at the start of a run** — *"DB access for this run: relay or manual?"* — default
   **manual**; written in the run's inputs file (`db_access`). Relay is possible only in an environment with
   `relay_allowed=yes` in the routes (today `tier2-dev`, DGBOUS). Never production.
2. **The query is the catalogue's**, every value filled in (no `&`), one statement per query — the agent's own hard
   rules (catalogue text as it is, one system per query, privacy) apply unchanged. `system` = the account family the
   catalogue's `Env` / account names: `GBO`, `DEVENG`, `BOX_ACC`, `BOX_FE`, `BOX_SYS`, `BOX_STC`. The account itself
   is never the agent's choice.
3. **Relay mode — one call per batch:** every query of a step that does not need another's result goes in one call:

   ```bash
   python3 scripts/relay_ask.py <run folder> --env tier2-dev \
       BOX_ACC:A-01-TGT=/tmp/q/a01.sql  GBO:A-04d-GBO=/tmp/q/a04d.sql
   ```

   - exit **0** → the CSVs are in `<run>/01-evidence/` under the catalogue's names: read them and go on;
   - exit **1** → a query refused or failed on the operator's side: its line says why (the database's error, or the
     guard). Fix only what the error names (hard rule 16: A-P8 for a column), ask again; a query the relay cannot run
     (e.g. it calls a package function) → manual for that query;
   - exit **2** → refused before sending (the guard, an unknown system, an evidence file already there): fix it or
     hand it to the operator — never rewrite a catalogue query to get past the guard;
   - exit **3** → no answer: the relay is not running. Tell the operator once, switch the run to **manual** and say
     so in the run's inputs (the pushed requests stay; the relay answers them when it starts).
4. **Manual mode** — as before: one query at a time, the environment and the account named, the CSV name given; the
   operator returns the file.
5. **Never:** a query outside the catalogue without saying why; DML, PL/SQL or a package call; a password or a
   connection string in a file, a log, the chat or a commit; production.

## Failure modes

| Failure | Detection (script code) | Handling |
|---|---|---|
| A value not filled in | `sql-unsubstituted` | fill it from the inputs / a CSV, ask again |
| More than one statement | `sql-statements` | one query per request |
| Not a query | `sql-not-select`, `sql-forbidden-word` | the relay reads only — DML / DDL / PL/SQL never go through it |
| A database link | `sql-db-link` | not run — say why the catalogue needs it |
| A package or unknown function | `sql-package-call`, `sql-unknown-function` | manual for that query (a package function can write) |
| A table never read | `sql-forbidden-table` | not asked, ever |
| An environment not allowed / a system with no account | `env-not-allowed`, `route-unknown` | manual; the operator changes `db-routes.csv` if it should be allowed |
| An answer already there / a name twice | `evidence-exists`, `name-twice` | a new name (or the operator deletes the old file) |
| A bad call | `spec-bad`, `file-missing`, `run-missing` | fix the call |
| A request the relay cannot read | `request-header`, `out-outside-evidence` | write it with `relay_ask.py`, never by hand |
| The operator declined it (`--review`) | `review-declined` | ask the operator why; manual if needed |
| No answer within the timeout | exit 3 | the relay is not running: tell the operator, manual mode |

## The operator's side (once)

In a clone of its own (never the one they work in): `python scripts/db_relay.py --save-passwords tier2-dev` (each
password checked, then kept in Windows Credential Manager), then `python scripts/db_relay.py --watch --branches
"devin/*"` while the agents run (`--review` to approve each query). Details: `scripts/README.md`.
