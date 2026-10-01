# Run log — NY_SCH BOX batch jobs, Tier 2 PRE

Agent: [`box-batch-jobs-agent`](../../../../agents/box-batch-jobs-agent/AGENT.md) (mode GAP) · Kickoff:
[`prompts/gap-ny-sch-tier2.md`](../../../../agents/box-batch-jobs-agent/prompts/gap-ny-sch-tier2.md)

Next to the FE run (`../`), which it reads for the branch's instruments and books. Same rules as every
run folder ([`runs/README.md`](../../../README.md)): real values live here, never in `docs/`.

**Status: not run yet.** The environment profile was seeded on 2026-09-29 from the operator's queries
(screenshots) while the agent was being designed — see `02-environment-profile.md`.

## Layout

| File | Written by | When |
|---|---|---|
| `00-inputs.md`, `00-decisions.md` | agent | first; then one row per decision card |
| `01-evidence/J-<ID>-<env>.csv`, `db.conf` extracts, Control-M excerpts | operator / agent | as each query is answered |
| `02-environment-profile.md` | agent | step 1 (seeded) |
| `03-reference-inventory.md` | agent | step 3 |
| `04-gap-analysis.md` | agent | step 6 |
| `05-target-job-matrix.csv`, `05-source-questions.md` | agent | steps 8 and throughout |
| `99-open-items.md` | agent | throughout (seeded) |

**Before a rerun:** archive the previous run's output to `archive/run-NN/`, as in `runs/README.md`.
