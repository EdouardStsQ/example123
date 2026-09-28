# Case: pre-steps block the config - typed PKs ahead of the sequence; no dummy label in the target

Covers: resolve-fe-config-prechecks (called by sigom-box-fe-configs-agent)
Type: failure path

Mechanically covered by `scripts/tests/test_validate_run_output.py` (the pre-step refusal cases).

## Given (input state)

As the happy path, except: (1) one of the ten tables holds a PK with this environment's fraction typed
above the sequence's current value; (2) Q-10d finds no label in the target that other branches use as
their dummy.

## When (action)

The agent renders with `--precheck`; the operator runs P1. The agent then tries the full render.

## Then (expected outcome)

- P1 ends `PK PRECHECK PROBLEM - 1 existing PK(s) ...` followed by the `ALTER SEQUENCE` PROPOSAL; the full
  render refuses with `pk-precheck-not-ok`. **No config file is written.**
- The agent puts **card 0** to the BOX FE team with the proposal and the counts. It runs no DDL. After
  the team reports the fix, P1 is run again and ends OK.
- Card 3 is answered C. The agent runs Q-10e, writes `prechecks.dummy_label_proposal` with a PK
  expression named by the team (a typed number is refused: `dummy-pk-typed`), holds step 11
  `EXTERNAL_CHECK_REQUIRED`, and renders the P2 PROPOSAL file for the team to run. Until the proposal is
  removed and the new label cited, `dummy-proposal-pending` keeps step 11 out of the config.
- Choosing the branch's own book instead is refused (`dummy-is-a-book`, or `dummy-not-in-use` if no
  other branch uses it).
