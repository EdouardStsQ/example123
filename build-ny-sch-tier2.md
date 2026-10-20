# Devin kickoff — `box-fe-jobs-agent` — NY_SCH BOX FE jobs

> **How to start — nothing to paste.** Open a Devin session with the repos below attached, and type:
> **`Run automation/agents/box-fe-jobs-agent/prompts/build-ny-sch-tier2.md`**
> Devin reads this file and asks you for anything it needs, one question at a time (with a default you can accept).

**If you were pointed at this file**, it is your task prompt: **follow [`build.md`](build.md) from Step 0** with
`<BRANCH>` = **`NY_SCH`** and `<tier>-<env>` = **`tier2-pre`** (the operator may choose `tier2-dev`). Do not ask for
the branch. Everything else — NY's values, answers, decisions and checks — is data that `build.md` reads:

| | |
|---|---|
| Values and answers | `runs/NY_SCH/tier2-pre/fe-jobs/fe-jobs-inputs.NY_SCH.json` |
| Decisions and history | [`runs/NY_SCH/tier2-pre/fe-jobs/README.md`](../../../runs/NY_SCH/tier2-pre/fe-jobs/README.md) |
| Open questions | `runs/NY_SCH/tier2-pre/jobs/99-open-items.md` |
| Repos | `docs/reference/branch-registry.csv` (rows `NY_SCH`, `SLB`) — `build.md` Step 0 lists them |
