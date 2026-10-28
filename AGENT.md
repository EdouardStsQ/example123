---
name: sigom-box-acc-configs-agent
description: Configures the BOX - Accounting SIGOM screens a new branch needs, branch-agnostic - only what depends on the branch (local properties, portfolio properties, cross account config, conf instrument type, the branch's accounts), verifying the global screens (topics, conditions, standard historic, event groups and events - used as they are). Phase 1 (built) is a read-only gap run with a GBO vs BOX portfolio-properties report; phase 2 renders the SQL.
---

# SIGOM BOX ACC Configs Agent

**Status: phase 1 built 2026-10-07 (the gap run); pre-checks and GBO-production usage added 2026-10-14
([ADR 0013](../../docs/decisions/0013-acc-prechecks-and-sigom-routines.md)); the BOX ACC expert's review applied 2026-10-22
([ADR 0014](../../docs/decisions/0014-box-acc-expert-review-1.md)); the scope from configuration, no usage window, one GBO
source per run 2026-10-22 ([ADR 0015](../../docs/decisions/0015-acc-configs-scope-from-configuration.md)); the
catalogue's text as it is, one system per query, find before asking (hard rules 16–18) 2026-10-23; phase 2
(rendered SQL) designed, not built.**
Why this shape: [ADR 0011](../../docs/decisions/0011-acc-configs-agent-scope.md). The model it works on — tables,
identity values, keys, PK rule, what runs on save, how the lists are generated — is
[`box-acc-model.md`](../../docs/reference/box-acc-model.md). Its FE counterpart is
[`sigom-box-fe-configs-agent`](../sigom-box-fe-configs-agent/AGENT.md) — unchanged by this agent.

## Goal

For a new branch, every **BOX - Accounting** SIGOM screen holds what the branch needs to post its accounting in
BOX — **and nothing global is touched that did not need to be**. Correct means: each branch-dependent row has a stated
source (the reference branch's BOX row, or the branch's own GBO row translated), each global object the branch relies
on is shown present in the target, each value no source gives is an open question — never a guess. GL accounts are
never derived.

## Definition of done

Phase 1 (gap run), for one target branch:
1. the **pre-checks** (A-P1–A-P7) passed in every tier the run reads — readable tables, live counts, identity values,
   negative owners listed, `PKG_ACCTPROP` version known, columns compared; a failure is the run's result. **A-P5** (PK
   generation: auth code, `F_GetPK` mode, next value vs the max PK of this installation's fraction) is the
   counterpart of the FE configs agent's pre-step P1: a table behind is a **finding** with a proposal for the BOX team
   (phase 1 writes nothing) and blocks that table in phase 2 `[2026-10-23]`;
2. the **target's GBO configuration in scope** (A-U1, A-U7) is in the evidence, read in the run's **GBO source**
   (asked once; default the target environment): its `Valid` portfolio properties whose branch condition is the
   target's, with their **full** lists, topics and accounts — **no usage window**; what is built comes from
   configuration, never from what was posted in a period `[ADR 0015]`;
3. the evidence CSVs of [`acc-config-mining.md`](../../docs/reference/queries/acc-config-mining.md) are in the run's
   `01-evidence/` (both tiers where tagged);
4. `02-acc-gap-matrix.md` says, per screen and instrument, **present / to create (from what) / to ask / N/A / OPEN**,
   each line with its evidence file, **only for the target's configuration in scope** (A-U7);
5. `03-portfolio-properties-report.md` shows, per BOX portfolio property to create, its topics per list, the account
   proposed for each and the target's **Valid** GBO portfolio properties it comes from — and, the other way, where
   each of those GBO properties went (from
   [`templates/portfolio-properties-report.md.tmpl`](templates/portfolio-properties-report.md.tmpl)) `[ADR 0014]`;
6. the operator's decisions are in the run's inputs file (the GBO source, the portfolio-property start date, …);
7. the BOX team has reviewed the matrix and the report (checkpoint 2).

Phase 2 adds the rendered SQL (proposal, verify, rollback) — not built.

## The screens — what a new branch changes `[stated: operator + Confluence checklist, 2026-10-07]`

| # | Screen (BOX - Accounting) | Table | Keyed by | For a new branch | Source of the values |
|---|---|---|---|---|---|
| 0 | Labels (books) | `PGT_SYS.PGT_DOMAINS` | — | prerequisite | `sigom-box-fe-configs-agent` (skill `set-up-book-labels`) |
| 1 | Config. > Condition Port Properties | `T_BOX_CONDPAR_PROP_S` | global | **verify**: the conditions the local properties use exist — **never asked** | — BOX as it is: not branch-dependent `[ADR 0014]` |
| 2 | Config. > Config. Local Properties | `T_BOX_CONF_LO_PROP_S` + 4 arrays in `T_BOX_LINK_ARRAY_X` (local / global / internal topics, conditions) | branch **group** | **create** per instrument, unless the group already has them (unique key group × instrument × date) | the **reference branch's BOX** rows (same arrays); **`INIVALPCDATE` = 01/01/1900**, always (`[ADR 0014]`, not asked). GBO's local properties have **one** topic array — not translatable |
| 3 | Config. > Cross Account Config | `T_BOX_CROSS_ACCTCONF_S` | branch | **create** | the **target's GBO** rows of **`<GBO schema>.T_MAD_REVAL_ACCOUNTS`** (the schema = the branch's GBO wrapper owner, registry `wrapper_owner`) `[ADR 0014]` — **not** `PGT_SYS.T_PGT_CROSS_ACCTCONF_S`. Columns differ from BOX's (`PK`, `FK_BRANCH`, `FK_INSTRUMENT`, `FK_GLTA`, `TIPO`… vs BOX's currency, entity, topic, account, `ACC_TYPE` `0` vencida / `1` viva / `2` balance viva): the column map and the translation (account by code, `TIPO` → `ACC_TYPE`?) learnt from the reference's GBO rows vs its BOX rows (A-03b, A-P7) |
| 4 | Config. > Portfolio Properties | `T_BOX_ACCT_PORT_PROP_S` → three topic lists + conditions generated by `f_GenTopicCond` | branch **group** | **create** per instrument **in scope** (A-U7: the `Valid` GBO properties of the target's branch, full lists), then generate the lists, then the account per BOX topic and list, then read `STATUS` | shape: the reference's BOX rows; accounts: the target's **Valid** GBO portfolio properties (`InValid` ones never read `[ADR 0014]`) **through the GBO → BOX topic mapping** — **never GBO topics** (operator); **internal-list topics take the internal account** the reference's internal lists use (`INTERNAL`), never left empty `[ADR 0014]`. GBO's portfolio properties are **consolidated** into fewer BOX ones (2,476 vs 71 in PRE-PROD) — an analysis, not a transcription (BOX team, [05-add-product](../../docs/process/05-add-product-procedure.md)). Conditions on portfolio / counterparty take the target's own values (asked). OPEN until the mapping is found |
| 5 | Data > Net Contract | `T_BOX_NETCONTRACT_S` | branch | **N/A** unless the target has net contracts in its GBO — in BOX today only one Tier 1 branch has real rows, copied from its GBO table by a PL ([`acc-config-mining.md`](../../docs/reference/queries/acc-config-mining.md)) | — |
| 6 | Data > Accounting Topics | `T_BOX_ACCT_TOPICS_S` | global | **verify** the topics of 2 and 4; GBO → BOX topics **by `CODE`**, always; a GBO topic in scope with no BOX `CODE` twin → **create as a global topic (`.65` PK), flagged *global — to review*** `[BOX ACC expert, 2026-10-27 — ADR 0018]` | the target's GBO topic (`CODE`, description) |
| 7 | Data > Standard Historic | `T_BOX_ACCT_HISTSTD` | global `[inferred — A-07]` | **verify**; one the branch needs and missing → **create as global (`.65` PK), *global — to review*** (ADR 0018) | the reference's row |
| 8 | (GBO>SYS>Process>Batch) Event Grouping | `PGT_PRC.T_PGT_BR_EVE_S` + `_EXT_S` | global (shared) | **verify** — the branch runs the **global** groups; no branch copy, no question `[ADR 0014]` | the reference's ACC groups (its MBJ rows, A-08a) |
| 9 | (GBO>SYS>Process>Batch) Event Config | `PGT_PRC.T_PGT_EVE_S` | global (shared) | **verify** | — |
| 10 | Data > Global Accounts | `T_BOX_ACCT_GLTA_S` (+ optional date rule `T_BOX_ACCT_PARENT_DATE_S`) | global catalogue | **create the missing ones** the branch's config **uses** | the **target's GBO** accounts (`T_PGT_ACCT_GLTA_S`): same as GBO (operator); the copy rule learnt from the reference (A-10c); GLTA type and direction translated **by `CODE`**; a value longer than BOX's column (20 / 20 / 50) is a finding; one row per account (+ its GBO date rule, A-10d, if any) |
| 12 | Config. > Conf Instru Type | `T_BOX_CONF_INSTRUM_TYPE_S` (owner `35000292.65`) | branch | **create** per instrument the reference has rows for — its values **as they are**, the target's branch PK; never read from GBO `[ADR 0014]` | the **reference branch's BOX** rows (A-12) |
| 13 | Config. > Net EOM to CCS ("BOX Net CCS PlanBS") | `T_BOX_NETCCS_BSPLAN_S` (owner `35000348.65`) | branch + instrument type + strategy + account | **only if the CCS end-of-month netting applies to the branch — asked every run** (no → N/A); then **create** the reference's rows **as they are** (same instrument types, strategies, `EOM_CCS_ACTIVE` switch row, account codes); the operator changes what the branch needs `[operator, 2026-10-26]` | the **reference branch's BOX** rows (A-13a); accounts by `CODE` (screen 10). What it is: [`box-acc-model.md`](../../docs/reference/box-acc-model.md) §8.1 |
| 14 | (Label Config) Systems Alias — **label aliases for MIC** | `PGT_TRD.T_PGT_OBJ_SOURCE_S` (owner `17910.4`, extension `118615.4`) | label (book) + GL source | **create** one per book label with ACC jobs, from the GL team's codes (`books/label-aliases.csv`) and the GL source (`label_aliases.source`); no code → `OPEN` and the book list for the GL team `[BOX expert, 2026-10-27 — ADR 0017]` | the GL team (Equation) — never derived, never the reference's codes; what and why: [`box-acc-model.md`](../../docs/reference/box-acc-model.md) §8.2 |
| 11 | MBJ Config | `T_BOX_MBJ_PROPERTIES_S` | branch | **not this agent** — the ACC jobs (`shell.conf`, Control-M, MBJ) go to **[`box-acc-jobs-agent`](../box-acc-jobs-agent/AGENT.md)** (the ACC equivalent of `box-fe-jobs-agent`, built 2026-10-21) | J-R2 |

**Outside the screens** (A-11, [`box-acc-model.md`](../../docs/reference/box-acc-model.md) §8): Conf Instru Type is
screen 12 (2026-10-22), Net CCS PlanBS screen 13 (2026-10-26); GLTA Local Dep checked against GBO's rows; GBO's
ConcMis and a branch's own GBO topic tables (e.g. a `T_PGT_TOPICS_RR`, model §8) are **out** — nothing to do (BOX ACC
expert, 2026-10-27); runtime objects out.

**Order** (each step needs the previous): gate (group, instruments) → **pre-checks** (A-P) → **the target's GBO
configuration in scope** (A-U1, A-U7) → 6, 7, 1, 9, 8 (verify) → 10 (accounts) → 2 (local properties) → 4 (portfolio properties,
`f_GenTopicCond`, accounts, the report) → 3 (cross account) → 12 (conf instrument type) → 13 (CCS EOM netting, if it
applies) → 14 (label aliases for MIC) → 5 (N/A check). Objects of the ACC module keyed on the
branch but not in this list are ruled in or out with A-11.

## Inputs — `runs/<BRANCH>/<env>/acc-configs/acc-configs-inputs.json`

| Value | From |
|---|---|
| target branch PK, reference branch PK | the run (the branch's inputs file, `acc-configs-inputs.<BRANCH>.json`) |
| target / reference branch **group** | **A-G1** — never typed |
| approved instruments (PKs) | registry `instruments` → the FE agent's `APPROVED_INSTRUMENTS` PKs |
| fixed, never asked `[ADR 0014]`: event groups **global**; local properties' `INIVALPCDATE` **01/01/1900**; conditions as BOX has them; Conf Instru Type as the reference's; GBO portfolio properties **Valid** only; internal-list topics → the **internal account** | the charter |
| the GBO schema of `T_MAD_REVAL_ACCOUNTS` for the target and the reference | registry `wrapper_owner` of each branch |
| decisions: the portfolio properties' `INIVALPCDATE` (≥ 01/01/1900, the local property's); Net Contract N/A confirmed | **asked**, one at a time (the topic mapping is not asked: by `CODE`, ADR 0018) |
| whether the CCS end-of-month netting applies to the branch (screen 13) | **asked every run** (no default) `[operator, 2026-10-26]` |
| label aliases for MIC (screen 14): `runs/<BRANCH>/branch/books/label-aliases.csv` (the GL team's code per book) and `label_aliases.source` (the GL source PK) | the operator, from the GL team; the source **proposed** from A-14 / model §8.2 and confirmed `[2026-10-27]` |
| what a PK is (a second branch / group on the reference's rows…); what a branch-condition value means (in / out of scope) | **found** — A-L1, A-U1 (g); never asked first (hard rule 18) `[2026-10-23]` |
| the target environment and the reference environment | **asked** (the candidates: the branch's `acc-configs/README.md`) |
| the **GBO source** — where the target's GBO configuration is read (env tag `GBO`): the target environment (default), or a fresher copy of production the operator names | **asked once per run**, written in the inputs file `[operator, 2026-10-22]` |

## Phase 1 — the gap run (built)

Kickoff: one per branch in `prompts/` — the first, [`prompts/tier2-gap-run.md`](prompts/tier2-gap-run.md), is the first Tier 2 branch's; a new branch copies it with its own values. The agent asks the operator to run the
queries one at a time (it has no database), reads the CSVs, and writes `02-acc-gap-matrix.md` from
[`templates/acc-gap-matrix.md.tmpl`](templates/acc-gap-matrix.md.tmpl): the pre-check results, the GBO configuration in scope, then per
screen × instrument the reference rows, what the target has and uses, the action, the source, the evidence file —
and `03-portfolio-properties-report.md` from
[`templates/portfolio-properties-report.md.tmpl`](templates/portfolio-properties-report.md.tmpl): GBO vs BOX, per BOX
portfolio property and per GBO one, for the users' review. It compares, it does not insert.

## Phase 2 — rendered SQL (planned)

Like the FE renderer (ADR 0006): a script renders, from the inputs and the evidence, the proposal per screen in the
order above, a verify and a rollback. **Designed** `[2026-10-14]` ([ADR 0013](../../docs/decisions/0013-acc-prechecks-and-sigom-routines.md)):
rows are created **the way SIGOM does**, in one transaction (nothing in the packages commits):

1. each row's `PK` and `FK_OWNER_OBJ` from **`PKG_SIGOM_COV.P_SETHEADER` / `F_GetPK`** (the installation's
   `AUTH_CODE` fraction, the connection's PK mode) — **no hard-coded PK**;
2. accounts (+ date rule), local properties and their four arrays (owner `35000194.65`, the four extensions),
   portfolio properties (owner `35000170.65`, `FK_BRANCH` = the **group**);
3. **`PKG_ACCTPROP.f_GenTopicCond(PK)`** per portfolio property — it creates the three topic lists and the condition
   list (and calls `p_StatusPortFolio`);
4. **UPDATE each list row's `FK_GLTA`** (no code does it) per portfolio property × list × topic, then fill the
   conditions' values;
5. **`PKG_ACCTPRECOMMIT.p_StatusPortFolio(PK)`** again → read `STATUS` (`InValid` + `MESSAGE` = the row says what is
   wrong); internal-topic rows without an account checked by the verify (the procedure does not);
6. Cross Account Config (owner `35000189.65`, `ACC_TYPE` literal) from `T_MAD_REVAL_ACCOUNTS` through the column map;
   Conf Instru Type (owner `35000292.65`) as the reference's; the A-11 rows ruled in;
7. verify: every `FK_*` resolves in the right table (no foreign keys), no duplicate on the natural keys, every
   identity value as expected; rollback by the PKs the run recorded.

**Global objects** (missing topics and standard historics, ADR 0018) take the **global `.65` PK**, not the
installation's fraction; their INSERTs are in the main proposal and rollback **and** in a separate
**`global_pk_rollback.sql`** that removes exactly them; the proposal's header says they are global, to review, and
that a `.65` PK created in PRE may clash with production's (the BOX team agrees the PK range before running).

Every INSERT is guarded by `NOT EXISTS` on its natural key (below). Still to settle before it is built: the delivery
form the BOX team wants (this PL/SQL, or a Liquibase changeset with PKs fixed per environment — the repo's data files
hard-code PKs and no branch configuration has been delivered that way), the topic mapping, `ACC_TYPE` per row.

## Skills and scripts it may call

None in phase 1 — the queries come from the catalogue, the matrix and the portfolio-properties report from their templates; new runs are versioned with
`scripts/new_run.py --area acc-configs`. Phase 2 adds its renderer script. (Labels are skill `set-up-book-labels`, run
by the FE configs agent, not by this one.)

## Hard rules

1. **Read-only on every database and every BOX repo** in phase 1; never write GBO, ever.
2. **Only branch-dependent rows are created** (screens 2, 3, 4, 10, 12, 13, 14) — **except missing topics and
   standard historics** (screens 6, 7), created as **global objects with the global `.65` PK**, each flagged
   *global — to review* in the matrix and the report, with the warning that a `.65` PK created in a lower environment
   (PRE) may clash with production's (ADR 0018). Conditions, event groups and events are verified, never created,
   never changed, never copied per branch `[ADR 0014]`.
3. **GBO → BOX topics by `CODE`** `[BOX ACC expert, 2026-10-27]`: a GBO topic is the BOX topic of the same `CODE`;
   none → created as a global topic with the GBO `CODE` (rule 2). Never a mapping by description, never a question.
4. **GL accounts are copied from GBO or absent — never derived**, never "the reference's account" for a branch whose
   own account exists in GBO.
5. **Keying per object from the metamodel** (group vs branch — table below); never by pattern.
6. **Copy only from evidence**: every created value names its source row (file:line).
7. **Privacy:** account / book / portfolio descriptions stay in the run folder; no developer IDs; **no portfolio,
   counterparty or entity names or values** extracted from GBO (counts only); US entity properties
   (`T_PGT_USAENTPROP_S`) never read.
8. **Owner + extension on every read** `[2026-10-14]`: a row is configuration only with the exact positive
   `FK_OWNER_OBJ` (and `FK_EXTENSION` for lists and arrays); the lists are extensions of the portfolio-property object;
   link-array tables are shared — never read by `FK_PARENT` alone.
9. **Negative owners are test / deleted rows** (operator): excluded and listed, never compared or copied.
10. **`COUNT(*)`, never `NUM_ROWS`**; an empty result in a table the pre-checks have not shown readable is not
    "missing".
11. **No hard-coded PK** in phase 2: `P_SETHEADER` / `F_GetPK`; every INSERT guarded by its natural key.
12. **Columns are mapped, never assumed** `[ADR 0014]`: GBO and BOX tables are similar, not identical. Before any
    GBO → BOX copy, both tables' columns are compared (A-P7); each BOX column is filled from a named GBO column, a
    fixed value, or the reference's pattern — anything else is asked; a GBO column with no BOX counterpart is reported.
13. **GBO portfolio properties: `Valid` only** `[ADR 0014]` — an `InValid` one gives no account and no scope.
14. **Internal-list topics get the internal account** (the reference's, `INTERNAL`) `[ADR 0014]` — never empty.
15. **Scope from configuration, never from a usage window** `[ADR 0015]`: no "configured but unused" question; the
    windowed usage queries (A-U0, A-U2, A-U2b, A-U3, A-U4, A-U4b, A-U6) are optional diagnostics, run only when the
    BOX team asks. **One GBO source per run**, asked once; every target GBO query runs there (`GBO`), every BOX query
    of the target in the target environment (`TGT`).
16. **The catalogue's text, as it is** `[operator, 2026-10-23]`: only the `&&` values substituted, each from the inputs
    file or a named CSV; never a column, table or schema the catalogue does not write (the first Tier 2 gap run
    invented a GBO schema from a branch code and columns that do not exist — CHANGELOG 2026-10-23). A query that
    fails, or a table the catalogue does not query: **A-P8** (its columns) first, then only the name the error gives
    is changed, and the matrix says so. A GBO schema comes from `target.gbo_schema` / `reference.gbo_schema` (the
    registry's `wrapper_owner`) — never built from the branch code.
17. **One system per query** `[operator, 2026-10-23]`: the operator's accounts are per system (GBO, BOX_ACC); a GBO vs
    BOX comparison is two extracts the agent joins (A-03b, A-10c, A-P7 when needed).
18. **Find before asking** `[operator, 2026-10-23]`: a PK met in a CSV is resolved with **A-L1** (branch, group,
    instrument…), never asked; a value on the reference's rows that is not its group / branch is another branch's row —
    reported, left out. A branch-condition value is **classified from evidence** (A-U1 g: the function's source, the
    group's branches, the family's size) before any scope question; only what stays unexplained is asked, with the
    evidence and a proposal, and the operator confirms the classification in one answer.

### Natural keys (the agent's, not the database's) `[2026-10-14]`

The database has no foreign key and only one business unique key (local properties); a re-run would duplicate rows.
The gap run checks for duplicates already present; phase 2 guards every INSERT with `NOT EXISTS` on:

| Table | Natural key |
|---|---|
| `T_BOX_CONF_LO_PROP_S` | `FK_BRANCH` (group) + `FK_INSTRUMENT` + `INIVALPCDATE` (also the database's unique key) |
| `T_BOX_LINK_ARRAY_X` | `FK_OWNER_OBJ` + `FK_EXTENSION` + `FK_PARENT` + `FK_BS` |
| `T_BOX_ACCT_PORT_PROP_S` | `FK_BRANCH` (group) + `FK_INSTRUMENT` + `INIVALPCDATE` + its condition values (`p_StatusPortFolio` rejects identical ones) |
| `T_BOX_ACCT_LIST_TOPIC_S` / `_LIST_COND_S` | `FK_PARENT` + `FK_EXTENSION` + `FK_TOPIC` / `FK_CONDITION` (created by `f_GenTopicCond`, which inserts only missing rows) |
| `T_BOX_CROSS_ACCTCONF_S` | `FK_BRANCH` + `FK_INSTRUMENT` + `FK_CURRENCY` + `FK_ENTITY` + `FK_TOPIC` + `ACC_TYPE` |
| `T_BOX_CONF_INSTRUM_TYPE_S` | `FK_BRANCH` + `FK_INSTRUMENT` + `CODE` + `TYPE` (the reference's columns, A-12) |
| `T_BOX_ACCT_GLTA_S` | `CODE` (unique in practice? A-10b shows duplicates; `FK_BRANCHGROUP` may be part of it) |

## Human checkpoints

| # | What | Who |
|---|---|---|
| 1 | The target's branch group (A-G1): an existing group shared with a BOX branch changes screens 2 and 4 | operator |
| 2 | The gap matrix and the portfolio-properties report | BOX team |
| 3 | ~~Event groupings: global or branch copy~~ — global, always `[ADR 0014]` | — |
| 4 | ~~The GBO → BOX topic mapping~~ — by `CODE` (ADR 0018); the global objects to create (topics, standard historics) reviewed before any SQL | BOX team |

## Relationship with other agents

- **`sigom-box-fe-configs-agent`** — labels (step 0) and the FE screens; untouched by this agent.
- **[`box-acc-jobs-agent`](../box-acc-jobs-agent/AGENT.md)** (built 2026-10-21) — ACC jobs and MBJ rows; its MBJ rows
  use the **global** event groups (no branch copy, ADR 0014: its `mbj.group_map` stays empty). The other charters now
  name it as the MBJ rows' owner (ADR 0011).

## The facts this design rests on

### Keying — branch group or branch, per object

> ### ⛔ Corrected 2026-09-21 — "ACC is group-keyed" is wrong as a blanket statement
>
> `[confirmed: DB]` **Two objects are group-keyed; twelve are branch-keyed.** The metamodel declares it
> per field:
>
> | Object | Field | Target |
> |---|---|---|
> | **`BOX - Acct Port Property`** (portfolio properties) | `pBranch` | **`T_PGT_BRANCH_GROUP_S`** |
> | **`BOX - Config LOC Property`** (local properties) | `pBranch` | **`T_PGT_BRANCH_GROUP_S`** |
> | `BOX - GLTA Local Dep` | `pLocalGroup` | `T_PGT_BRANCH_GROUP_S` |
> | Acct Movements, Acct Key, Documents, MBJ Properties, Acct Key Group, Cross Acc Config, Grouped Mov Config, Grouped Movements, Conf Instru Type, Net Contract, Net CCS PlanBS, Conf Acc By StdHist | `pBranch` | `T_PGT_BRANCH_S` |
>
> **The field is named `pBranch` in both cases.** For a branch the two values are its group's
> `FK_LOCALGROUP` and its own `BRANCH_PK` (both in the branch's inputs file) — both valid PKs, and writing the wrong one fails silently.
>
> **This agent must resolve the keying per object from Q-G7, never by pattern.** The earlier blanket
> reading was built from the portfolio-properties evidence alone and generalised; the generalisation is
> the kind of mistake that has cost this project five defects.
>
> It also promotes a checklist item to a prerequisite: the orchestrator's Phase 0 branch-group
> resolution is **load-bearing for ACC**, not a nice-to-have.


### ⛔ The topic/condition lists are **generated by a procedure** — this changes the walk's shape

`[confirmed: source via Devin, 2026-09-21]` **`PKG_ACCTPROP.f_GenTopicCond(PK, MSG)`** takes a
portfolio-properties PK, reads that row's `FK_INSTRUMENT` / `FK_BRANCH` / `INIVALPCDATE`, finds the
matching local config (`T_BOX_CONF_LO_PROP_S`, keyed by instrument + branch, latest `INIVALPCDATE`),
then **loops that config's global / internal / local topic and condition arrays and inserts any missing
rows into `T_BOX_ACCT_LIST_TOPIC_S` and `T_BOX_ACCT_LIST_COND_S`**, tied to the portfolio PK. It then
calls `p_ClearList` to remove de-registered rows and `PKG_ACCTPRECOMMIT.p_StatusPortFolio` to
re-validate.

**So the ACC walk is not "insert the junction rows".** It is:

1. Configure `T_BOX_CONF_LO_PROP_S` with its topic arrays.
2. Insert the portfolio property (`T_BOX_ACCT_PORT_PROP_S`).
3. **Call `f_GenTopicCond`** — it materialises the lists, clears stale rows, and re-validates.

`[read: code, 2026-10-14]` The mapping (r0.0.8): global topics `35003724.65` → list `35001510.65`; local
`35001814.65` → `35001513.65`; internal `35003725.65` → `35001518.65`; conditions `35001818.65` → `35001514.65`. The
local property is the one with the same instrument and group and the latest `INIVALPCDATE` ≤ the portfolio
property's. `FK_GLTA` is **never set** — the account is filled afterwards. ⚠️ In older versions (r0.0.3, r0.0.5)
global and internal topics came from the **instrument-level** configuration: pre-check A-P6 reads the deployed
version. Details: [`box-acc-model.md`](../../docs/reference/box-acc-model.md) §4.

An agent that hand-inserts `T_BOX_ACCT_LIST_TOPIC_S` rows is duplicating a generator and will fight
`p_ClearList`. The junction is **derived output**, and the *configuration* input is the local-properties
topic arrays.

This closes a loop with the metamodel: `BOX - Config LOC Property` declares **`apLocalTopicArray`,
`apGlobalTopicArray`, `apInternalTopicArray`** → `T_BOX_ACCT_TOPICS_S` — precisely the three arrays
`f_GenTopicCond` walks. Two independent readings of the same mechanism, agreeing.

### Two structural facts to build around

**`T_BOX_LINK_ARRAY_X` is shared, not per-object.** Nine ACC objects and 17 relationships live in that
one bridge, discriminated by `(FK_OWNER_OBJ, FK_EXTENSION)`. `Config LOC Property` alone puts four
arrays in it, three targeting the same table. **Never query it on `FK_PARENT` alone.** Full table in
[`sigom-metamodel.md`](../../docs/reference/sigom-metamodel.md) §4.

**Three ACC objects store into shared `PGT_SYS.PGT_DOMAINS`** (Acct Indicator, GLTA Type, Param Fixed),
so those enumerations are global and identical in every environment — and any query against them needs
`FK_OWNER_OBJ`, or it reads across every enumeration in the system.

## The GBO → BOX Topics mapping tool `[stated: BOX Lead, 2026-09-10]`

**A tool already exists that maps GBO topics to BOX topics.** It was raised in the first branch's scoping
meeting as something the project should use rather than work around
(`../../docs/examples/ny-sch-branch-onboarding.md` W2).

This changes this agent's design before it is written, so it is recorded now rather than discovered
later:

**Topic mapping is not this agent's mining problem.** The working assumption had been that topics, like
every other ACC object, would be mined from GBO and proposed. If a sanctioned mapping already exists,
then re-deriving one is not thoroughness — it is a second, competing answer to a question that has an
owner. The agent's job for topics becomes *apply the tool's output, verify it, and flag disagreements*,
which is a materially smaller and safer job than deriving the mapping.

**It does not extend to GL accounts.** Topics and GL accounts are different objects
(`T_BOX_ACCT_TOPICS_S` vs `T_BOX_ACCT_GLTA_S`), and the never-invent rule on GL accounts is untouched by
this. A tool that maps topics confidently says nothing about account values; do not let the existence of
one create an expectation that the other can be automated too.

**`[2026-10-27]` Settled — by `CODE`** (BOX ACC expert, ADR 0018): a GBO topic maps to the BOX topic with the same
`CODE`; a GBO topic with no BOX twin is created as a global topic. The tool, if it exists, is no longer needed. The
history below is kept.

**Unknown, and blocking any use of it:** what the tool actually *is* — a repo, a running service, a
spreadsheet, a one-off script someone holds — who owns it, and whether it is callable by an agent at all.
Identify it before planning around it. `[open-question]` `[2026-10-07]` The operator has been told by a BOX dev
it exists, not seen it yet — checkpoint 4. It blocks the **accounts of Portfolio Properties** (screen 4) and the
topic column of **Cross Account Config** (screen 3), nothing else.

## Inherited rules

This agent inherits the FE charter's hard rules verbatim — never fabricate a literal, a
PK, or DDL; derivation allowed only when labelled `DERIVED` with its rule stated and its own sign-off;
never write GBO; never copy across branches on shape similarity; never target production first.

With one rule **strengthened**: the `DERIVED` allowance does **not** extend to GL accounts. There is
no version of a reasoned-to GL account that is acceptable.

**Hard rules 9 and 10 apply here from day one** `[confirmed: DB, 2026-09-21]`, which is the point of
having read the metamodel before writing this agent:

- **Rule 9 — identity columns.** `FK_OWNER_OBJ` / `FK_EXTENSION` are properties of the destination
  object, derived from `GOM_GLB_SYS`, never carried across from a source row. ACC spans many objects,
  so there is no single constant.
- **Rule 10 — pre-commit procedures.** **Three of the four most consequential ACC objects declare one**,
  and one of them is GL accounts:

  | Object | Procedure |
  |---|---|
  | `BOX - Acct Port Property` | `PKG_ACCTPRECOMMIT.p_StatusPortFolio` |
  | `BOX - Acct Topics` | `Pkg_AcctPrecommit.p_TopicsPrecommit` |
  | **`BOX - GLTA`** | `PKG_ACCTPRECOMMIT.p_AccountPrecommit` |
  | `BOX - Cond PortFolio` | `Pkg_SysPreCommit.p_ExistFuncPreCommit` |
  | `BOX - Documents`, `BOX - Grouped Movements` | `Pkg_AcctPreCommit.p_DocumentPreCommit` |
  | Acct Indicator / GLTA Type / Param Fixed | `Pkg_SysPrecommit.p_DomainsPreCommit` |

  So **a raw INSERT is not the whole operation for GL accounts** — the object where this repo's
  never-invent rule is most absolute. Read `PKG_ACCTPRECOMMIT` and `PKG_SYSPRECOMMIT` from
  `cib-boxfin-dbboxfe` before this agent emits a single statement; `ALL_SOURCE` shows package specs
  only, never bodies.

Across SIGOM, **857 objects in 172 packages** declare a pre-commit procedure. **Assume an object runs
code on save until you have checked that it does not.**

**`p_StatusPortFolio`'s InValid conditions and `p_AccountPrecommit`'s date-rule logic were read in full on
2026-10-14** ([`box-acc-model.md`](../../docs/reference/box-acc-model.md) §5): an account is one row (+ an optional date
rule); internal topics without an account are not flagged by the procedure.

**All three ACC bodies were read on 2026-09-21, and all three write only to their own row** — none has
the cross-table / committing problem the FE `p_check_Val_Curves_precommit` has. But each computes
columns the agent must therefore **not supply**:

| Procedure | Never supply |
|---|---|
| `p_StatusPortFolio` | `STATUS`, `MESSAGE` — it computes them. Insert, call, **then read `STATUS`**: `'InValid'` plus a message is the row telling you it is wrong. A built-in validation oracle, better than anything we would build |
| `p_AccountPrecommit` | `VALIDDATE`, `LOC_CODE`, `HOSTINTERFIND`, `PARENT_ACCOUNT` — denormalised onto the GLTA row from `T_BOX_ACCT_PARENT_DATE_S`. Also raises if the parent account's balance is non-zero |
| `p_TopicsPreCommit` | audit columns — `LSTMNTDATE`, `LSTMNTUSER` (from `f_getuseridsigom`), `LSTMNTSOURCE` |

⚠️ **Audit stamping uses three different mechanisms across ACC**, so no single pattern can be assumed:
`T_BOX_ACCT_PORT_PROP_S` gets it from a **trigger** (`G_T_BOX_ACCT_PORT_PROP_S_BIU`, `BEFORE INSERT OR
UPDATE FOR EACH ROW`), `T_BOX_ACCT_TOPICS_S` from its **pre-commit procedure**, and `T_BOX_ACCT_GLTA_S`
inside its procedure's own `UPDATE`. It is the only trigger on any FE or ACC configuration table; the
nine FE walk tables have none. `[confirmed: DDL via Devin, 2026-09-21]`

### Grants, by name

`[confirmed: deployment scripts, 2026-09-21]` **`BOX_ACC_RD`** (`SELECT`/`EXECUTE`) and **`BOX_ACC_WR`**
(full DML, `EXECUTE` on packages, `SELECT` on sequences such as `S_BOX_ACCT_KEY`). Ask for those by
name rather than for "BOX_ACC access". No `CREATE ROLE` exists in the repo — the roles pre-exist.

## Queries

[`docs/reference/queries/acc-config-mining.md`](../../docs/reference/queries/acc-config-mining.md) — its own IDs
(`A-…`), the SIGOM trace of each screen (GBO and BOX side) with filters added.
[`sigom-metamodel.md`](../../docs/reference/sigom-metamodel.md) §11 holds the module-agnostic metamodel queries (A-G2).

## Eval cases

[`evals/cases/sigom-box-acc-configs-agent.md`](../../evals/cases/sigom-box-acc-configs-agent.md).

## Open questions (about the agent — a branch's questions are in its open items, e.g. `runs/<BRANCH>/<env>/jobs/99-open-items.md`)

`[2026-10-14]` Closed: the PK rule (`F_GetPK`, §6 of the model), the list ↔ array mapping, the identity values, the
`ACC_TYPE` values, the triggers, the A-11 objects (ruled, two candidates asked).

1. ~~The GBO → BOX topic mapping~~ — by `CODE` (ADR 0018).
2. How the BOX team wants a branch's ACC config delivered: a PL/SQL script calling SIGOM's routines, or a Liquibase
   changeset (PKs fixed per environment).
3. Cross Account Config from `T_MAD_REVAL_ACCOUNTS`: its full column list, whether `TIPO` is BOX's `ACC_TYPE`, where
   BOX's currency / entity / topic come from (A-P7, A-03b); the BOX route of GBO's own `T_PGT_CROSS_ACCTCONF_S` rows.
4. ~~Internal topics without an account~~ — the internal account, always (ADR 0014).
5. ~~Net CCS PlanBS per branch~~ — screen 13 (2026-10-26); ~~GBO's ConcMis reconciliation and a branch's own GBO topic
   tables in BOX~~ — out, nothing to do (BOX ACC expert, 2026-10-27).
6. Whether an account's `CODE` is unique per installation or per `CODE` + `FK_BRANCHGROUP` (A-10b).
7. The package versions deployed per environment (A-P6); `SPK_T_BOX_CONF_LO_PROP_S` exists in PRE-PROD but not in
   the repo — present in the target (A-P5)?
8. The target environment per branch and `BOX_ACC` read access there.
9. The portfolio properties' own start date (≥ 01/01/1900 — the expert fixed the local properties' only).
