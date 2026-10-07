# BOX ACC configs — NY_SCH, Tier 2 PRE

Agent [`sigom-box-acc-configs-agent`](../../../../agents/sigom-box-acc-configs-agent/AGENT.md), phase 1 (gap run),
kickoff `Run automation/agents/sigom-box-acc-configs-agent/prompts/tier2-gap-run.md`.

| File | State |
|---|---|
| `acc-configs-inputs.NY_SCH.json` | NY's known values: branch `20007.4`, reference SLB `20087.4` (Tier 1), six instruments with PKs; group PKs and the decisions are filled in the run |
| `acc-configs-inputs.json` | the run's copy (created by the run) |
| `01-evidence/` | the `A-…` CSVs ([catalogue](../../../../docs/reference/queries/acc-config-mining.md)) — `-REF` Tier 1, `-TGT` Tier 2 |
| `02-acc-gap-matrix.md` | the result, for the BOX team |

Not started. Known before the run: Portfolio Properties' accounts wait on the GBO → BOX topic mapping (BOX dev);
Net Contract is Madrid-real only; MBJ rows belong with the planned `box-acc-jobs-agent`.
