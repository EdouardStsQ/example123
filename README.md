# BOX FE jobs — NY_SCH, Tier 2 PRE

Agent [`box-fe-jobs-agent`](../../../../agents/box-fe-jobs-agent/AGENT.md), kickoff
`Run automation/agents/box-fe-jobs-agent/prompts/build-ny-sch-tier2.md`. One sub-folder per instrument
(`depos/`, `irs/`…), each with `fe-jobs-inputs.json`, `01-evidence/` and the script's `out/`.

| File | State |
|---|---|
| `fe-jobs-inputs.NY_SCH.json` | NY's known values (reference SLB, `PGT_NY` 5 arguments `[J-E4 Tier 2, 2026-09-29]`, `CST_PK_BRA_NYSCH`, 22 books); Control-M folder values, renames and external events are asked in the run `[operator, 2026-10-02]` |

Not started. While `PGT_NY.f_ExecuteGroup` takes no label, the per-book lines come out `OPEN` (jobs run, open item 1).
