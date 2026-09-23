# SQL templates — the shape of `03-sql/` `[2026-09-23]`

Three files, one per job. The agent fills every `{{NAME}}` with the recorded value; a finished file
contains no `{{` and no `&&` — the validator FAILs either. **Provenance goes in the step header's
`Source` line or the constant's declaration comment — never a `--` inside a statement**, where it
comments out the rest of the line and the block no longer compiles.

| Template | Becomes | Runs |
|---|---|---|
| `config.sql.tmpl` | `<BRANCH>-<env>-config.sql` | once; its last procedure **COMMITs** |
| `verify.sql.tmpl` | `<BRANCH>-<env>-verify.sql` | straight after, read-only; every query states its expected result |
| `rollback.sql.tmpl` | `<BRANCH>-<env>-rollback.sql` | only to undo; prints counts, operator commits |

**The rules the templates encode, and the reason for each:**

1. **Sets mined from GBO are read in-script and count-guarded; values a person signed are literals.**
   Step 4's quote references and step 7's exceptions come from `DEVENG` inside the script, so nobody
   types 38 numbers — the BOX FE expert's point 3. Steps 6, 11, 12, 14a are decisions and are written
   out so a reviewer can read them.
2. **PKs are allocated before the rows that point at them.** Step 2 allocates the curve's PK too, because
   the header's curve columns are `NOT NULL`: no NULL-then-UPDATE.
3. **The auth code is checked three times** — against `00-inputs.md` before the first INSERT, on every
   allocated PK (`chk_pk`), and on every created row (verify V1). Point 1.

**Empty lists:** where a list can be empty (`DAYS_MATURED_INSTRUMENTS` when every instrument already
has a Days Matured row), write `-1` — `IN ()` is a syntax error — and emit `0 rows` in the step header.

**Guards before inserting where the rollback keys by branch or instrument** (steps 11, 12, 14a): the
script aborts if rows already exist, so "the branch's rows" can only mean this run's. The rollback
deletes everything except step 14a, which it lists — Days Matured is global.

They are skeletons for the *shape*, not a source of values: never fill a `{{…}}` from the template's
comments or from another branch's run. Column lists follow the query catalogue; where a run's Q-G7
result declares a different field set, Q-G7 wins and the difference is a finding.
