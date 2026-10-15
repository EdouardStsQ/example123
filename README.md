# BOX ACC configs — NY_SCH

Agent [`sigom-box-acc-configs-agent`](../../../../agents/sigom-box-acc-configs-agent/AGENT.md), phase 1 (gap run),
kickoff `Run automation/agents/sigom-box-acc-configs-agent/prompts/tier2-gap-run.md`. Model it works on:
[`box-acc-model.md`](../../../../docs/reference/box-acc-model.md).

| File | State |
|---|---|
| `acc-configs-inputs.NY_SCH.json` | NY's known values: branch `20007.4`, reference SLB `20087.4` (Tier 1), six instruments with PKs, the expected structure (owner objects, list / array extensions, package version); the target environment, group PKs, usage window and decisions are filled in the run |
| `<run>/` | each run is a new versioned folder `acc-configs/gap_<YYYYMMDD>_<n>/` (`scripts/new_run.py --area acc-configs`), in `tier2-pre/` or `tier2-dev/` (DGBOUS) — the target environment is asked |
| `<run>/acc-configs-inputs.json` | the run's copy |
| `<run>/01-evidence/` | the `A-…` CSVs ([catalogue](../../../../docs/reference/queries/acc-config-mining.md)) — `-REF` Tier 1, `-TGT` the target, `-GBOPROD` GBO production |
| `<run>/02-acc-gap-matrix.md` | the result, for the BOX team |
| `01-evidence/` (this folder) | kept empty — evidence lives in each run |

Not started. Known before the run `[2026-10-14]`:
- the structure was read in PRE-PROD (tables, columns, keys, identity values, sequences, triggers) and the packages in
  `cib-boxacc-dbboxacc` — the run's pre-checks confirm it in NY's environment;
- Portfolio Properties' accounts wait on the GBO → BOX topic mapping (BOX dev);
- GBO Cross Account Config had 17 rows for all branches in PRE-PROD — NY may have none (A-U1 d);
- Net Contract is Madrid-real only; MBJ rows belong with the planned `box-acc-jobs-agent`;
- no NY portfolio property in `BOX_ACC` yet — the FE technical test uses any Valid one (open item 4m).

Open items for this agent: 4r–4w in [`../jobs/99-open-items.md`](../jobs/99-open-items.md).
