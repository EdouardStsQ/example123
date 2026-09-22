# Scripts

Runnable code that belongs to this repo. A sibling of `skills/` and `agents/`, per the convention in
[`../skills/README.md`](../skills/README.md): one script per purpose, named for what it does, never
nested inside an agent's folder.

| Script | Purpose | Run by |
|---|---|---|
| `validate_run_output.py` | Mechanical checks on a run folder — the charter's hard rules, expressed as code | a human, or CI, after any run produces artifacts |

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

**SQL** (`03-sql/*.sql`)

| Check | Catches |
|---|---|
| `no-ddl` | `CREATE`/`ALTER`/`DROP` in the config script — hard rule 4 |
| `pk-bare-nextval` | `SQ_BOX_FINANENG*.NEXTVAL` without `F___SEQUENCE` — drops the auth-code fraction |
| `pk-no-sequence-call` | INSERTs with no `F___SEQUENCE` anywhere — i.e. literal PKs |
| `insert-select-from-gbo` | **`INSERT … SELECT … FROM DEVENG`** — the 2026-09-18 defect that carried GBO's `FK_OWNER_OBJ` into a BOX row |
| `insert-no-column-list` | an INSERT without an explicit column list — collapses mined / allocated / structural columns |
| `identity-constant-literal` | a hard-coded `35000126.65` and friends — derive per object, don't type them |
| `identity-single-constant` | one `FK_OWNER_OBJ` across many INSERTs — the walk spans three screens |
| **`commit-vs-rollback`** | a committing pre-commit procedure in a script framed as reversible — hard rule 11 |
| **`step8-null-curves`** | step 8 emitted without its curve values, so the step-2 pre-commit back-fills them *and commits* |
| `insert-order` | a child INSERT before its parent |
| `insert-for-no-insert-step` | a statement for a read-only, derived, not-branch-scoped or parked step |
| `draft-header` / `no-verification-select` / `no-rollback-delete` | missing draft marking or the E3 pairing |

**Findings table** (`02-findings.md`)

| Check | Catches |
|---|---|
| `missing-walk-step` | any of the 15 walk steps with no row — *the* failure this agent exists to prevent |
| `status-vocabulary` | a status outside the canonical eight (`CROSS_TIER_VERIFIED` is the recurring offender) |
| `unstatused-row` / `no-evidence-tags` | rows with no status, or a table with no `[stated:]`/`[confirmed:]` provenance |

**Cross-artifact**

| Check | Catches |
|---|---|
| `no-preflight` | no visibility-preflight CSV — hard rule 8: a result set whose preflight was not run is not evidence |
| `evidence-missing` | a query cited in the findings with no CSV behind it |
| `sql-with-open-sme-decision` | SQL emitted for a decision nobody has made |
| `unmarked-sql-pending-evidence` | `EVIDENCE_REQUIRED` rows with SQL that isn't marked as a draft |

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
