# Runs

Working folders for actual agent runs — one per branch per environment. This is where evidence,
findings and generated SQL live while a run is in progress and after it completes.

## Why this is a top-level folder, not part of `docs/`

`docs/` holds the four **document kinds** (process / reference / examples / decisions) — things
written to be read and kept correct. A run folder is neither: it's working data produced by one
execution against one environment. `docs/examples/` is the closest relative, but that folder holds a
*narrative* of what happened, written up afterwards; this holds the raw material.

The split that matters: **the capability is branch-agnostic, the run is branch-specific.** An
`AGENT.md` describes how to configure any branch; a run folder is one branch, once, in one
environment. Keeping them apart is what lets the agent be reused without editing it.

## ⚠️ Run folders contain real configuration data

Unlike `docs/`, which follows the repo's no-real-names discipline, evidence CSVs here hold actual
production-copy config values — that's their purpose. Two consequences:

- **Don't paste CSV contents into `docs/`.** When a run produces a finding worth keeping, write the
  *finding* into the reference docs (table names, relationships, counts), not the rows.
- Treat these folders with the same care as a DB extract, because that's what they are.

## Layout

```
runs/<BRANCH_CODE>/<ENVIRONMENT>/
  README.md              # run log: current stage, outstanding queries, blockers and who owns them
  00-inputs.md           # the agent's input contract, filled in. Written before any query runs
  01-evidence/
    Q-G1-branch-identity.csv
    Q-02-generic-gbo.csv
    ...                  # one file per query, named EXACTLY by its catalogue query ID
  02-findings.md         # one row per walk object, statused, each citing its evidence file
  03-sql/
    01-pre-<branch>-fe-config.sql
    02-pre-<branch>-verify.sql
    03-pre-<branch>-rollback.sql
  04-provisioning/       # only if gate 0e found missing tables
    schema-diff.md
    ddl-sources.md       # paths into cib-boxfin-dbboxfe — sourced, never authored
  99-open-items.md       # unresolved items and who each is blocked on
```

`<ENVIRONMENT>` names the target, not the source — e.g. `tier2-pre`. One run configures one
environment; a production run is a separate folder derived from the verified PRE one.

## Filename convention is a contract, not a suggestion

Evidence CSVs are named after the query ID in
[`docs/reference/queries/fe-config-mining.md`](../docs/reference/queries/fe-config-mining.md) —
`Q-05-accrual-gbo.csv`, not `accrual.csv` or `results_final_v2.csv`. The agent detects which evidence
is still missing by looking for these filenames. A renamed file reads as absent evidence, and absent
evidence blocks the walk.

Where a query produces multiple result sets, the catalogue states the suffixes (`-1`, `-2`, `-3`, or
`-sequences` / `-triggers` / `-defaults`).

## Current runs

| Run | Agent | Status |
|---|---|---|
| `NY_SCH/tier2-pre/` | `sigom-box-fe-configs-agent` | Not started — kickoff prompt at `agents/sigom-box-fe-configs-agent/prompts/kickoff-ny-sch.md`. Gates 0d (PK mechanism) and 0e (schema completeness) both expected to fail on first attempt |
