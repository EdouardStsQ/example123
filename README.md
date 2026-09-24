# SQL templates — rendered, never filled by hand `[2026-09-24]`

**The agent does not fill these.** It writes `RUN_FOLDER/03-sql/values.json` (start from
[`values.example.json`](values.example.json)) and runs:

```bash
python3 scripts/render_sql.py runs/<BRANCH>/<env>/
```

The renderer checks every value against the run's inputs, decisions, findings and evidence, **refuses**
(with the JSON path and the fix) anything it cannot stand behind, writes the files below and runs the
validator. The validator re-renders and FAILs any `.sql` file that differs from what `values.json`
renders to. Why: [ADR 0006](../../../docs/decisions/0006-render-sql-from-values.md) — five hand-written
runs, five new structural defects.

| Template | Renders | Run | Expected last line |
|---|---|---|---|
| `config.sql.tmpl` | `<BRANCH>-<env>-rehearsal.sql` | **1st** — the config block, pre-commits included, ending in `ROLLBACK`; keeps nothing, run it as often as needed | `REHEARSAL OK …` |
| `config.sql.tmpl` | `<BRANCH>-<env>-config.sql` | 2nd — the same block, ending in **`COMMIT`** | `DONE - committed …` |
| `verify.sql.tmpl` | `<BRANCH>-<env>-verify.sql` | 3rd — read-only, operator's account; every query states `Expect` | — |
| `rollback.sql.tmpl` | `<BRANCH>-<env>-rollback.sql` | only to undo; each delete must match the config's count; does not commit | `ROLLBACK READY …` |
| `values.example.json` | — | the shape of `values.json`; the untouched example is refused (placeholders) | — |

## What the rendered block does, in order

1. Refuses to start if the session has an open transaction (the final COMMIT would keep it too).
2. Checks the recorded auth code and fraction agree.
3. **Step 0 pre-flight** — no configuration for the branch (Q-01), no DESCRIPTION collision, no step
   11 / 12 / 14a rows already there (the rollback keys those by branch or instrument).
4. Steps 2–14a. Every PK from `<owner>.F___SEQUENCE('<table>','X')` on its own line, then `chk_pk`:
   the auth-code fraction **and** that the PK is unused. Header and curve PKs allocated first.
   Step 4 loops over the list read from Q-04c; step 7 over the rows read from Q-06c; decided steps are
   one visible INSERT per row, each with its source.
5. The curve pre-commit after step 4's array; a self-check of every step's count; a check that no called
   routine ended the transaction midway.
6. The Config pre-commit (a no-op with no step-8 rows — source-confirmed 2026-09-24), then a check that
   the transaction is still the block's own. Both pre-commits run through `EXECUTE IMMEDIATE`: an account
   that cannot call the package gets a `WARNING` line, not a stop.
7. Rehearsal: `ROLLBACK`. Config: `COMMIT`. **That is the only difference between the two files.**

Any error stops the block and Oracle undoes everything it did.

## Rules for changing a template

- **ASCII only**, and `SET DEFINE OFF` stays the first line. The renderer refuses non-ASCII output; text
  values that need it are rendered as `UNISTR('…')`.
- Lines starting `--#` are template notes (not rendered). `-- @@BEGIN <key>` / `-- @@END <key>` keep
  their lines only when `<key>` applies: `apply`, `rehearsal`, `draft`, `step4`, `step6`, `step7`,
  `step11`, `step12`, `step14a`, `days_present`; `a&b`, `a|b` and `!a` combine them.
- Provenance goes on its own `--` line or after a statement's `;` — never inside a statement.
- A column the templates write must be in `WRITES` in `scripts/render_sql.py`, which checks it against
  the target (Q-G3d (e)).
- After any change: `python3 scripts/tests/test_validate_run_output.py` must pass, and the rendered
  fixture (`scripts/tests/fixtures/good/03-sql/`) should be read by someone who knows Oracle.
