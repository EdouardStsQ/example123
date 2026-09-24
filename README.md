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

## ⛔ A rerun overwrites the previous run. Archive first.

`RUN_FOLDER` is a fixed path, so a second run writes over `02-findings.md`, `01-evidence/*.csv`,
`03-sql/` and `99-open-items.md`. **The previous run's artifacts are the evidence behind its review** —
losing them makes the review unfalsifiable, which is the one thing this repo does not allow.

**Before starting a rerun, archive:**

```bash
cd runs/<BRANCH_CODE>/<ENVIRONMENT>
mkdir -p archive/run-NN
git mv 02-findings.md 99-open-items.md 01-evidence 03-sql archive/run-NN/ 2>/dev/null
mkdir -p 01-evidence 03-sql
```

**What stays at the root, because it spans runs:** `README.md` (the run log), `00-inputs.md`, and the
gate sign-off pack. **What moves:** everything the run produced.

An archived run validates on its own — `python3 scripts/validate_run_output.py
runs/<branch>/<env>/archive/run-NN/` — so a rejected run stays checkable against the rules that
rejected it. A review file moves with the run it reviews.

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
  00-decisions.md        # one row per decision card answered: decision, value, name, role, date, evidence
  03-sql/
    values.json          # WRITTEN by the agent: every value with its source (the only SQL input)
    <BRANCH>-<env>-rehearsal.sql   # RENDERED by scripts/render_sql.py - never edited (ADR 0006)
    <BRANCH>-<env>-config.sql
    <BRANCH>-<env>-verify.sql
    <BRANCH>-<env>-rollback.sql
    render-report.md     # what was rendered, from what, and which rows were filtered out
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
| `NY_SCH/tier2-pre/` | `sigom-box-fe-configs-agent` | **ACTIVE 2026-09-18** — the real run, in **deferred-verification** mode: mines GBO Tier 2 and targets BOX Tier 2 PRE, deferring only the BOX-side existence reads (procedure C2) and gate 0e, which is the release gate. Output is a marked draft, executable without regeneration once `BOX_FE` access lands |
| `NY_SCH/tier1-pre-rehearsal/` | `sigom-box-fe-configs-agent` | **SUPERSEDED 2026-09-18** — split-tier rehearsal writing to Tier 1 PRE. Withdrawn in favour of the deferred-verification run above. Kept for the findings it produced (`PGT_MRK` environment-specificity, the `6401.4` collision, the Tier 1 structural reference, four query defects) |

## Charter file casing — `AGENT.md` showing as `agent.md` on GitHub

**Why it happens.** Windows and macOS file systems ignore case. If a file was ever committed as
`agent.md`, then copying or unzipping `AGENT.md` over it **keeps the old name** — the content changes,
the case does not — and git (with `core.ignorecase = true`, the Windows default) sees no rename to push.

**Fix once, from the checkout root** (`cib-box-auki-nbranch`), in **Git Bash**:

```bash
git ls-files | grep -i '/agent\.md$' | grep -v '/AGENT\.md$'      # lists the lower-case ones
for f in $(git ls-files | grep '/agent\.md$'); do
  d="${f%agent.md}"
  git mv -f "$f" "${d}AGENT.md.tmp" && git mv -f "${d}AGENT.md.tmp" "${d}AGENT.md"
done
git commit -m "Restore AGENT.md casing" && git push
```

Or on GitHub itself: open the file → ✏️ edit → change the name in the path box to `AGENT.md` → commit.

The two-step `git mv` (via a temporary name) is what makes a case-only rename stick on a
case-insensitive disk. **Check afterwards on GitHub**, not locally — the local file browser will show
whichever case it likes. **To stop it recurring:** delete the old `automation/` folder before unzipping
a new copy, rather than extracting over it.

The run prompts search for the charter case-insensitively, so a run works either way; this fix is so
nobody has to tell the agent.
