---
name: resolve-fe-config-prechecks
description: Resolves pre-step P1 of a BOX FE configuration run - the PK mechanism in the target environment - before any config SQL is rendered, and hands the book and dummy labels to skill set-up-book-labels before step 11. Use in every sigom-box-fe-configs-agent run, as soon as Q-G3b and Q-G3c are in.
---

# Resolve the BOX FE config pre-steps (P1 PK mechanism; labels via set-up-book-labels)

`[BOX Lead review, 2026-09-25]` *"The PK check should be a pre-step, resolved before we run the config
... raise concerns and propose solutions. The dummy portfolio should also be a pre-check; if there is
none, propose an insert on the label table."* Why pre-steps and not checks inside the config:
[ADR 0007](../../docs/decisions/0007-pre-steps-pk-and-dummy-label.md).

**Since 2026-09-30 the labels are their own skill.** The dummy label (formerly P2) and the book labels
(formerly P3) are [`set-up-book-labels`](../set-up-book-labels/SKILL.md) — other agents need the same
books ([ADR 0009](../../docs/decisions/0009-book-labels-skill.md)). This skill keeps **P1** and the
**step-11 gate**: the renderer re-checks the book folder and refuses step 11 until every label exists.

**Called by:** `sigom-box-fe-configs-agent` (its run prompt says when). **Script:**
`scripts/render_sql.py --precheck` - this skill has no code of its own; the renderer's gate is what
enforces it. **Branch-specific values** (auth code, past-run lessons) stay in the calling run prompt.

## Inputs

| Input | Source | Used by |
|---|---|---|
| `RUN_FOLDER` (`runs/<BRANCH>/<env>/`) | the run | both |
| `values.json` `run` and `environment` sections (auth code, `F___SEQUENCE` owner) | Q-G3b, Q-G3c | P1 |
| `01-evidence/Q-P1-pk-precheck.txt` - the Script Output of the P1 file | the operator, **applying account** | P1 gate |
| Card 0 answer, in `00-decisions.md` | the BOX FE team | P1 |
| `books/` - the book folder of skill `set-up-book-labels` | that skill | step-11 gate |

## Preconditions

- Gate 0d's Q-G3b: `F___SEQUENCE` visible and `VALID` (a `PKG_ENGPRECOMMIT` 0-row result is not a stop).
- Q-G3c: exactly one row in `gom_glb_sys.t__CORE_INFO_S`; its auth code recorded in `00-inputs.md` and
  `values.json` `environment.target_auth_code`.
- **No config file exists yet.** The full render refuses until P1 is resolved.

## How to run

```bash
python3 scripts/render_sql.py runs/<BRANCH>/<env>/ --precheck   # P1 only
python3 scripts/render_sql.py runs/<BRANCH>/<env>/              # the config files - only after P1 is OK
```

## Steps

### P1 - the PK mechanism (always, first)

1. Write `values.json` `run` and `environment`; render with `--precheck`.
2. Ask the operator to run `03-sql/<BRANCH>-<env>-P1-pk-precheck.sql` **with the applying account** and
   save the whole Script Output as `01-evidence/Q-P1-pk-precheck.txt`. It writes nothing; for each of the
   ten tables the config writes it draws one PK from `F___SEQUENCE(<table>,'X')`, checks the fraction, and
   counts existing PKs with this environment's fraction **at or ahead of** the sequence - typed PKs the
   next values would collide with. (Typed PKs below the sequence, or with another fraction, can never
   collide and are not counted.)
3. Read the last line:
   - `PK PRECHECK OK - auth code <code> ...` → P1 is done.
   - `PK PRECHECK PROBLEM - F___SEQUENCE returned ... without the fraction` → wrong environment or wrong
     auth code recorded. **Stop the run**; ask the BOX FE team.
   - `PK PRECHECK PROBLEM - <n> existing PK(s) ... sit at or ahead of the sequence` → **card 0 to the BOX
     FE team** (below), carrying the printed PROPOSAL and the per-table counts. When they report it done,
     go back to step 2.

### Labels - before step 11

4. Run skill [`set-up-book-labels`](../set-up-book-labels/SKILL.md) on `runs/<BRANCH>/<env>/books/` until
   `scripts/set_up_book_labels.py` exits 0. Until then step 11 is `EXTERNAL_CHECK_REQUIRED`.
5. Step 11's `books` = exactly the register's book PKs, `dummy_book` = its dummy PK (and
   `DUMMY_BOOK_LABEL` in `00-inputs.md`). The renderer writes one row per approved instrument × (each book
   + the dummy) and re-evaluates the book folder, so a stale register cannot pass.

## Decision card

```text
DECISION 0 - PK mechanism: the sequence is behind typed PKs
Why it matters : the config would allocate PKs that already exist
Evidence       : Q-P1 - <n> PK(s) at/ahead of the sequence in <tables>; highest <PK>; sequence near <value>
Options        : A) run the printed ALTER SEQUENCE proposal   B) correct the typed rows   C) other: ____
Recommendation : A - it moves the shared sequence past them and changes no data
If wrong       : ORA-00001 in the rehearsal (constraint) or a silent duplicate PK (none)
Authority      : BOX FE team (sequence owner) - the agent never runs DDL
```

Omit card 0 when P1 prints OK. The dummy and PK-rule cards for labels are in `set-up-book-labels`.

## Output

- `03-sql/<BRANCH>-<env>-P1-pk-precheck.sql`, and its saved output `01-evidence/Q-P1-pk-precheck.txt`
  ending in `PK PRECHECK OK - auth code <code>`.
- A complete book register (skill `set-up-book-labels`) before step 11 is emitted.
- `00-decisions.md` row for card 0 (if raised).

**Success** = the full render (`render_sql.py <RUN>`) raises none of the codes below.

## Failure modes

| Failure | Detection (renderer code) | Handling |
|---|---|---|
| P1 not run, or output not saved | `pk-precheck-missing` | ask the operator to run P1 and save the output; no config until then |
| P1 last result not OK for this auth code | `pk-precheck-not-ok` | card 0 to the BOX FE team; P1 again after their fix. Fraction problem → **abort**, escalate |
| Step 11 emitted, no book folder | `book-setup-missing` | run skill `set-up-book-labels` |
| The book folder is refused | `book-setup-invalid` | run `scripts/set_up_book_labels.py` and fix what it names |
| Step 11 emitted while labels are only proposed | `book-labels-pending` | hold step 11 (`EXTERNAL_CHECK_REQUIRED`) until the BOX FE team ran the proposal |
| Step 11's books or dummy differ from the register | `book-labels-disagree` | copy the PKs from `books/books-register.csv` |
| The dummy is also one of step 11's books | `dummy-is-a-book` | the register's dummy, never a book |
| The dummy not cited as a decision | `decision-missing` | cite the dummy decision |
| The old P2/P3 proposals still in `values.json` | `values-moved` | remove `prechecks`; the labels are the skill's |

## Never

- Run DDL. The sequence fix is a proposal the BOX FE team decides and runs.
- Render or hand-write a config file before P1 prints OK.
- Emit step 11 before the book register is complete.

## Eval cases

[`evals/cases/resolve-fe-config-prechecks-happy-path.md`](../../evals/cases/resolve-fe-config-prechecks-happy-path.md),
[`evals/cases/resolve-fe-config-prechecks-failure-paths.md`](../../evals/cases/resolve-fe-config-prechecks-failure-paths.md).
