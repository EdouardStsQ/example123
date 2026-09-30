# BOX batch — the chain from a Control-M job to a posted entry

How a BOX FE / BOX ACC batch job gets from the scheduler to the accounting entries it posts, level by
level, with the key that joins each level to the next. Branch-agnostic: it holds the **mechanism**.
Values for one branch or one environment live in a run folder
(`runs/<BRANCH>/<env>/jobs/02-environment-profile.md`), never here.

Used by [`box-batch-jobs-agent`](../../../agents/box-batch-jobs-agent/AGENT.md). The queries named `J-…`
are in [`../queries/box-jobs-queries.md`](../queries/box-jobs-queries.md). The worked example is
[`../../examples/gmbx3es02d07-trace.md`](../../examples/gmbx3es02d07-trace.md).

**Neighbouring layer docs** (read them, do not duplicate them):

| Doc | What it adds |
|---|---|
| `box-fe-acc-batch-runtime.md` (Devin's; **not in this scaffold**, see [README](README.md)) | Control-M topology: job families, subapplications, FE→ACC completion events |
| [`fe-batch-event-groups.md`](fe-batch-event-groups.md) | The FE event groups in order (`2628.65` … `2389.65`) `[stated: team page]` |
| [`../../process/04-add-book-procedure.md`](../../process/04-add-book-procedure.md) Part 2 | The team's runbook for adding a book: meshes, job names, `db.conf` block, Unix scripts, label config, MIS book `[stated: team runbook]` |
| [`control-m-batch-layer.md`](control-m-batch-layer.md) | The Data-Lake feed jobs — **out of scope** for this chain |

Evidence tags: `[confirmed: …]` (a query result or a file:line), `[stated: …]` (a person), `[inferred]`
(reasoning — never used as a fact), `[open-question]`.

---

## 1. The chain in one picture

```
L1 SCHEDULE  Control-M job  (JSON folder repo)        when it runs, what it waits for / releases
   │  job name = db.conf step name
L2 STEP      db.conf line   (Unix app tree, per env)  entry point + arguments (group, branch, date,
   │  1st argument = group PK                          instrument, mode, label, sub-label)
L3 GROUP     T_PGT_BR_EVE_S  →  T_PGT_BR_EVE_EXT_S   the group's events, in ORDERTOEXECUTE order
   │  EVENTCODE = T_PGT_EVE_S.PK
L4 EVENT     T_PGT_EVE_S + T_PGT_TABLE_S / _COND_S / _COLS_S   the query that selects the deals
   │  FK_PARENT = event PK
L5 ENTRIES   T_PGT_UPDATE_S   calculation rows, then debit/credit posting rows
   │  TXFUNCNAME = <schema>.<package>.<procedure>
L6 CODE      package source (repo, or ALL_SOURCE in the env)
```

Beside the chain, per job: **`BOX_ACC.T_BOX_MBJ_PROPERTIES_S`** binds a `JOB_NAME` to (branch,
instrument, label, sub-label, group) plus parallelism settings (`Workers`, `Task_per_worker`,
`Concurrence`) `[confirmed: DB extract, 2026-09-16 — box-data-model.md]`. **Who reads it is still
`[open-question]`** — see §7.

## 2. Level by level

### L1 — Schedule (Control-M)

- One repo per Control-M folder (Tier 1 Madrid: `cib-boxfin-t1mdesfe`, `cib-boxacc-t1mdesac`,
  `cib-boxacc-t1mdacccheck`, `cib-boxfin-t1mdalmfields`, `cib-boxfin-mdfinancialcheck` — see
  [`../repo-index.md`](../repo-index.md)). File `projects/*.json`, Control-M Automation API format.
  `[confirmed: repository configuration via Devin, 2026-09-29]`
- Each job is `Type: Job:Script`, `FileName` = the job name, `FilePath: /appl/gm/scripts`, `Arguments:
  ["%%$ODATE"]`. Order between jobs: `eventsToWaitFor` (`<JOB>-OK`) and `eventsToAdd` (emits
  `<JOB>-OK`); these cross folders (FE ↔ ACC). Timing: `When` (calendar, `FromTime`, days).
  `[confirmed: cib-boxfin-t1mdesfe.json:7-20, 107-120]`
- **Per-book meshes** also exist (`JACD-T1MD<ABBREV>-BOXFE-…` / `-BOXAC-…`) next to the core folders,
  and adding a book edits in-conditions of existing check jobs. `[stated: team runbook, 04-add-book §2.1-2.2]`

### L2 — Step (`db.conf`)

- Lives in the Unix app tree, **one per environment**. **The link with Control-M is the job name**.
  `[stated: operator, 2026-09-29]`
- Line format `<JOB>:<type>:<flag>:<PL/SQL call>;` — `T:F` is unexplained. `[open-question]`
- `GMBX*` = BOX jobs, `GMGB*` = GBO jobs. `[stated: operator, 2026-09-29]` **Only `GMBX*` is in scope.**
- The Unix script `/appl/gm/scripts/<JOB>` is copied from a template (`templates/db_job`) and jobs are
  registered with `add_new_jobs.ksh` / `delete_jobsBX.ksh`. `[stated: team runbook, 04-add-book §2.3]`
- **Entry points** live in the environment's **wrapper** `<wrapper owner>.PKG_GMBATCHPROCESS`:
  `f_executegroup`, `f_executegroupcontaswap`, `f_executegroupcontacap`, `pgeneraeventosautomatic`, and
  others (§5). `[confirmed: ALL_SOURCE spec, Tier 1 and Tier 2]`
- `f_ExecuteGroup` arguments **in Tier 1**: `P_GROUP, P_BRANCH (VARCHAR2), P_DATE, P_INSTRUMENT
  (VARCHAR2), P_VSTATIC (default 0), P_LABEL, P_SUBLABEL` — label and sub-label added in 2019.
  `[confirmed: PGT_ES spec lines 1535-1542]` **Not the same in every environment** — see §5.
- Arguments are usually wrapper constants: `CST_PK_BRANC_<x>` / `cst_pk_bra_<x>` (branch PKs),
  `CST_PK_<product>` (instrument PKs, e.g. `CST_PK_SWAP = 20092.4`), `CST_PK_DINAMIC = 0` /
  `CST_PK_STATIC = 1` (mode), and group constants by function (`CONT` accounting, `CIE` closing,
  `MTM`, `RECLA`, `FICH` / `DIURNO` / `EXT` files, `FINAC`, `ALERT`, `EXPORT`). The book is passed by
  **code** through `BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('<label code>')`, so the line is the same in
  every environment. `[confirmed: db.conf line + spec]`
- **Job name convention** `GMBX<n>ES<label>D<nn>`: `<n>` = the instrument's local number (`0` generic,
  `1` depos, `3` IRS), `ES<label>` = the book's label number, `D<nn>` = the step. `[stated: team
  runbook]` — consistent with `GMBX3ES02D07` passing `CST_PK_SWAP` and label `XES02`.
  **The `ES<nn>` part is the book's label code without its leading `X`**: the NY equivalent of
  `GMBX3ES02D07` (book `XES02`) is **`GMBX3NY02D07`** (book `XNY02`) `[stated: operator, 2026-09-30]`.
  Labels follow `X<country code><nn>` (04-add-book §2.4), so a branch's job names follow from its labels.

### L3 — Group → events

- Header `PGT_PRC.T_PGT_BR_EVE_S` (`PK`, `GROUPDESCRIP`). Members `PGT_PRC.T_PGT_BR_EVE_EXT_S`
  (`FK_PARENT` = group, `EVENTCODE`, `ORDERTOEXECUTE`), keyed by the metamodel identity
  `FK_OWNER_OBJ` / `FK_EXTENSION` (Tier 1: `12709.4` / `39007.4`). **Derive the identity per
  environment** (like FE Q-G7); J-C2 works without it and must return no stray rows.
  `[confirmed: DB Tier 1 and Tier 2, 2026-09-29]`
- Events run in `ORDERTOEXECUTE` order. `[confirmed: DB]` An event whose `FK_INSTRUMENT` is NULL is
  generic (e.g. `4117.65` "BOX Generic Accounting document", order 0); whether the engine skips events
  of another instrument is not read from code. `[inferred]`
- **Catalog schema is `PGT_PRC` in both tiers, and the BOX catalog is deployed to Tier 2 even where no
  BOX job runs**: 51 `BOX%` groups in Tier 2 with the same `.65` PKs; group `2735.65` identical in both
  tiers (7 events, same order, same update-row counts). `[confirmed: DB Tier 2, 2026-09-29]`

### L4 — Event = a query

- `T_PGT_TABLE_S` = the FROM (aliases → tables), `T_PGT_COND_S` = the WHERE, `T_PGT_COLS_S` = the
  SELECT (`ALIAS_COL` → column expression). Bind placeholders substituted from the entry point's
  arguments: `#BRANCH#`, `#LABEL#`, `#EV_DATE#`, `#INSTRUMENT#`. `[confirmed: 001-data_eventsheader_360865.sql:288-345,
  cib-boxacc-dbboxacc, via Devin]`
- **ACC events read BOX FE tables** (e.g. 3608.65 reads `BOX_FE.T_BOX_IRDATADEAL_S` and
  `BOX_FE.T_BOX_IRFINANCST_S`, loan and borrow legs), and require `FK_ACCTDOC IS NOT NULL`. So **FE
  configuration and FE batch must be in place before ACC jobs process anything.** `[confirmed: same file]`
- Branch and instrument arguments are `VARCHAR2`, consistent with text substitution into the query.
  `[inferred]`

### L5 — Entries (`T_PGT_UPDATE_S`)

- Two kinds of row per event:
  - **Calculation** rows (`MC_UPDATETYPE = 'U'`, alias columns empty), e.g. `p_GetGroupNo`,
    `p_GetNominalSWAPAccount`: they fill working fields (alias columns seeded `'0.00'`).
  - **Posting** rows (`p_Put_Mov`, `p_Put_Nivelacion`): `ACCT_AL_COL` (account), `CCY_AL_COL`,
    `DREG_AL_COL`, `VAL_AL_COL` / `VAL_CCY_AL_COL` (amount), `MC_DRCR`.
- **Run order: all calculation rows first, then all posting rows**; `ORDERTOEXEC` orders rows only
  within each set. `[confirmed: pkg_batchprocess_mbj_body.sql:1037-1043, cib-boxacc-dbboxacc r0.0.36]`
- **`MC_DRCR`: 1 = debit, 0 = credit.** `[confirmed: 000-pkg_acctgeneral_body.sql:284-290, 411-456, r0.0.38]`
  Postings come in balanced pairs (account and its counterpart). Devin's first reading (0 = debit) was
  wrong; the code settled it.
- So "what does this event do" is answered as **entries**: which deals (L4), what is calculated, and
  which account is debited / credited with which amount — not as a list of procedure names.

### L6 — Code

- BOX packages are in `cib-boxfin-dbboxfe` (BOX_FE) and `cib-boxacc-dbboxacc` (BOX_ACC), both
  **read-only**. Liquibase layout `src/main/resources/code/<NN>-<SCHEMA>/r<ver>/…`; every file is
  `CREATE OR REPLACE`, so **the highest `r` folder containing an object is its latest committed
  version**. `[confirmed: via Devin, 2026-09-29]`
- **Committed ≠ deployed.** The parent changelog activates only some releases; what runs in an
  environment is `ALL_SOURCE` there. Always say which one is cited. `[confirmed: changelog.yaml:1-4, 166-172]`
- The wrapper (`PKG_GMBATCHPROCESS`) is in **no repo**: read its spec from `ALL_SOURCE`; its body is not
  visible to the read-only account (`PACKAGE` rows only). `[confirmed: DB, both tiers]`

## 3. Where each layer lives, per environment

| Layer | Tier 1 | Tier 2 | Evidence |
|---|---|---|---|
| Wrapper `PKG_GMBATCHPROCESS` | `PGT_ES` | **`PGT_NY`**, `PGT_BOS` (Boston), `PGT_CO` (Colombia) — one per regional instance | `[confirmed: DB]`, `[stated: operator]` |
| Engine core `PKG_BATCHPROCESS` | `PGT_PRG` (to confirm in Tier 1) | `PGT_PRG`, `PGT_STL` | `[confirmed: DB Tier 2]` |
| Catalog | `PGT_PRC` | `PGT_PRC` | `[confirmed: DB]` |
| Label lookup `PKG_BOXUTILITY` | `BOX_SYS`, `BOX_FE` (VALID) | `BOX_SYS`, `BOX_FE` (VALID) | `[confirmed: DB]` |
| `db.conf` | Unix app tree | Unix app tree | `[stated: operator]` |
| Control-M folders | `t1m*` / `md*` repos | **unknown** | `[open-question]` |

**The wrapper differs between environments.** Tier 2's `PGT_NY.f_executegroup` has **5** arguments —
no `P_LABEL` / `P_SUBLABEL` — and no overload with them. `[confirmed: PGT_NY spec lines 620-626 and a
`P_LABEL` search, 2026-09-29]` Tier 2's constants also differ (US branches `cst_pk_bra_nysch = 20007.4`,
`nyibf`, `miami`, `scusa`; its own group PKs). **A Tier 1 `db.conf` line cannot be copied to Tier 2.**

**PK fractions tell where a row was created**: `.65` BOX catalog, `.21` Madrid, `.4` shared master
data; in Tier 2 `.35` = built on the old NY server, `.44` = Tier 2's own auth code. `[stated: GBO
expert via operator, 2026-09-29]`

## 4. What running one (branch, instrument, book) needs

A BOX batch job runs per **branch × instrument × book**. For one such cell to run, every row below must
hold. This is the checklist the gap analysis walks.

| # | Needed | Where | Owner of the change | Source |
|---|---|---|---|---|
| 1 | FE configuration for the branch, incl. the book registered for the instrument (Book tab) | `BOX_FE` (`T_BOX_ENGCONF_*`, `T_BOX_CONF_BY_BOOK_S`) | `sigom-box-fe-configs-agent` | FE charter; 04-add-book §2.5 |
| 2 | The book's **BOX** label exists: code `X<CC><nn>`, description exactly the data-lake book label, fixed PK | `PGT_SYS.PGT_DOMAINS`, `FK_OWNER_OBJ = 17910.4` (Label Config screen) | BOX FE team, via skill [`set-up-book-labels`](../../../skills/set-up-book-labels/SKILL.md) | 04-add-book §2.4 |
| 3 | The groups the jobs call exist in the catalog | `PGT_PRC` | BOX team (repo DML) | §2 L3 |
| 4 | The wrapper knows the branch (a constant, or a literal PK) and can receive the book | `<wrapper owner>.PKG_GMBATCHPROCESS` | the wrapper's owner — **code change** | §3; 04-add-book §2.3 |
| 5 | One `db.conf` line per job | Unix app tree | BOX team | 04-add-book §2.3 |
| 6 | One Unix script per job, registered | `/appl/gm/scripts` | BOX team | 04-add-book §2.3 |
| 7 | The Control-M jobs, chained (`-OK` events), and the in-conditions added to the check jobs | Control-M folder repos | BOX team / scheduling | 04-add-book §2.1-2.2 |
| 8 | MBJ properties row per job (if the runtime reads it) | `BOX_ACC.T_BOX_MBJ_PROPERTIES_S` | `sigom-box-acc-configs-agent` scope | box-data-model.md |

## 5. Wrapper entry points seen

| Entry point | Tier 1 `PGT_ES` | Tier 2 `PGT_NY` |
|---|---|---|
| `f_executegroup` | 7 args (with label, sub-label) | **5 args** |
| `f_executegroupcontaswap`, `f_executegroupcontacap` | 7 args | 5 args |
| `pgeneraeventosautomatic(branch, create, instrument, events, refdate)` | — (not seen) | ✓ |
| `p_borrarlog`, `ptratapoolcolaterales`, `pglobalizaentity`, `p_ejecutarpositioncontrol`, `f_positioncontrol`, `f_executepositioncontrol`, `f_checkprices` | not listed yet | ✓ |
| `Pkg_Locbatchdepend.f_GenMainDay(company, date)` (other package) | seen in `db.conf` | not checked |

## 6. Corrections recorded

| Was said | Is | Evidence |
|---|---|---|
| 3609.65 is "SWAP revaluation" (Devin, from column names) | "BOX SWAP Interest Adjust Local Anti Natura (No Reval No BM)" | `T_PGT_EVE_S.NAME`, Tier 1 |
| `MC_DRCR` 0 = debit (Devin, from data) | 1 = debit, 0 = credit | `p_Put_Mov` code |
| `f_ExecuteGroup`'s 4th argument is the company (Devin's 2nd answer) | the instrument (`P_INSTRUMENT`) | wrapper spec |
| 2735.65 = "Accounting General Local wFE No Reval-BM" ([acc-add-product-checklist](../../process/checklists/acc-add-product-checklist.md) §4) | "BOX SWAP - Accounting General by Book" | `T_PGT_BR_EVE_S`, both tiers |
| "`T_MBJ_PROPERTIES_S` is not read by any code" (Devin; `ALL_SOURCE` search returned 0 rows) | **Not proven.** Both searches used `T_MBJ_PROPERTIES`, which cannot match `T_BOX_MBJ_PROPERTIES_S` | J-E6 re-runs it |

Rule taken from the first two rows: **meanings come from names in the database and behaviour from
code, never from column names or data patterns.**

## 7. Open questions

1. **How does the book reach the engine in an environment whose wrapper has no label argument?**
   Candidates: the wrapper needs Tier 1's upgrade; a BOX-owned wrapper is used; or the label arrives
   another way (e.g. `T_BOX_MBJ_PROPERTIES_S`, which has `pLabel`). **For the BOX Lead.**
2. Who reads `T_BOX_MBJ_PROPERTIES_S` — the Unix runner, the engine, or both (J-E6, J-E8)?
3. Which engine core version runs in each environment (`PGT_PRG` / `PGT_STL` vs the repo's r0.0.38)?
4. `db.conf` `<type>:<flag>` (`T:F`) meaning.
5. The Tier 2 Control-M folder repos, and the Tier 2 job-name token (Tier 1 uses `ES`).
6. Whether the engine skips events of another instrument (needs the wrapper or core body).
