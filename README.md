# Scripts

Runnable code that belongs to this repo. A sibling of `skills/` and `agents/`, per the convention in
[`../skills/README.md`](../skills/README.md): one script per purpose, named for what it does, never
nested inside an agent's folder.

| Script | Purpose | Run by |
|---|---|---|
| **`render_sql.py`** | Builds a run's four SQL files from the templates and `03-sql/values.json`, after checking every value; then runs the validator | the agent, whenever `values.json` or the evidence changes — **the only way SQL is produced** |
| `validate_run_output.py` | Mechanical checks on a run folder — the charter's hard rules, expressed as code; re-renders the SQL and fails any hand edit | the renderer, a human, or CI |
| `evidence_to_sql.py` | The CSV reader and number normaliser the other two share; its CLI still prints SQL literals for ad-hoc use | imported; rarely run by hand |

---

## `render_sql.py` `[2026-09-24, ADR 0006]`

```bash
python3 scripts/render_sql.py runs/NY_SCH/tier2-pre/
```

Reads `03-sql/values.json` (shape: `agents/sigom-box-fe-configs-agent/templates/values.example.json`),
`00-inputs.md`, `00-decisions.md`, `02-findings.md`, `01-evidence/Q-04c-quote-ref-column-gbo.csv`,
`Q-04c-quote-ref-column-counts.csv`, `Q-06c-accrual-exceptions-emit.csv` and `Q-G3d-columns.csv`.
Writes `<BRANCH>-<env>-{rehearsal,config,verify,rollback}.sql` and `render-report.md` into `03-sql/`,
then runs the validator. Exit `0` clean · `1` refused or validator FAIL · `2` bad invocation · `3`
nothing to render (steps 2–5 not all ready). **Nothing is written when anything is refused.**

**What it refuses** (each REFUSED line names the JSON path and the fix): a `<placeholder>`, `TODO` or
`TBD`; a value without a source, or a source naming no query, input or decision; a decision cited but not
in `00-decisions.md`, or signed by no named person with a role and date; a status that differs from
`02-findings.md` or is not canonical; a held step that names no one it waits on; any value that
disagrees with `00-inputs.md`; four owners that are not four different objects; step 1 not
`CONFIRMED_ABSENT`, or 4b/8/9/10 reopened; step 6 or 12 rows that are not exactly one per approved
instrument; a step-6 column missing, misspelt, or NULL where NOT NULL; `LIMIT_ERRORS` not a whole number
> 0; the dummy book equal to a real book, or without its decision; step 14a instruments neither present
nor created, or created twice; a count that disagrees with its CSV; an unresolved quote reference; a
column the templates write that the target lacks, a NOT NULL column they do not write, a DESCRIPTION
longer than its column (Q-G3d); non-ASCII output.

**What it guarantees** is listed in the charter (*The SQL is rendered, never written*) and the templates
README. Held optional steps (6, 7, 11, 12, 14a) render a **DRAFT**: the config file stops on its first
statement; the rehearsal still runs.

---

---

## `validate_run_output.py`

```bash
python3 scripts/validate_run_output.py runs/NY_SCH/tier2-pre/
python3 scripts/validate_run_output.py runs/NY_SCH/tier2-pre/ --strict --quiet
```

Exit `0` when there are no FAILs, `1` otherwise. `--strict` promotes WARN to FAIL; `--quiet` hides INFO.
No dependencies beyond the standard library.

### Why it exists

Every gate in the charter is prose that a model evaluates **about its own output**. A model that
misreads a rule once will misread it the same way again — which is exactly what happened: the same class
of defect recurred across five drafts. These checks run identically every time and do not get tired.

**Each check encodes a defect this project actually produced.** Nothing here is hypothetical.

### What it checks

**SQL** (`03-sql/*.sql`) — the config file

| Check | Catches |
|---|---|
| `no-ddl` | `CREATE`/`ALTER`/`DROP` in the config script — hard rule 4 |
| `pk-bare-nextval` | `SQ_BOX_FINANENG*.NEXTVAL` without `F___SEQUENCE` — drops the auth-code fraction |
| `pk-no-sequence-call` | INSERTs with no `F___SEQUENCE` anywhere — i.e. literal PKs |
| **`auth-code-not-asserted`** / **`pk-not-checked`** / **`auth-code-mismatch`** | *2026-09-23, expert point 1.* No `c_expected_fraction`, or no `chk_pk()` before the first INSERT; an allocation without `chk_pk()`; an expected fraction that is not `TARGET_AUTH_CODE`'s |
| **`source-column-wrong`** / `source-column-missing` | *Point 2.* `FK_SOURCE_BACK ≠ 586.4`, or `FK_SOURCE_FRONT ≠ SOURCE_FRONT` — run 3 copied GBO's `9.4`/`11.4` |
| **`config-reads-other-schema`** | any `DEVENG`/`PGT_*`/`GOM_GLB_SYS` reference in the config script — the applying account sees `BOX_FE` only |
| **`quote-refs-not-generated`** / **`quote-refs-not-evidence`** | *Point 3.* step 4 without a `v_quote_refs` list, or a list ≠ Q-04c's CSV column `QUOTE_REF_COLUMN` |
| **`exceptions-not-evidence`** | step 7's rows ≠ Q-06c's CSV filtered to `BRANCH_PK` and the approved instruments |
| `runtime-set-no-guard` | a set read from `DEVENG` at runtime with no count guard (legacy; the config may not read `DEVENG` at all now) |
| **`branch-fk-copied`** / **`branch-fk-not-branch`** | *Point 4.* steps 7/11/12 writing `r.FK_BRANCH` or any value ≠ `BRANCH_PK` — run 3 wrote the GBO branch config `141.35` |
| **`conf-by-book-no-dummy`** | *Point 5.* step 11 without the `DUMMY_BOOK_LABEL` row per instrument |
| `insert-select-from-gbo` | **`INSERT … SELECT … FROM DEVENG`** — whole GBO rows, identity columns included (a cursor that reads one mined column is not this) |
| `insert-no-column-list` | an INSERT without an explicit column list |
| `identity-single-constant` | one `FK_OWNER_OBJ` across many INSERTs — the walk spans three screens |
| `identity-sampled-from-target` | `FK_OWNER_OBJ`/`FK_EXTENSION` read with `SELECT … INTO` from a table, in any dress |
| `curve-fk-literal` / **`curve-fk-null`** / `orphan-curve` | a literal in `FK_CURVEMAN`/`FK_CURVEACC`; **NULL there (both `NOT NULL` — ORA-01400)**; a curve the header never points at |
| `commit-vs-rollback` | a committing pre-commit procedure in a script that also relies on `ROLLBACK` |
| `precommit-wrong-package` | a pre-commit called through an invented package |
| `step8-null-curves` | step 8 emitted without its curve values |
| `insert-order` | a child INSERT before its parent |
| `insert-for-no-insert-step` | a statement for 1, 4b, 9, 10, 13 or 14b |
| `step-row-count-mismatch` | a header's row count ≠ what the step emits (loop-aware; runtime and nested sets reported `INFO`) |
| `instrument-out-of-scope` | an instrument PK not in `APPROVED_INSTRUMENTS` in steps 6, 7, 8, 11, 12, 14a — read from instrument positions only (`FK_INSTRUMENT` values), so a strategy or basis PK can no longer trip it |
| `sql-no-step-headers` (+ WARNs) | no `-- STEP n` blocks, or no `If wrong` line |
| **`cursor-field-undeclared`** | *Run 4.* `r.instrument` where the cursor's `SELECT` named the field `FK_INSTRUMENT` — PLS-00302, the block does not compile |
| **`identity-wrong-object`** | *Run 4.* the Config owner on a table that has its own object (curve, quote link, allowed errors, Days Matured) |
| **`dummy-is-a-book`** | *Run 4.* step 11 writing a single label — dummy and real book the same row |
| **`curve-precommit-missing`** / **`no-existing-row-guard`** | no `P_ENGFixingCurve_PreCommit`; steps 11/12/14a inserting without first counting that table's rows **and testing the count against 0** (the rollback relies on it) |
| **`step-header-incomplete`** / **`step-without-header`** | a step that writes rows without a *Source*, *Findings* and *If wrong* line — or with no header at all |
| **`local-procedure-in-sql`** | *Run 5.* `chk_pk(...)` (or any block-local procedure/function) inside an INSERT — PLS-00222/00231, the block does not compile |
| **`guard-placebo`** | *Run 5.* a row guard that cannot fire (`IF c_… = -1`); `no-existing-row-guard` now needs a `COUNT(*)` on the guarded table |
| **`quote-refs-typed`** / **`quote-refs-list-unused`** | *Run 5.* step-4 INSERTs with typed `FK_BS` literals, or a `v_quote_refs` list nobody reads |
| **`conf-by-book-no-parent`** | *Run 5.* step-11 rows without `FK_PARENT` |
| **`config-precommit-missing`** / **`curve-precommit-before-array`** | *Run 5.* no `p_check_Val_Curves_precommit`; the curve pre-commit called before the array exists |
| **`quote-refs-unchecked`** / **`exceptions-unchecked`** | the Q-04c / Q-06c CSV the list was generated from is not in `01-evidence/` |
| **`values-missing`** / **`values-invalid`** | *2026-09-24.* SQL with no `03-sql/values.json`; values the renderer refuses (each refusal reported) |
| **`sql-edited-by-hand`** / **`sql-not-rendered`** | *2026-09-24.* a `.sql` file that differs from what `values.json` renders to — a hand edit, or values changed without rendering again; a `.sql` file the renderer did not produce |

**Every file in `03-sql/`**

| Check | Catches |
|---|---|
| **`unresolved-substitution`** | `&&` or a double-brace placeholder left in — run 3 hid its identity constants behind `&&QG6_*` |
| **`rollback-dead-code`** | `IF 1 = 0` — run 3's unreachable undo |
| `define-not-off` (WARN) | an `&` anywhere without `SET DEFINE OFF` — SQL Developer prompts mid-script |

**Findings table** (`02-findings.md`)

| Check | Catches |
|---|---|
| `missing-walk-step` | any walk step (1–14b, incl. 4b, 14a, 14b) with no row |
| `status-vocabulary` | a status outside the canonical eight (`CROSS_TIER_VERIFIED` is the recurring offender) |
| `unstatused-row` / `no-evidence-tags` | rows with no status, or a table with no `[stated:]`/`[confirmed:]` provenance |
| **`decision-tagged-confirmed`** | a person's decision tagged `[confirmed: …]`, which is for query results |

**Cross-artifact**

| Check | Catches |
|---|---|
| `no-preflight` | no visibility-preflight CSV — hard rule 8 |
| `evidence-missing` | a query cited in the findings with no CSV behind it |
| `no-approved-instruments` (WARN) | no `APPROVED_INSTRUMENTS:` line in `00-inputs.md` |
| **`verify-script-missing`** / **`verify-no-auth-check`** | config SQL with no `*-verify.sql`, or one that does not check the auth code (V1) |
| **`rollback-script-missing`** | config SQL with no runnable `*-rollback.sql` |
| **`verify-placebo`** / **`verify-incomplete`** | *Run 4.* a verify query that cannot fail (`WHERE 1=0`, `0.44 <> 0.44`); a verify script without the schema-qualified auth-code read, the two GBO comparisons, or the identity check |
| **`decisions-log-missing`** | SQL for decided steps (6, 11, 12, 14a) but no `00-decisions.md` |
| `sql-with-open-sme-decision` | an INSERT for a step still `SME_DECISION_REQUIRED` — **per step**, so steps 1–5 may be emitted while gate 0c is open |
| `unmarked-sql-pending-evidence` | `EVIDENCE_REQUIRED` rows with SQL that isn't marked as a draft |
| `ready-step-without-sql` | a step statused `PROPOSED`/`DERIVED` with no INSERT |

**Inputs it reads from `00-inputs.md`** (`NAME: value`, one per line): `APPROVED_INSTRUMENTS`,
`BRANCH_PK`, `SOURCE_FRONT`, `DUMMY_BOOK_LABEL`, `TARGET_AUTH_CODE`, `QUOTE_REF_COLUMN`. **And two
evidence files:** `01-evidence/Q-04c-…-gbo.csv` and `Q-06c-….csv`, which steps 4 and 7 must equal (a
missing one is a FAIL). **And `03-sql/values.json`**, which it renders itself to compare with the files.

### Tests

```bash
python3 scripts/tests/test_validate_run_output.py
```

Builds a complete **fixture** run folder (inputs, decisions, findings, evidence, `values.json`) and
**renders its SQL with `render_sql.py`**, exactly as a run does — it must render four files and validate
clean. Then, 101 checks in three groups:

1. **The renderer** — each bad `values.json` (or evidence file) is refused with the code written for it,
   and nothing is written; a DRAFT, a 14a-all-present run and a core-held run render as designed.
2. **The rendered SQL** — ASCII, no placeholder left, and a structural PL/SQL lint (blocks, `IF`/`LOOP`
   pairs, parentheses, quotes, declarations before subprograms, no procedure inside an INSERT). The lint
   is itself tested on broken samples.
3. **The validator** — each hand edit trips `sql-edited-by-hand` **and** the specific check for the
   defect it introduces, so the checks still stand behind the renderer.

The fixtures are written to `scripts/tests/fixtures/` — **generated on every run and git-ignored**.
**Run it after changing any template, the renderer or a check.** There is no Oracle here: the
rehearsal file is where compilation and constraints are first proved against the real database.

### Deferred-verification runs are handled deliberately

`EVIDENCE_REQUIRED` rows alongside **draft-marked** SQL are the *designed* state of a
deferred-verification run, so that combination reports `INFO`, not a warning — otherwise the validator
would cry wolf on every legitimate run of the mode the charter recommends. **Unmarked** SQL with
`EVIDENCE_REQUIRED` rows is a FAIL, and an open `SME_DECISION_REQUIRED` is always a FAIL.

### What it does not do

It is a linter, not a reviewer. It cannot tell whether a **value** is right, whether a join points at
the correct table, or whether the walk is complete for a new schema — those need the metamodel
(gate 0g), the evidence trail, and a human. It catches the mechanical failures so that review attention
goes to the ones that need judgement.

It also parses SQL by pattern, not by grammar. A check that cannot be made reliable is a WARN with its
reason stated, never a silent pass.

### Maintaining it

The constants at the top — the canonical statuses, the walk steps, the INSERT order, the identity
constants, the committing procedures — **are the repo's facts expressed as code.** When the walk changes,
change them here too, or the validator will quietly enforce last month's design. Allowed Errors entering
the walk as step 12 is the precedent: several documents were not updated for weeks.
