---
name: resolve-fe-config-prechecks
description: Resolves the two pre-steps of a BOX FE configuration run - the PK mechanism (P1) and the dummy portfolio label (P2) - in the target environment, before any config SQL is rendered. Use in every sigom-box-fe-configs-agent run, as soon as Q-G3b and Q-G3c are in.
---

# Resolve the BOX FE config pre-steps (P1 PK mechanism, P2 dummy label)

`[BOX Lead review, 2026-09-25]` *"The PK check should be a pre-step, resolved before we run the config
... raise concerns and propose solutions. The dummy portfolio should also be a pre-check; if there is
none, propose an insert on the label table."* Why two pre-steps and not checks inside the config:
[ADR 0007](../../docs/decisions/0007-pre-steps-pk-and-dummy-label.md).

**Called by:** `sigom-box-fe-configs-agent` (its run prompt says when). **Script:**
`scripts/render_sql.py --precheck` - this skill has no code of its own; the renderer's gate is what
enforces it. **Branch-specific values** (auth code, the reference environment's dummy row, past-run
lessons) stay in the calling run prompt, never here.

## Inputs

| Input | Source | Used by |
|---|---|---|
| `RUN_FOLDER` (`runs/<BRANCH>/<env>/`) | the run | both |
| `values.json` `run` and `environment` sections (auth code, `F___SEQUENCE` owner) | Q-G3b, Q-G3c | P1 |
| `01-evidence/Q-P1-pk-precheck.txt` - the Script Output of the P1 file | the operator, **applying account** | P1 gate |
| `01-evidence/Q-10d-*.csv` - the reference dummy row, target candidates, labels in use | Q-10d (a)(b)(c) | P2, card 3 |
| `01-evidence/Q-10c-dummy-book-label.csv`, `Q-10c-dummy-book-target.csv` - with the chosen label | Q-10c (a)(c), **in the target** | P2 gate |
| `01-evidence/Q-10e-domains-columns.csv` - the label table's columns | Q-10e, only for option C | P2 proposal |
| Card 0 / card 3 answers, in `00-decisions.md` | the BOX FE team | both |

Queries are in [`fe-config-mining.md`](../../docs/reference/queries/fe-config-mining.md): Q-P1, Q-10c,
Q-10d, Q-10e.

## Preconditions

- Gate 0d's Q-G3b: `F___SEQUENCE` visible and `VALID` (a `PKG_ENGPRECOMMIT` 0-row result is not a stop).
- Q-G3c: exactly one row in `gom_glb_sys.t__CORE_INFO_S`; its auth code recorded in `00-inputs.md` and
  `values.json` `environment.target_auth_code`.
- **No config file exists yet.** The full render refuses until both pre-steps are resolved.

## How to run

```bash
python3 scripts/render_sql.py runs/<BRANCH>/<env>/ --precheck   # P1, plus P2 when a proposal is in values.json
python3 scripts/render_sql.py runs/<BRANCH>/<env>/              # the config files - only after both are resolved
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

### P2 - the dummy portfolio label (before step 11)

4. Run Q-10d; put **card 3 to the BOX FE team** (below).
5. **A / B - an existing label.** Run Q-10c (a) and (c) **in the target** with that label. Cite it in
   `steps.11.dummy_book` as `decision 3`. The renderer requires that it exists and that **at least one
   other branch uses it** - a dummy is shared - and that it is not one of the branch's real books.
6. **C - none exists: create one.** Run Q-10e. Write `prechecks.dummy_label_proposal` (shape:
   `_prechecks_example` in [`values.example.json`](../../agents/sigom-box-fe-configs-agent/templates/values.example.json)):
   every column modelled on the reference environment's dummy row (Q-10d (a)), each with its source; the
   PK is **the allocation expression the BOX FE team names** on the card, never a typed number. Hold step
   11 as `EXTERNAL_CHECK_REQUIRED` (waits on the BOX FE team) and render with `--precheck`. The BOX FE team
   reviews and runs `03-sql/<BRANCH>-<env>-P2-dummy-label-PROPOSAL.sql` (it writes `PGT_SYS.PGT_DOMAINS`
   and does not commit - they do), then gives the new PK. Then: Q-10c (a) with it, remove the proposal,
   cite the label as `decision 3` with `"created_by_p2": true`, and release step 11.

## Decision cards (one at a time; record each answer in `00-decisions.md`)

```text
DECISION 0 - PK mechanism: the sequence is behind typed PKs
Why it matters : the config would allocate PKs that already exist
Evidence       : Q-P1 - <n> PK(s) at/ahead of the sequence in <tables>; highest <PK>; sequence near <value>
Options        : A) run the printed ALTER SEQUENCE proposal   B) correct the typed rows   C) other: ____
Recommendation : A - it moves the shared sequence past them and changes no data
If wrong       : ORA-00001 in the rehearsal (constraint) or a silent duplicate PK (none)
Authority      : BOX FE team (sequence owner) - the agent never runs DDL
```

```text
DECISION 3 - Step 11: dummy portfolio label in <env>
Why it matters : every instrument needs a (dummy book x instrument) row
Evidence       : Q-10d - reference dummy '<CODE> - <DESCRIPTION>'; target candidates with branch counts
Options        : A) use <label PK>   B) another label: ____   C) none exists - propose a new one (P2)
Recommendation : the candidate matching the reference CODE that the most target branches use
If wrong       : that (book, instrument) is never scheduled by the FE batch - silently
Authority      : BOX FE team (technical), not the product SME
```

Omit card 0 when P1 prints OK. Never put card 3 before Q-10d is in.

## Output

- `03-sql/<BRANCH>-<env>-P1-pk-precheck.sql`, and its saved output `01-evidence/Q-P1-pk-precheck.txt`
  ending in `PK PRECHECK OK - auth code <code>`.
- Either a cited, shared dummy label in `steps.11.dummy_book`, or `03-sql/<BRANCH>-<env>-P2-dummy-label-PROPOSAL.sql`
  handed to the BOX FE team (then, once run, the new label cited with `created_by_p2`).
- `00-decisions.md` rows for card 0 (if raised) and card 3.

**Success** = the full render (`render_sql.py <RUN>`) raises none of the codes below.

## Failure modes

| Failure | Detection (renderer code) | Handling |
|---|---|---|
| P1 not run, or output not saved | `pk-precheck-missing` | ask the operator to run P1 and save the output; no config until then |
| P1 last result not OK for this auth code | `pk-precheck-not-ok` | card 0 to the BOX FE team; P1 again after their fix. Fraction problem → **abort**, escalate |
| Chosen label absent in the target | `dummy-label-not-in-target` | put card 3 again; never reuse the reference environment's label unchecked |
| No other branch uses the label | `dummy-not-in-use` | put card 3 again: a shared label, or option C |
| The dummy is one of the branch's books | `dummy-is-a-book` | put card 3 again; a real book is never the dummy |
| Dummy not cited as a decision | `decision-missing` | record card 3's answer; cite `decision 3` |
| P2 proposed but not yet run | `dummy-proposal-pending` | step 11 held, waiting on the BOX FE team; everything else can still close |
| P2 PK typed as a number | `dummy-pk-typed` | ask the BOX FE team for the allocation expression |
| P2 column not in the target, or a NOT NULL column unset | `target-column-missing`, `target-not-null-not-written`, `target-null-in-not-null` | fix the proposal from Q-10e / Q-10d (a) |
| Q-10c / Q-10e evidence missing | `evidence-missing` | run the query named in the message |

## Never

- Run DDL, or the P2 insert. Both are proposals the BOX FE team decides and runs.
- Render or hand-write a config file before P1 prints OK.
- Pick a dummy label without card 3's answer, or type a PK.

## Eval cases

[`evals/cases/resolve-fe-config-prechecks-happy-path.md`](../../evals/cases/resolve-fe-config-prechecks-happy-path.md),
[`evals/cases/resolve-fe-config-prechecks-failure-paths.md`](../../evals/cases/resolve-fe-config-prechecks-failure-paths.md).
