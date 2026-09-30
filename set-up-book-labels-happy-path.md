# Case: a branch's book labels - some exist, the rest are proposed, then the register completes

Covers: set-up-book-labels (called by sigom-box-fe-configs-agent, read by box-batch-jobs-agent)
Type: happy path

Mechanically covered by `scripts/tests/test_validate_run_output.py` (the `labels skill:` cases).

## Given (input state)

A book folder `runs/<BRANCH>/<env>/books/` with the operator's book list (`BOOK_A`, `BOOK_B` — placeholder
names), `book-labels.json` with the branch PK and country code, and the BOX FE team's dummy decision (an
existing label other branches use). In the target, `BOOK_A`'s label exists; `BOOK_B`'s does not.

## When (action)

The agent writes the codes (`X<CC>01`, `X<CC>02`), the operator runs Q-10f and Q-10c (c), and the agent
runs `scripts/set_up_book_labels.py`. On `book-labels-rule-missing` it puts the PK-rule card; the BOX FE
team answers "fixed" and gives the PK; the operator runs Q-10e; the agent runs the script again.

## Then (expected outcome)

- First run: exit 1 (`book-labels-rule-missing`), register shows `BOOK_A` `exists` with its PK, `BOOK_B`
  `to_create`.
- Second run: exit 4 and `book-labels-PROPOSAL.sql` inserting **only** `BOOK_B`'s label, with the exact
  description, the fixed PK, `FK_OWNER_OBJ = 17910.4`; it stops if any code/description/PK exists and has
  no COMMIT.
- After the BOX FE team runs it and Q-10f is re-run: exit 0, every register row `exists`, a `dummy` row
  with its PK. FE step 11 carries exactly those PKs.
