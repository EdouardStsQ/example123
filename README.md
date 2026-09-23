# Scripts

Runnable code that belongs to this repo. A sibling of `skills/` and `agents/`, per the convention in
[`../skills/README.md`](../skills/README.md): one script per purpose, named for what it does, never
nested inside an agent's folder.

| Script | Purpose | Run by |
|---|---|---|
| `validate_run_output.py` | Mechanical checks on a run folder — the charter's hard rules, expressed as code | a human, or CI, after any run produces artifacts |
| `evidence_to_sql.py` | Turns an evidence CSV into SQL literals — step 4's quote list, step 7's exception rows — so nobody types them | the agent, while writing the config script |

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
| `instrument-out-of-scope` | an instrument PK not in `APPROVED_INSTRUMENTS` in steps 6, 7, 8, 11, 12, 14a |
| `sql-no-step-headers` (+ WARNs) | no `-- STEP n` blocks, or no `If wrong` line |

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

**Cross-artifact**

| Check | Catches |
|---|---|
| `no-preflight` | no visibility-preflight CSV — hard rule 8 |
| `evidence-missing` | a query cited in the findings with no CSV behind it |
| `no-approved-instruments` (WARN) | no `APPROVED_INSTRUMENTS:` line in `00-inputs.md` |
| **`verify-script-missing`** / **`verify-no-auth-check`** | config SQL with no `*-verify.sql`, or one that does not check the auth code (V1) |
| **`rollback-script-missing`** | config SQL with no runnable `*-rollback.sql` |
| `sql-with-open-sme-decision` | an INSERT for a step still `SME_DECISION_REQUIRED` — **per step**, so steps 1–5 may be emitted while gate 0c is open |
| `unmarked-sql-pending-evidence` | `EVIDENCE_REQUIRED` rows with SQL that isn't marked as a draft |
| `ready-step-without-sql` | a step statused `PROPOSED`/`DERIVED` with no INSERT |

**Inputs it reads from `00-inputs.md`** (`NAME: value`, one per line): `APPROVED_INSTRUMENTS`,
`BRANCH_PK`, `SOURCE_FRONT`, `DUMMY_BOOK_LABEL`, `TARGET_AUTH_CODE`, `QUOTE_REF_COLUMN`. **And two
evidence files:** `01-evidence/Q-04c-…-gbo.csv` and `Q-06c-….csv`, which steps 4 and 7 must equal. A missing one turns its check into a
WARN rather than a silent pass.

### Tests

```bash
python3 scripts/tests/test_validate_run_output.py
```

Builds two fixtures from `agents/sigom-box-fe-configs-agent/templates/` — the templates filled with
**fixture** values (must be clean) and a run-3-like file (must trip every expert-review check) — then
applies one mutation per check and asserts that exactly that check fires. The fixtures are written to `scripts/tests/fixtures/`, which is **generated on every run and
git-ignored** — it is not part of the repo and never needs editing. **Run it after changing any
check.** The run-3 review found a check of mine that would have failed a correct run; this is what
stops the next one.

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
