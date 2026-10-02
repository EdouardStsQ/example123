# Case: find a branch's executed jobs for a product, in Control-M order

Covers: find-box-jobs (used by box-batch-jobs-agent and box-fe-jobs-agent)
Type: happy path + failure paths

Mechanically covered by `scripts/tests/test_validate_run_output.py` (`find_jobs:` cases).

## Given

An inventory where a branch's deposits FE jobs include an old-named job (found only by its `db.conf` instrument
constant), a Madrid job of the same product, and an ACC job whose `db.conf` line is legacy; the branch's FE Control-M
folder JSON with the events between them.

## When

`find_jobs.py <env> --side FE --product deposits --branch SLB --controlm <folder repo>`.

## Then

- Only executed `db.conf` rows of that branch: the old-named one included, the Madrid one and the legacy line not.
- Order levels follow the events; a prerequisite outside the list is named; a job missing from the JSON is listed as
  "not found", with no order invented.
- Unknown product / branch, or a missing or old inventory → refused with its code (`product-unknown`,
  `branch-unknown`, `inventory-missing`, `inventory-old`).
