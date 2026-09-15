# Job Chains

The batch/job sequencing already configured in BOX (or its scheduler) that entity onboarding depends on or triggers — e.g. end-of-day jobs that must have run before an entity is considered "live", or a chain of dependent jobs a specific onboarding step kicks off.

## Convention

Matched pair, same basename, same idea as `../queries/`:

- `<chain-name>.md` — what the chain does, what triggers it, what depends on it finishing, owner/team
- `<chain-name>.xlsx` — the actual chain export (job list, order, dependencies) as maintained today

Keep the `.xlsx` as-is from source (don't hand-edit it into something it isn't) and put any interpretation or "why this matters for onboarding" narrative in the `.md`.

## Rules

- Placeholder identifiers only if any entity/counterparty/portfolio data appears in a chain export — scrub before committing, same as queries and examples.
- If a chain changes, replace both files together and note the change in `../../../CHANGELOG.md` — an onboarding agent may be relying on the old shape.

## Layer reference docs

A branch onboarding's batch path has more than one layer, and each layer that has been reverse-engineered gets its own "how this layer works" reference doc here — not a chain pair itself, but what makes the chain pairs for that layer interpretable. This folder is **not** scoped to Data-Lake ingestion specifically; it's every batch layer a branch touches, from Murex arriving in the Data Lake through to posted ACC movements.

| Doc | Layer | Repo(s) reverse-engineered from |
|---|---|---|
| `control-m-batch-layer.md` | Data Lake ingestion (Murex → Data Lake → BOX RAW tables) — the per-book job template, naming convention, deterministic expansion method for a new branch | `cib-auki-aukictrlmcntrm` |
| `box-fe-acc-batch-runtime.md` | **Scheduler layer.** BOX_FE *and* BOX_ACC Control-M job topology (RAW tables → FE calcs → ACC postings) — job families, subapplications, completion events, the FE→ACC handoff, and the `T_BOX_MBJ_PROPERTIES_S` job→(branch, instrument, MBJ group) binding. Distinct from the Data-Lake layer above | `cib-boxfin-t1mdesfe`, `cib-boxfin-t1mdalmfields`, `cib-boxfin-mdfinancialcheck`, `cib-boxacc-t1mdesac`, `cib-boxacc-t1mdacccheck` |
| `fe-batch-event-groups.md` | **Inside-Oracle layer, FE only.** What the dispatcher runs once a scheduled job fires: the nine ordered FE event groups with PKs, the eight per-product Deal Data inserts, and procedure order inside two groups | *(none — team Confluence page, `[stated]`)* |

> **These last two are a pair, not alternatives.** `box-fe-acc-batch-runtime.md` has the dispatcher
> signature `f_ExecuteGroup(group, branch, process-date, instrument, mode, label, sub-label)` but not
> the `group` values; `fe-batch-event-groups.md` is the list of those values. They also differ in
> evidence strength — repository configuration and DB extracts versus a team-stated Confluence page —
> so where they disagree, the former wins. Read both before touching either.

Read the relevant layer doc before adding a `<chain-name>.md` + `.xlsx` pair for that layer.
