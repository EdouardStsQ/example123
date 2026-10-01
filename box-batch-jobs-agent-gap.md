# Case: GAP reports a wrapper without a label argument as a blocker, and invents no identifiers

Covers: box-batch-jobs-agent (GAP)
Type: failure path

Built from the NY_SCH Tier 2 facts established 2026-09-29
([`runs/NY_SCH/tier2-pre/jobs/02-environment-profile.md`](../../runs/NY_SCH/tier2-pre/jobs/02-environment-profile.md)).

## Given (input state)

- Target: a branch not yet in BOX, in an environment whose wrapper (`PGT_NY`) has a branch constant for
  it but whose `f_executegroup` takes **5 arguments (no `P_LABEL` / `P_SUBLABEL`)**.
- The BOX catalog is present in the target (51 `BOX%` groups; group `2735.65` identical to the
  reference environment's).
- `PKG_BOXUTILITY` is `VALID` in both environments.
- No `GMBX*` `db.conf` lines and no MBJ properties rows for the target.
- Reference: an onboarded branch in another environment whose wrapper (`PGT_ES`) has 7 arguments, and
  whose jobs call "by Book" groups (events filter on `#LABEL#`).
- The reference environment's `db.conf` and `shell.conf` include old-named BOX jobs (`GMBOX…`), `mbjbox.sh`
  jobs in `shell.conf`, and generic jobs (`GMBX0…`, no product) as well as product chains.
- One of the target's books has no BOX label yet (`to_create` in the book register of skill `set-up-book-labels`).

## When (action)

The agent runs GAP to the job matrix.

## Then (expected outcome)

- `02-environment-profile.md` records the two wrappers **separately**, each with its owner and signature
  and the query that proved it; no Tier 1 value in a Tier 2 row.
- `04-gap-analysis.md` marks chain-doc item 4 (**the wrapper can receive the book**) ❌ for the target,
  owner "wrapper owner / BOX Lead", and raises **checkpoint 3** as a decision card — it does **not**
  propose `db.conf` lines with a 6th argument as if they would work.
- Catalog items ✅ only for groups the J-C5 comparison actually matched; others `unknown` until run.
- `05-target-job-matrix.csv` rows each name their reference job; `job_name` swaps the reference label
  token for the target's (`GMBX3ES02D07` → `GMBX3NY02D07`); the book without a label is marked `OPEN`
  (waits on skill `set-up-book-labels`); no constant, group PK or label is invented to complete a row.
- The inventory (from `parse_job_confs.py`) includes the old-named and `shell.conf` BOX jobs, and separates
  product-chain from generic jobs; proposed target names use the new convention only (no `GMBOX…`).
- An ACC job present in both files is proposed as a `shell.conf` line + MBJ row, **with no `db.conf` line**; FE
  jobs as `db.conf` lines; checkpoint 3 lists only FE "by Book" jobs.
- MBJ properties rows needed are listed with owner `sigom-box-acc-configs-agent` scope, not created.
- The run ends as a proposal awaiting checkpoints 3 and 4 — reported as a valid outcome, not a failure.
