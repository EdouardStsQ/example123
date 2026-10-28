# Devin kickoff — `sigom-box-acc-configs-agent` — NY_SCH BOX ACC gap run (Tier 2, reference SLB Tier 1)

> **How to start — nothing to paste.** Open a Devin session with this repo attached and type:
> **`Run automation/agents/sigom-box-acc-configs-agent/prompts/tier2-gap-run.md`**
> Devin reads this file and asks you for anything it needs, one question at a time.

**What this run produces:** for NY_SCH, the **pre-check results**, **NY's GBO configuration in scope**,
a **gap matrix** of the BOX - Accounting SIGOM screens — per screen and instrument: present / to create (and
from what) / to ask / N/A / OPEN — a **portfolio-properties report** (one BOX property per `Valid` in-scope GBO
property, the GBO → BOX **condition map**, the **clashes**, ADR 0020) for the users' review, and your decisions, in a new versioned run folder under
`runs/NY_SCH/<tier>-<env>/acc-configs/`. **Read-only: no SQL is written or run against any database by Devin.**

## Before you start

| | |
|---|---|
| **Repos** | this automation repo `cib-box-aukinbranch` (**read/write**); optional read-only `cib-boxacc-dbboxacc` (ACC packages: `PKG_ACCTPROP`, `PKG_ACCTPRECOMMIT`, `PKG_SIGOM_COV`) |
| ⛔ **Write protection** | No commit, branch, push, PR or edit on any repo except this automation repo; no DML anywhere |
| **Database** | Devin gets no connection. You run the queries it gives you — **Tier 1** for `REF`, the **target environment** for `TGT` (BOX), the run's **GBO source** for `GBO` (NY's GBO configuration — asked once, default the target environment) — and return each CSV with the name it says |
| **Already given** | NY_SCH branch `20007.4`; reference SLB `20087.4` (Tier 1); the six approved instruments (registry / gate 0c) — in `acc-configs-inputs.NY_SCH.json`; the expected structure in `docs/reference/box-acc-model.md` |
| 🔎 **Devin finds, never asks** `[2026-10-23]` | what a PK is (A-L1 — e.g. a second `FK_BRANCH` on SLB's rows); what each branch-condition value of NY's GBO properties means (A-U1 g — in / out, with evidence); the columns of a table (A-P8); a GBO → BOX condition pair when the field domain or the description is the same (ADR 0020) |
| ✏️ **Devin asks** | the target environment (Tier 2 PRE or DGBOUS); the **GBO source** — where NY's GBO configuration is read: the target environment (default) or PRE PARALELO (fresher copy of production; Tier 2 PRE's GBO was older on 2026-10-15) — once per run; the start date (`INIVALPCDATE`) of NY's new **portfolio** properties (≥ 01/01/1900); that Net Contract is N/A for NY; whether the CCS end-of-month netting applies to NY (screen 13); **each GBO → BOX
condition pair it is not sure of** — once per pair, with both functions' lines and the value translation (kept in
`runs/NY_SCH/branch/acc-configs/condition-map.csv`, never asked again); the **clash mode** — (a) hold the clashing
portfolio properties for your choice (default) or (b) create them all, the clashing ones `InValid` — every run (ADR 0020). Not asked: the topic mapping (by `CODE`, ADR 0018). **No usage window** ([ADR 0015](../../../docs/decisions/0015-acc-configs-scope-from-configuration.md)) |
| 🔒 **Never asked** (BOX ACC expert, [ADR 0014](../../../docs/decisions/0014-box-acc-expert-review-1.md), [ADR 0020](../../../docs/decisions/0020-portfolio-properties-imported-from-gbo.md)) | conditions (BOX as it is — never created); event groups (global — no NY copy); local properties' start date (01/01/1900) and content (NY's GBO, not SLB's); Conf Instru Type (SLB's BOX rows, as they are); GBO portfolio properties (`Valid` only, **one BOX property each**, its description as GBO's); internal-list topics (the internal account) |
| **Not touched** | the FE configs agent, the jobs agents, their runs |

---

**If you were pointed at this file**, it is your task prompt: skip the table above, check the repo is attached, start.

You are running as the `sigom-box-acc-configs-agent`, **phase 1 (gap run)**.

**Step 0 — repo root.** The folder containing `agents/` of the `cib-box-aukinbranch` checkout's `automation/` folder.

**Step 1 — read in full:** `agents/sigom-box-acc-configs-agent/AGENT.md`, `docs/reference/box-acc-model.md`,
`docs/reference/queries/acc-config-mining.md`, `docs/decisions/0011-acc-configs-agent-scope.md`,
`docs/decisions/0013-acc-prechecks-and-sigom-routines.md`, `docs/decisions/0014-box-acc-expert-review-1.md`,
`docs/decisions/0020-portfolio-properties-imported-from-gbo.md`,
`docs/process/checklists/acc-add-product-checklist.md` §0.

**Step 2 — the run folder and the GBO source.** Ask the target environment (`tier2-pre` or `tier2-dev` = DGBOUS),
then **once** the GBO source (`gbo_source.env`: the target environment by default, or PRE PARALELO) — every `GBO`
query runs there, every `TGT` query in the target environment, for the whole run. Then
`python3 scripts/new_run.py --branch NY_SCH --tier tier2 --env <pre|dev> --area acc-configs --name gap` — never
write over an earlier run; with an earlier run, `--from <its folder>` offers its answers one by one. Copy
`runs/NY_SCH/tier2-pre/acc-configs/acc-configs-inputs.NY_SCH.json` to the run as `acc-configs-inputs.json` (if the
script did not) and keep its answers. Evidence goes in the run's `01-evidence/`; a CSV already there is not asked
again (say so).

**Step 3 — the gate.** Ask, one at a time: **A-G1** in the target (NY) and in Tier 1 (SLB) → write
`target.group_pk`, `reference.group_pk`; A-G1 (b) in the target → if another branch of NY's group is already in BOX,
**stop and tell the operator** (checkpoint 1: screens 2 and 4 may already be configured for the group). Then **A-G2**
and **A-G3** (target).

**How every query is given** (hard rules 16–18 of the charter): the catalogue's text **as it is**, `&&` values
substituted from the inputs file (`target.gbo_schema` / `reference.gbo_schema` for the GBO schemas — SLB is
`PGT_ES`, never `PGT_SLB`) or a named CSV; **one system per query** — the operator has a GBO account and a BOX_ACC
account in each tier, so say which one, and a GBO vs BOX comparison is two CSVs you join; a failing query → A-P8 first,
then change only the name the error gives. Never a column the catalogue does not write.

**Step 4 — the pre-checks**, in the target and in Tier 1: **A-P1** (readable, live counts), **A-P2** (identity values
= the owner table of the catalogue), **A-P4** (negative owners), **A-P5** (target only: PK generation — (a), (b) auth code and the
max PK of this fraction, (c) the `F_GetPK` mode; a table behind → a finding with a proposal for the BOX team, not a
stop), **A-P6**
(package versions), **A-P7** (GBO vs BOX columns of every table copied: Cross Account Config, Global Accounts —
the column maps of the matrix). **A-P3** in the target. A failure → stop, say what failed and what it means (a missing grant: ask
for `BOX_ACC_RD` by name; an unknown owner / extension pair; `PKG_ACCTPROP` older than r0.0.8 — global / internal
topics come from the instrument-level configuration, the screen-2 / screen-4 reading changes and is asked).

**Step 4b — what the PKs are.** Every PK met in a CSV and not in the inputs file (e.g. a second `FK_BRANCH` value on
the reference's rows): **A-L1** in that tier — never a question. A row of another branch / group is reported and left
out.

**Step 5 — NY's GBO configuration in scope** (`GBO` = the run's GBO source, read-only, counts and codes only; **no
usage window** — the scope is configuration, ADR 0015): **A-U1** (a) and (f) (NY's portfolio properties with their
`STATUS` and branch value), then **A-U1 (g)** — classify **every** branch value (g1 the
branch condition's function source, g2 the group's branches, g3 each value's size) into in / out with its evidence;
show the classification table and get **one** confirmation; a blank value (no branch condition, or no branch row) is
**out**, not asked (BOX ACC expert, 2026-10-27); only a value g1–g3
cannot explain is asked, with the evidence and a proposal. `&&OUT_BRANCH_CODES` = the values classified out. Then
**A-U7** (a) and (b) (`Valid` properties of NY_SCH, full lists: topics, real
accounts). Summarise: properties `Valid` / `InValid` per instrument, in scope (branch value `NY_SCH`) / out, the
topics of the in-scope lists (the input for the topic mapping), their real accounts (→ `&&ACCOUNT_CODES` with A-03a's).
The windowed queries (A-U0, A-U2, A-U2b, A-U3, A-U4, A-U4b, A-U6) are **not run** unless the BOX team asks.

**Step 6 — the screens, in the charter's order**, one query at a time, each with its Env, the values substituted,
and the CSV name: A-06, A-07, A-01 (both) → A-08a (Tier 1), A-08b, A-09 (both) → A-03a (`GBO`: `PGT_NY.T_MAD_REVAL_ACCOUNTS`), A-03c (target), A-03b
(Tier 1, two CSVs: `PGT_ES.T_MAD_REVAL_ACCOUNTS` for SLB in the GBO account, SLB's BOX rows in the BOX_ACC account) → A-04a, A-04b (Tier 1, comparison only), A-04c (target), A-04d, A-04e, **A-04g then A-04f** (`GBO`) → **the condition map** (ADR 0020: A-04f / A-04g vs A-01-TGT; an existing `runs/NY_SCH/branch/acc-configs/condition-map.csv` is reused — its pairs are not asked again; a pair not sure → **A-04h** for both functions, then asked once) → A-02a, A-02b (Tier 1, comparison only), A-02c (target), A-02d (`GBO`) →
A-10a, A-10d (`GBO`), A-10b (target; `&&ACCOUNT_CODES` = A-U7b's accounts + A-03a's), A-10c (Tier 1, two CSVs: BOX and GBO accounts) → A-12a (Tier 1),
A-12c (target) → **A-13** (only if the CCS end-of-month netting applies to NY — asked first, Step 7: A-13a Tier 1,
A-13b and A-13c target) → **A-14** (label aliases for MIC: A-14a Tier 1, A-14b / A-14c target; codes from
`runs/NY_SCH/branch/books/label-aliases.csv` — the same in every environment, source `label_aliases.source`) → A-05 (target) → A-11 (Tier 1: (a) the columns first, then (b) per table). A query that fails: show the error, fix only what the error names, ask again. **Every list read is by
owner + extension; negative owners are excluded; counts are `COUNT(*)`.**

**Step 7 — the decisions**, one at a time, written to the inputs file with the date (nothing of the 🔒 row above):
- `INIVALPCDATE` for NY's new **portfolio** properties (≥ 01/01/1900, the local properties' fixed date): propose
  01/01/1900 (NY's GBO properties all start on `01-JAN-00`, model §9.2; show the reference's), ask;
- Net Contract: N/A for NY (not Madrid real) — confirm;
- **the CCS end-of-month netting** (screen 13, model §8.1): does it apply to NY? — asked **before** A-13, every run, no
  default. Yes → SLB's rows **as they are** (instrument types, strategies, `EOM_CCS_ACTIVE`, accounts by code), each
  account shown with whether NY's CCS portfolio properties use it on a netting topic; you change what NY needs. No →
  `N/A`;
- ~~the GBO → BOX topic mapping~~ — not asked: always by `CODE` (BOX ACC expert, 2026-10-27, ADR 0018);
- **the clash mode** (`decisions.pp_clash_mode`, ADR 0020) — every run, before the report: (a) the portfolio
  properties that clash in BOX are held for your choice (default); (b) all are created and the clashing ones end
  `InValid` in BOX. Clash choices already in the inputs (`decisions.pp_clash_choices`, from an earlier run's report)
  are applied: the chosen property of each group is created, the others listed as not carried.

**Step 8 — the gap matrix and the report.** Write `02-acc-gap-matrix.md` from
`agents/sigom-box-acc-configs-agent/templates/acc-gap-matrix.md.tmpl`, and `03-portfolio-properties-report.md` from
`agents/sigom-box-acc-configs-agent/templates/portfolio-properties-report.md.tmpl` (per BOX property: topics, account,
the GBO properties it came from; per GBO property: where it went; what is not carried). Matrix: the pre-check results, the GBO configuration in scope, then
per screen and instrument (for screen 4: per GBO portfolio property) the reference rows (comparison), what NY has
in scope, the action, the source, the evidence file:line. Rules (ADR 0020): **screen 2** = NY's GBO — per instrument
the topics of the in-scope properties (each in its GBO list) and their conditions with a BOX twin; a property whose
topics or conditions differ from the instrument's set → a finding; **screen 4** = **one BOX property per `Valid`
in-scope GBO property**, its description as GBO's, its conditions through the condition map (the others dropped,
listed), its own topic → account rows; **clash groups** (identical kept condition values, masked values by hash) per
the clash mode, each in the report's clashes section with why they clash (the dropped conditions that told them apart)
and what choosing one leaves out — no recommendation; GBO → BOX topics **by `CODE`**; a GBO topic in scope with no BOX `CODE` twin,
or a standard historic the branch needs and missing → **`create (global .65)`, flagged *global — to review*** (own
section of the matrix, with the PRE / PROD PK-clash warning, ADR 0018); a condition, event group or event missing →
a finding (never created); GBO portfolio properties with a blank branch condition or no branch row → **out** (not
asked); `T_PGT_TOPICS_RR` and GBO ConcMis → **out**; an account not in A-10a → **OPEN**, never the reference's account; a GBO value
longer than BOX's column → a finding; no reference rows for an instrument (e.g. CDS) → **N/A — no reference** (say so);
an approved instrument with no `Valid` in-scope GBO property → **N/A — not configured in GBO** (asked); a condition naming a portfolio, a counterparty or an entity → its
hash only (A-04f; phase 2: open question 10 of the charter); a topic with several accounts in one GBO property → **OPEN**; an internal-list topic → the internal account (never empty); a GBO `InValid` portfolio property → not
read; a BOX column with no source in the column map → asked.

**Step 9 — finish:** show the matrix summary (counts per action and screen), the report's summary (properties
to create / held in a clash / OPEN per instrument, the clash groups, the conditions dropped), the open questions, and that this is a proposal for the BOX team (checkpoint 2). Commit the run folder to the automation repo only.
