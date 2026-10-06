# Case: explain one job from files, and say who emits an event

Covers: explain-box-job (used by box-fe-jobs-agent mid-run and in `pending-questions.md`; optional for
box-batch-jobs-agent EXPLAIN `overview`)
Type: happy path + failure paths

Mechanically covered by `scripts/tests/test_validate_run_output.py` (`explain_job:` and
`build_fe_jobs pending-questions:` cases).

## Given

An inventory with an FE job (`db.conf`) and an ACC job (`shell.conf` → `mbjbox.sh`); the branch's FE folder JSON
and, in another repo, its ACC folder JSON; a DB repo whose `dml/03-PGT_PRC` holds the FE job's group in two
releases (`r1.0.0` with an old name, `r1.1.0` with the current one and its events).

## When

1. `explain_job.py <env> <FE job> <ACC job> --controlm <FE repo> <ACC repo> --dml <DB repo>`.
2. The same for the ACC job with `--mbj <J-R2 export>`.
3. `box-fe-jobs-agent` is waiting for an external-event answer and the operator asks "what does <ACC job> do?".

## Then

- FE job: folder, file:line, waits / emits, `db.conf` line, group named from the **newest** release, events in
  `ORDERTOEXECUTE` order, meanings tagged INFERRED.
- ACC job: found in the ACC repo, bound by `shell.conf`; without `--mbj` its group is "ask J-R2", with it the group
  and events are read.
- Mid-run: the agent answers with the card, then repeats the pending question — it does not take the explanation
  as the answer.
- No inventory, or a path that does not exist → refused (`inventory-missing`, `path-missing`).
