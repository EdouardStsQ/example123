# Case: pre-steps block the config - typed PKs ahead of the sequence; book labels not created yet

Covers: resolve-fe-config-prechecks (called by sigom-box-fe-configs-agent)
Type: failure path

Mechanically covered by `scripts/tests/test_validate_run_output.py` (the pre-step and step-11 refusal
cases).

## Given (input state)

As the happy path, except: (1) one of the ten tables holds a PK with this environment's fraction typed
above the sequence's current value; (2) in the book folder, one book's label does not exist yet and the
BOX FE team has not run the labels proposal.

## When (action)

The agent renders with `--precheck`; the operator runs P1. The agent then tries the full render with
step 11 emitted.

## Then (expected outcome)

- P1 ends `PK PRECHECK PROBLEM - 1 existing PK(s) ...` followed by the `ALTER SEQUENCE` PROPOSAL; the full
  render refuses with `pk-precheck-not-ok`. **No config file is written.**
- The agent puts **card 0** to the BOX FE team with the proposal and the counts. It runs no DDL. After
  the team reports the fix, P1 is run again and ends OK.
- With step 11 emitted, the render refuses with `book-labels-pending`; the agent holds step 11
  (`EXTERNAL_CHECK_REQUIRED`, waits on the BOX FE team) and hands over `books/book-labels-PROPOSAL.sql`.
- Leaving the old `prechecks` block in `values.json` is refused (`values-moved`).
