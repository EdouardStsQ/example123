# 0006. The SQL is rendered from a values file, never written by the agent

Date: 2026-09-24
Status: accepted `[stated: Edouard, 2026-09-24 — "yes please apply your recommendation"]`

## Context

Runs 1–5 of `sigom-box-fe-configs-agent` wrote the config SQL by hand from the templates. Each run fixed
the previous run's defects and introduced new ones **in the SQL's structure**: an UPDATE on NOT NULL
columns (run 3), a cursor field that did not exist (run 4), `chk_pk` inside `VALUES`, guards that could
not fire, 38 typed INSERTs beside an unused list, a pre-commit replaced by `COMMIT` (run 5). From run 4
some defects satisfied a validator check's wording rather than its purpose. More checks were chasing it
([`REVIEW-run-05.md`](../../runs/NY_SCH/tier2-pre/03-sql/REVIEW-run-05.md)).

## Decision

- The agent writes **`RUN_FOLDER/03-sql/values.json`** — every value with its `source` (query ID, input,
  or `decision N`). Shape: `agents/sigom-box-fe-configs-agent/templates/values.example.json`.
- **`scripts/render_sql.py`** checks the values against `00-inputs.md`, `00-decisions.md`,
  `02-findings.md`, the evidence CSVs (Q-04c, Q-06c) and the target's columns (new **Q-G3d**), refuses
  with a JSON path and a fix, and otherwise renders **four** files from the templates: `-rehearsal.sql`
  (the config block ending in `ROLLBACK`), `-config.sql`, `-verify.sql` (V1–V12), `-rollback.sql`.
- The **validator re-renders** and FAILs any `.sql` file that differs, or that it did not produce.
- The operator runs the **rehearsal first**: the exact block, every guard and every insert, then
  `ROLLBACK`.
- An independent Oracle review of the rendered files (2026-09-24) found no blocker and several
  assumptions; they became run-time checks (open transaction refused, PK unused, transaction never ended
  midway, pre-commit really committed) and the new pre-apply query Q-G3d.

## Alternatives considered

- **More validator checks.** Tried for four runs; each run found a new shape the checks did not cover.
- **The agent generates the SQL with a script it writes itself.** Same problem one level down.
- **No templates, SQL built in Python.** Rejected: the templates are what a BOX FE reviewer reads; the
  renderer only fills and repeats.

## Consequences

- The agent's job is the queries, the decision cards and `values.json` — where its judgement is needed.
- A structural defect is now a **template defect**: fixed once, in the repo, with a test.
- `values.json` is a reviewable artifact: every value, its source, and the decision it rests on.
- Not verified against a real Oracle instance from this repo: the rehearsal is where compilation and
  constraints are first proved, and it keeps nothing.
