# 0030. GBO vs BOX FE reconciliation: one standard pack, a clean set, and known causes as rules

Date: 2026-11-25
Status: accepted — builds on [ADR 0029](0029-gbo-box-trade-key-auki-migration-crosswalk.md) (the trade key)

## Context

`[operator, 2026-11-25]` The IRS parallel test of 25-Sep-2026 (NY SCH, PRE-PARALELO) took some thirty queries and
two days of back-and-forth with Devin: every join (crosswalk, flows, schedule, RAW source), every BOX behaviour
(cancelled flows counted, payment date as maturity, PLACC not calculated) and every GBO convention (06-JUN-66, RATECUR
0 on USD legs) was found one query at a time, and a mistaken step (a too-strict clean filter, a lost decimal suffix)
changed the counts twice. The operator wants the next run - more deals, more dates - to be faster and reliable.

## Decision

1. **One standard pack**: `fe_reconcile.py pack` writes every file the assessment needs, with the joins proven on the
   25-Sep run and the account each one runs under: 05 crosswalk checks, 10 / 20 the GBO / BOX financial and deal
   extracts, **12 BOX flows per deal** (BOX_ADMIN) and **06 the BOX import funnel** (diagnostic). The operator exports
   each once per date; no improvised query.
2. **A clean set before any comparison** (`scripts/fe_assess.py`): a deal is compared only when BOX holds it
   completely - (a) the same legs on both sides after the all-zero rows are dropped, (b) every leg in both deal
   extracts, (c) a current interest flow on every direction in BOX, (d) no BOX input blank (rules `input_required`).
   Deals left out are counted per reason as **missing data**, never mixed with calculation differences.
3. **Known causes are data, not memory**: `docs/reference/fe-recon-rules.csv` holds the exclusions, normalisations
   (blank = 0, the dead-date sentinel), decodes, renames, and the classes found on 25-Sep (rebooked deal, by design,
   to confirm, payment lag, GBO zero, functional) with their source and status. A difference no rule explains is
   `DIFF - unexplained`: the only class that needs a person.
4. **Explain an unexplained difference from the code first**: BOX's in `cib-boxfin-dbboxfe` (read-only); GBO's engine
   bodies are not readable (`pgtadmin` sees specs only), so GBO is tested on the data. A confirmed explanation becomes
   a rule (a PR to the rules file), so the next run classes it by itself.
5. **Outputs**: `03-assessment.md` (counts only, committed) and, in the run's git-ignored `local/`, the xlsx (Summary,
   Issues with one real example per type, Deals, Details, Excluded, Rules) and the detail CSV - written with the
   standard library (`scripts/xlsx_lite.py`; no package install on the bank PC).
6. **Headline** = full-match deals on the clean set (no unexplained, rebooked or functional difference), plus the
   same leaving aside the functional differences.

## Alternatives considered

- **Keep Devin improvising per run**: rejected - slow, and the counts moved with each mistake.
- **Rules in the code**: rejected - the rules change with each product and each expert answer; a CSV with sources is
  reviewed like the field map.
- **Compare every deal BOX has**: rejected - missing data (RAW load, import drops) would swamp the calculation
  differences; it is followed by the funnel (06) and the data owners.

## Consequences

- New: `scripts/fe_assess.py`, `scripts/xlsx_lite.py`, `docs/reference/fe-recon-rules.csv`, tests
  `scripts/tests/test_fe_assess.py`; `fe_reconcile.py pack` writes 12 and 06 and the plan's steps 4a / 4c / 5b
  (input `raw_source`); the parallel-test skill, the lookups doc, the eval case.
- Rules proven on IRS only; another product's first run confirms or changes them (rows `INFERRED` until then).
- The BOX flows step uses `T_BOX_FLOW_DATA_S` columns seen on 25-Sep; a column missing in another environment stops
  the query - fix the pack, not the export.
