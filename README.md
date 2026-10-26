# BOX ACC configs — NY_SCH

Agent [`sigom-box-acc-configs-agent`](../../../../agents/sigom-box-acc-configs-agent/AGENT.md), phase 1 (gap run),
kickoff `Run automation/agents/sigom-box-acc-configs-agent/prompts/tier2-gap-run.md`. Model it works on:
[`box-acc-model.md`](../../../../docs/reference/box-acc-model.md).

| File | State |
|---|---|
| `acc-configs-inputs.NY_SCH.json` | NY's known values: branch `20007.4`, group `21447.4`, reference SLB `20087.4` (Tier 1), six instruments with PKs, the expected structure (owner objects, list / array extensions, package version), the usage source (PRE PARALELO) and NY's branch conditions `[2026-10-15]`; the target environment, usage window and decisions are filled in the run |
| `<run>/` | each run is a new versioned folder `acc-configs/gap_<YYYYMMDD>_<n>/` (`scripts/new_run.py --area acc-configs`), in `tier2-pre/` or `tier2-dev/` (DGBOUS) — the target environment is asked |
| `<run>/acc-configs-inputs.json` | the run's copy |
| `<run>/01-evidence/` | the `A-…` CSVs ([catalogue](../../../../docs/reference/queries/acc-config-mining.md)) — `-REF` Tier 1, `-TGT` the target, `-GBOPROD` GBO production |
| `<run>/02-acc-gap-matrix.md` | the result, for the BOX team |
| `<run>/03-portfolio-properties-report.md` | GBO vs BOX portfolio properties, for the users' review `[2026-10-22]` |
| `01-evidence/` (this folder) | kept empty — evidence lives in each run |

First gap run `gap_<date>_1` (Steps 0–5) in Devin's branch; the usage queries were then re-run by the operator in
**PRE PARALELO** `[2026-10-15]`. What is known — mechanisms in
[`box-acc-model.md`](../../../../docs/reference/box-acc-model.md) §9, queries in the
[catalogue](../../../../docs/reference/queries/acc-config-mining.md):

- **Pre-checks pass** in Tier 2 PRE (tables, identity values, metamodel, `PKG_ACCTPROP` r0.0.8); findings: the
  `PARENT_DATE` sequence is at its max PK (phase-2 blocker for an account date rule — BOX dev), Tier 1's package
  version unverified, 5 Tier 1 `LIST_TOPIC` rows under GBO extension `38422.4` (excluded, a Tier 1 data defect).
- **GBO source = PRE PARALELO** (Tier 2 PRE is older: Cross Account Config 17 vs 24 rows).
- **NY SCH is the first branch of group `21447.4` in BOX** (A-G4 = 0 rows): every row is created at group level; the
  group holds 25 branches.
- **No usage window, one GBO source per run** `[operator, 2026-10-22]` ([ADR 0015](../../../../docs/decisions/0015-acc-configs-scope-from-configuration.md)):
  the scope is configuration (`Valid` properties of `NY_SCH`, full lists); the GBO source (Tier 2 PRE or PRE PARALELO)
  is asked once at the start of each run. The usage results below (July, PRE PARALELO) stay as diagnostics.
- **BOX ACC expert review** `[2026-10-22]` ([ADR 0014](../../../../docs/decisions/0014-box-acc-expert-review-1.md)):
  conditions and event groups as BOX has them (global, nothing asked); local properties start 01/01/1900; Cross
  Account Config from **`PGT_NY.T_MAD_REVAL_ACCOUNTS`** (SLB: `PGT_ES.T_MAD_REVAL_ACCOUNTS`); Conf Instru Type = SLB's
  BOX rows; GBO portfolio properties **`Valid` only**; internal-list topics → the internal account; a GBO vs BOX
  portfolio-properties report. The counts below were read before it — re-run A-U7 with the `Valid` filter, and A-03.
- **Screen 4 scope** = the portfolio properties whose branch condition is `NY_SCH` (A-U1 f): 58 (before the `Valid` filter); to decide: IRS
  `INTERNAL` `2212.35`, 6 CDS (no branch condition); the 6 `NY_IBF` depos properties are out. Full lists copied.
- **Screen 3** ~~= NY's 24 GBO Cross Account Config rows~~ — those are GBO's `T_PGT_CROSS_ACCTCONF_S` (`EXTERNALSETTACC`
  by currency, A-U6), **not** BOX's source: read `PGT_NY.T_MAD_REVAL_ACCOUNTS` (A-03a) and SLB's GBO vs BOX rows
  (A-03b: `TIPO` = `ACC_TYPE`?) — 4zr.
- **Topics / accounts** for BOX: the in-scope lists (A-U7a / A-U7b); BOX dev questions 4za–4zd.
- BOX as SLB uses it (Tier 1) is not read yet — 4zf.

- **Gap run `gap_20261023_1`** (Tier 2 PRE, GBO source Tier 2 PRE) `[2026-10-23]`: 62 `Valid` NY_SCH properties in
  scope → 95 BOX properties (shape), 7,259 topic rows' account OPEN, 54 GBO topics with no BOX code, 570 accounts +
  364 date rules to create, 348 Cross Account Config rows from `PGT_NY.T_MAD_REVAL_ACCOUNTS`. Issues the run showed,
  fixed in the agent (hard rules 16–18): `PGT_SLB` instead of `PGT_ES` (A-03b), columns that do not exist (A-04a
  `NAME` / `FK_GROUP`, A-11 GLTA Local Dep), questions the data answers (`269.4` = a branch group, Madrid — A-L1; the
  branch-value families `PAR_NY_SCH`, `SAT_2`, `SAT_NY`, `NY_SCH2` — A-U1 g). The families decision (NY_SCH only) is
  **provisional** until A-U1 (g) is run — 4zu.

Open items for this agent: 4r–4w, 4za–4zf, 4zr, 4zu in [`../jobs/99-open-items.md`](../jobs/99-open-items.md).
