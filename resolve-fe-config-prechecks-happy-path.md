# Case: pre-steps resolved - P1 OK, and the book register complete before step 11

Covers: resolve-fe-config-prechecks (called by sigom-box-fe-configs-agent)
Type: happy path

Mechanically covered by `scripts/tests/test_validate_run_output.py` (the `good` fixture, whose `books/`
folder is complete).

## Given (input state)

A run folder with Q-G3b and Q-G3c in (auth code recorded, one `t__CORE_INFO_S` row), `values.json`
`run` and `environment` written, no config file yet. In the target, the sequence is ahead of every PK
with this environment's fraction in the ten tables. The book folder `books/` has been through skill
`set-up-book-labels` and `scripts/set_up_book_labels.py` exits 0 (every label exists, a shared dummy).

## When (action)

The agent renders with `--precheck`; the operator runs the P1 file with the applying account and saves
its output as `01-evidence/Q-P1-pk-precheck.txt`. The agent writes step 11 from the book register.

## Then (expected outcome)

- The P1 output ends `PK PRECHECK OK - auth code <code>`; no card 0 is put.
- Step 11's books are exactly the register's book PKs and its dummy the register's dummy.
- `render_sql.py <RUN>` renders the rehearsal, config, verify and rollback files with none of
  `pk-precheck-*`, `book-*` refusals.
