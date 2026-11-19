# 0028. GBO reports rebuilt in BOX: a report-migration agent, the GBO file as the reference, decisions with defaults

Date: 2026-11-18
Status: accepted

## Context

`[operator, 2026-11-18]` The BOX lead asked for NY's GBUX file (NY UME Extendida, a 164-character fixed-width
position-classification file GBO sends to Equation) to be produced by BOX "using the BOX data model". The GBO US team
sent its analysis of the current GBO report: an overview, the process specification, the 22-field dictionary and
the source lineage matrix (`runs/NY_SCH/branch/reports/gbux/gbo-spec/`). Their documents stop at the GBO contract;
the BOX mapping is ours. Other branches have the same kind of GBO interfaces, and the BOX lead cannot answer the
open questions (trade id, scope, field 21's source, where it runs) right now.

## Decision

1. **A generic agent, `box-report-migration-agent`**, and GBUX its first run. The charter is branch-agnostic; the
   report's files live once per branch in `runs/<BRANCH>/branch/reports/<report>/`; runs in
   `runs/<BRANCH>/<tier>-<env>/reports/<report>_<date>_<n>/` (`new_run.py` area `reports`).
2. **The GBO side's specification is the reference, read-only**, and the **report's structure is data**: `layout.csv`
   (positions, widths, allowed values, sensitive fields) and `decodes.csv` (every value the GBO logic tests), each row
   citing its section. Scripts read the layout; nothing re-types it.
3. **Reproduce what the GBO file contains, not what its code intended** — unreachable branches, legacy defects,
   duplicates — unless `deviations.csv` says `fix`; operational defects (swallowed errors, non-atomic writes,
   session date formats) are fixed because the content does not change.
4. **Every BOX source evidenced or OPEN** (`02-field-matrix.csv`, from a seed built from the repo's model docs).
5. **Decisions have owners and defaults.** `decisions.csv` holds each open question with the default the runs apply,
   so the gap run, the build and the parallel run go on; only `check_report_run.py --go-live` requires every one
   `decided` (answer and date) — no agent writes an answer.
6. **Build as a read-only SELECT first**, run by the operator and spooled (`TRIMSPOOL OFF`); the PL/SQL procedure,
   the batch wiring and the directory come after the go-live decisions.
7. **Compared on the common key.** `compare_fixed_width.py` maps each side's trade id to `FRONT_ID` (the GBO / BOX
   common key, `box-fe-test-lookups.md`), matches byte-identical records as a multiset (duplicates count), pairs the
   rest by key fields, and classes each difference by a decision or deviation id; the result is `UNEXPLAINED|<n>`.
8. **Trade-level data never in the repository**: files, spools, id crosswalks and detail differences in the run's
   git-ignored `local/`; reports hold counts, sensitive fields hashed; `--detail` is refused inside the repo.

## Alternatives considered

- **Wait for the BOX lead's answers before building**: rejected — none of them changes the scripts or the gap run; the
  defaults keep the work moving and the go-live check keeps them from being forgotten.
- **A one-off script for GBUX**: rejected — every branch has GBO interfaces to move; the layout-as-data and the
  comparer are the same for all.
- **Write the BOX PL/SQL package straight away**: rejected — where it runs (D7) is undecided, and a read-only SELECT
  is enough to prove the mapping in the parallel run.
- **Recompute GBO's intended behaviour (fix every defect)**: rejected as a default — Equation receives GBO's actual
  content; every content change is the owner's decision (`deviations.csv`).
- **Retype the specification from screenshots into the repo**: rejected — error-prone; the operator adds the files
  as received (one edit: a local path with a user id removed).

## Consequences

- New: `agents/box-report-migration-agent/` (charter, kickoffs `gap-run.md` / `build.md` / `parallel-run.md` /
  `kickoff-gbux.md`, templates), `docs/reference/queries/report-migration-mining.md` (R-P, R-B, R-G, R-T),
  `scripts/fixed_width.py`, `check_fixed_width.py`, `compare_fixed_width.py`, `check_report_run.py` with tests
  (`scripts/tests/test_report_migration.py`), `runs/NY_SCH/branch/reports/gbux/` (README, `gbo-spec/README.md`,
  layout, decodes, seed matrix, decisions D1–D8, deviations DV1–DV13), an eval case; `new_run.py` area `reports`;
  `.gitignore` `runs/**/local/`.
- The field-21 source (early termination) and the BOX FX legs are OPEN until the gap run's queries or the BOX lead
  say otherwise; the first slice is NY SCH deposits and IRS.
- The comparison doubles as a check of the ACC configuration: a portfolio property BOX resolves differently (a clash
  group, an empty condition) shows up as a GL-account difference named with its property.
