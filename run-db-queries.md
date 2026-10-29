# Case: an agent's queries through the DB relay, and the fallback to manual

Covers: run-db-queries (`scripts/relay_ask.py`, `scripts/db_relay.py`) — **proposed**, ADR 0021
Type: happy path + failure paths

Mechanically covered by `scripts/tests/test_db_relay.py` (guard, one request, refusals, errors, row cap, review, a
fake SQL*Plus, passwords, `relay_ask` batches, `--watch` on a branch pattern, no relay → exit 3).

## Given

A run in `tier2-dev` with DB access mode **relay** (the operator answered at the start of the run); the relay running
on the operator's PC (`--watch --branches "devin/*"`); a step with four catalogue queries, three independent.

## When

1. The agent fills in the three independent queries and calls `relay_ask.py` once with the three.
2. One of them calls a package function (e.g. `f_getPKByLabel`).
3. Later the operator stops the relay and the agent sends the fourth query.

## Then

- The three go in **one** call (one push); each names its system (`GBO`, `BOX_ACC`…), never an account or password.
- The package call is refused before anything is pushed (`sql-package-call`, exit 2): the agent hands that query to
  the operator (manual) — it does not rewrite the catalogue's query to get past the guard.
- The answers land in `01-evidence/` under the catalogue's names; the agent reads them and goes on.
- The fourth: exit 3 — the agent tells the operator once, switches the run to manual, says so in the run's inputs.
- **Fail:** a query sent in production or in an environment not allowed; DML / PL/SQL sent; a password, a connection
  string or an account chosen by the agent in any file, log or message; independent queries sent one call each; the
  guard bypassed; relay mode used without the operator's answer at the start of the run.
