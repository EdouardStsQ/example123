# Case: pre-steps resolved - P1 OK, an existing shared dummy label chosen

Covers: resolve-fe-config-prechecks (called by sigom-box-fe-configs-agent)
Type: happy path

Mechanically covered by `scripts/tests/test_validate_run_output.py` (the `good` fixture).

## Given (input state)

A run folder with Q-G3b and Q-G3c in (auth code recorded, one `t__CORE_INFO_S` row), `values.json`
`run` and `environment` written, no config file yet. In the target, the sequence is ahead of every PK
with this environment's fraction in the ten tables. Q-10d found a label matching the reference
environment's dummy that several target branches already use.

## When (action)

The agent renders with `--precheck`; the operator runs the P1 file with the applying account and saves
its output as `01-evidence/Q-P1-pk-precheck.txt`. The agent puts card 3 to the BOX FE team, who answer
A (the candidate); the agent runs Q-10c (a)(c) in the target with it and cites it as `decision 3`.

## Then (expected outcome)

- The P1 output ends `PK PRECHECK OK - auth code <code>`; no card 0 is put.
- `00-decisions.md` holds card 3's answer, named, with role and date.
- `render_sql.py <RUN>` renders the rehearsal, config, verify and rollback files with none of
  `pk-precheck-*`, `dummy-*` refusals; no P2 file exists.
