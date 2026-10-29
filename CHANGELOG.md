### 2026-10-29 (3) — BOX ACC configs: what NY's first DEV run taught (ADR 0023)

`[operator, 2026-10-29]` NY_SCH's gap run `gap_20261029_1` (DGBOUS, GBO source PRE PARALELO, Devin's PR #111) and its
SQL step to the precheck, reviewed run by run ([ADR 0023](docs/decisions/0023-acc-configs-lessons-of-the-first-dev-run.md)).
Nothing of ADR 0020 / 0022 reversed.

- **Rules** (charter hard rules 21–24, checkpoint 2b, screens 4 / 10 / 13): duplicates only when every condition
  value and topic → account row are identical — a rule keeping one ("keep the `.44`") is a proposal, asked; a proposal
  is never written as a decision; a kept condition value with no BOX value, or a list account no source has → the
  property **OPEN**, not carried; every property counted once (create + held only + OPEN only + held and OPEN); screen
  10 creates only the accounts the carried configuration uses (lists ∪ Cross Account Config ∪ Net CCS), the Net CCS
  ones from the reference's BOX rows; columns BOX sets itself never supplied; every table in its schema; a finding
  names its GBO source; **continuing a run** after a repo update (no CSV asked again unless its query changed).
- **Catalogue** (`acc-config-mining.md`): rule 4 and *Where each table lives* — `PGT_NY.T_PGT_ACCT_PORT_PROP_S`,
  `PGT_SYS.T_MAD_REVAL_ACCOUNTS`, `PGT_ACT.T_PGT_TOPICS_S` do not exist (asked by the run); the grants seen (DGBOUS:
  `BOX_ACC` cannot read `PGT_STC.T_PGT_BRANCH_GROUP_S`); A-G1 / A-L1 in the GBO account; A-P2 and A-P7 owners (A-P7's
  pair table: `T_MAD_REVAL_ACCOUNTS` in `&&TARGET_GBO_SCHEMA`, never `PGT_SYS`; computed columns); A-P5 read per
  fraction, (d) before any finding; A-02c / A-04c written for the target without the group table; A-04i (b) (by topic
  `CODE`, rows without an account) and the GBO-source dependence; A-04h from `NOM_FUNC`, before a pair is proposed;
  the condition-value rule (A-01); duplicates (§4); which accounts (§10); A-10a with the type / direction codes; new
  **A-10e** (BOX's type / direction values); Net CCS accounts and `FFM` (§13).
- **`scripts/render_acc_sql.py`**: the precheck no longer reads `PGT_STC.T_PGT_BRANCH_GROUP_S` (ORA-00942 at line 92
  in DGBOUS) — the group is proved by its branch (`FK_LOCALGROUP`). Tests: that check, and `_not_carried` ignored (27
  pass). Already sent alone as `fix-precheck-group.zip`.
- **Kickoffs**: `tier2-gap-run.md` (continue a run; schemas checked before a query is handed over; A-P5 (d); A-04h
  first; A-10a codes, A-10e; duplicates, OPEN, counts, accounts, computed columns; *Decisions* vs proposals);
  `tier2-sql.md` (Step 2: clash mode (a) with no choice is not a stop; continue in the run's folder; `_not_carried`;
  accounts' sources). **Templates**: matrix (count line, A-P5, expert rulings only, computed columns, duplicates
  column, decisions vs questions), report (held / OPEN counted once, OPEN status, duplicates evidence, section 6
  questions), values (`_not_carried`, account sources, computed columns). Eval case: the run's guard rails.
- **NY facts**: `box-acc-model.md` §9.8 (DGBOUS, scope, the 18-pair condition map, 8 clash groups / 38 properties, no
  duplicate, the counts, accounts, Net CCS, label source) and §9.7 / §9.4 / §10 notes; open item **4zz** (the BOX
  expert's questions) and 4zb, 4ze, 4zw, 4zx, 4zy updated; NY's acc-configs README; ADR 0020 / 0022 cross-references;
  `runs/README.md` (continuing a run).

### 2026-10-29 (2) — ADR 0020 point 6: the NY multi-account cases depend on the GBO source

- `[operator, 2026-10-29]` The 14 cases recorded on 2026-10-28 (OTC `2485.35` / `2487.35`) came from GBO **PRE**; in GBO
  **PRE PARALELO** (NY's gap run `gap_20261029_1`) A-04i returns **0 cases**, and a direct check of both properties
  (rows per topic `CODE`, rows without an account counted) returns none either. ADR 0020 point 6 and the NY inputs
  comment say so; A-04i stays a per-run query against the run's own GBO source. No rule changed.

### 2026-10-29 — ACC configs SQL step: date rules and built-in owners (fix before the first DEV run)

- **`render_acc_sql.py`**: an account's date rule (`T_BOX_ACCT_PARENT_DATE_S`) is an **extension of the account
  object** (box-acc-model.md §2): now inserted with the account's owner `35000169.65`, `FK_EXTENSION` `35001497.65`
  (`amDateDep`) and `FK_PARENT` = the account — it was rendered as a base row with an owner asked for. Topics
  (`35000179.65`) and standard historics (`35000180.65`) owners built in (A-P2 still checks them per environment).
  Test and values template updated.

### 2026-10-28 (4) — ACC configs phase 2: the SQL step (ADR 0022)

`[operator, 2026-10-28]` ([ADR 0022](docs/decisions/0022-acc-configs-sql-step.md)) — "as the FE configs agent", first
run in DEV (DGBOUS).

- **`scripts/render_acc_sql.py`**: the agent writes `03-sql/acc-values.json` (every value with its source), the
  script renders: `--precheck` (read-only: auth code, group / branch, the routines' signatures in `ALL_ARGUMENTS`,
  each sequence ahead of its fraction, NOT NULL columns supplied, columns exist, topics / accounts / conditions
  present, the `.65` range free) → rehearsal (ROLLBACK) / config (COMMIT only with no problem) / verify, refused until
  the precheck's saved output says `ACC PRECHECK OK` for the same values → `--rollback` from the config's output
  (exactly its `CREATED|` rows, children first) + `global_pk_rollback.sql` (only `.65`). Rows made as SIGOM does:
  topics → `p_TopicsPreCommit`; account + date rule → `p_AccountPrecommit`; local property + its four arrays; portfolio
  property → `f_GenTopicCond` → accounts → condition values → `p_StatusPortFolio` → `STATUS` Valid (unless
  `expect_invalid`, clash mode b); cross account config, conf instrument type, net CCS plan by natural key.
- **PKs**: the table's sequence + the installation's fraction (as the MBJ rows). **Global objects `.65`**: a Tier 2
  session can write a `.65` PK but nothing allocates one there (BOX's functions append `.44`) — the number part from
  `global_pk.<table>.start` (the BOX team's range) or `next-free` (DEV only).
- Refusals: open / masked / unsourced values, a condition or topic the local property lacks, a missing condition value
  or account, a clash, reserved / computed columns, a table outside the supported ones.
- Charter (status, phase 2 section and design list, scripts, hard rule 11, open question 2 closed), kickoff
  `prompts/tier2-sql.md`, template `acc-values.example.json`, model §6, eval case, NY inputs (`decisions.delivery`,
  `decisions.global_pk`), scripts README. Tests `scripts/tests/test_render_acc_sql.py` (26). Not run against Oracle
  here: the precheck is the first contact.

### 2026-10-28 (3) — DB relay (proposed, ADR 0021): agents' read-only queries through the operator's PC

`[operator, 2026-10-28]` ([ADR 0021](docs/decisions/0021-db-relay-read-only-queries.md), **proposed** — no agent uses
it until the operator approves it after a test on DGBOUS). The agents stay in Devin (cloud), the bank allows no Python
package: git is the channel; Python's standard library, git and the PC's SQL*Plus 21.17 do the rest.

- **`scripts/db_relay.py`** (operator's PC, a clone of its own): `--watch --branches "devin/*"` (one `git ls-remote`
  every 10 s, a pull only when a branch moved), runs each new request read-only through SQL*Plus (guard: one
  `SELECT` / `WITH`, no DML / DDL / PL/SQL / `FOR UPDATE` / `INTO` / package function / db link / unsubstituted `&` /
  `T_PGT_USAENTPROP_S`; `SET TRANSACTION READ ONLY`, rollback, exit on error, `TERMOUT OFF`, exact numbers, UTF-8, row
  cap, time limit), writes the CSV in `01-evidence/` and a log, pushes them; `--save-passwords` (checked, then Windows
  Credential Manager, standard library only), `--check`, `--once`, `--forget`, `--review`.
- **`scripts/relay_ask.py`** (the agent): one call per batch — the same checks before anything is pushed, push, wait,
  print the answers; exit 3 when no relay answers (manual mode).
- **Skill `run-db-queries`**: the DB access mode (relay / manual, asked at the start of a run, default manual) and how
  an agent uses it. Not referenced by any kickoff yet.
- **`docs/reference/db-routes.csv`**: DGBOUS (`dgbous.nngg.corp:1528`, SID `dgbous`), accounts per system — GBO
  `pgtadmin`, DEVENG `deveng`, `box_acc`, `box_fe`, `box_sys`, `box_stc`; no password.
- **Tests** `scripts/tests/test_db_relay.py` (21): the guard (every ACC configs catalogue query passes, 82), one
  request, refusals without connecting, errors, row cap, review, a fake SQL*Plus (what it is sent, in which order, the
  password never on its command line), passwords (store, rejected password, saved only once accepted), `relay_ask`
  (refusals before sending, a two-query batch answered through `--watch "devin/*"`, no relay → exit 3), git round
  trips through a bare repo. Not tested against Oracle or Windows Credential Manager here.
- Test steps for the operator: `runs/NY_SCH/tier2-dev/relay-test/README.md` (+ three ready-made requests). Skills and
  scripts READMEs.

### 2026-10-28 (2) — ACC configs: topics with several accounts in one GBO property → the operator's decision

`[operator, 2026-10-28]` ([ADR 0020](docs/decisions/0020-portfolio-properties-imported-from-gbo.md) point 6). GBO
allows a topic with several accounts in one portfolio property; BOX holds one (Tier 1 BOX: no case). NY (GBO
query, 2026-10-28): 14 cases, OTC `2485.35` / `2487.35`, 7 FX netting / level topics of the local list, each
`INTERNAL` + one real account (the newer row); GBO's list table has no column to tell them apart.

- New query **A-04i**; when it returns rows the agent asks: one question for every `INTERNAL` + one real account case
  (keep the real account — proposed — or `INTERNAL`), the account to keep once per identical case otherwise; never
  chosen by the agent; unanswered → OPEN. Inputs `decisions.multi_account_topics`.
- Charter (screen 4, inputs, checkpoint 2b, open question 11 closed), kickoff (Devin asks, Step 6, Step 7, Step 8),
  report template (new section 4), matrix template, catalogue, model §9.4, eval case, NY inputs, open item 4zy.

### 2026-10-28 — ACC configs: portfolio properties imported from GBO one by one; condition map; clashes (ADR 0020)

`[BOX expert via operator, 2026-10-28]` Review of `03-portfolio-properties-report.md` of NY's gap run
`gap_20261023_1` ([ADR 0020](docs/decisions/0020-portfolio-properties-imported-from-gbo.md)): the run used SLB's shape
(Swap: 3 GBO properties → 5 BOX ones).

- **Screen 4:** one BOX portfolio property per `Valid` in-scope GBO property — description as GBO's, its own topic →
  account rows; never merged. **Conditions:** its GBO conditions that exist in BOX, through the branch's **condition
  map** (`runs/<BRANCH>/branch/acc-configs/condition-map.csv`): paired automatically on the same field domain or
  description, otherwise proposed from both functions (new **A-04h**) with the value translation and asked once per
  pair; no BOX twin → dropped; a BOX condition never created or added.
- **Screen 2:** local properties built from the target's GBO (the in-scope properties' topics in their GBO list and
  their conditions with a BOX twin), not copied from the reference; a property off the instrument's set → a finding.
- **Clashes** (identical kept condition values — BOX refuses them): clash mode **asked every run** — (a) hold them for
  the accounting user's choice (default), (b) create all, the clashing ones `InValid`; the report says why each group
  clashes and what choosing one leaves out, no recommendation; `decisions.pp_clash_choices` applied by the next run.
- New catalogue queries **A-04f** (each in-scope GBO property's condition values; portfolio / counterparty / entity
  values hashed) and **A-04g** (the GBO conditions' catalogue); sections 1, 2, 4 rewritten.
- Charter (screens 1, 2, 4, inputs, phase 2 steps, hard rules 19–20, checkpoint 2b, open questions 10–11), kickoff,
  report template (condition map, per GBO property, clashes), matrix template, model §9.7, ACC add-product checklist,
  eval case, ADR 0014 status. NY: inputs (`fixed.local_properties`, `fixed.portfolio_properties`,
  `decisions.pp_clash_mode`, `decisions.pp_clash_choices`, `condition_map.file`), `branch/acc-configs/condition-map.csv`
  (header only), branch README, runs README, acc-configs README, open items 4zb (updated) and 4zy (new); `new_run.py`
  lists every branch-level CSV.

### 2026-10-27 (3) — Branch-level folder (`runs/<BRANCH>/branch/`); repo index completed (ADR 0019)

`[operator, 2026-10-27]` ([ADR 0019](docs/decisions/0019-branch-level-run-folder.md))

- **Branch-level folder:** `books-excluded.csv` and `label-aliases.csv` moved from `runs/NY_SCH/tier2-pre/books/` to
  `runs/NY_SCH/branch/books/` (the same in every environment). `build_fe_jobs.py` `excluded_books_csv` (used by the
  FE build, the `excluded-book-built` post-check and `build_acc_jobs.py`): explicit path → beside the environment's
  register (override, `excluded-books-env-override` when it differs) → the branch folder; an older run's path that no
  longer exists finds the branch's. The FE report says when the branch folder's file was used. `new_run.py` lists the
  branch-level files. `00-books.csv` and `instrument-plan.csv` stay per environment (environment-specific columns).
- NY inputs (FE jobs, ACC jobs, ACC configs `label_aliases.file`), templates, charters, FE build prompt, ACC configs
  kickoff, labels skill, catalogue screen 14, eval cases, runs README, books README, new branch README, open item 4zw,
  ACC / FE jobs READMEs, scripts README.
- **Repo index:** `cib-efapex-javagboclmbjbtch` (MBJ Java, read-only), `cib-boxfin-mdschedulmonitor` (read-only), and
  NY's target repos `cib-boxfin-t2usnyfe`, `cib-boxfin-t2nyloadprices`, `cib-boxacc-t2usnyac` (PR targets, ADR 0012).
- Tests: 3 new (branch-folder resolution and override warning; FE and ACC builds identical from the branch folder).
  Cross-version check: `build_acc_jobs.py` before / after on the same fixture (no file, file beside the register,
  explicit path) — byte-identical `out/`.

### 2026-10-27 (2) — ACC configs: topics by CODE; global topics / standard historics (.65, to review) (ADR 0018)

`[BOX ACC expert via operator, 2026-10-27]` Review of NY's gap run `gap_20261023_1`
([ADR 0018](docs/decisions/0018-acc-configs-global-objects-and-topics-by-code.md)).

- **Topics by `CODE`**, always — no mapping question (kickoff Step 7, charter checkpoint 4, open question 1, model).
- **Missing topics and standard historics** → `create (global .65)`, flagged *global — to review*, with the PRE / PROD
  PK-clash warning (charter hard rules 2–3, screens 6–7; catalogue A-06 / A-07 checks; matrix template *Global objects
  — to review* section); phase 2 design: in the main rollback and in `global_pk_rollback.sql`. Conditions, event groups
  and events stay verify-only. NY's 54 GBO topics with no BOX twin: created, to review `[operator]`.
- **Blank branch condition / no branch row → out**, not asked: A-U1 (g) table, A-U7 (a) / (b) keep only properties
  with a branch value classified in (`EXISTS`, was `NOT EXISTS` on the out codes).
- **`T_PGT_TOPICS_RR`, GBO ConcMis → out** (A-11 rulings, charter).
- **A-P5 (d)**: one table in detail (sequence, rows per fraction, counter, triggers); NY's `T_BOX_ACCT_PARENT_DATE_S`
  warning was a false alarm — next `2`, rows `1.44` / `2.65`, no counter row.
- NY: ACC configs inputs (`decisions.topic_mapping`, `screen4_scope`, `fixed.global_objects`, `fixed.out_of_scope`),
  README; open items 4za / 4w closed, 4v / 4zu updated, 4zx new (the `.65` PK range in PRE). Eval case.

### 2026-10-27 — ACC jobs: MIC end-of-day for every instrument, sender lastly; label aliases for MIC (ADR 0017)

`[BOX expert via operator, 2026-10-27]` ([ADR 0017](docs/decisions/0017-mic-end-of-day-and-label-aliases.md))

- `build_acc_jobs.py`: the MIC end-of-day ("scanning") steps are **mandatory** — no `mic.<instrument>` question.
  An instrument the reference runs without them gets a D12 per book (after the book's last step) and a 00D13 (after
  the ruler update), the ruler update waiting for every D12, copied from a reference instrument that has them
  (`mic.eod_template`, else the first found; `eod-steps-added`, `eod-template-missing`); their MBJ rows take the
  template's values with the instrument's own `FK_INSTRUMENT`, no group; descriptions from the instrument's own jobs.
  `MIC_SENDER_TYPE` `lastly` on every row. A D12 / D13 row not `MIC_EOD 1` + Accounting / Revaluation →
  `eod-row-unexpected`. The report lists the label aliases for MIC as a readiness item.
- ACC jobs charter, prompt (no MIC question; the MBJ Java repo `cib-efapex-javagboclmbjbtch` optional read-only),
  inputs template and NY inputs (`mic.eod_template`), NY ACC README; `box-batch-chain.md` (what D12 / D13 do, the
  MBJ repo).
- **Label aliases for MIC**: `box-acc-model.md` §8.2 (owner `17910.4`, extension `118615.4`, GL code, GL source; SLB's
  14 aliases, source `287.4`); `sigom-box-acc-configs-agent` **screen 14** (A-14a–c, inputs `books/label-aliases.csv`
  + `label_aliases.source`, matrix row, kickoff, eval); skill `set-up-book-labels`: aliases optional, never required
  for the FE side; NY: `books/label-aliases.csv` (Equation's codes for the 18 books with jobs, source `629.4`
  proposed), books README, ACC configs inputs.
- NY open items: 4zm closed; 4zk (SLB CAP rows in every book in the expert's environment); 4zw (alias source).
- Tests: every instrument with D12 / D13 (IRS added on depos' pattern; descriptions; a `drop` answer ignored), the
  sender `lastly`, `eod-template-missing`; MIC refusal cases removed.

### 2026-10-26 (2) — ACC jobs: the BOX team's answers on MBJ (B1–B8, ADR 0016)

`[BOX expert / BOX dev / BOX team via operator, 2026-10-26]` The eight blocking questions of the first ACC jobs run
answered ([ADR 0016](docs/decisions/0016-box-acc-jobs-expert-answers.md)).

- `build_acc_jobs.py`:
  - **B4**: a per-book step with no MBJ row in any reference book, run from `db.conf` there → `db.conf` per book with
    the book's label (`f_getPKByLabel('<target book>')`), as the reference (`step-in-dbconf-as-reference`); no shell.conf
    line, no MBJ row; `mbj.missing_rows` only overrides it; no row and no `db.conf` line → `mbj-row-missing`.
  - **B2**: `FK_CALENDAR` copied from the reference row (MBJ does not read it); `mbj.calendar` retired; the pre-flight
    checks the reference rows' calendars exist.
  - **B3**: `mbj.sequence` (required, `OWNER.NAME`, `mbj-sequence-bad`) replaces `mbj.pk_call`: PK =
    `<sequence>.NEXTVAL` + the fraction, `chk_pk` also refuses a PK already in the table; new read-only
    `<base>-mbj-precheck.sql` (sequence vs the table's highest PK of the fraction; `MBJ PK PRECHECK OK` / `PROBLEM` +
    a proposal for the BOX team).
  - **B5**: `controlm.ControlmServer` optional — the FE run's folder server (`controlm-server-from-fe-run`), refused
    when neither is there.
  - Report: how jobs run (the B4 line, the precheck, the server).
- **B7**: `controlm.CreatedBy` is the user ID of the person running the agent, asked every run — ACC and FE prompts,
  charters, templates, `build_fe_jobs.py` / `build_acc_jobs.py` input descriptions, NY inputs.
- **B8**: ACC prompt / charter: the operator says which FE run to treat as OK (frozen or not); no sign-off, no FE PR
  needed before the ACC jobs.
- Catalogue: **J-E11** (the MBJ PK sequence; Tier 1 `BOX_ACC.SPK_T_BOX_MBJ_PROPERTIES_S`); J-R2's calendar note.
- NY: ACC inputs (`mbj.sequence`, `missing_rows` emptied, `CreatedBy`, `fe_run`), FE inputs (`CreatedBy`), ACC README;
  open items 4zi, 4zl, 4zn, 4zq closed; 4b, 4zg, 4y updated.
- Tests: fixture `mbj.sequence` and an FE folder server; the five SQL files; B4 per-book db.conf; a step with no row
  and no db.conf line refused; the server from the FE run (and refused without one); `mbj-sequence-bad`.

### 2026-10-26 — ACC configs: Net CCS PlanBS is the CCS end-of-month netting (screen 13)

`[BOX ACC expert via operator, Confluence "CCS Netting and Undo EOM Process", 2026-10-26]` `T_BOX_NETCCS_BSPLAN_S`
(SIGOM *BOX - Accounting › Config. › Net EOM to CCS*) configures the CCS end-of-month netting (event `5210.65`) and its
first-day undo (`5211.65`): per branch × instrument type × strategy, an `EOM_CCS_ACTIVE` switch row and the accounts
whose balances are netted. The load PL on the page selects the CCS instrument types whose parameter `367.4` is not
`YES` — `367.4` = `STM` Settle to Market (`PGT_STC.T_PGT_PARAMETERTYPE_S`, operator queries Tier 1).

- `box-acc-model.md` §8.1: the process (postings, standard historics, topic translator), the configuration, the load
  PL and the parameter path; §8 row → screen 13.
- Charter: **screen 13** — asked every run whether it applies (no → N/A); yes → the reference's rows **as they are**,
  the operator changes what the branch needs `[operator, 2026-10-26]`; order, inputs, hard rule 2, open question 5.
- Catalogue: **A-13a** (the reference's rows with codes), **A-13b** (target), **A-13c** (the object's fields, the
  instrument types / strategies, account codes, events / historics / topics / `FFM` / `INTERNAL` in the target);
  A-11 no longer lists Net CCS PlanBS. Kickoff (Step 6, Step 7 question), matrix template (screen 13 row), eval case.
- NY: inputs `decisions.eom_ccs_netting`, open item 4zv (4v updated).

### 2026-10-23 (2) — ACC configs: the catalogue's text as it is, one system per query, find before asking

`[operator, 2026-10-23]` NY's gap run `gap_20261023_1` (Tier 2 PRE) gave queries that do not run: A-03b on
`PGT_SLB.T_MAD_REVAL_ACCOUNTS` (SLB and Madrid are `PGT_ES`), A-04a with `NAME` / `FK_GROUP` / `FK_INILOCPROPERTY`
(not columns of `T_BOX_ACCT_PORT_PROP_S`), A-11 with `FK_BRANCHGROUP` on `T_BOX_GLTA_LOCAL_S` — none of them the
catalogue's text. It also asked what `269.4` was and which NY branch-value families are NY_SCH config — both answerable
from the data.

- **Charter** hard rules 16–18: the catalogue's text as it is (`&&` values only; GBO schemas from the inputs file,
  never from the branch code; a failing query → A-P8 then only the named column); one system per query (GBO vs BOX
  = two extracts the agent joins); find before asking (PKs by A-L1, branch values by A-U1 g, one confirmation).
  Definition of done: A-P5 is the counterpart of the FE configs agent's pre-step P1 — a finding with a proposal, not a
  stop (phase 1 writes nothing; `F_GetPK` in counter mode updates `T___SEQUENCE`), blocking that table in phase 2.
- **Catalogue**: "How a query is run"; **A-L1** (what a PK is: branch group / branch / instrument); **A-P5** (b) the
  auth code and the max PK of this fraction, (c) the `F_GetPK` mode (`T__REMCONN_S`), the proposal rule; **A-P8**
  (a table's columns); A-P7 per account when needed; **A-U1 (g)** (the branch condition's function source, the group's
  branches, each value's size) and its classification table → `&&OUT_BRANCH_CODES` (A-U7, was `&&OTHER_BRANCH_CODES`);
  **A-03b** and **A-10c** split into GBO / BOX extracts; A-04a's real columns; **A-11** (a) columns first, (b) per
  table.
- Kickoff (the "Devin finds" row, how queries are given, Step 4b, A-U1 g in Step 5, two-CSV steps), matrix template
  (Branch values, PKs resolved, decisions with evidence / provisional, A-P5 proposal), eval case.
- NY: inputs (`branch_conditions.values_seen`, `out_codes` to classify — the operator's "NY_SCH only" is provisional),
  README (the run's results and issues), open item 4zu.

### 2026-10-23 — FE technical test: the re-run rule, which step writes what, the folder alias pre-check

`[operator, 2026-10-23]` NY's IRS technical test in DGBOUS ended every step OK with no financial status: the trades'
folder had no alias for source `279.4`. Once the alias was created, the financial steps could not simply be re-run —
the BACK group `2815.65` comes first.

- **Re-run rule**: after `2608.65` has run for a branch / instrument / date, run `2815.65` ENG GN Main Back Dia Queue
  By Book BOX (Run Batch: branch, instrument, label), check the Monitor (Process Calendar "Generation of Financial
  Status", queues "Programmed Financial Status Generation"), then `2608.65` and `2389.65`. `fe_tech_test.py` writes it
  on the run card (rows R1–R4, constant `RERUN`); skill, `box-fe-test-lookups.md` §7, `fe-batch-event-groups.md`.
- **Which step writes what**: the insert group writes `T_BOX_DATADEAL_S` + `T_BOX_<CODE>DATADEAL_S` (IRS
  `T_BOX_IRDATADEAL_S`); `2608.65` → `2389.65` write `T_BOX_<CODE>FINANCST_S`; `T_BOX_MTM_DATA_S` has no `FRONT_ID`
  (`DEAL_ID` NUMBER, `DDATE`, `FK_DIRECTION`). `fe_test_sql.stage_checks()`: the MtM check by `DEAL_ID` (a
  `TRUNC(DEAL_ID)` fallback commented), the insert-group block on the two deal tables, a new block `2389.65` with
  `<CODE>FINANCST`; the run card's fourth STOP after `2389.65`; `sql/70` (and `fe_reconcile.py`'s diagnose) also cover
  `2608.65` / `2389.65`. The Y / parallel tests' trace files get the `2389.65` step.
- **Folders**: `PGT_STC.T_PGT_FOLDER_S` (was the INFERRED `PGT_TRD`), confirmed — `box-fe-static-aliases.csv`, the
  `sql/30` folder-branch check. New **folder alias pre-check** in `sql/30` (`folder_alias_check()`): per trade the
  target branch's folders whose `DESCRIPTION` or `CODE` is the RAW `FOLDER`, their `279.4` alias, all their aliases;
  `OK` / `MISSING` / `OTHER CODE` / `CODE ON <pk>` (the two unique keys of `T_PGT_OBJ_SOURCE_S`). Lookups §6: the
  alias facts and how to create one in DEV (`P_SETHEADER`, IN OUT arguments reset before each call).
- **Job runner**: `db.sh` runs as `GM_ENV`'s user (or a per-job profile); the `PLS-00201` on `BOX_SYS.PKG_BOXUTILITY`
  was a DGBOUS-only grant to `pgtadmin` — granted, not expected in PRE / PRO (`runs/_reference/tier2-pre/README.md`,
  lookups §8). Open items 4zs (BOX FE team: the folder's `513.4` alias, PRE folder `203.35`) and 4zt (closed).
- Tests: 329 checks (one new: the re-run rows, `PGT_STC`, the pre-check; MtM / STOP / diagnose expectations updated).

### 2026-10-22 (3) — ACC configs: no usage window, one GBO source per run

`[operator, 2026-10-22]` Devin still asked for a GBO usage window, and ran the GBO reads in PRE PARALELO although
the run started in Tier 2 PRE. [ADR 0015](docs/decisions/0015-acc-configs-scope-from-configuration.md) (supersedes
ADR 0013's usage step):

- **No usage window**: the scope is configuration — the `Valid` GBO portfolio properties of the target's branch with
  their full lists (A-U1 a / f, A-U7 a / b), the reference's BOX rows, `T_MAD_REVAL_ACCOUNTS`. No "configured but
  unused" question; `&&ACCOUNT_CODES` = A-U7b + A-03a. The windowed queries (A-U0, A-U2, A-U2b, A-U3, A-U4, A-U4b,
  A-U5, A-U6) are optional diagnostics, run only when the BOX team asks.
- **One GBO source per run**, asked once at Step 2 (`gbo_source.env`: the target environment by default, or PRE
  PARALELO): new env tag **`GBO`** for every query on the target's GBO tables (A-U1, A-U7, A-02d, A-03a, A-03d,
  A-04d, A-04e, A-10a, A-10d); `TGT` is the target's BOX only; `GBO-PROD` / `GBO-PREPAR` retired.
- Charter (definition of done, screen 4, order, inputs, hard rule 15), kickoff (Steps 2, 5–8), gap-matrix template
  ("GBO configuration in scope"), NY inputs (`gbo_source`, `usage` emptied, no `configured_not_used`), NY README,
  catalogue, add-product checklist, eval case; ADR 0013 marked superseded on that point. No script changed.

### 2026-10-22 (2) — the `db.conf` branch argument is the wrapper's branch constant, not the PK

`[BOX team via operator, 2026-10-22]` No fixed values in the job lines: the core call's branch argument is now the
target wrapper's branch constant — NY: `PGT_NY.PKG_GMBATCHPROCESS.CST_PK_BRA_NYSCH` (= `20007.4`, J-T1) — as SLB's
lines pass `PGT_ES.PKG_GMBATCHPROCESS.CST_PK_BRANC_LND`, instead of `20007.4` typed in.

- `build_fe_jobs.py`: `branch_arg()` (`<wrapper owner>.PKG_GMBATCHPROCESS.<branch_const>`) on every core-call line
  (FE, load prices, scheduling monitor, Initial Accounting); `branch_const_check()`: refused `branch-const-unknown`
  when the run's `01-evidence/J-E4-wrapper-TGT.csv` does not hold the constant, warned `branch-const-unchecked` when the
  CSV is not there. The report states the constant and its value. `target.branch_pk` stays (the value, the checks).
- `build_acc_jobs.py`: the ruler updates pass the same constant; new required input **`target.branch_const`**
  (NY: `CST_PK_BRA_NYSCH`, template updated), refused `branch-const-mismatch` when it differs from the FE run's, checked
  in the FE run's J-E4 CSV. The MBJ SQL keeps `target.branch_pk` (`FK_BRANCH` values, plain-SQL verify queries).
- `fe_tech_test.py`: the group card read a core-call line with a plain comma split, so the comma inside
  `to_date('$ODATE','YYYYMMDD')` gave the instrument column `'YYYYMMDD')`; now a top-level split (found while
  checking this change).
- The agents know it for every branch: FE hard rule 9, ACC hard rule 12, both procedures (Step 4), eval cases,
  scripts README; NY inputs annotated, open item 4j, the Tier 2 reference README, `reference-slb-fe.md`.
- **Tests:** 5 new checks (323 → 328), all passing. **Regression:** every `db.conf` core line changes (the branch) in
  `db.conf.proposal` / `unix/db_nuevo.conf` of both agents — expected; every other deliverable identical. An ACC run
  built before this has no `target.branch_const`: its rebuild refuses (`input-missing`) — build a new run instead.

### 2026-10-22 — Unix files kept LF; `db.conf` time without colons; the BOX ACC expert's review of the ACC configs agent

`[operator, 2026-10-22]` From the BOX team's review of the FE jobs and the operator's test in Tier 2, and the BOX ACC
expert's review of the ACC configs plan.

- **Unix package written as CR LF on the server** — the scripts write LF (checked); a Windows clone with
  `core.autocrlf=true` turned the files into CR LF, so `job_unix.sh` created job files whose names end in a hidden CR.
  New **`.gitattributes`**: `*.sh`, `*.ksh`, `*.conf`, `*.proposal` and `**/out/unix/**` are LF on every checkout. FE's
  `db.conf.proposal` now also written with `newline="\n"`. A test fails on any CR in `out/unix/` or the confs.
- **`db.conf` lines cut at a colon** — the job runner keeps field 4 of a line (`cut -d: -f4`), so
  `to_char(sysdate,'RRRR-mm-DD HH24:MI:SS')` was cut at `HH24` (`ORA-01756`). `P_TIME` is a VARCHAR2 (operator's
  `ALL_ARGUMENTS` check); the default (`build_fe_jobs.TIME_ARG`, also the ACC agent's) and NY's FE / ACC inputs are now
  `to_char(sysdate,'RRRR-mm-DD HH24'||CHR(58)||'MI'||CHR(58)||'SS')` (tested by the operator). Both scripts refuse a
  `db.conf` call holding `:` (`dbconf-colon`, nothing written). Templates, FE charter, eval, scripts README, the
  Tier 2 reference README, `reference-slb-fe.md` and open item 4j annotated.
- **`sigom-box-acc-configs-agent` — the BOX ACC expert's review** ([ADR 0014](docs/decisions/0014-box-acc-expert-review-1.md);
  ADR 0011 marked partly superseded):
  - never asked any more: conditions (BOX as it is), event groups (**global**, no branch copy — checkpoint 3 gone;
    `box-acc-jobs-agent`'s `mbj.group_map` stays empty), local properties' `INIVALPCDATE` (**01/01/1900**);
  - **Cross Account Config from `<GBO schema>.T_MAD_REVAL_ACCOUNTS`** (`PGT_ES` Tier 1, `PGT_NY` NY Tier 2), not
    `T_PGT_CROSS_ACCTCONF_S`: A-03a / A-03b / A-03c rewritten (`SELECT *`; SLB's GBO vs BOX rows: `TIPO` = `ACC_TYPE`?),
    the old query kept as A-03d (usage evidence); new placeholders `&&TARGET_GBO_SCHEMA` / `&&REFERENCE_GBO_SCHEMA`
    (registry `wrapper_owner`);
  - **Conf Instru Type = screen 12**: the reference's BOX rows per instrument, as they are (A-12a / A-12c), never GBO;
  - GBO portfolio properties **`Valid` only** (A-U7, A-04d / A-04e); internal-list topics → the **internal account**;
  - **A-P7** compares a GBO table's columns with its BOX counterpart before any copy; hard rules 12–14;
  - new deliverable **`03-portfolio-properties-report.md`** (template `portfolio-properties-report.md.tmpl`): per BOX
    property its topics, account, how chosen and its GBO properties; per GBO property where it went; what is not
    carried. Gap-matrix template: A-P7, screen 12, the fixed rules, column maps.
  - Charter, kickoff, NY inputs (`fixed`, `gbo_schema`, the portfolio properties' start date still asked — proposal
    01/01/1900), NY README, `box-acc-model.md`, catalogue, add-product checklist, eval case, open items 4u / 4v
    updated, **4zr** added. Still open: the portfolio properties' start date, `ACC_TYPE` if `TIPO` is not it, the BOX
    route of GBO's own `T_PGT_CROSS_ACCTCONF_S` rows.
- **Tests:** 4 new checks (319 → 323), all passing. **Regression:** `db.conf.proposal` / `db_nuevo.conf` / the ACC
  `db.conf` differ on every line from the frozen runs (the time expression) — expected; every other deliverable
  identical.

### 2026-10-21 (3) — fixes from the first live run of both jobs agents (NY_SCH Tier 2)

`[operator, 2026-10-21]` Found while running `box-fe-jobs-agent` (`fe-jobs/all_20261021_1`) and `box-acc-jobs-agent`
(`acc-jobs/all_20261021_1`, a TEST run: calendar `1.21` and `pk_call` test values, CCS left out) with Devin.

- **PR before the freeze** — both procedures: the PR question is Step 7, the freeze **Step 8, last** (Devin froze the FE
  run before asking). `stage_target_pr.py` refuses a frozen run (`run-frozen`) and a run with `test_values`
  (`run-test-values`).
- **`box-acc-jobs-agent`**
  - The hand-off's Initial Accounting drafts take `controlm.CreatedBy` (`omit` → removed), like every other job (they
    kept the FE run's value).
  - **New input `mbj.missing_rows.<reference job>`** for a step with no MBJ row in any book (SLB's CCS D08 runs from
    `db.conf` only): `from:<job of the same instrument>` (its values; the group stays the step's own, from its `db.conf`
    line - a D09 row would carry D09's group) or `<OPEN …>` (the job built, its row left out of the SQL, exit 4).
    Refusals `mbj-row-source-unknown`, `mbj-row-source-other-instrument`; warning `mbj-row-from-other-step`.
  - **New input `test_values`** (the fields given for a test only): a banner in the report and every SQL file, the
    rehearsal and config blocks stop at their first statement (`-20098`), exit 4, no PR.
  - `mbj-row-from-other-book` warned once per step with its job count (was once per book: 54 lines for CAP).
  - `unix.existing_scripts` read as in the FE agent (`add_new_jobs.ksh` was reported missing); NY's ACC inputs list it.
- **`box-fe-jobs-agent` report** — a `db.conf` job defined in the reference's ACC folder (`reference.controlm_other`:
  Initial Accounting) is `dbconf-only-other-folder` (the ACC agent's, no question) instead of a `dbconf-only` question;
  the run summary writes an identical warning of several instruments once, with its instruments.
- **Procedures and charters** — only answers the script has an input for are offered (Devin offered "exclude D08" /
  "paste the row" / "drop D08", which no input took); a refusal no input answers is a script gap: stop, change
  nothing. Every value not asked in the session (inputs file, FE run, FE configs run) is listed with its source and
  confirmed before the first build (Devin filled host, Application, `CreatedBy` and the auth code from earlier answers
  without saying). ACC hard rule 11.
- **NY** — open item 4zq (CCS D08's MBJ row, BOX team); `acc-jobs/README.md`: CCS D08, the TEST run; ACC inputs:
  `mbj.missing_rows` asked, `test_values: []`, `unix.existing_scripts`. Template, eval cases (FE, ACC), scripts README,
  `reference-slb-fe.md` updated.
- **Regression:** expected identical deliverables for both live runs (their inputs have none of the new keys; the
  ACC run's `CreatedBy` is the FE run's) — only `report.md` differs; checked with `regress_fe_jobs.py` on each. On a run whose `CreatedBy` differs from the FE run's, the
  Initial Accounting jobs of the ACC folder now take it. 10 new checks (309 → 319), all passing.

### 2026-10-21 (2) — `box-acc-jobs-agent`: the FE run is required and checked

`[operator, 2026-10-21]` The Initial Accounting jobs the FE agent builds are the ACC agent's input: `target.fe_run` is now
**required** (was optional, with names by rule as a fallback). `build_acc_jobs.py` refuses `fe-run-missing` (not an FE
run), `handoff-missing`, `fe-run-instruments-missing` (the FE run did not build every instrument of this run),
`ia-not-in-handoff` (was a warning and a name by rule) and `acc-folder-mismatch` (the FE run put the Initial Accounting
jobs in another ACC folder); warns `fe-run-not-frozen` and `acc-folder-unchecked`. Which FE run: the operator's, the
procedure proposing the latest frozen run of the environment that built every instrument (Step 2). Hard rule 10: the
FE run is no longer optional; the MBJ engine still never blocks (the jobs can be built and reviewed before it is
deployed). Charter, procedure, NY inputs and README, template, eval updated; 5 new checks (304 → 309).

### 2026-10-21 — `box-acc-jobs-agent` built; SLB's ACC chain recorded; the MBJ engine check fixed

`[operator, 2026-10-21]` The ACC equivalent of `box-fe-jobs-agent`, with **`shell.conf` + an MBJ row for every per-book
step**. Inputs: SLB's MBJ rows (J-R2, 145 rows), Devin's read-only audit of SLB's ACC folder and conf files
(`runs/NY_SCH/tier2-pre/acc-jobs/00-discovery.md`), the calendar and package queries, the BOX expert's confirmation that
`BOX_ACC.PKG_BATCHPROCESS_MBJ` is not deployed in Tier 2 (she will deploy it). Decisions: MBJ rows as SQL files; MIC
end-of-day steps asked every run; built now, run on NY once the BOX expert has answered.

- **New `scripts/build_acc_jobs.py`** (reuses `build_fe_jobs.py`'s helpers without changing them): the ACC Control-M
  folder, `shell.conf.proposal`, `db.conf.proposal` (branch-level steps as the core call), `sql/<BASE>-mbj-{rehearsal,
  config,verify,rollback}.sql` (PKs from `mbj.pk_call`, auth code checked, labels by code, pre-flight and self-check),
  `mapping.csv`, `report.md`, the Unix package; Initial Accounting from the FE agent's `acc-handoff.json`; excluded
  books; readiness of the MBJ engine as a warning, never a refusal. Refusals: `input-missing`, `mic-decision-missing`,
  `rename-missing`, `external-event-unmapped`, `mbj-row-missing`, `template-book-unusable`, `nothing-to-copy`,
  `reference-cross-book-wait`, `constant-unmapped`, `excluded-book-built`…
- **New agent `agents/box-acc-jobs-agent/`**: `AGENT.md` (branch-agnostic, hard rules 1–10), `prompts/build.md` (any
  branch), `prompts/build-ny-sch-tier2.md` (NY pointer), `templates/acc-jobs-inputs.example.json`; NY's
  `runs/NY_SCH/tier2-pre/acc-jobs/acc-jobs-inputs.NY_SCH.json` and `README.md`; `evals/cases/box-acc-jobs-agent.md`.
- **Shared scripts**: `regress_fe_jobs.py` also rebuilds ACC runs (and keeps the `<env>/<area>/<run>` names in its
  temporary copy); `stage_target_pr.py` reads `acc-jobs-inputs.json`; `new_run.py` knows the `acc-jobs` area.
- **Docs**: new `docs/reference/job-chains/reference-slb-acc.md`; `box-batch-chain.md` *The ACC chain*;
  `box-jobs-queries.md` **J-E9 checks owner `BOX_ACC`** (the `PGT_PRG` package of the same name made Tier 2 pass) and
  the MBJ calendar note; `reference-slb-fe.md` corrected (IRS `00D03` and CCS's per-book D08 are ACC jobs); NY's FE
  inputs: CDS's Initial Accounting has no conf line; open items 4b, 4e updated, 4zk–4zp added; the other charters name
  `box-acc-jobs-agent` as the MBJ rows' owner; indexes.
- **Tests**: 20 new checks (chain, waits, environment fields, confs, SQL, MBJ values, MIC keep / drop, 7 refusals,
  excluded book, regression check + PR staging on an ACC run, the NY inputs and the template asked, the new charter and
  procedure branch-free). 284 → 304 checks, all passing; `build_fe_jobs.py` unchanged.

### 2026-10-20 (3) — BOX FE jobs: one procedure for every branch, the branch as data, a regression check

`[operator, 2026-10-20]` After an agent-design review (Anthropic's guidance: a workflow with the repeatable work in
scripts, the smallest context per step, evals on real runs).

- **`prompts/build-tier2.md` → `prompts/build.md`** (nothing in it was Tier 2-specific). It runs **directly**: Step 0
  asks the branch and its environment folder when no kickoff names them, creates the branch's inputs file from the
  template when it has none, and lists the repos to attach from the registry rows. **Just-in-time reading:** Step 1
  reads only the charter, the inputs file, the branch's README and open items; the skills, the batch chain doc and the
  reference's facts are read at Step 3 (once the reference is chosen), the script header at Step 5. New last section:
  the regression check.
- **`prompts/build-ny-sch-tier2.md`** — same command, now a pointer: `NY_SCH`, `tier2-pre`, then `build.md`. Its NY
  values were already in NY's inputs file and README; the two not there moved: the proposed ACC folder name (in the
  `acc.folder_name` question) and the environments (README).
- **`AGENT.md`:** "asked to run this file? follow `prompts/build.md`"; the procedure row; the excluded-books check;
  evals and scripts rows.
- **`scripts/build_fe_jobs.py`:** after every build, a job or label of an excluded book anywhere in `out/` (not
  `report.md`) → refused **`excluded-book-built`** (was a manual grep in NY's kickoff).
- **New `scripts/regress_fe_jobs.py`:** rebuilds a finished run from its own answers in a temporary copy and compares
  every file of `out/` (exit 0 / 1 / 2). Use it on the branch's last frozen run after any change to the agent.
- **Evals:** `evals/cases/box-fe-jobs-agent.md` — the regression check and a 6-point **session checklist** for a real
  Devin run.
- **Tests:** the post-check (clean run passes, a planted job is caught); the regression check (one instrument with a
  relative input path, several instruments with parts / hand-off / Unix package: identical; a changed deliverable:
  exit 1 with its diff; a bad `--as-of`: exit 2); the branch-identifier check also covers `prompts/build.md`. 279 → 284
  checks, all passing.

### 2026-10-20 (2) — agent charters branch-agnostic

`[operator, 2026-10-20]` The agents are for every branch (NY_SCH first, then Peru, HK…): a charter (`AGENT.md`) holds
rules, never a branch's values. Branch facts moved, nothing dropped; hard-rule numbers unchanged (other files cite
them).

- **`box-fe-jobs-agent`:** charter rewritten generic (placeholders `<BRANCH>`, `<TT>` target token, `<RT>` reference
  token; rules grouped: the chain / waits on other folders / what is generated; new hard rule 8 "never blocked by an
  optional input"; source tags kept). SLB facts → new
  [`docs/reference/job-chains/reference-slb-fe.md`](docs/reference/job-chains/reference-slb-fe.md); NY values,
  decisions and its settled questions → `runs/NY_SCH/tier2-pre/fe-jobs/README.md` ("NY values and decisions"); NY's
  open questions → open items 4zg–4zj. Prompts: new generic `prompts/build-tier2.md` (the procedure; renamed `prompts/build.md` in 2026-10-20 (3));
  `prompts/build-ny-sch-tier2.md` is now NY's thin kickoff (same command) that follows it.
- **`box-batch-jobs-agent`, `box-datalake-expert`, `branch-config-agent`, `branch-onboarding-orchestrator`,
  `sigom-box-acc-configs-agent`, `sigom-box-fe-configs-agent`:** branch names, PKs, repos and examples replaced by the
  rule or by a pointer (branch registry, `repo-index.md`, the branch's record / run / inputs file). The orchestrator's
  goal is now a parameter (`<BRANCH>`). FE configs' branch examples (question G for NY, the CCS residual, SLB / Madrid
  examples, the gate 0c worked template) → [`fe-walk-notes.md`](docs/reference/fe-walk-notes.md) "Branch examples
  moved from the charter"; a personal name in a source tag replaced by `operator`.
- **Test:** every `agents/*/AGENT.md` (except the example agent) is checked for branch identifiers (branch codes and
  names, job prefixes of a branch, labels, owners, calendars, branch repos, branch / group PKs, Control-M servers);
  platform values (group PKs, platform repos) stay allowed.
- **Indexes:** `reference-slb-fe.md` added to `docs/README.md`, `docs/topic-index.md`, `docs/reference/job-chains/README.md`.

### 2026-10-20 — BOX FE jobs: NY's GBO events read from its PRO folder; GBO event answers checked

`[operator / Devin, 2026-10-20]` SLB's chains per product explained (batch-jobs agent, descriptor waits included) and
NY's GBO Control-M folder for **production** (`P-GBO-NY-TIER2`, the only one available) read.

- **`scripts/build_fe_jobs.py`:** new optional `target.gbo_folders` (`[{path, env}]`): every external-event answer
  naming a GBO event is checked against the events the target's GBO folder emits (eventsToAdd and If-block
  `Event:Add`) — not emitted → refused `gbo-event-not-emitted` with the closest names; used only in an environment
  with no GBO folder → `gbo-event-unchecked`; `target.gbo_event_override` for an event emitted by a folder not
  attached. **Optional, never blocking:** no folder given, or a missing file → the run goes on and the GBO event
  answers are reported as not checked (`gbo-events-not-checked` / `gbo-folder-missing` warnings); the kickoff prompt
  asks once whether the operator can provide it. Tests added.
- **NY inputs:** `GMGB1420D02-OK` → `GMNY0012D01-OK_PR` (was `GMNY0012D01_PR-OK`, wrong); `GMGB1575D01-OK`,
  `GMGB4436D02-OK`, `GMGB4465D02-OK` → `DROP-REVIEW`; PRO `ControlmServer` proposed `GCB.GCB-P-D012`; PRE asked;
  `template_book` 15 for ccs, otc, cap; `target.gbo_folders`.
- **Knowledge:** `box-batch-chain.md` (DEV server in the folder files, `G0…` cross-server events, NY's GBO price chain
  and event spellings, NY MtM through the Data Lake, no SwapAgent); `box-fe-jobs-agent` AGENT.md open questions 5
  (settled), 10 (server), 12–14 (CCS clearing house, CCS D07 / D09, conf lines scheduled nowhere); fe-jobs README;
  external README (`gbo-ny/`); open items **4zg–4zj**.

### 2026-10-15 (3) — GBO accounting as NY uses it: knowledge from the PRE PARALELO usage queries

`[operator, 2026-10-15]` The ACC gap run's usage step, re-run by the operator in **PRE PARALELO** (a recent copy of
GBO production; production is not accessible): A-G1, A-G4, A-U0–A-U3, A-U1 (e) / (f), A-U2b, A-U5, A-U6, A-U7a.
Counts and codes only.

- **`docs/reference/box-acc-model.md` §9 (new):** where to read usage (PRE PARALELO over Tier 2 PRE); everything is
  keyed on the branch **group** (NY's holds 25 branches; NY SCH is the first in BOX); how a trade finds its portfolio
  property — NY's condition functions per instrument and the **branch condition** (`NY_SCH` / `NY_IBF` /
  `INTERNAL`); how a topic finds its account (lists, internal list → `INTERNAL`, Cross Account Config = settlement
  account by currency, property `0`, topic `0`); NY SCH in numbers; reading rules (scope by branch condition, full
  lists, A-U3 amounts are not balances, `0` = none); what is known vs not about BOX as SLB uses it. §10 Open: new
  questions.
- **`docs/reference/queries/acc-config-mining.md`:** env tag `GBO-PREPAR`, placeholders for the branch condition and
  the group's branches; new **A-G4** (is the group in BOX), **A-U1 (e) / (f)** (branch values, screen-4 scope),
  **A-U2b** (movements with no topic), **A-U4b** (optional), **A-U5** as a concrete count query, **A-U6** (accounts
  outside the lists), **A-U7a / b** (topics and accounts of the in-scope lists); A-U3 corrected (not balances);
  queries are shown with every value filled in.
- **`docs/reference/confirmed-joins.md`:** `0` = none on movements; the branch condition join; GBO Cross Account
  Config → topic / branch; key amounts are not balances.
- **NY:** `acc-configs-inputs.NY_SCH.json` (group, usage source and window, branch conditions, CDS and screen-4
  decisions), acc-configs `README.md` (what is known), open items **4za–4zf** (topic codes, BOX branch condition,
  postings with no topic, `T9…` accounts, scope decisions, the Tier 1 SLB reads still to do).
- **Repo name** corrected to `cib-box-aukinbranch` in the prompts and `runs/README.md` (the Step 0 search also tries
  the old spelling).

### 2026-10-15 (2) — BOX FE jobs: fixes from the `depos-irs_20261015_1` run

`[Devin, 2026-10-15]` First combined depos + IRS run (exit 4, one OPEN: NY's index-load job). Three script gaps:

- `out/parts/<instrument>/pending-questions.md` written before its folder existed (crash) → folder created first;
- an external event answered `<OPEN …>` was refused as unanswered → accepted and reported OPEN (`<ask …>` still
  refused); `{…}` keeps working;
- SLB's CDS Initial Accounting `GMBX9LB00D02` (another group than `2409.65`) was asked as an external event →
  `initial_accounting.group` may be a list; the hand-off row carries the job's own group. NY inputs: the CDS group
  `<ask>` (from the Tier 1 inventory).
- Tests: two new cases. Docs: AGENT.md, kickoff prompt, eval case, open item 4y (run done, review pending).

### 2026-10-15 — BOX FE jobs: one reference book for the shared jobs, separate runs refused (IRS run review)

`[operator / Devin, 2026-10-13–15]` Review of the IRS run (`irs_20261013_1`, PR #72 not merged) against `depos-v2/`:
the two separate runs wrote different shared per-book jobs (`GMBX0NY<bk>D01-D03`, their waits depend on the
instruments built, and the Unix package deletes then adds the lines), and IRS took its D01 from SLB book 04 through
SLB's cross-book wait `GMBOX0031D02` → `GMBOX0033D01`. Devin's read-only check: the desk token is the same across the
Data Lake DD / DDOTC / FD / MD events, SLB books 14 and 15 are identical, every NY book has its triple, D02 waits the
standard 8 except book 03.

- **`scripts/build_fe_jobs.py`:**
  - shared jobs from **one reference book**: `reference.generic_book`, or the majority form of the complete,
    new-named books without a cross-book wait (tie → template book's, else the highest); waits on any other book's
    shared job (also old-named `GMBOX00nn`, by label + group) are read as that book's; warnings
    `generic-book-chosen`, `generic-books-differ`, `generic-book-none`, `reference-cross-book-wait`; refusal
    `generic-book-not-usable`;
  - template book not given → the book with the most active jobs of the instrument (counts shown), highest on a tie;
  - an instrument `built` in the plan but outside the run → refused `shared-jobs-other-run` unless `separate_run`;
  - an external event answered with a placeholder (`{desk}`, `<…>`) → OPEN in the report, exit 4;
  - PR #72's rename fix: an old-named job renamed to a per-book name builds one job per target book;
  - old-book jobs not in the chain summarised (`old-book-jobs-not-needed`) instead of one warning each.
- **`scripts/tests/test_validate_run_output.py`:** seven new cases (template / shared-book choice, explicit and refused
  `generic_book`, cross-book, per-book rename, placeholder OPEN, separate run refused).
- **`box-fe-jobs-agent`:** charter (reference books section, rule 6 one run for undeployed instruments, rule 6b SLB
  context on every question, the Unix package's delete step described correctly, open question 9), kickoff prompt
  (build `depos irs` together, show the script's book choices, questions with `explain-box-job` context), eval case.
- **NY:** `fe-jobs-inputs.NY_SCH.json` (`template_book` irs 15, `generic_book` 15 with source), `instrument-plan.csv`
  (depos / irs: rebuild together, not to deploy), fe-jobs README, open items **4x** (SLB cross-book wait, BOX team) and
  **4y** (close PR #72, one `depos irs` run, BOX expert review).

### 2026-10-14 — BOX ACC: the model read from the database and the code; the ACC configs agent's pre-checks

`[operator, 2026-10-14]` Structural queries in PRE-PROD (GBO D1–D2, BOX B1–B4, metamodel M1–M3, the A-11 objects)
and Devin's read-only answers from `cib-boxacc-dbboxacc` (`PKG_ACCTPROP` r0.0.8, `PKG_ACCTPRECOMMIT` r0.0.14,
`PKG_SIGOM_COV`, Liquibase layout). Negative `FK_OWNER_OBJ` = test / deleted rows (operator).

- **New `docs/reference/box-acc-model.md`:** GBO vs BOX accounting tables (same columns; Cross Account Config renamed
  + `ACC_TYPE`), the identity values per table confirmed against the rows (the topic / condition lists are
  extensions of the portfolio-property object: three topic lists by `FK_EXTENSION`; GBO local properties have one
  topic array), keys (no foreign keys, three unique keys, no defaults), sequences (some lag their data; one not in the
  repo), triggers, `f_GenTopicCond` (array → list mapping, `FK_GLTA` never set, no COMMIT, version caveat), what runs
  on save (`p_StatusPortFolio`'s InValid rules, `p_AccountPrecommit`: an account is one row), the PK rule (`F_GetPK`
  + the installation's `AUTH_CODE`), Liquibase delivery, `ACC_TYPE` 0 / 1 / 2, A-11 rulings, NY-specific GBO tables.
- **New ADR 0013:** structural pre-checks, GBO-production usage, reading rules (owner + extension, negative owners
  out, `COUNT(*)`), phase 2 through SIGOM's own routines; ADR 0011 points to it.
- **`docs/reference/queries/acc-config-mining.md`:** pre-checks A-P1–A-P6, usage A-U0–A-U5 (env tag `GBO-PROD`),
  the owner / extension table filled (Cross Account Config `35000189.65` / `18051.4`, portfolio property
  `35000170.65` / `12646.4`, lists, arrays), owner and list-extension filters on every list read (A-04b mixed the
  three lists), concrete A-04e, A-10b, A-10c, new A-10d (account date rules), A-11 rulings.
- **`sigom-box-acc-configs-agent`:** charter (definition of done, screens 2 / 3 / 4 / 10, A-11 candidates, order,
  inputs, phase 2 call sequence, hard rules 8–11, natural keys, the list mapping, open questions), kickoff prompt
  (versioned run folder, environment asked, Step 4 pre-checks, Step 5 usage), matrix template (pre-check and usage
  sections, per-list rows), eval case (new fail conditions), NY inputs (`usage`, `expected_structure`, decisions),
  run README.
- **`scripts/new_run.py`:** area `acc-configs` (versioned gap runs, branch inputs offered).
- **Corrected:** `box-data-model.md` BOX_ACC rows (non-existent columns), `sigom-metamodel.md` new §6e,
  `confirmed-joins.md` (ACC lists, arrays, movements, date rules, negative owners), `acc-add-product-checklist.md` §0
  owner objects, `agents/README.md`, `docs/topic-index.md`.
- **Open items 4r–4w** (environment and access, package versions, delivery form, rules, objects outside the
  checklist, topic mapping).
- **Tests:** 1 new check (`new_run.py --area acc-configs`).

### 2026-10-13 (3) — `box-fe-jobs-agent` prompt: the versioned run folder everywhere

- `agents/box-fe-jobs-agent/prompts/build-ny-sch-tier2.md`, `AGENT.md`: the old `fe-jobs/<instrument>/` paths replaced by
  the versioned run folder of Step 2a (`runs/<BRANCH>/<tier>-<env>/fe-jobs/<name>_<YYYYMMDD>_<n>/`); "one instrument or
  several" in the prompt header. Before the run with IRS / CCS / OTC / C&F.

### 2026-10-13 (2) — GBO / BOX Financial Status tables per product

`[operator, 2026-10-13]` The SIGOM Financial Status menus of both systems, product by product (screenshots): the
product codes differ (BOX CCS = GBO SW "CS (Currency Swap)", CFM = IF, CDS = CD, FRA = FR, OTC = five GBO products,
FX = four); financial data (`FINANCST`) is the table to compare first.

- **New `docs/reference/gbo-box-product-tables.csv`:** every GBO product (deal, financial, MtM, MIS-MDR tables; GBO-only
  products marked) and every BOX product, with the pairing (MM confirmed, the others INFERRED; CES / BRS OPEN).
- **`gbo-box-fe-field-map.csv` regenerated from it:** per BOX product one `table` + `link` row per GBO table (OTC 5, FX
  4); financial key `FRONT_ID`, date `DDATE`.
- **`fe_test_sql.py`:** reads the product list (`box_code`, `gbo_products`, `gbo_code_of`); `financial_pair` writes one
  GBO statement per GBO table. **`fe_reconcile.py`:** one GBO query per GBO table (`…-<area>-<GBO code>`), compare reads
  them together; `files` takes several GBO CSVs (comma-separated). **`fe_tech_test.py`:** plan step 9 for several 80 CSVs.
- **Docs:** `box-fe-test-lookups.md` §4 (the pairing) and §5 (static MIS / IT tables both sides), `sigom-reference.md`
  (GBO codes ≠ BOX codes), the Y test and technical test skills, Y eval case, open item 4q.
- **Tests:** 1 new check (CCS → SW tables; OTC's five GBO queries read together; `files` with two GBO CSVs).

### 2026-10-13 — lessons of the NY technical test, applied to every FE test

`[operator, 2026-10-13]` The NY_SCH technical test ran in DGBOUS (run `tier2-dev/tests/technical/depos_20261009_1`).
Devin could not find the counterparty table (`PGT_STC.T_PGT_ENTITY_S`); 2632.65 ended OK but imported no MtM row
(`p_Import_Mtm_Data` filters `INSTRUMENT = 'Loan / Depos'`, the RAW market data carried `'Deposit'`) and nothing
checked it; the GBO vs BOX financial data comparison was done by hand.

- **New `scripts/fe_test_sql.py`** (shared): the checks after each key step, the diagnosis of a step that wrote
  nothing, the INSTRUMENT text check, the static-table locator, GBO vs BOX product financial data by `FRONT_ID`.
- **New `docs/reference/box-fe-test-lookups.md`:** static tables, the stage tables per step, group → event →
  procedure → filters, the GBO / BOX product tables (`<CODE>`: `MM` deposits).
- **`fe_tech_test.py`:** the run card STOPs after 2629.65, 2632.65 and the insert group (`sql/60` blocks:
  `T_BOX_DEAL_DATA_S` + flows, `T_BOX_MTM_DATA_S`, `T_BOX_DATADEAL_S` + `T_BOX_<CODE>FINANCST_S`); new
  `sql/70-DEV-diagnose.sql`; `sql/30` locates the static tables (`T__OBJ_DEF_S`, the alias's static row - counterparty
  `T_PGT_ENTITY_S`) and checks the INSTRUMENT text per RAW table; optional `compare_gbo` → `sql/80-PROD-GBO-financial.sql`,
  `sql/81-DEV-BOX-financial.sql` (NY: on).
- **`fe_reconcile.py`:** `files` (two CSVs compared directly, common columns, ids skipped); auto compare when the map
  has no field rows; map role `link` (financial data keyed by `FRONT_ID` through the deal table); composite keys;
  the Y / parallel test take **the products the operator chooses** (`products`: one, several, all; trades per
  product; files `…-<product>-<area>`); the Y test pack adds `sql/30-BOX-trace-<product>.sql` and
  `sql/70-BOX-diagnose-<product>.sql`; `insert_group` / `raw_instrument` default per product (shared with
  `fe_tech_test.py` in `fe_test_sql.py`).
- **Data:** `box-fe-static-aliases.csv` columns `static_table`, `static_status`; field map: deposits financial
  confirmed (tables, link, `FRONT_ID`, `DDATE`), the other products INFERRED on the same pattern; NY Y-test inputs
  (`tier2-dev/tests/y/y-test-inputs.NY_SCH.json`, deposits, the technical test's trades).
- **Docs:** the three test skills, eval cases, scripts / runs READMEs, open item 4p.
- **Tests:** 3 new checks (the lessons in the technical test pack; link, auto and `files` in the reconciliation;
  several products in one Y test run).

### 2026-10-09 (4) — Y test and parallel test (basics), FE jobs for more instruments

`[operator, 2026-10-09]` Basics of the second and third tests, to be completed when the Y test starts; NY's PRE
Paralelo environment is IGBOUSIB; the SLB chains of IRS / CCS / OTC / C&F (explain.md) reviewed for the next run.

- **New `scripts/fe_reconcile.py`:** `pack` (GBO / BOX queries per area from the field map, filtered by dates and trades
  or the branch filter; OPEN points) and `compare` (per key and field: OK / DIFF with tolerances / ONLY_GBO / ONLY_BOX /
  NO_COLUMN; Spanish-locale amounts, any date format; `03-recon/`, `03-results.md` keeping the explanations; parallel:
  `04-breaks.csv` NEW / OPEN / RESOLVED). Refusals `inputs-missing`, `run-frozen`, `map-missing`, `evidence-missing`,
  `key-missing`.
- **New `docs/reference/gbo-box-fe-field-map.csv`:** depos, IRS, CCS, OTC, C&F × deal / financial / mtm - the tables
  (BOX confirmed, GBO codes INFERRED), the BOX deal filter; keys, date columns and fields OPEN.
- **New skills `box-fe-y-test`, `box-fe-parallel-test`** (templates, eval cases); NY parallel inputs
  `runs/NY_SCH/tier2-preparalelo/tests/parallel/parallel-test-inputs.NY_SCH.json` (IGBOUSIB); `new_run.py` knows the
  areas `tests/y`, `tests/parallel`.
- **`build_fe_jobs.py`:** warning `dbconf-only` - executed `db.conf` jobs with no Control-M job in the reference folder
  (not copied, for the BOX team). `AGENT.md`: what to expect with several instruments.
- **Docs:** skills / scripts / runs READMEs, open items 4n (Y / parallel) and 4o (more instruments).
- **`fe_tech_test.py`:** C&F's insert group 3922.65 (SLB's D05, operator's explain.md list) - the technical test can run for `cap`.
- **Tests:** 15 new checks (reconciliation, break tracking, refusals, `dbconf-only`, the two skills' sync checks).

### 2026-10-09 (3) — technical test: portfolio property by branch group and sub-product, DEAL_ID, QR prices columns, process calendar

`[operator, 2026-10-09]` `FK_PORTPROP` is the PK of a portfolio property (`BOX_ACC.T_BOX_ACCT_PORT_PROP_S`, SIGOM
Portfolio Properties) whose `FK_BRANCH` is the branch **group**; the columns of `PGT_MRK.T_PGT_QUOTE_PRICES_S`;
`BOX_FE.T_BOX_BRPROCCAL_S` = `FK_BRANCH` (branch PK) + `DATETOPROCESS`.

- **`scripts/fe_tech_test.py`:** new input `branch_group_pk` (NY 21447.4). `sql/50`: the branch's group, the portfolio
  properties of the group (candidates), how trades in BOX carry them, the update, a check per trade (`NO PORTPROP` /
  `OTHER GROUP` / `NO REFERENCE` / `OK`); `FK_PORTPROP` and `REFERENCE_ACCOUNTING` asked separately. `sql/20`: the
  given date column (until then PUBLISHDATE and SETTLEDATE counted side by side), optional `quote_prices_filter`, DEV
  counts before / after, ORA-00001 / ORA-02291 recorded never forced. `sql/30`: the process calendar by `FK_BRANCH` +
  `DATETOPROCESS` (OK / MISSING + the month) - no longer an OPEN point. `sql/60`: the sql/50 check before the insert
  group.
- **From `p_Import_Deal_Data` (operator's screenshots) and the Tier 1 queries:** MERGE on `FRONT_ID` + `SOURCESYSTEM`
  + `DIRECTION` (one row per leg), `DEAL_ID` = `FRONT_ID` `.` the source system's PK - the update and checks key on
  the trades' `FRONT_ID`; its filters (process date, label's book, `DATA_EXECUTION_TYPE` = `BOOK`, maturity + 5) in
  `sql/30`; no status filter (the `BoValidated` OPEN reduced to "does c_Deal filter on a status?"); every column from
  `BOX_TRD.T_BOX_DEAL_S` is NULL under the bypass and reset by a re-run of 2629.65 - new `bypass.extra_fields`, a
  run-card note, the NULL-argument functions to suspect on ORA-20001 in `sql/40`; flow checks by `FRONT_ID` +
  `PROCESSDATE`; NY's DEV = DGBOUS (template). The portfolio property's `FK_INSTRUMENT` is the sub-product
  (`PGT_SYS.T_PGT_SUB_PRODUCT_S`; depos 2.4, IRS 20092.4, else `sub_product_pk`), `STATUS` Valid, `DESCRIPTION`
  Trading / Hedging + sector - candidates by group + sub-product, check adds `OTHER INSTRUMENT` / `NOT VALID`;
  `REFERENCE_ACCOUNTING` = the deal's own `DEAL_ID` on the SLB trade, a contract reference on Madrid's - asked, the
  answer `DEAL_ID` sets `TO_CHAR(DEAL_ID)`.
- **NY's test in DGBOUS (operator):** 24/09/2026, two ALCO trades (label XNY02), RAW already in DGBOUS, the join
  already LEFT. New inputs `raw_in_dev` (-> `sql/10-DEV-raw-check.sql`, no PROD extract; RAW `DEAL_STATUS` column),
  `bypass.join: already-left` (-> `sql/40` only the check, no rollback), `reference_group_pk`; market data rows by the
  trades' `FRONT_ID` by default; `sql/50` finds the portfolio property (2: group + sub-product Valid; 2b: what the group
  has; 2c: the reference group's shape to create); `sql/20` counts in DEV too. New
  `runs/NY_SCH/tier2-dev/tests/technical/tech-test-inputs.NY_SCH.json`; `new_run.py` points to a branch's inputs file
  of the area and lists an fe-jobs environment's gaps on every run.
- **QR prices copied to DGBOUS (PUBLISHDATE / EXPIREDATE 24/09/2026):** `quote_prices_in_dev` ->
  `sql/20-DEV-quote-prices-check.sql` (count, EXPIREDATE range, per quote type), no PROD extract; NY: PUBLISHDATE.
- **`REFERENCE_ACCOUNTING` found by queries:** `sql/50` 3a (its kind per portfolio-property group, source system,
  instrument: DEAL_ID / FRONT_ID / other + length, with an example), 3b (its origin `T_BOX_DEAL_S.ACCOUNTING_REF` vs
  `BO_CODE`), 3c (type and length), 3d (the code that reads it) - in PROD and DEV; the agent proposes.
- **Portfolio property for FE only (operator):** NY's group 21447.4 confirmed in DGBOUS; no NY portfolio property in
  BOX_ACC yet (sigom-box-acc-configs creates them from GBO's `PGT_ACT` ones) and FE does not read it -> new
  `bypass.portprop_scope: any`: `sql/50` query 2d lists any Valid one of the instrument (the reference group's first),
  the check drops `OTHER GROUP`. NY inputs set to `any`.
- **Data / docs:** template inputs, `SKILL.md` (rules, how to run, failure modes), eval case, open item 4m.
- **Tests:** the technical-test check extended (group-keyed candidates, calendar query, both date columns counted).

### 2026-10-09 (2) — versioned runs, scheduling monitor, the FE technical test skill

`[operator / BOX job expert, 2026-10-09]` Runs must never overwrite each other and the environment is asked; the
scheduling monitor (2935.65, fills `T_BOX_BRPROCCAL_S`) was missing; the priority is the FE technical test in DEV.

- **New `scripts/new_run.py`:** `runs/<BRANCH>/<tier>-<env>/<area>/<name>_<YYYYMMDD>_<n>/`, `RUN.md`, `RUNS.md`,
  `--freeze` / `--list` / `--from`; a new environment listed with what it lacks. `build_fe_jobs.py` refuses a frozen
  run (`run-frozen`).
- **`build_fe_jobs.py`:** prerequisite folders `select: instruments` (no FE job waits for them; another instrument's
  wait inherited); `group_map` (target and per prerequisite) and `target.local_group_suffix` (`local-group-unmapped`);
  `unix.existing_scripts`.
- **New skill `box-fe-technical-test`** (`scripts/fe_tech_test.py`, template, eval case) and
  `docs/reference/box-fe-static-aliases.csv` (the aliases `c_Deal` / `p_Import_Deal_Data` resolve, per source).
- **Data:** NY inputs (`prerequisites[1]` scheduling monitor, `local_group_suffix`, `existing_scripts`), template,
  registry (Madrid / SLB `prereq_controlm_repos` + `cib-boxfin-mdschedulmonitor`).
- **Docs:** charter (run folder, scheduling monitor), NY prompt (Step 2a environment + versioned folder, any
  instrument, Step 6b freeze, the scheduling monitor repo), `runs/README.md`, agents / skills / scripts READMEs, run
  README, open item 4m.
- **Tests:** 6 new checks (new_run, frozen run, scheduling monitor and `local-group-unmapped`, technical test pack and
  its frozen refusal) + the skill sync checks. All earlier checks unchanged.

### 2026-10-09 — `box-fe-jobs-agent`: excluded books, Unix package as Tier 1's, target-repo PR, the all-instruments gaps

`[operator / BOX job expert, 2026-10-08/09]` The depos rerun looked good; to fix: no jobs for XNY07, XNY09, XNY18, XNY19
(labels kept); `job_unix.sh` as the Tier 1 CDS package (delete + add, NY's copy of `delete_jobsBX.ksh`); the target
repos created (`cib-boxfin-t2usnyfe`, `cib-boxfin-t2nyloadprices`, `cib-boxacc-t2usnyac`) — PR of
`projects/<repo>.json` after the operator's yes. The all-instruments run (Devin) showed old-named per-book jobs, weak
look-alikes, no way to record "drop, to review".

- **`build_fe_jobs.py`:** `books-excluded.csv`; old-named per-book jobs → the template book's step (label + group);
  `DROP-REVIEW`; look-alikes via `explain_job.lookalikes` (same group with J-E4b constants / same script / same
  function + argument; "no confident match"); `template_book` per instrument in a one-instrument run; sed-safe
  banners; the full Unix package.
- **`unix_package.py`** rewritten: `job_unix.sh` in the expert's layout, `db_nuevo.conf`, `db_delete.txt`, the target's
  `delete_jobsBX.ksh` / `add_new_jobs.ksh` from `runs/_reference/<env>/unix/`.
- **New `stage_target_pr.py`** and **ADR 0012** (the one exception to read-only). **`explain_job.py`:** `--target`,
  `load_constants`, `lookalikes`.
- **Data:** registry NY row (target repos), `runs/NY_SCH/tier2-pre/books/books-excluded.csv`, NY inputs
  (`target_repo`s, `/gmny/etc`, `books_excluded`), template.
- **Docs:** charter (hard rule 1 exception, inputs, outputs `unix/` `pr/`, the three gaps, checkpoint 4b), NY prompt
  (Step 2a fresh run, Step 6a, Step 7 PR), skills `explain-box-job` (`--target`) and `set-up-book-labels`
  (`books-excluded.csv`), agents README, chain doc (`delete_jobsBX.ksh`), run README, open item 4l, eval case.
- **Tests:** 4 new checks (excluded books + old book jobs + DROP-REVIEW, unknown excluded book, look-alikes by group, PR staging), 2 rewritten (Unix package). All earlier checks unchanged.

### 2026-10-08 — `box-fe-jobs-agent`: every instrument in one run, Initial Accounting jobs, Unix package

`[BOX job expert via operator, 2026-10-08]` Second review of the NY outputs: (1) the Initial Accounting jobs (group
`2409.65`, one per instrument, ACC Control-M folder, run from `db.conf`) are missing — the FE agent writes their
`db.conf` lines and hands them to `box-acc-jobs-agent`; (2) `OrderMethod` PRO `JAC1400` (Mexico's, NY time zone),
PRE `ON DEMAND`, both folders — never SLB's `JAC0500`; (3) enhancement: the Unix package `job_unix.sh` (Tier 1 CDS
package). Operator: next run with every instrument; one package per agent.

- **`build_fe_jobs.py`:**
  - `instrument` may be a list: each instrument built into `out/parts/<instrument>/` knowing the others are built
    (their waits on each other kept), then merged (one set of outputs; a shared job once; `merge-differs` warning;
    final wait check across the merged folders);
  - Initial Accounting (`initial_accounting.group`): per instrument its core `db.conf` line (own banner), FE waits
    re-wired without a question (an instrument not in the run → dropped, listed), `out/acc-handoff.json`
    (draft ACC job from `reference.controlm_other`, `acc.*` values);
  - `OrderMethod` never copied from the reference (like `Host`);
  - `out/unix/job_unix.sh`.
- **New `scripts/unix_package.py`** (shared with the future ACC agent): `add_new_jobs.ksh`, `cp db_job` / `shell_job`,
  `chmod 755`; no delete step; etc folder missing → OPEN line.
- **NY inputs:** `instrument` = `depos irs ccs otc cap`, `template_book` per instrument, `OrderMethod`,
  `initial_accounting`, `acc` (asked), `unix` (`/gmny/scripts`; etc asked). **Plan:** all five `in progress`, run
  folder `fe-jobs/all/`.
- **Docs:** charter (inputs, rules, outputs, open questions 3 / 7 / 9 closed or changed, 10, 11), NY prompt (Step 2
  one run for all, Step 5b), agents README (the hand-off), chain doc (FE ↔ ACC, deploying conf changes, CDS in
  Tier 1), run README, open item 4k, eval case, scripts README, template.
- **Tests:** 5 new checks + 2 extended (several instruments, Initial Accounting `db.conf` lines, hand-off, Unix
  package, OPEN etc folder; `OrderMethod` to review / from the inputs). All earlier checks unchanged.

### 2026-10-07 — `box-fe-jobs-agent`: the core `db.conf` call, modelled on Mexico

`[BOX job expert via operator, 2026-10-07]` Mexico's `db.conf` (first 30 lines read) is the model for NY's
`PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup` lines, with two corrections: the **branch PK on every line**, also the
per-book ones (Mexico passes NULL), and **`P_TIME` = `to_char(sysdate,'RRRR-mm-DD HH24:MI:SS')`** (Mexico repeats the
date).

- **`build_fe_jobs.py`** (`pgt_prg` format): branch = `target.branch_pk`; `CST_PK_VACIO` → `NULL`; vstatic by value
  (`0`); time = `target.core_time` (default above); label `NULL` at branch level; sub-label `NULL`. New refusal:
  `target.branch_pk` missing. The "check with the BOX Lead" note is gone (settled).
- **NY inputs:** `branch_pk` `20007.4` (`cst_pk_bra_nysch`, J-E4), `core_time`. Template too.
- **Docs:** charter (rule, checkpoint 3, open question 8 settled), open item 4j closed, `tier2-pre/README.md`, run
  README, prompt, eval case, scripts README. **Test:** the core-call check rewritten (per-book, generic and
  branch-level lines) + the `branch_pk` refusal.

### 2026-10-07 — `box-fe-jobs-agent`: the BOX expert's review of the first NY run (depos)

`[BOX expert review via operator, 2026-10-07]` plus the operator's answers (SLB descriptors `pre.json` / `pro.json`
for FE and load prices, `GMBX7LB15D11` read in the SLB folder file, Tier 1 / Tier 2 `MARKET DATA` lines, package
constants, `PGT_PRG` spec; the reference for NY is SLB, not Mexico; NY calendar `CALC-USA`).

- **`build_fe_jobs.py`:**
  - instrument scope + inheritance + OR-groups — `GMBX0NY01D03` now waits for `D02`, not for the copied `GMBX6/7…D11`;
  - events renamed anywhere (`-NOK` of `If` blocks);
  - ended rule with descriptor `Delete`s;
  - descriptors of every entry type, per environment (`controlm.env`), both folders, mandatory Host / server flagged;
  - Data Lake `IAUKI` / `PAUKI`;
  - sibling-based rename suggestions;
  - `keep-reference-event`;
  - `dbconf_format: pgt_prg` (core call);
  - GBO look-alikes ranked by first argument value.
- **`parse_job_confs.py`:** decodes `PGT_PRG.Pkg_BatchProcess.p_ExecuteGroup` (8 arguments); new last column `time`.
  `f_ExecuteGroup` decoding unchanged (Tier 1 counts unchanged — check on the operator's copy).
- **NY inputs** (`fe-jobs-inputs.NY_SCH.json`):
  - DEV host `bvmnglapgbod101.nngg.corp` in the folder file, PRE / PRO hosts in `controlm.env`;
  - `CALC-USA`;
  - `pgt_prg`;
  - constant values;
  - answers: `GMBOX0114D01` → `GMBX1NY00D01`, `GMBOX0028D01` → `GMBX1NY00D02` (+ its event),
    `GMGB1420D01-OK` → `GMNY0011D01_PR-OK`, `GMGB1420D02-OK` → `GMNY0012D01_PR-OK` (event name INFERRED).
- **Docs:** agent charter (rules, inputs, suggestions, checkpoint 3, open questions 5, 8, 9), NY prompt (merge an
  earlier run's inputs; re-parse the job confs), inputs template, run README, `tier2-pre/README.md`, chain doc, eval
  case, scripts README.
- **Tests:** 9 new checks (scope, `-NOK`, built instrument, core call, sibling rename, KEEP refusal, descriptors with
  and without per-environment values, `p_ExecuteGroup` parsing). All earlier checks unchanged.
- **Unchanged:** `box-batch-jobs-agent`, `sigom-box-fe-configs-agent`, `sigom-box-acc-configs-agent`, `find_jobs.py`,
  `explain_job.py`.

### 2026-10-07 — `sigom-box-acc-configs-agent` phase 1: the BOX ACC gap run

`[stated: operator, 2026-10-07]` Scope rules (only branch-dependent configs; topics and events global, event grouping
global or a branch copy — ask; cross account config and global accounts from GBO; portfolio properties never from GBO
— GBO topics; a GBO → BOX topic mapping exists, not seen yet) and the Confluence checklist of the eleven BOX -
Accounting SIGOM screens with the SIGOM trace queries.

- **ADR 0011** — the scope, per screen; phase 1 = read-only gap run, phase 2 = rendered SQL after the evidence.
- **Agent charter rewritten** (`agents/sigom-box-acc-configs-agent/AGENT.md`): goal, definition of done, the screens
  table (keying, action, source), order, inputs, hard rules, checkpoints; the confirmed facts kept (keying per object,
  `f_GenTopicCond`, the shared bridge, pre-commits, never-supply columns, grants).
- **New:** prompt `prompts/tier2-gap-run.md` (NY_SCH, self-starting), template `templates/acc-gap-matrix.md.tmpl`,
  query catalogue `docs/reference/queries/acc-config-mining.md` (A-G1-3, A-01-A-11, from the SIGOM traces), run folder
  `runs/NY_SCH/tier2-pre/acc-configs/` (README, inputs), eval case.
- **Docs:** add-product checklist §0 (the eleven screens for a new branch + corrections), agents README (and the
  planned `box-acc-jobs-agent` for MBJ), agent-architecture, procedures 03 / 05 status lines.
- **Unchanged:** the FE configs agent, the jobs agents (their charters still name this agent for MBJ rows — updated
  when `box-acc-jobs-agent` is built), all scripts and tests.

### 2026-10-07 — NY's Tier 2 job confs

`[operator, 2026-10-07]` NY's Tier 2 `db.conf` / `shell.conf` obtained (1,600+ lines; screenshots read). Parser handles
them unchanged (`_PR` suffix, `T:P` flags, nested date functions, duplicates flagged; tested on sample lines).

- **New:** `runs/_reference/tier2-pre/README.md` — where to put them, how to parse, what they show (`GMNY…_PR` = NY's
  GBO jobs; `PGT_NY.f_ExecuteGroup` with 5 arguments, corroborating J-E10; branch constants `NYSCH` and `NYIBF`).
- **`build_fe_jobs.py`:** with `target.env_folder`, a generated name already in the target's job confs is refused
  (`target-name-exists`). Test added.
- **NY inputs:** `target.env_folder = runs/_reference/tier2-pre`. **Prompt:** parse it first when needed. Open item 4d.

### 2026-10-06 — instruments in one place; reference per instrument; Data Lake waits per book; GBO look-alikes

`[stated: operator, 2026-10-06]` After the NY deposits run: (1) the instruments were asked again — they are known from
gate 0c (six, CCS included); CDS is not run by SLB; (2) `cib-auki-aukicnfgsrvc` and `cib-auki-aukictrlmcntrm` are in
another organisation — copies kept in the repo; (3) in PRO each book waits for its book's Data Lake job
(`G010012-PAUKISCIB…`); (4) a GBO wait (`GMGB1420D01`, currency pairs) should come with what it does and NY's
equivalent (`GMNY0011D01_PR`).

- **Registry:** columns `display`, `instruments` (NY: `irs|depos|ccs|otc|cap|cds`, gate 0c). The NY prompt reads them —
  never asks the list again.
- **`find_jobs.py`:** `--references` (which onboarded branch runs a product); product `cds` (by `CST_PK_CDS`).
  Default behaviour unchanged.
- **`build_fe_jobs.py`:** `datalake.*` — per-book Data Lake waits mapped by label description = `book_vr`
  (`datalake-book-unmapped` with closest books; `datalake-link-unverified` warning); `target.env_folder` — GBO look-alikes
  in `pending-questions.md` (INFERRED); descriptor entries of other reference books covered by the template book's.
- **`explain_job.py`:** shows the conf call of a job that runs no group.
- **NY prompt:** reference branch per instrument (registry row → `reference.*`); copies under `runs/_reference/external/`;
  J-E4 / J-R3b reused across instruments. **New:** `runs/_reference/external/README.md`.
- **Skip / force an instrument** `[stated: operator, 2026-10-06: "CDS are still not in BOX for Madrid / SLB"]`: new
  `runs/NY_SCH/tier2-pre/fe-jobs/instrument-plan.csv` (status `to build` / `in progress` / `done` / `skip`, forced
  `reference`); CDS = `skip`. The prompt never builds a `skip`, proposes `skip` when no branch runs the instrument, and
  removes skipped instruments from `target.instruments`. `nothing-to-copy` now says so. The registry list is unchanged
  (scope for the SIGOM configs).
- **Docs:** agent charter, skill `find-box-jobs`, chain doc (Data Lake and GBO waits), Data Lake doc (NY file, `book_vr`
  link), repo index, NY open items 4d / 4h / 4i, inputs (NY + template), evals. Tests: 4 new; all earlier unchanged.

### 2026-10-06 — load prices run first; environment descriptors (PRO-only waits)

`[stated: BOX dev via operator, 2026-10-06]` Before the FE batch, the load-price jobs run (`cib-boxfin-t1mdloadprices`,
Madrid and SLB, two jobs per branch, `db.conf` groups). The FE batch waits for `GMBOX0026D04-OK` **only in PRO**, added by
`cib-auki-aukicnfgsrvc/cib-boxfin-t1mdslbfe/pro.json` (`DeployDescriptor`); not in PRE because FE / ACC are not automated
there (ideally they would be). NY: folder `JACD-T2NYLOADPRICES-BOX_FE-100068124`, jobs `GMBX0NY00D01` / `D02`, same
Control-M values as NY's FE folder.

- **`build_fe_jobs.py`:** `prerequisites[]` → `out/<PREREQ_FOLDER>.json` first (only the jobs the chain waits for and
  theirs: the other branch's left out; old names → `GMBX0<TT>00D01`… in chain order), their `db.conf` lines first under
  their own banner. Descriptors (`reference.descriptor_dir`, `prerequisites[].descriptor_dir`) read as waits and
  re-pointed to `out/descriptors/<folder>/<env>.json`; the folder file keeps no PRO-only wait (as the reference);
  entries with a reference environment value or for one book → review. Duplicate target names refused
  (`target-name-duplicate`) with the next free name in `pending-questions.md`; a GBO event with no emitter → "ask the
  GBO team". Without `prerequisites` the build is unchanged. Tests: 5 new.
- **Docs:** agent charter (goal = 3 outputs in run order + descriptors, inputs, rule 1, checkpoint 4, open question 4),
  NY prompt (attach `cib-boxfin-t1mdloadprices` + `cib-auki-aukicnfgsrvc`; the queue-job name conflict), inputs (NY +
  template), branch registry (`prereq_controlm_repos`, `env_descriptor_repo`), chain doc L1 + §7.9, repo index, skill
  `explain-box-job` (descriptors not in its card), eval case.
- **`box-batch-jobs-agent`:** unchanged.
- NY prompt resumes an earlier run: keeps the existing inputs file and adds the missing keys; skips a query whose CSV
  is already in `01-evidence/`.

### 2026-10-06 — "what does job X do?" mid-run; every rename / external-event question comes with context

`[stated: operator, 2026-10-06]` "i would have liked to be able to ask questions like 'what is job GMBOX0028D01
doing?'" + "do not remove box-batch-jobs-agent … i dont want any regression".

- **New skill `explain-box-job`** + **`scripts/explain_job.py`**: one job at overview depth, 0 queries — Control-M
  folder / file:line / `When` / waits / emits from every folder repo given (FE and ACC), the executed `db.conf` or
  `shell.conf` binding, the group and its events by name from the repo DML (newest `rX.Y.Z`); ACC group via `--mbj`
  (J-R2 export) or "ask J-R2". Eval case `explain-box-job.md`.
- **`build_fe_jobs.py`:** on `rename-missing` / `external-event-unmapped` writes `<run>/pending-questions.md` — emitter,
  folder, what it is, side · product · level, suggested answer (approved instrument → target name; not approved / ended
  / ACC → `DROP`; GBO → ask the GBO team; not found → ask the BOX team; rename → `GMBX<n><TT>00D<ss>`). New optional
  inputs `reference.controlm_other`, `reference.dml_repos`, `reference.mbj_csv`, `target.instruments`. Existing
  inputs files keep working; build output unchanged.
- **`box-fe-jobs-agent`:** asks the pending rows one at a time with their suggestion; answers "what does job X do?"
  mid-run with the skill and repeats the question. NY prompt attaches `cib-boxacc-t1mdslbac` + `cib-boxacc-dbboxacc`.
- **`box-batch-jobs-agent`:** unchanged — one optional row in its skills table; EXPLAIN procedure, depths, prompts as tested.
- Tests: 7 new (pending card, rebuild after answers, explain FE / ACC / MBJ, 2 refusals); all earlier tests unchanged.

### 2026-10-06 — NY's Control-M folder values; FilePath, ended jobs, documentation file, host config repo

`[stated: operator, 2026-10-06]` NY PRE: folder `JACD-T2USNYFE-BOXFE-100068124`, server `GCB.GCB-D-D023`, site standard
`…CIB-BOXFIN`, `Manual`, host `bvmnglapgboi111.nngg.corp` (PRO `…bop111…`, applied by `cib-auki-aukicnfgsrvc`), `FilePath
/gmny/scripts`, `RunAs gmny`, application `G-GBMSA-D-100068124_Des`, calendar `CALC-USA`, documentation file as SLB;
`CreatedBy` asked. SLB headers read: some jobs carry `When.EndDate` (ended).

- **`build_fe_jobs.py`:** `FilePath` is an environment input; optional `DocumentationFile`, `host_config_repo` /
  `host_by_env` (report hand-off); reference jobs with a past `EndDate` are not copied (waits on them become external);
  a future `EndDate` is dropped (warning); `FromTime` values listed for review. Test extended.
- **Inputs:** NY's pre-filled (`fe-jobs-inputs.NY_SCH.json`); example template. **Docs:** agent charter (inputs, rule
  4), NY prompt, chain doc L1, repo index (`cib-auki-aukicnfgsrvc`), NY fe-jobs README.

### 2026-10-05 (note) — Tier 1's `PGT_SYS.F___SEQUENCE` is the same code

`[operator]` Same 53 lines in Tier 1; Tier 1 labels still carry `.21` → the fraction is added after the call in both tiers, as the label proposal now does. Q-10h evidence, skill rule.

### 2026-10-05 — `PGT_SYS.F___SEQUENCE` never adds the auth code: the label proposal adds it

`[read: operator, Q-10h, Tier 2]` `PGT_SYS.F___SEQUENCE(Table_Name, Seq_Range, SigomSeq)` returns `SPK_<TABLE>.NEXTVAL`
and ignores `Seq_Range` — `'X'` gave `24042`. It is not `BOX_FE`'s function. The label proposal now reads `AUTH_CODE` from
`GOM_GLB_SYS.T__CORE_INFO_S` (stops if it is not the run's, 44), adds `auth / 10^len` to the sequence value, checks the
PK is unused, inserts, calls the pre-commit. Skill rule, Q-10h result + evidence, Q-10g note, test.

### 2026-10-05 — branch-agnostic audit: no reference-branch value in a generic file's logic

`[stated: operator, 2026-10-05]` "remember we want to build agents that are branch agnostic." Audit of charters,
skills, scripts and query catalogues: worked examples and dated evidence stay (labelled); **values that would be used
for another branch** are now parameters or registry rows.

- **New:** `docs/reference/branch-registry.csv` (branch, aliases, env, token, `db.conf` constant, wrapper, FE / ACC
  Control-M repos) — `find_jobs.py --branch` reads it; a new branch is a row, not code.
- **Parametrised:** Q-13 (b) (`20087.4` → `&&REFERENCE_BRANCH_PK`), Q-10d (a) (`26391.4` → `&&REFERENCE_DUMMY_LABEL_PK`,
  + the operator's dummy card), Q-05d comments, the `Env: REF` rule, Q-05c header (fe-config-mining); J-E9's regex
  (box-jobs-queries); FE prompt input `REFERENCE_DUMMY_LABEL_PK`; fe-jobs example `env_folder`.
- **Charters/skill:** box-batch-jobs-agent and find-box-jobs point to the registry instead of listing Madrid/SLB
  tokens and repos; box-fe-jobs-agent inputs cite it.

### 2026-10-02 (run 7 issues) — Q-05d's GBO header; label PKs need `SEQ_RANGE = 'X'`

`[operator, 2026-10-02]` (1) Q-05d used `333105.21` (SLB's **BOX** header) on the GBO side too — the GBO header was a
placeholder no step resolved. (2) The label proposal stopped before inserting: `F___SEQUENCE(…, SEQ_RANGE => 1)`
returned `24038` (no `.44`) — the fraction guard worked; the call was wrong (Q-G3: only `'X'` adds the auth code).

- **Q-05d:** `&&REFERENCE_GBO_MIS_HEADER_PK` from Q-G2 level 1 for SLB (Tier 1) and `&&REFERENCE_FE_CONFIG_PK`;
  the two must differ; prompt inputs + Order 4 step 2a.
- **Labels:** `SEQ_RANGE => 'X'`; new guard: the allocated PK must be unused; Q-10g correction; new Q-10h (read
  `PGT_SYS.F___SEQUENCE`, try `'X'` once). Test updated.

### 2026-10-02 (J-E10 results) — the engine takes the label in Tier 2; only `PGT_NY`'s wrapper does not

`[operator, 2026-10-02]` Tier 1 `PGT_ES` 7 arguments; Tier 2 `PGT_NY` / `PGT_BOS` 5, **`PGT_BRL` 7**; core
`PGT_PRG.PKG_BATCHPROCESS.P_EXECUTEGROUP` has `P_LABEL` / `P_SUBLABEL` in both tiers. The NY fix is a wrapper
pass-through, with a Tier 2 precedent.

- **New:** `runs/NY_SCH/tier2-pre/jobs/01-evidence/J-E10-label-args-BOTH.md`; J-E10 (d) (are the label arguments
  defaulted? `PGT_BRL`'s spec).
- **Updated:** J-E10 result, NY open item 1, environment profile, chain doc §7 Q1, `box-fe-jobs-agent` checkpoint 3.

### 2026-10-02 (note) — J-E10: who takes a label

New query J-E10 (`ALL_ARGUMENTS` for every `f_ExecuteGroup*` and every `P_LABEL` / `P_SUBLABEL`, both tiers, plus wrapper DDL dates) to settle NY open item 1.

### 2026-10-02 (note) — `build_fe_jobs.py` falls back to `books/00-books.csv`

When the books register is not written yet (labels pre-step not run), the FE jobs are built from the book list, with a warning. +1 test.

### 2026-10-02 (new agent) — `box-fe-jobs-agent` + skill `find-box-jobs`

`[stated: operator, 2026-10-02]` Keep `box-batch-jobs-agent` for searching; a new agent generates a new branch's BOX
FE jobs (`db.conf` + Control-M JSON) from a reference branch and an instrument; values not known yet (folder name…)
are asked by the agent. `[read: Devin]` SLB's deposits chain: per book `GMBX0LB<bb>D01-D03` → `GMBX1LB<bb>D04-D06`,
`D06` waits for the branch queue job `GMBOX0114D01` (`FromTime 2200`); cross-folder and GBO waits; `G010014-` events
with no consumer found.

- **New:** `agents/box-fe-jobs-agent/` (`AGENT.md`, `prompts/build-ny-sch-tier2.md`,
  `templates/fe-jobs-inputs.example.json`); `skills/find-box-jobs/SKILL.md`; `scripts/build_fe_jobs.py` (seed →
  same-folder closure → per-book copy → events re-wired → `db.conf` swapped → checks; refusals name the input to
  ask); ADR 0010; eval cases `find-box-jobs`, `box-fe-jobs-agent`; query J-R3b; `runs/NY_SCH/tier2-pre/fe-jobs/`
  (README, NY's known inputs). 9 tests.
- **Updated:** `find_jobs.py` (named refusals), `box-batch-jobs-agent` (PROPOSE FE → new agent; skill in its table;
  relationship), agents / skills / scripts READMEs.

### 2026-10-02 (repos) — SLB has its own Control-M folder repos

`[stated: operator, 2026-10-02]` FE: Madrid `cib-boxfin-t1mdesfe`, SLB `cib-boxfin-t1mdslbfe`; ACC: Madrid
`cib-boxacc-t1mdesac`, SLB `cib-boxacc-t1mdslbac`. `[read: Devin]` the JSON layout (folder header, per-job fields,
environment-specific values, `G010014-` events). Repo index, chain doc L1, jobs agent charter / explain / GAP prompt,
scripts README (SLB example uses `t1mdslbfe`).

### 2026-10-02 (run 7 + jobs tests) — pre-steps placed where they run; reference queries go to Tier 1; repo first for groups

`[operator, 2026-10-02]` FE run 7 went from the gates straight to mining (no P1, no labels pre-step), and asked
Q-05c (SLB, `333105.21`) in Tier 2 → 0 rows. Jobs agent tests "look pretty good"; group / event definitions are in
the BOX repos (`dml/03-PGT_PRC`).

- **FE prompt:** P1 and the labels pre-step are rows of Order 2 **right after Q-G3c** (what they need), plus a
  ⛔ status gate before Order 3 (`PRE-STEPS P1 … Labels …`); tier rule in *How you get data*; Q-05c in Order 4
  (Tier 1); Q-10d (a) cited, not re-asked. **FE charter:** reference queries run in the reference tier.
- **Catalogue:** new `Env: REF` tag + rule; Q-05c retagged.
- **Jobs agent:** groups and events read from the repo first (paths, file names, newest release wins), J-C queries
  confirm the environment; charter depth table, `explain.md`, J-C note.

### 2026-10-02 (note) — `XNY00` was never created

`[stated: operator, 2026-10-02]` The trace's test label was not saved in Tier 2; warnings removed from the NY books README and Q-10g evidence.

### 2026-10-02 (later) — start from the prompt file itself; dummy proposed as `<CC>DUM` / `<CC> EMPTY`

`[stated: operator, 2026-10-02]` "START.md looks like a workaround" — the prompts already exist; the dummy should be
proposed as `NYDUM` "NY EMPTY" (code max 5 characters).

- **Removed:** `START.md`. **Instead:** `explain.md`, `gap-ny-sch-tier2.md`, `tier2-full-run.md` start with *"type `Run
  automation/<path>`"*; when pointed at the file, Devin asks the empty inputs one at a time and checks the repos.
- **Dummy:** create proposes `<CC>DUM` / `<CC> EMPTY`; new refusal `dummy-code-too-long` (> 5 characters), +1 test.
  The test label `XNY00` in Tier 2: delete it. Skill, FE prompt card, NY books README / evidence / json, README.

### 2026-10-02 — labels as SIGOM saves them; the operator decides the dummy; agents start by asking

`[operator, 2026-10-02]` DB trace of a label saved in SIGOM `PGT - Label Config` (Tier 2): PK from
`PGT_SYS.F___SEQUENCE(TABLE_NAME => PGT_DOMAINS, SEQ_RANGE => 1)` (`24044.44`), insert of `PK, FK_OWNER_OBJ, CODE,
DESCRIPTION`, then `PGT_SYS.Pkg_SysPrecommit.p_DomainsPreCommit(PK)`. The dummy: the agent proposes, the operator
accepts or creates one (code + description). Testing should not need a pasted prompt.

- **Skill `set-up-book-labels`:** PK rule **`screen`** (default) reproduces the trace — allocate and check every PK
  for the auth code first, then insert + pre-commit; `auth_code` input; pre-commit now after every insert (all
  modes); new codes `book-label-auth-code`, `book-label-pk-auth-code`; no PK-rule card; dummy card to the operator
  (create → code `X<CC>00` proposed + description); proposal run by the operator. 4 tests.
- **New:** `START.md` — say "run the jobs agent" / "run the fe agent"; Devin asks the questions one at a time,
  checks the repos, then follows the prompt. Q-10g (the trace) in the catalogue and NY's `books/01-evidence/`.
- **Updated:** FE prompt (dummy card authority, 2b-2, applying), FE charter, 04-add-book §2.4, NY
  `book-labels.json` (`screen`, auth code 44; dummy still open) and README (test label `XNY00` left in Tier 2),
  `explain.md` / `gap-ny-sch-tier2.md` (pointer to START, ask unfilled fields), README.

### 2026-10-01 (list + order) — `find_jobs.py`: which jobs, and in what order

`[operator, 2026-10-01]` *"Give me all BOX FE jobs for Deposits for SLB branch and their order."*

- **New:** `scripts/find_jobs.py` — executed BOX jobs by side / product / branch from `jobs-inventory.csv` (old
  names found by their `db.conf` arguments), and with `--controlm` their order from the Control-M JSON events
  (level, folder, file:line, prerequisites outside the list, jobs not found). 2 tests.
- **Updated:** charter (LIST questions run the script; order via `--controlm`; skills table), `explain.md`,
  J-R4 (use the script), explain eval variant D, scripts README.

### 2026-10-01 (first EXPLAIN test) — depth levels, group-wide queries, list questions, robust Step 0

`[operator, 2026-10-01]` Test 1 (`GMBX4ES55D07`, Tier 1): Devin did not find the charter with `find /`, then asked for
60+ queries to walk every event of group `3275.65`.

- **Step 0** in all 7 prompts: tries `~/repos/cib-box-auki-nbranch/automation`, the working dir and git root, then
  `find`; nothing found → **ask the operator**, don't stop.
- **EXPLAIN depth** (charter + `explain.md`): `overview` (default, ≤ 3 queries: binding + events by name),
  `event <PK>`, `full`; always offers the next depth.
- **New queries** J-C3g / J-C4g: a whole group's entries / event queries in one (three) query(ies).
- **LIST questions** answered from `jobs-inventory.csv` with no query (FE/ACC by file, product by family or
  constant, branch by token or constant), with what the filter cannot see.
- **Eval** explain case: depth `full`; variants B (overview budget) and C (list question).

### 2026-10-01 (inventory regenerated) — family table confirmed from `db.conf`; 180 BOX jobs in both files

`[read: parser summary, Devin, 2026-10-01]` Each `GMBX<n>` passes one instrument constant (0 `VACIO`, 1 `DEP`,
2 `CES`, 3 `SWAP`, 4 `CCS`, 5 `CFM`, 6 `FRA`, 7 `OTC`, 8 `CAP`). 180 BOX jobs are in both files (the earlier 822
counted GBO too); executed BOX bindings: `db.conf` 2,640, `shell.conf` 701.

- Chain doc (counts, family confirmation, FE-only check of the 2,640), parser summary label, gap prompt (FE / ACC
  by group name), NY open item 4f, profile, reference README.

### 2026-10-01 (BOX dev answer) — ACC runs from `shell.conf` via MBJ, FE from `db.conf`; `GMBX8` = Cap & Floors

`[stated: BOX dev via operator, 2026-10-01]` ACC jobs used to run from `db.conf`; their lines are still there but
the `shell.conf` lines are executed. MBJ is for BOX ACC jobs only, not FE. `GMBX8` = CF (Cap & Floors).
The "50" Madrid MBJ rows was SQL Developer's first fetch page, not a count.

- **Parser:** new column `executed` (`N-legacy` on the `db.conf` row of a job in both files); summary prints the
  executed bindings per file; family 8 = cap & floor. Test updated.
- **Consequence:** NY's ACC jobs = `shell.conf` + MBJ row (no `db.conf`); NY's FE jobs = `db.conf` via `PGT_NY` —
  so the label problem (item 1, checkpoint 3) is now about **FE "by Book" jobs**.
- **Updated:** chain doc (L2 table, family 8, §1/§7 renumbered), agent hard rule 7, gap prompt, gap eval case,
  worked trace (L2 = legacy binding), data model, queries J-R2, sigom-reference, 04-add-book §2.3, NY open items
  1 / 4c / 4f, profile, Madrid evidence, reference README, scripts README.

### 2026-10-01 (inventory checked) — Tier 1 PROD job confs: 822 jobs bound in both files

`[read: Devin's jobs-inventory-check.md, operator screenshots]` The parser read both files completely (the
44-line gap is comment headings). Active BOX jobs: 2,821 `db.conf` (all `PGT_ES` `f_ExecuteGroup`), 701
`shell.conf` (637 `mbjbox.sh`). **822 job names are in both files**; family `GMBX8` (342 jobs) is unknown; 446
`ES` `mbjbox.sh` lines vs 50 Madrid MBJ rows.

- **Parser:** new columns `bound_in` (job in both files) and `dup_in_file`; summary prints both counts and, per
  `GMBX<n>`, the `db.conf` instrument constants (checks the family table). +1 test.
- **Chain doc:** Tier 1 PROD counts, the dual-binding warning, family 8, §7 Q6–Q7. **Worked trace** GMBX3ES02D07:
  caveat (also in `shell.conf`). NY open items 4c, new 4f, 4g; profile; scripts README; reference README.

### 2026-10-01 (wrap-up) — MBJ table structure; reference conf files stay on the operator's side

`[operator, 2026-10-01]` `DESCRIBE BOX_ACC.T_BOX_MBJ_PROPERTIES_S`: 32 columns, NOT NULL `PK` and `MIC_EOD`;
5 columns the screen does not declare (`FK_EXTENSION`, `FK_CALENDAR`, `RECOVER_*` ×3); `RETURN_DATA` ∈ {0, 1}.

- **New:** `runs/NY_SCH/tier2-pre/jobs/01-evidence/J-R2b-mbj-properties-describe.md`.
- **Updated:** data model (columns, NOT NULL, calendar never copied), J-R2 (extra columns + flag profile +
  calendar queries), J-T8 evidence, NY open item 4e, ACC agent's MBJ row.
- **Removed from this copy:** `runs/_reference/tier1-prod/mbjbox.sh` (transcription) and `EXTRACTED.md` — the
  operator holds the real `db.conf`, `shell.conf`, `mbjbox.sh` there; the delivered zip no longer overwrites them.

### 2026-10-01 (close) — J-T8 passes in Tier 2; GAP prompt brought up to date

`[operator, 2026-10-01]` The MBJ Config screen object `35000182.65` (*BOX - MBJ Properties*, module
`35000006.65`, no pre-commit, 25 fields) is identical in Tier 1 and Tier 2.

- **New:** `runs/NY_SCH/tier2-pre/jobs/01-evidence/J-T8-mbj-screen-object-BOTH.md`.
- **Gap prompt:** job confs marked required before pasting; two set-ups (`mbjbox.sh` + MBJ row vs `db.conf`);
  checkpoint 3 limited to `db.conf` "by Book" jobs; Tier 2 Unix question; J-E9.
- **Updated:** J-T8 result, data model, NY open item 4e, profile.

### 2026-10-01 (late) — MBJ jobs run through `PKG_BATCHPROCESS_MBJ`; two new checks

`[stated: operator / BOX dev, 2026-10-01]` The jar calls `PKG_BATCHPROCESS_MBJ` (not the branch wrapper), so
NY's `mbjbox.sh` jobs are **not affected** by `PGT_NY`'s missing label. `INSTANZE` is always `AUKI`;
`FK_PARENT IS NULL` filters nothing (child-row query dropped). Tier 2 US: `T_BOX_MBJ_PROPERTIES_S` empty.

- **New queries:** J-E9 (`PKG_BATCHPROCESS_MBJ` in both tiers: status, version, branch-specific code), J-T8 (the
  MBJ Config screen object `35000182.65` in `GOM_GLB_SYS.T__OBJ_DEF_S`, both tiers).
- **Updated:** J-R2, J-X4, data model, sigom-reference, chain doc L2 + §7, NY open items 1 / 4b / 4e, profile,
  Madrid evidence, ACC agent's MBJ row.

### 2026-10-01 (night) — MBJ Config screen query read; `0000` = time

`[read: operator screenshot, Tier 1]` The SIGOM `MBJ Config` query: `T_BOX_MBJ_PROPERTIES_S` joined to branch,
sub-product (instrument), event group, label and sub-label (`PGT_DOMAINS`); filter branch, `FK_PARENT IS
NULL`, `FK_OWNER_OBJ = 35000182.65`. Madrid: 50 job-level rows; `D07` = Accounting General by Book, `D09` = MtM /
Reval by Book. `[stated: BOX dev]` `mbjbox.sh`'s 3rd argument is the time, always `0000`.

- **New:** `runs/NY_SCH/tier2-pre/jobs/01-evidence/J-R2-mbj-properties-madrid-REF.md` (8 visible rows, book
  names not copied).
- **Updated:** `box-data-model.md` (full column list), `sigom-reference.md` (screen query; off-screen columns
  resolved), J-R2 (the screen query, generic, + child rows), chain doc (families 4/6/7 confirmed, D07/D09,
  `0000`, lead `PKG_BATCHPROCESS_MBJ`), NY open items 4b + new 4e, profile, ACC agent's MBJ row,
  `parse_job_confs.py` family comment (7 = OTC option).

### 2026-10-01 (end of day) — confirmed: `mbjbox.sh` jobs are driven by `T_BOX_MBJ_PROPERTIES_S`

`[stated: BOX dev via operator, 2026-10-01]` `mbjbox.sh` (through `MBJBOXACC.jar`) uses
`T_BOX_MBJ_PROPERTIES_S` for its jobs. So those jobs get their book from their MBJ row, not from a wrapper
argument: the Tier 2 "no label in `PGT_NY`" problem narrows to `db.conf` "by Book" jobs.

- Chain doc L2, §6 (Devin's "not read by any code" now marked wrong) and §7 Q1–Q2; queries J-E6, J-R2, J-X4;
  NY open items 1, 4b, 9 and profile; 04-add-book §2.3. Still open: what the jar calls in the database,
  whether Tier 2's Unix has it, the meaning of `0000`.

### 2026-10-01 (later) — `mbjbox.sh` read: a launcher for `MBJBOXACC.jar`

`[read: operator screenshot of the Tier 1 PROD script]` `mbjbox.sh` holds no binding: it runs
`java -jar MBJBOXACC.jar <JOB> <ODATE> 0000` from `/appl/gm/bin/GBOCL_MBJBATCH`, config `conf/BOX`, log per job
and date. The MBJ-properties question moves to the jar.

- **New:** `runs/_reference/tier1-prod/mbjbox.sh` (transcribed), `EXTRACTED.md`; query **J-X4** (jar source,
  `conf/BOX` file list, one PROD log).
- **Updated:** chain doc L2 (what the script does) and §7 Q2; J-X3; NY open item 4b and profile;
  04-add-book §2.3; the reference README.

### 2026-10-01 — jobs live in `db.conf` **and** `shell.conf`; inventory script

`[stated: operator, 2026-10-01]` Tier 1 PROD `db.conf` (database jobs) and `shell.conf` (Unix scripts) hold
every job running for Madrid and SLB; Devin sessions can read the BOX repos; old BOX jobs keep old names
(new ones follow `GMBX…`); BOX has product chains **and** generic jobs for all products.

- **New:** `scripts/parse_job_confs.py` → `jobs-inventory.csv` (BOX by name, `mbjbox.sh`, BOX schema or
  banner; name decoded; `f_ExecuteGroup` args); `runs/_reference/tier1-prod/README.md` (where to save the
  files, unchanged); 4 tests.
- **Chain doc L2:** two files, `mbjbox.sh` jobs take their binding from `T_BOX_MBJ_PROPERTIES_S`
  `[inferred]` — a possible answer to the Tier 2 label question; old names; product vs generic; the
  `GMBX<n>` family table (CAP/CDS unknown).
- **Jobs agent:** `JOB_CONFS` replaces `UNIX_EXTRACTS`; repos list adds `cib-boxfin-mdschedulmonitor`;
  matrix gets kind / level / conf_file; hard rule 7 = BOX whatever the name, new names only. Queries J-R1,
  J-R2, J-T5 re-pointed; J-X3 (`mbjbox.sh`) added. Gap prompt, NY open items 4–4d, profile, 04-add-book
  §2.3, scripts README, gap eval case, `runs/README.md` updated.

### 2026-09-30 (end of day) — book setup becomes a skill: `set-up-book-labels`

`[stated: operator, 2026-09-30]` *"its going to be better to fix issues if its a skill. and its not only
related to sigom box fe configs."* [ADR 0009](docs/decisions/0009-book-labels-skill.md). The book labels
(yesterday's FE pre-step P3) **and the dummy label** (P2) are one skill with one script and one PK rule.

- **New:** `skills/set-up-book-labels/` (`SKILL.md`, `book-labels.example.json`,
  `templates/book-labels-proposal.sql.tmpl`), `scripts/set_up_book_labels.py`, two eval cases. Its folder
  `runs/<BRANCH>/<env>/books/` spans runs: book list, `book-labels.json`, decisions, evidence; outputs the
  **book register** (`books-register.csv`), the report and — when labels are missing — the proposal SQL.
- **FE renderer:** P2 and P3 removed (and their templates); P1 stays. Step 11 now re-evaluates `books/`
  through the skill's script: `book-setup-missing`, `book-setup-invalid`, `book-labels-pending`,
  `book-labels-disagree`; `values.json` `prechecks` is refused (`values-moved`). The fixture has a `books/`
  folder.
- **Skill `resolve-fe-config-prechecks`:** P1 + the step-11 gate only. FE kickoff, charter, templates README,
  `values.example.json`, catalogue (Q-10c/e/f), walk notes, and the jobs agent (reads the register; J-T3)
  re-pointed. NY: `00-books.csv` moved to `runs/NY_SCH/tier2-pre/books/`; `book-labels.json` seeded (dummy and
  PK rule not decided yet). Open item 7c closed.
- **Tests:** 155 — the P2/P3 renderer tests became skill tests, plus the step-11 gate; the skill-sync check now
  reads the script(s) a skill names.

### 2026-09-30 (later) — FE pre-step P3: book labels checked, missing ones proposed as SQL

`[stated: operator, 2026-09-30]` The FE agent gets a third pre-step: ask for the branch's books, check
their BOX labels exist, and generate the inserts for the missing ones. Step 11 = one row per branch ×
approved instrument × book (**every book for every instrument**) plus the dummy row per instrument — the
renderer already wrote that shape; it now also checks the books are exactly the list's labels. Job names:
`GMBX3ES02D07` (book `XES02`) ↔ `GMBX3NY02D07` (book `XNY02`) — stated, no longer inferred.

- **Renderer** (`render_sql.py`): reads `00-books.csv` (as written — descriptions must match exactly) and
  `01-evidence/Q-10f-book-labels-target.csv`; found labels give their PKs; missing ones render
  `<BASE>-P3-book-labels-PROPOSAL.sql` (template `precheck-book-labels.sql.tmpl`): one block that stops,
  inserting nothing, if any code / description / fixed PK already exists; no COMMIT. The PK rule is the
  BOX FE team's (card 7): `fixed` (PKs in `00-books.csv`) or an allocation `expression`. New refusals:
  `book-label-code-bad`, `book-label-conflict`, `book-labels-rule-missing`, `book-label-pk-rule`,
  `book-label-pk-missing`, `book-label-owner`, `book-labels-pending`, `book-labels-disagree`.
- **Catalogue:** Q-10f. **Skill** `resolve-fe-config-prechecks`: P3 steps, card 7, failure modes.
  **Kickoff:** Order 2b lists P3; `BOOKS` and card 2 reworded; step 11 books = Q-10f's PKs.
- `00-books.csv`: `G10NY` confirmed (zero); instruments = all approved. Jobs agent: token closed,
  instruments-per-book closed; P2's typed-PK refusal still to align with the "fixed PK" rule (open 7c).
- Tests: 143 (+14 for P3).

### 2026-09-30 — NY's 22 books, and the BOX label rules

`[stated: operator, 2026-09-30]` The books to set up for NY arrived:
[`runs/NY_SCH/tier2-pre/00-books.csv`](runs/NY_SCH/tier2-pre/books/00-books.csv) — 22 books, proposed BOX labels
`XNY01`…`XNY22` in the order given, instruments per book `OPEN`. Rules recorded in
[`04-add-book-procedure.md` §2.4](docs/process/04-add-book-procedure.md): `PGT_SYS.PGT_DOMAINS`
(`FK_OWNER_OBJ = 17910.4`); code `X` + country code + `01`…; description **exactly** the data-lake book
label; **PK fixed, not dynamic**.

- **FE kickoff:** `BOOKS` now reads `00-books.csv`; the labels do not exist in Tier 2 yet (`NY001`, used
  by runs 4 and 6, is not a BOX label), so step 11 waits on the BOX FE team creating them; card 2 becomes
  "which instruments each book carries".
- **Jobs agent:** the label code gives the job-name token (`XES02` ↔ `GMBX3ES02D07`, so NY → `NY<nn>`) —
  `[inferred]`, to confirm; J-T3 rewritten (existing / colliding labels), J-T3b added; open items 6-7c.
- **Open (7c):** label PKs are fixed, while FE pre-step P2 refuses a typed PK (`dummy-pk-typed`) — to
  settle with the BOX FE team before a dummy label is proposed.
- `runs/README.md`: `00-books.csv` spans runs (not archived).

### 2026-09-29 — new agent: `box-batch-jobs-agent` (BOX FE/ACC batch jobs), phase 1

Scope agreed with the operator: *first explain how Tier 1 BOX jobs work, then propose what NY needs.*
[ADR 0008](docs/decisions/0008-box-batch-jobs-agent.md). Branch-agnostic, read-only; phase 1 = EXPLAIN
(trace a job / group / event) and GAP (target vs an onboarded reference branch → gap report + proposed
job matrix); phase 2 (rendering `db.conf` / Control-M / labels) is not built.

**What one traced job established** (GMBX3ES02D07, Tier 1, operator queries + Devin on the repos):
Control-M job = `db.conf` step by name; `f_ExecuteGroup(group, branch, date, instrument, vstatic, label,
sub-label)`; group → events by `ORDERTOEXECUTE`; each event is a query (`#BRANCH#`, `#LABEL#`,
`#EV_DATE#`) over `BOX_FE` tables; calculation rows run before posting rows; **`MC_DRCR` 1 = debit**
(from `p_Put_Mov`, correcting Devin's data-based reading); event names from `T_PGT_EVE_S` (3609.65 is
"Anti Natura", not a revaluation).

**Tier 2 is not Tier 1:** the wrapper is `PGT_NY` (also `PGT_BOS`, `PGT_CO`), its `f_executegroup` has
**no label argument**, and it already has `cst_pk_bra_nysch = 20007.4`; the BOX catalog (`PGT_PRC`, 51
groups) is already deployed there, group 2735.65 identical. How NY BOX jobs will pass the book is now a
question for the BOX Lead. `PKG_BOXUTILITY` is VALID in both tiers.

- **New:** `agents/box-batch-jobs-agent/` (`AGENT.md`, `prompts/explain.md`, `prompts/gap-ny-sch-tier2.md`),
  `docs/reference/job-chains/box-batch-chain.md`, `docs/reference/queries/box-jobs-queries.md` (J-E, J-C,
  J-R, J-T, J-X), `docs/examples/gmbx3es02d07-trace.md`, two eval cases, ADR 0008, and the run folder
  `runs/NY_SCH/tier2-pre/jobs/` (seeded environment profile and open items).
- **Corrected:** 2735.65 is "BOX SWAP - Accounting General by Book" (acc-add-product-checklist had
  another name). The earlier "`T_MBJ_PROPERTIES_S` is read by no code" is **not proven** — the search
  pattern could not match `T_BOX_MBJ_PROPERTIES_S`; J-E6 re-runs it.
- **Re-pointed:** W3 BOX jobs → the new agent in the orchestrator, `02-target-state.md` step 5,
  `agent-architecture.md`, the branch-onboarding checklist; `04-add-book-procedure.md` §2.3's `PGT_ES`
  open question answered.

### 2026-09-28 — the pre-steps become a skill: `resolve-fe-config-prechecks`

The P1 / P2 procedure lived in the NY_SCH run prompt (*Order 2b*), so the next branch would have had to
copy it. It is now [`skills/resolve-fe-config-prechecks/SKILL.md`](skills/resolve-fe-config-prechecks/SKILL.md)
— inputs, steps, cards 0 and 3, every refusal code with its handling — generic across branches. No new
script: it runs `render_sql.py --precheck`, whose gate already enforces it. The run prompt's *Order 2b*
keeps only NY_SCH's values (auth code 44, Tier 1 dummy `26391.4`, run 6's lesson) and points to the skill.
AGENT.md lists it (the first real skill). Two eval cases (happy path, failure paths). Tests: the skill's
command, file names and refusal codes are checked against the renderer, and every skill must have an
eval case. Tests: 129.

### 2026-09-25 — BOX Lead review of run 6: two pre-steps, run metrics

[ADR 0007](docs/decisions/0007-pre-steps-pk-and-dummy-label.md). **P1** (`templates/precheck-pk.sql.tmpl`,
`render_sql.py --precheck`): the PK mechanism checked on the applying account before any config exists;
a PROBLEM prints a sequence-fix proposal for the BOX FE team; the full render refuses until P1 says OK
(`pk-precheck-missing` / `-not-ok`). `chk_pk` in the config keeps only the auth-code check. **P2**
(`templates/precheck-dummy-label.sql.tmpl`): the dummy label must exist in the target and be shared with
another branch (`dummy-label-not-in-target`, `dummy-not-in-use` — run 6's NY001 would be refused), or a
`PGT_SYS.PGT_DOMAINS` insert is proposed for the BOX FE team (Q-10e; `dummy-proposal-pending`,
`dummy-pk-typed`). **Metrics:** `scripts/run_metrics.py` → `06-run-metrics.md`; `03-sql/render-log.csv`.
Charter: FKs are SIGOM's (metamodel), not Oracle's — made explicit in hard rule 12; hard rule 4's one
reviewed exception. Catalogue: Q-P1, Q-10c in the target, Q-10d (a) `SELECT *`, Q-10e. Tests: 124.

### 2026-09-24 (late night) — source answers on the pre-commits; run 6's `PKG_ENGPRECOMMIT` stop removed

`cib-boxfin-dbboxfe` answered (read-only, cited): `F___SEQUENCE` and `P_ENGFixingCurve_PreCommit` have no
transaction control; **`p_check_Val_Curves_precommit` commits only inside its loop over step-8 rows with a
NULL curve** (`023-pkg_engprecommit_body.sql:408-442`), so with none it commits nothing; no triggers on
the ten tables. Run 6 stopped because `PKG_ENGPRECOMMIT` returned 0 rows in `ALL_OBJECTS` on the
read-only account.

- **Template:** both pre-commits are called with `EXECUTE IMMEDIATE`; not callable (ORA-06550) →
  `WARNING`, never a stop. The Config pre-commit now runs after the self-check (which proves no step-8
  rows) **in the rehearsal too**; the block then checks its transaction is still its own and ends with
  its own `COMMIT` (rehearsal: `ROLLBACK`) — the only difference between the two files. The -20094 /
  -20095 logic is gone: with no step-8 rows the pre-commit never commits, so it would have stopped every
  apply.
- **Fixed:** verify V6 had one `)` too many after the NULL-safe change (ORA-00907/00933 at verify time).
  The tests now run the structural lint on the verify file too. The validator detects a pre-commit
  **call** (`.name(`), not a message naming it.
- **Catalogue:** Q-G3b (d) with 0 rows is not a stop (owner `BOX_FE` from the source); Q-G3d (a)/(b)
  answered from the source; new **Q-G3e** (sequence headroom — Tier 2 may hold typed PKs, stated by a BOX
  Dev). Prompt gates updated; charter hard rule 10 records the confirmed behaviour. Tests: 104.

### 2026-09-24 (night) — the SQL is rendered from `values.json`; the agent no longer writes SQL

Operator's decision on run 5's review: *"apply your recommendation … make it perfect so next run has no
surprises."* [ADR 0006](docs/decisions/0006-render-sql-from-values.md).

**New:** `scripts/render_sql.py` — reads `03-sql/values.json` (every value with its source), cross-checks
it against `00-inputs.md`, `00-decisions.md`, `02-findings.md`, Q-04c (set + counts), Q-06c and the
target's columns (new **Q-G3d (e)**), refuses with a JSON path and a fix, and renders **four** files:
`-rehearsal.sql` (the config block ending in `ROLLBACK`), `-config.sql`, `-verify.sql`, `-rollback.sql`,
plus `render-report.md` (rows filtered out of step 7, counts, sources). Then runs the validator.
`templates/values.example.json` is the shape.

**Templates rewritten** (ASCII only, section markers): step-0 pre-flight for every guard (existing
configuration, DESCRIPTION collisions, steps 11/12/14a); decided steps as one visible INSERT per row with
its source; qualified `<owner>.F___SEQUENCE` / `<owner>.PKG_ENGPRECOMMIT` (Q-G3b (d)); `"INTERVAL"`
quoted; a self-check of every count before anything is kept. **After an independent Oracle review of the
rendered files** (no blocker; assumptions made explicit): refuse to start with an open transaction; `chk_pk`
also checks the PK is unused; the block detects a called routine ending its transaction; after the Config
pre-commit, stop (-20094, nothing kept) if it never committed, and fail (-20095) if it rolled the
configuration back; the rollback refuses an open transaction too; `SET DEFINE OFF` on line 1, `SET AUTOCOMMIT OFF`, `NLS_NUMERIC_CHARACTERS` fixed. Verify: V1
also checks `t__CORE_INFO_S` has one row; V2 lists only mismatches; NULL-safe V6/V9; V10 with `TO_CHAR`;
new **V11** (decided values = `values.json`, both ways) and **V12** (every reference value exists).
Rollback: each delete must match the config's count or nothing is deleted; step 8 counted, not deleted;
re-apply note for 14a. `DDATE` may be `SYSDATE` or `TRUNC(SYSDATE)` (Q-12 now shows the time part).

**Validator:** re-renders and compares — `sql-edited-by-hand`, `sql-not-rendered`, `values-missing`,
`values-invalid`; `no-existing-row-guard` now looks for the count before the table's first INSERT and
requires it to be tested against 0; `instrument-out-of-scope` reads instrument positions only (a strategy
PK like `11.4` no longer trips it); the step-7 row parser no longer starts at an earlier `SELECT`; the
rehearsal is a role file; the COMMIT/ROLLBACK checks ignore string literals. **Tests:** 101 — renderer refusals, DRAFT / 14a-present / core-held renders, a
structural PL/SQL lint (itself tested), and every hand-edit mutation.

**Docs:** charter (*The SQL is rendered, never written*; Outputs; gate 0d + Q-G3d), run prompt (SQL
section rewritten around `values.json`; Q-G3b (d), Q-G3d gates; card 5 `DDATE`; operator run order),
query catalogue (Q-G3b (d), **Q-G3d**, Q-04c/Q-06c/Q-12 notes), walk notes (*The four SQL files*),
templates and scripts READMEs, eval case, review prompt, run README, run-5 review, executive summary
rev. 10. Step 0 in the other four prompts is case-insensitive and names the right folder.

### 2026-09-24 (evening) — run 5 reviewed: right values, SQL that would not compile

Review: `runs/NY_SCH/tier2-pre/03-sql/REVIEW-run-05.md`. Dummy book found (`2741.44`, BR00 - BR DUMMY),
Days Matured identity fixed, auth code cross-checked. But `chk_pk` inside `VALUES` (PLS-00222 — the block
does not compile), guards that cannot fire, 38 typed quote INSERTs beside an unused generated list, step 11
without `FK_PARENT`, the Config pre-commit replaced by `COMMIT`, the curve pre-commit before the array,
steps 2–5 unheaded, step 7 withheld.

**Validator:** `local-procedure-in-sql`, `guard-placebo` (and `no-existing-row-guard` now needs a real
`COUNT(*)`), `quote-refs-typed`, `quote-refs-list-unused`, `step-without-header`, `conf-by-book-no-parent`,
`config-precommit-missing`, `curve-precommit-before-array`. A reconstruction of run 5 trips all of them.
32 tests pass.

**Session:** Step 0 searches case-insensitively (`agent.md`), with the expected path spelled out;
`runs/README.md` explains the Windows casing cause and the two-step `git mv` fix. **One query per message.**
New input **`REFERENCE_BRANCH_PK: 20087.4`** (SLB) — Q-13 (b) had used an undefined placeholder and got
Tier 1's dummy label `26391.4`; Q-13 (b) now names its columns and the branch outright.

**Proposed, not built:** render the SQL from the templates with a script, so the agent writes values and
decisions and never the SQL's structure.

### 2026-09-24 (later) — the run-4 WARNs become FAILs

Devin iterates to 0 FAIL and treats WARNs as optional, so every run-4 defect is now a FAIL:
`curve-precommit-missing`, `no-existing-row-guard`, `quote-refs-unchecked`, `exceptions-unchecked` (were
WARN), plus new `step-header-incomplete` (Source / Findings / If wrong on every writing step) and
`decision-tagged-confirmed`. Config template: asserts `c_expected_fraction` = `c_expected_auth_code /
10^digits`, so both recorded values are used and a typo in either stops the script. Reconstruction of
run 4: 11 distinct FAILs. 25 tests pass.

### 2026-09-24 — run 4 reviewed; session problems fixed at the source

Review: `runs/NY_SCH/tier2-pre/03-sql/REVIEW-run-04.md`. **Best run yet, not executable**: step 7 does not
compile (cursor fields), Days Matured carries the Config owner, the dummy book was "waived" by relabelling
the real book, and the verify script's auth-code query could not fail.

**Session fixes:**
- **"Charter missing"** (runs 3, 4): the automation repo sits in `automation/` of the checkout. Every
  prompt now starts with **Step 0** — `find` the charter, `cd` to its root, never report a file missing
  before searching.
- **Q-04c settled: `FK_BS`** `[stated: operator, BOX Dev]`. The PK-vs-FK_BS test that stopped run 4 on a
  coincidental `87.35` is withdrawn; Q-04c is now the decoded, export-ready step-4 set (LEFT JOINs,
  resolved-count check).
- **Decision cards**: one decision at a time — what, why, releases, evidence, options, recommendation,
  if wrong, **authority**, "reply with decision, name, role" — recorded in new `00-decisions.md`. Replaces
  run 4's "three blockers, stop". Charter *Who may close a gate* and the kickoff carry the format.
- **Dummy book**: Tier 1's `26391.4` is absent in Tier 2 (so `PGT_SYS` is not identical across tiers for
  labels — `confirmed-joins.md` corrected). New **Q-10d** lists candidates; the label is a **BOX FE** card,
  the books a product-SME card; the row is never waived, never a real book.

**Validator:** `cursor-field-undeclared`, `identity-wrong-object`, `dummy-is-a-book`, `verify-placebo`,
`verify-incomplete`, `decisions-log-missing` (FAIL); `curve-precommit-missing`, `no-existing-row-guard`
(WARN). Against a reconstruction of run 4: 6 FAIL, one per defect. 22 regression tests pass.

### 2026-09-23 (late) — the config script touches `BOX_FE` only

`[assumed: Edouard, 2026-09-23]` The account that applies the script sees `BOX_FE` and nothing else. The
earlier version of this day's change read `DEVENG` (steps 4, 7) and `GOM_GLB_SYS` (the auth-code check)
inside the script; that would not have compiled. Now:

- **Auth code:** checked through the PKs themselves — `F___SEQUENCE` reads it with its owner's rights,
  and `chk_pk` compares every PK's fraction with `TARGET_PK_FRACTION` from Q-G3c, the first time before
  any INSERT. Verify V1 still reads `t__CORE_INFO_S` directly, on the operator's read-only account.
- **Steps 4 and 7:** literals **generated** from the evidence CSVs by new `scripts/evidence_to_sql.py` —
  never typed. The validator reads the same CSVs and FAILs any difference (`quote-refs-not-evidence`,
  `exceptions-not-evidence`); verify V4 and new V10 compare BOX with GBO both ways. New query **Q-06c**
  (step 7's rows with unique, aliased columns) and input **`QUOTE_REF_COLUMN`** (Q-04c's outcome).
- **New check `config-reads-other-schema`**: any `DEVENG`/`PGT_*`/`GOM_GLB_SYS` reference in the config.
- The question to the BOX FE team about `DEVENG` grants is withdrawn; the executive summary's Question J
  now states the assumption instead.
- `scripts/tests/fixtures/` is generated on every test run and now git-ignored. 16 regression tests pass.

### 2026-09-23 (evening) — BOX FE expert review of run 3: seven points adopted, each now a check

Reviewed with a BOX FE expert using the reviewer's guide. **No objection to the walk order**, the
insert-then-update of steps 2–4, or the pre-commit placement. Seven points, recorded in
[ADR 0005](docs/decisions/0005-box-fe-expert-review-run-3.md):

1. **Auth code** — already added by `F___SEQUENCE(…,'X')`, but invisible. Now: **Q-G3c** records it; the
   config script asserts it before the first INSERT and on every PK (`chk_pk`); verify V1 checks every row.
2. **Step 2** — `FK_SOURCE_BACK = 586.4` always; `FK_SOURCE_FRONT` = the branch's Murex instance (NY
   `513.4`), new input `SOURCE_FRONT`. Run 3 had copied GBO's `9.4`/`11.4`. **Q-02c**.
3. **Step 4** — no typed quote list: read in-script from `DEVENG`, count-guarded, verified both ways.
   ⚠️ The expert's query copies `PK`, ours copies `FK_BS` — **Q-04c** decides, and blocks step 4 until it runs.
4. **Step 7** — one GBO config carries several branches' exceptions; GBO's `FK_BRANCH` is a branch
   *config*. Filter to NY through `T_PGT_BRANCH_CONFIG_S`, write `BRANCH_PK`, copy `CRITERIAL`. **Q-06**.
5. **Step 11** — a dummy-book row per instrument (Tier 1 label `26391.4`): `(books + 1) × instruments`.
   **Q-10c**, new input `DUMMY_BOOK_LABEL`.
6. **Step 14a** — Days Matured: insert a row for any approved instrument missing one, proposed from
   Tier 1. **Q-12** revised.
7. **Step 14b** — `T_BOX_ENGSETUP_S`: nothing to configure.

**Also fixed:** step 12's "no identity because the table is empty" (the metamodel derivation needs no
row); `LIMIT_ERRORS = 0` explicitly never proposed (ADR 0004 stands).

**Found by an independent check of these changes, before release** (ADR 0005): steps 2–4's
insert-then-update **fails on its first INSERT** — `FK_CURVEMAN`/`FK_CURVEACC` are `NOT NULL`, ORA-01400;
run 3 was written that way and never applied. Replaced by **allocate-first** (curve PK allocated before
the header; no UPDATE), new check `curve-fk-null`. Also: guards so the rollback cannot delete rows it did
not create (steps 11, 12, 14a), 14a rows kept on rollback (global table), and the validator's
open-decision checks made **per step** so an honest partial run can pass. 14 regression tests pass.

**A generalisation, hard rule 13:** a fourth FK kind, **re-keyed** — same column name, different target
table in GBO and BOX. Points 2 and 4 were both this. Recorded in `confirmed-joins.md`.

**Structure:** `03-sql/` is now **three files** — config, verify (V1–V9), rollback (runnable; no more
`IF 1 = 0`) — built from new `agents/sigom-box-fe-configs-agent/templates/`. Sets mined from GBO are read
in-script and count-guarded; values a person signed are literals with provenance.

**Validator:** 15 new checks (`auth-code-not-asserted`, `pk-not-checked`, `auth-code-mismatch`,
`source-column-wrong`, `quote-refs-typed`, `runtime-set-no-guard`, `branch-fk-copied`,
`branch-fk-not-branch`, `conf-by-book-no-dummy`, `unresolved-substitution`, `rollback-dead-code`,
`verify-script-missing`, `verify-no-auth-check`, `rollback-script-missing`, `define-not-off`); step 14 split
into 14a/14b; two false-positive risks fixed (`identity-sampled-from-target` matching across statements;
loop counting on runtime and nested sets); the obsolete `draft-header` and `identity-constant-literal`
warnings removed. **First regression tests** — `scripts/tests/` builds a clean fixture from the templates
and a run-3-like one, and asserts each check fires on its mutation and not on good output. All pass.

**Kickoff rewritten for run 4** (`prompts/tier2-full-run.md`), also removing four instructions that
contradicted the charter — steps 4b/9/10 "parked", "do not call `p_check_Val_Curves_precommit`", "gate 0c
must stay open", the disproven `20314.4` hypothesis. The first is the likely reason run 3's outputs still showed
Question G open: the prompt said "parked" after the charter had closed it.

### 2026-09-23 — reviewer's guide for run 3's SQL

Added `runs/NY_SCH/tier2-pre/03-sql/NY_SCH-tier2-pre-steps-1-to-11-executive-summary.md`, to travel
with the SQL to a BOX FE developer: the walk in execution order, every value's source, files produced,
decisions (test-signed vs SME-signed), known defects, and seven ranked questions. Raises two points not
in the run-3 review: NY's GBO `LIMIT_ERRORS = 0` on all six instruments, and Q-09's 124 NY
currency-basis rows against the "step 10 not needed" decision. No names, no account IDs.

### 2026-09-22 (run 3) — every mechanical defect fixed; the rejection is now about scope

Third run. **Rejected**, but for the first time not for mechanics. Review at
`runs/NY_SCH/tier2-pre/03-sql/REVIEW-run-03.md`.

**Fixed, all of it:** `FK_CURVEMAN` no longer a GBO PK · insert-then-update · identity from `&&QG6_*`
substitution variables instead of sampled rows · **all 38 quote references** · correct
`PKG_ENGPRECOMMIT` · step headers with `If wrong:` on every step · `00-inputs.md` present with the
preflight quoted · step 14 `NOT_BRANCH_SCOPED`.

Two pieces of reasoning worth naming: step 8 refused on a zero control (*"the predicate is not proven
by a non-zero control"*), and step 12 **refused to substitute** a missing identity rather than guessing.
Both unprompted, both against the run's own interest in looking complete.

#### ⛔ Step 7 wrote six instruments gate 0c never approved

Twenty rows across **eleven** instrument PKs where the approved scope is six. `8.4`, `11.4`, `13.4`,
`10022.4`, `20134.4`, `20173.4` — 6 of 20 rows — are out of scope; `2.4` Deposit & Loan is in scope and
absent. **The mining was correct; the scope filter was missing.** Step 7 is downstream of step 6, and
an exception row for an instrument with no accrual configuration is orphaned at best.

New check **`instrument-out-of-scope`**, covering steps 6, 7, 8, 11 and 12 against an
`APPROVED_INSTRUMENTS:` line now required in `00-inputs.md`. **Gate 0c's answer has to be written as
PKs** — names are not checkable.

#### ⛔ Step 12's blocker is probably self-inflicted

Statused `PROPOSED` with no SQL — which is what `ready-step-without-sql` catches, and the right status
is `EVIDENCE_REQUIRED`. But the gap itself: Q-G6 returned no identity for `T_BOX_ERRORS_FE_S`, a table
**empty in Tier 2**. Q-G6 reads `GOM_GLB_SYS` and needs **no `BOX_FE` read** — so it was run against
the table. Re-run it against the metamodel and step 12 unblocks.

#### ⚠️ And the findings table overstated one step

Step 8 is `CONFIRMED_ABSENT` in the findings and `EVIDENCE_REQUIRED` in the open items. The open item is
right. A findings table that overstates the run is the one defect a reviewer cannot see from the SQL.

#### 🔧 My own check would have been wrong about a correct run

`step-row-count-mismatch` assumed one INSERT per row. Run 3 emits N rows from **one statement inside a
loop**, which is correct — and the check would have **false-failed three steps**. It now counts what
the loop iterates (a `UNION ALL` list or an `ODCINUMBERLIST`) and prefers the header's *runtime
enumeration* figure over the statement count.

**Recorded as plainly as the agent's own defects.** A check that fires on good output costs more than
no check, because it teaches everyone to ignore the checks.

### 2026-09-22 (Question G closed) — steps 4b, 9 and 10 are not needed

`[stated: Edouard Sintes, 2026-09-22]` **NY_SCH does not need `T_BOX_ENGFIXDISC_S` (4b),
`T_BOX_ENGZCCONF_S` (9) or `T_BOX_ENGCURRENCYBASIS_S` (10).** All three are empty in Tier 1 PRE,
nothing in either deployment repo writes them, and Madrid and London run without them.

**They stay in the walk as verify-only steps** — `CONFIRMED_ABSENT` with evidence, no SQL, and the
validator continues to FAIL any INSERT into them. Not dropped from the table, because *an object
silently skipped is indistinguishable from one forgotten* — the same reason steps 13 and 14 stay.

⚠️ **One residual, recorded once.** NY has **Cross Currency Swap** in scope and **Currency Basis** is
what a cross-currency product prices off. SLB also has CCS and also has no rows, so the precedent
supports the decision — but if cross-currency pricing later looks wrong for NY, step 10 is the first
place to look.

**Three steps closed, so the remaining blockers are gate 0c's three answers and nothing else.**

#### The executive summary had drifted, and this caught it

Updating Question G surfaced that `fe-agent-executive-summary.md` — the **customer-facing** document —
still carried:

- the **withdrawn CDS claim**, in full, telling the developer that Credit Derivatives blocks three walk
  steps. Corrected everywhere else on 2026-09-22; this instance survived because the correction targeted
  a string this file did not contain.
- gate 0e as *"deferred — blocked on Tier 2 grants"*, two days after access landed
- steps 4b/9/10 as *"parked — see question C"*, pointing at a question letter that no longer matches

Now rev. 8, with an explicit correction paragraph addressed to the reader: *"a correction we owe you."*
**The document we would actually have sent an external reviewer was the most out-of-date one in the
repo** — because nothing routes a correction to it, and no check covers prose.

### 2026-09-22 (charter cut) — 1179 → 708 lines, and the verification found three run-breakers

`[stated: Edouard, 2026-09-22]` The charter had grown to 1,179 lines and was being followed
selectively. Cut by **relocating, never deleting**, into two reference files read when needed rather
than every run:

| File | Lines | Read |
|---|---|---|
| `AGENT.md` | **708** | every run — inputs, 13 hard rules, gates, walk table, outputs, escalation |
| `docs/reference/fe-walk-notes.md` | 578 | the step you are on |
| `docs/reference/fe-run-modes.md` | 117 | only if a run uses dry-run or deferred-verification |

Hard rules compressed 286 → 147 with **all thirteen intact** — rules stated to be applied, incidents
and worked examples moved. *Skills it may call* deleted: three were named, none was ever implemented,
and a promise the repo does not keep is worse than no promise.

#### ⛔ The verification pass earned its keep — three of these would have broken run 3

A fresh-context agent cross-checked the cut against the eval case and the validator:

1. **Steps 4b, 9 and 10 had stopped being marked parked.** The walk table showed them as ordinary
   INSERT steps with GBO sources and queries, while `validate_run_output.py`'s `NO_INSERT_STEPS` and
   `parked_tables` FAIL any INSERT into them. **A run following the charter would have emitted SQL the
   validator rejects.** Now marked ⏸ **PARKED — mine, never INSERT** in the table itself, with Question
   G named as the blocker.
2. **The four `NOT NULL` accrual values were demanded in three places and enumerated in none** — the
   charter said "the four values" without ever saying which four. `FK_FEEFIRSTDAYSEL`,
   `FK_INTFIRSTDAYSEL`, `INTCOMMONBASIS`, `BYTRIGGER` are now named where gate 0c needs them, with the
   unconfirmed screen-label mapping stated.
3. **Three eval conditions had no rule behind them** — a field's target assumed from its name
   (`pBranch`), an identifier taken from a `DESCRIPTION` rather than a `CODE`, and a missing
   *reference-side* row read as a limit of zero. All three restored under hard rule 8.

Plus four dangling pointers ("see *Dry-run mode* below" with no section below), and one over-claim —
the charter promised the notes held "three ways this has gone wrong" where they hold one.

**The cut itself was routine. The verification was where the value was** — and none of it would have
surfaced from re-reading my own work, which is the argument for the review pass now standing between
every run and its acceptance.

### 2026-09-22 (process) — the evals never ran, and that was the whole problem

Edouard: *"I thought we had evals to catch things like this."* **We do not.**
`evals/cases/sigom-box-fe-configs-agent-walk.md` is ~70 failure conditions in prose, referenced from
exactly one line of the charter, executed by nothing. Every "eval pass" this project has had was me
reading output by hand.

**Two runs make the pattern unambiguous:** every rule with a validator check behind it was followed;
every prose-only rule was not — including step headers, asked for in the charter *and* the prompt, in
bold, with a rationale, four hours before the run that ignored them.

#### The eval case is now enforced in two halves

| Half | Enforced by | |
|---|---|---|
| **Mechanical** | `validate_run_output.py` | run it, fix, re-run until 0 FAIL |
| **Judgement** | new `prompts/review-run.md`, **fresh session** | is the value right · does the evidence support the conclusion · whose decision was it · does the run overstate itself |

**A condition violated in a real run now moves into one of those halves in the same round.** Prose-only
conditions have been measured at worth nothing.

#### Two checks that would have caught run 2's worst defects

- **`step-row-count-mismatch`** — the step header declares a count; the file must emit it. Run 2
  declared a 38-row quote array and emitted one. No rule can know 38 is right, but the file can be made
  to agree with itself.
- **`ready-step-without-sql`** — run 2 closed gate 0c and emitted nothing for steps 6, 11, 12. If the
  status says releasable, the SQL exists; if it does not, the status overstates the run.

#### The validator is now a gate, not a report

**Neither run pasted validator output**, though both prompts asked. It is now step-by-step: run, fix,
re-run, repeat to 0 FAIL, paste the clean output last — and *"do not present the run as finished"*
before that. Plus an explicit prohibition on the run-2 move of reshaping SQL to slip past a check
(`ROWNUM = 1` → `GROUP BY … HAVING`, same defect, new spelling): **a check you disagree with is a
finding about the check.**

### 2026-09-22 (run 2) — every mechanical rule held, every prose rule did not

`ny_sch_steps_1_to_5.sql`, second run. **Rejected — regenerate.** Review at
`runs/NY_SCH/tier2-pre/03-sql/REVIEW-run-02.md`.

**The result is unusually clean as evidence.** Run 1's defects split into two groups after the review:
the ones converted into validator checks, and the ones left as prose. **Every check-backed rule was
followed. Every prose-only rule was not** — including the step headers, which were asked for in the
charter *and* the prompt, in bold, with a rationale, four hours earlier.

#### Fixed, and these were the ones with checks behind them

`FK_CURVEMAN` no longer carries a GBO PK · the curve is linked by `UPDATE`, not orphaned · step 14 is
`NOT_BRANCH_SCOPED` · insert-then-update implemented exactly as specified.

Unprompted and correct, step 8: *"NY count and SLB control count were both zero; no non-zero control
proves the absence"* → `EVIDENCE_REQUIRED`. Hard rule 8 applied without being told.

#### ⛔ New defects, all prose-only rules

1. **37 of 38 quote references dropped.** Run 1 emitted 38 `T_BOX_ENGLKFC_X` rows; run 2 emits one. The
   run's own open item calls it *"a normalized projection of the wide returned join"* — that is a silent
   enumeration loss, the same shape as the Q-05c inner join of September.
2. **Q-05d's answer inverted.** It showed SLB GBO ≠ SLB BOX; the run concluded *"SLB **BOX** values with
   NY GBO fallback"*. A GBO→BOX difference is a rule to apply to **NY's** values, never a reason to use
   London's — and the hybrid puts two branches' decisions in one row with no way to tell them apart.
3. **`PGT_MRK.P_ENGFixingCurve_PreCommit`** — invented qualifier; the recorded package is
   `PKG_ENGPRECOMMIT`. The call would fail, and an invented schema name is a fabricated literal.
4. **Gate 0c closed on "same as SLB"** — the phrase the sign-off pack opens by calling unusable.
   Attribution is now properly formed (`[stated: Edouard Sintes, BOX Dev, 2026-09-22]`), but the role is
   BOX Dev and the decisions are the product-scope SME's.

#### Three more checks, and a prohibition

`sql-no-step-headers` · `identity-sampled-from-target` (catches `ROWNUM=1`, `GROUP BY/HAVING` and
`MIN()` alike — run 2 swapped one for another) · `precommit-wrong-package`. All three fire on this file.

Q-05d now carries an explicit, numbered prohibition on inverting its result, written so it cannot be
read the way run 2 read it.

**The operating conclusion for this repo: a rule that matters gets a check, or it gets ignored.**

# Changelog

## Unreleased

### 2026-09-22 (pre-run-2d) — phase 3 was in the wrong order

**Q-05d sat in batch 4, *after* the section where the SME is asked to decide the accrual values** — and
Q-05d is what makes that question answerable. An SME in the room would have been asked to sign values
before the query establishing what they mean had run, which is the one thing the sign-off pack says
never to do.

Batch 4 now runs **first** in phase 3, with the reason stated: *without Q-05d nobody can answer the
accrual question, whoever is in the room.* The outputs and pass criteria are conditional on
`SME_IN_SESSION` rather than assuming steps 6/11/12 emit nothing.

### 2026-09-22 (pre-run-2c) — the operator/SME rule was too blunt, and the repo isn't needed

#### `SME_IN_SESSION` — an SME in the room **can** close a gate

Yesterday's rule said an in-session answer is *"evidence for a value, not gate closure."* **Written for
the wrong case.** It was aimed at run 1, where the operator answered on the SME's behalf — but as
written it would also block the case Edouard actually wants, and that case is legitimate: *the SME is
the person running the agent.*

**The rule is about authority, not channel.** A live answer from the right person, properly asked and
properly recorded, beats a document round-trip — they see the proposal, the evidence and the
consequence in front of them.

Gate closure now needs three checkable things: **a named person** (`[stated: user]` is not
attribution), **authority for that specific decision**, and **a properly put question** — what is being
decided, which steps it releases, the proposal with its evidence, and what goes wrong if it is wrong.
An answer to a question never framed is not a decision.

New required input **`SME_IN_SESSION`**. Named and authorised → the run puts each decision, closes gate
0c and **emits steps 6, 7, 8, 11, 12 in the same session**. `none` → sign-off pack, steps held. Partial
closure is normal: one decision can close while another waits.

Run 1 failed all three tests at once — no name, not its decision, never asked — and then marked the
gate `CONFIRMED_PRESENT`. Each is separately fatal; none of them is "it answered in-session".

⚠️ **One thing an SME cannot substitute for: evidence.** Step 6 still waits on **Q-05d**. Whether the
two schemas store accrual values the same way is a fact about the system, not a decision anyone is
authorised to make.

#### `cib-boxfin-dbboxfe` is not needed for run 2 — correcting yesterday's claim

Edouard asked why run 1 never touched it. Answer: nothing required it — gate 0e passed, so no DDL
sourcing; no pre-commit was called, so no body to read.

I then said run 2 *would* need it, for `P_ENGFixingCurve_PreCommit`'s body. **Wrong** — that body was
read on 2026-09-21 and is recorded in seven files, including this run folder's own README with a ✅.
The prompt now says the repo is **not** needed, and to attach it only if the agent raises a source
question mid-run and asks for it.

### 2026-09-22 (pre-run-2b) — SQL step headers, and the repo attach clarified

#### 📝 Every walk step in the SQL opens with a header block

`[stated: Edouard, 2026-09-22]` Run 1's SQL was ~290 lines of undifferentiated `INSERT` with one
comment at the top. Someone debugging a failed load cannot tell where to look.

One block per step — **What · Source · Findings row + status · Depends on · If wrong**. Step 4's 38
quote-reference rows get **one** block for the set, not 38.

**The `If wrong` line is the one that earns its place.** It tells a reviewer what failure to look for
when this step is the suspect, and it forces the agent to say whether it understands what it is
writing: *a step whose consequence cannot be stated in one line is not understood well enough to emit.*

#### The BOX FE repo — one specific use, and opting out is legitimate

Edouard noticed run 1 never touched `cib-boxfin-dbboxfe`. Correct: gate 0e passed so no DDL was needed,
and no pre-commit was called so no body was read.

**Run 2 does need it, for exactly one thing** — reading `P_ENGFixingCurve_PreCommit`'s body before
calling it, since `ALL_SOURCE` returns the package spec only (hard rule 10). The prompt now says so,
and says that not attaching it is a valid choice with a stated consequence: steps 3–4's pre-commit
stays `EVIDENCE_REQUIRED` and uncalled. `cib-boxacc-dbboxacc` is not attached for an FE run at all.

### 2026-09-22 (pre-run-2) — rerun hygiene, and the rule run 1 broke that was never written down

#### ⛔ A rerun overwrites the previous run — archive first

`RUN_FOLDER` is a fixed path, so run 2 writes over `02-findings.md`, `01-evidence/`, `03-sql/` and
`99-open-items.md`. **Those are the evidence behind run 1's review**, and losing them would make the
review unfalsifiable — the one thing this repo does not allow.

`runs/README.md` now carries the convention: archive to `archive/run-NN/`, keeping `README.md`,
`00-inputs.md` and the sign-off pack at the root because they span runs. An archived run validates on
its own, so a rejected run stays checkable against the rules that rejected it.

#### An operator's answer is evidence for a value, not gate closure

Run 1 marked gate 0c `CONFIRMED_PRESENT` citing `[stated: user, 2026-09-22]`. **The rule it broke was
never written anywhere** — the charter said gate 0c needs a named SME, but nothing said that the person
driving the session answering a question does not constitute that.

Now a section of its own: take the answer, tag it with who gave it, use it, **and leave the gate where
it was**, with the sign-off pack updated so the SME sees what was assumed on their behalf. The test:
*would this person's name on this decision satisfy an auditor asking who authorised it?*

#### Steps 7 and 8 are mined, not skipped

Both were blocked in run 1 and both were wrong to block. Step 7's `FK_BRANCH` semantics are a
verification item on the *values* — `WHERE FK_PARENT = <GBO config PK>` returns the rows regardless.
Step 8 was called `CONFIRMED_ABSENT` from **Tier 1** emptiness with `Q-07` never run. Both may still
end `SME_DECISION_REQUIRED`, but with rows attached.

#### Also into the run prompt

`P_ENGFixingCurve_PreCommit` called after steps 3–4 (no DML, safe as a gate; run 1 called nothing) and
explicitly **not** `p_check_Val_Curves_precommit` while step 8 is out of scope · a `DESCRIPTION`
uniqueness pre-check, since that index is global not per-branch · step 14 statused
`NOT_BRANCH_SCOPED` · **Q-05d** added to the Tier 1 batch.

### 2026-09-22 (run 1 follow-up) — step 6's defect confirmed, and a confound found in the proof

`[confirmed: DB via Edouard, 2026-09-22]` **Deposit & Loan — in scope — differs on four columns:**

| | `INTCOMMONBASIS` | `BYTRIGGER` | `BYRESIDUAL` | `INTERVAL` |
|---|---|---|---|---|
| NY, GBO Tier 2 | 1 | 1 | 0 | 377 |
| SLB, BOX Tier 1 | 0 | 0 | *null* | *null* |

**Two of the four are gate-0c `NOT NULL` values.** So the step-6 finding is no longer "nothing
checked" — the run proposed values that differ from the branch's own configuration on an in-scope
instrument.

#### ⚠️ But the comparison varied two things at once

**NY in GBO against SLB in BOX** — the branch *and* the system. The difference is either a genuine
branch difference **or** a GBO→BOX transformation applied when a configuration is created in BOX. The
data collected so far cannot separate them, and the two lead to opposite behaviour: copy the values, or
transform them and tag `DERIVED`.

**New `Q-05d`** holds the branch constant and varies only the system — SLB's GBO row against SLB's BOX
row, both Tier 1, one query. Three outcomes are tabulated with what each means for step 6.

⛔ **No step-6 value is `PROPOSED` until Q-05d runs.** Copying a GBO value into BOX unexamined is the
same class of error as copying another branch's; it just fails in a different direction. The walk's own
premise is that the twin tables are *similar, not identical* — which is what `DERIVED` exists for, and
this is the first place it has actually been tested.

The gate 0c pack now carries Deposit & Loan as a filled-in worked example, and says plainly not to sign
Question 2 until the Q-05d column is settled.

### 2026-09-22 (run 1) — the agent ran end to end for the first time, and found a bug in the charter

`ny_sch_steps_1_to_5.sql` produced against Tier 2 PRE. **Rejected — regenerate.** Full review at
`runs/NY_SCH/tier2-pre/03-sql/REVIEW-ny_sch_steps_1_to_5.md`.

**Every mechanical rule held. All three blocking defects are semantic.** That is the finding about the
agent, and it is why three of them are now mechanical checks.

#### ⛔ 1. A GBO PK written into a BOX column — and the rule already existed

The header carried `FK_CURVEMAN = FK_CURVEACC = 1.35`, NY's curve PK in **`DEVENG.T_PGT_ENGFCURVE_S`**,
into a column that must reference **`BOX_FE.T_BOX_ENGFCURVE_S`**. The script then created the correct
BOX curve with 38 quote references and **nothing referenced it.**

The query catalogue's three-kinds-of-value table names *"the GBO curve's own `PK = 1.35`"* as its
worked example of what never to carry. **It was buried inside the gate 0f section — and gate 0f is not
applicable to a same-environment run.** Same structural failure as `Gate 0b is narrowed` living inside
the deferred-PK section: a rule that generalises, filed under a heading that reads as inapplicable.

Promoted to **hard rule 13**, with the test that makes it checkable: *for every FK, name the table it
points into and the schema that table is in. If the answer is `DEVENG`, it is wrong.*

#### ⛔ 2. The charter's walk order was wrong, and the run collided with it

`T_BOX_ENGCONF_S.FK_CURVEMAN` points **at** `T_BOX_ENGFCURVE_S`, so the curve must exist before the
header — yet the header is step 2 and the curve step 3, and the charter called that FK-dependency
order. **No ordering of plain INSERTs satisfies both.** Devin hit a genuine contradiction and resolved
it by reaching for a value that already existed.

Fixed as **insert-then-update**: header with NULL curves → curve → quote array → `UPDATE` the header to
the curve's variable. Chosen over renumbering because renumbering would strand every "step 2"/"step 3"
reference in the corpus, and because it matches what SIGOM plausibly does through the screen.

#### ⛔ 3. Step 6 proposed London's values with NY's own rows already mined

`Q-05-accrual-gbo.csv` was in the run's evidence. NY has 18 accrual rows under `FK_PARENT = 64408.35`.
The run used London's for five of six anyway — hard rule 6, and ADR 0004 covers `LIMIT_ERRORS` only.

**The branches do differ:** SLB carries `INTERVAL = 370` for Forward Rate Agreement against NY's `377`
`[confirmed: DB via Edouard, 2026-09-22]`. Q-05 and the sign-off pack now put **NY's value and the
reference branch's value side by side**, so agreement is a confirmation and difference is the finding.

#### Three new validator checks — all three fire on this file, all three pass on the corrected form

`curve-fk-literal` · `orphan-curve` · `identity-from-rownum`. Plus a positional
`insert_columns_and_values` helper. **The validator passed this file before they existed** — the honest
measure of what mechanical checking was worth here.

#### What the run got right

The `20313.4`/`20314.4` discrepancy investigation is the best work in it: it established that SLB's
accrual table holds 7 rows that all join cleanly and no Credit Derivatives row at all, and it
**explicitly disproved this repo's own typo hypothesis**. The 2026-09-18 finding is now fully closed.
Preflight first and quoted, every PK an `F___SEQUENCE` variable, explicit column lists, no
`INSERT … SELECT FROM DEVENG`, steps 4b/9/10 correctly parked, ADR 0004 correctly applied at step 12,
and CDS sourced from NY's own GBO row for the right stated reason.

#### Still to fix before the rerun

Identity columns read with `WHERE ROWNUM = 1` (with `Q-G6-identities.csv` unused); step 8 concluded
from **Tier 1** emptiness with `Q-07` absent; step 7 over-blocked on `FK_BRANCH` semantics; no
pre-commit calls and no `DESCRIPTION` uniqueness pre-check; step 14 statused `CONFIRMED_PRESENT` rather
than `NOT_BRANCH_SCOPED`. And gate 0c was marked `CONFIRMED_PRESENT` on the operator's in-session
acceptance — fine as a test input, not as gate closure.

### 2026-09-22 (correction) — ⛔ "Credit Derivatives has no Sub-Product row" was wrong, and was ours

`[confirmed: DB via Edouard, 2026-09-22]` **Credit Derivatives IS in `PGT_SYS.T_PGT_SUB_PRODUCT_S`:**
PK **`20313.4`**, CODE `Credit`, `FK_OWNER_OBJ 1451.4`, `FK_EXTENSION 10507.4`, `FK_PARENT 20326.4`.
The table holds 50 rows. Caught by Edouard reading the table directly after this repo asserted the
opposite four times in one week.

#### What the original evidence actually showed

On 2026-09-18, Q-05c's **`INNER JOIN`** from `T_BOX_ENGACCRCONF_S` to `T_PGT_SUB_PRODUCT_S` returned
**seven** of SLB's nine configured instruments. Credit Derivatives and Bond Return Swap dropped.

**That is a fact about the join.** It is equally consistent with the row being absent, the join being
written on the wrong column, or `FK_INSTRUMENT` holding a different value. The repo recorded the first
of the three and tagged it **`[confirmed: DB]`**.

**This is hard rule 8 — the repo's own rule — violated by the repo itself.** *"A zero-row result proves
nothing on its own."* The rule was written from three incidents where someone else's query was read as
a finding; it was then not applied to this repo's own inference, and the `[confirmed]` tag made the
inference unfalsifiable downstream. It propagated to **ten files** and reached a run prompt that was
about to be executed.

#### Corrected in ten files, originals retained

`AGENT.md` · `prompts/tier2-full-run.md` · `prompts/kickoff-ny-sch.md` · `prompts/dryrun-ny-sch.md` ·
`fe-config-mining.md` · `fe-branch-configuration.md` · `ny-sch-branch-onboarding.md` ·
`runs/NY_SCH/tier2-pre/README.md` · `00-gate-0c-signoff-request.md` · `ADR 0004`.

**Withdrawn:** *"CDS has no Sub-Product row"*, *"CDS blocks steps 6, 11 and 12"*, *"at most five of six
can resolve"*, *"a clean six-row result is a signal something is wrong"*. **Expect six.**

#### What is still open, and it is now narrow and cheap

**Why did the join miss?** Read SLB's Credit Derivatives accrual row and compare its `FK_INSTRUMENT`
against `20313.4`. Three candidates: the FK holds a different value (what?); the join used the wrong
column; or `FK_INSTRUMENT` points into another key space for some instruments — the only one that would
be a data-model finding, and the only one that would block anything.

**One hypothesis to test, not assume:** the rejected 2026-09-18 draft listed an instrument PK of
**`20314.4`** — one away from `20313.4`. If it mis-keyed Credit Derivatives by one, that is an
independent defect of the fabricated-literal class.

#### Bond Return Swap — a separate, weaker claim that survives

Ordered by `DESCRIPTION`, the table's first row is *Caps And Floors*, so **no Sub-Product description
begins with A or B**. Bond Return Swap is not present under that name. It is out of NY_SCH's scope, so
nothing depends on it — but note the asymmetry: the original finding bundled two instruments, and only
one of them held up. **Bundled findings should be split at the point they are recorded.**

### 2026-09-22 (later) — read-only Tier 2 account; the run is no longer deferred

`[stated: Edouard, 2026-09-22]` The Tier 2 PRE account is **read-only**, and **all queries run in Tier
2** except three SLB reference reads that stay in Tier 1.

**Three consequences, all simplifications:**

1. **Deferred-verification is retired for this run.** The shape existed only because `BOX_FE` could not
   be read. The C2 reads run normally, `CONFIRMED_ABSENT` becomes writable (the preflight is what earns
   it), and the draft headers come off without regenerating anything.
2. **No cross-tier workarounds anywhere in the walk.** Source and target share an environment, so no
   mined value has a portability question and gate 0f does not arise.
3. **Read-only enforces a hard rule in the environment**, rather than by instruction. A backstop, not a
   licence — the agent still emits SQL to a file and never attempts execution.

#### The Tier 1 reads, and the line they must not cross

Three SLB queries stay in Tier 1: Q-13's `LIMIT_ERRORS` (ADR 0004), the four accrual values on SLB's
configuration (sign-off Question 2, which also confirms the `FK_FEEFIRSTDAYSEL` ↔ `FeeCalcInterval`
mapping), and Q-05c for instrument identities.

⛔ **None of them may enter the SQL as a mined value.** They are proposal aids under hard rule 6: a Tier
1 `LIMIT_ERRORS` becomes a **`PROPOSED`** number awaiting sign-off, and a Tier 1 FK is never INSERTed.
Every such value is labelled with the environment it came from — environment is part of a run's
identity, not a footnote.

#### `prompts/tier2-full-run.md` replaces `tier2-gate-verification.md`

The gates-only prompt was split out while access was pending. With access in hand, two overlapping
prompts would be exactly the drift this repo keeps getting caught by, so it is **deleted** and its
content is phase 1 of the full run, with a **hard stop** if any release gate fails.

The prompt ends with **what a passing run looks like** — because the expected outcome is a run that
mines steps 1–5 and *correctly stops*, with steps 6–8, 11 and 12 `SME_DECISION_REQUIRED` and no SQL.
Judged against "did it produce a complete configuration" that reads as a failure; it is not. It is the
charter's definition of done, criteria 1–5.

### 2026-09-22 — Tier 2 `BOX_FE` access landed; gates reclassified

`[stated: Edouard, 2026-09-22]` **Both `DEVENG` and `BOX_FE` are readable in Tier 2 PRE.** Four gates
blocked on that access for three weeks are now evaluable.

#### Release gates vs scope gates — the charter was ambiguous, and it mattered

The gates section read *"no SQL is written until all pass."* Gate 0c is open, so on that reading nothing
could be produced at all. But the walk table's *Blocked by* column says 0c blocks steps **6, 7, 8, 11,
12** — not steps 1–5. The two statements disagreed, and the disagreement was invisible until access
arrived and made the difference load-bearing.

Resolved by classifying them:

| Kind | Gates | While open |
|---|---|---|
| **Release** | 0a, 0b, 0d, 0e, 0g | No SQL at all — each is a prerequisite of *every* INSERT |
| **Scope** | **0c** | Blocks only its dependent steps |

So a run with every release gate passed and 0c open **proceeds through step 5 and stops** — the
configuration's spine, including the association row that ties it to the branch. Explicitly *not*
permission to guess a scope, or to treat 0c as closed because the instrument list is known: it also
carries the four `NOT NULL` accrual values, the error limit and the book list.

#### New: `prompts/tier2-full-run.md` *(first written as `tier2-gate-verification.md`; merged into the full run on 2026-09-22)*

A session of its own, before any mining, because two of the four gates can still **fail** — and a
mining session run first would be wasted. Nine queries in order, each with what it settles and what a
failure means.

⚠️ **The preflight is query 1 and nothing else runs until it returns non-zero.** The last reading of
gate 0e reported Tier 2 PRE as missing many `BOX_FE` tables; it was wrong, taken from an account with no
grants, and withdrawn. `BOXFE_VISIBLE = 0` is an **access escalation**, not a provisioning gap. This is
the single case hard rule 8 was written for.

It also carries: don't reuse Tier 1's identity constants (`35000126.65`, `35001566.65`) — they are the
destination's own identity and must be read from Tier 2, one row per table, more than one being a stop;
finding nothing for NY_SCH is the **precondition**, not a problem; and the C2 reads are what release the
run from deferred-verification shape.

### 2026-09-21 (latest+1) — step 12's source changed: propose from the reference branch

`[stated: Edouard, 2026-09-21]` **Do not mine the GBO twin for Allowed Errors.** For each in-scope
instrument, propose **SLB's `LIMIT_ERRORS` for that same instrument**, tagged `PROPOSED`, for the SME to
accept or customise. This supersedes the 2026-09-18 position that step 12 is an ordinary
mine-and-propose step because `DEVENG.T_PGT_ERRORS_FE_S` exists.

Recorded as **[ADR 0004](docs/decisions/0004-step12-limits-from-reference-branch.md)** rather than a
quiet edit, because it contradicts a standing hard rule and the reasoning has to survive the person who
made the decision.

#### Why it is not a hard-rule-6 breach

Hard rule 6 forbids copying a value **because the shape matches** — unattributed, presented as derived.
What differs here is the **status**, not the source: `PROPOSED` never `CONFIRMED`, the rule written
down, its own per-instrument sign-off, and no SQL until that sign-off exists. That is hard rule 2
applied to a value sourced from a reference branch.

The column-level reason: **`LIMIT_ERRORS` is an operational tolerance, not a fact about the branch.**
Copying a curve asserts something false about NY; copying a limit asserts only *"start where London
started."*

#### 🚧 The boundary, which is the point of writing it down

**One column, one step.** It does not extend to step 6's four accrual values, to curves, calendars or
anything that asserts what the branch *is*. The test for any other column: *is it an operational
tolerance, or does it describe the branch?* Only the first qualifies, and extending it needs its own
ADR, never an analogy. Where a branch has an instrument the reference lacks, that limit is
`SME_DECISION_REQUIRED` — **never** the nearest-looking instrument's value, which is the exact
shape-matching hard rule 6 exists to stop. Five new eval failure conditions guard this.

#### ⚠️ Stated to the SME as a default, not a recommendation

SLB's limits reflect SLB's volumes; nobody has looked at NY's. Too high and failed deals are skipped
while the run reports success; too low and the first bad deal aborts the load. The sign-off pack now
carries a per-instrument accept/change table and keeps *"needs volume data first"* as a valid answer.

#### A stale claim caught while propagating

`kickoff-ny-sch.md` carried six unattributed instrument PKs from the rejected draft. An SME has now
confirmed six instruments **by name** — and that does **not** validate those PKs. Same count is not
evidence. The prompt now requires resolving the confirmed names to PKs from the data and reporting the
diff, and notes that **at most five of six can resolve** since CDS has no Sub-Product row — so a clean
six-row result is itself a signal something is wrong.

### 2026-09-21 (latest) — gate 0c: instruments confirmed, and the hypothesis was wrong

`[stated: <SME_NAME>, via Edouard, 2026-09-21]` **NY_SCH gets six instruments:** Swap, Deposit & Loan,
Cross Currency Swap, OTC Option, Caps And Floors, CDS (Credit Derivatives).

⚠️ **Fill in the SME's name.** The placeholder `<SME_NAME>` appears in six files and is **not a valid
evidence tag** — gate 0c requires a *named* SME in writing.

#### The working hypothesis was disproven, and that is the finding

The repo's standing assumption was **"the same set as SLB"** — nine instruments, held as a hypothesis to
confirm rather than assume. The answer is **six of those nine**: Cash Flow Matching, Forward Rate
Agreement and Bond Return Swap are **out of scope**.

Acting on the hypothesis would have configured **three instruments nobody asked for** — not a crash, a
silent scope expansion, with rows in steps 6, 11 and 12 for each. The discipline of holding a plausible
analogue as a *proposal aid* rather than authorisation (hard rule 6) is what caught it, and the cost of
asking was one question. Worth recording as the case for the rule, since the rule's cost is usually
visible and its benefit usually isn't.

#### ⛔ The chosen set includes the instrument we predicted would block

`00-gate-0c-signoff-request.md` carried this warning when it was written: *"two of SLB's nine (Credit
Derivatives, Bond Return Swap) do not resolve to a Sub-Product row… if the SME picks either of those
two, that resolution gap becomes a blocker."* **Credit Derivatives was picked.**

`FK_INSTRUMENT` for it has no `PGT_SYS.T_PGT_SUB_PRODUCT_S` row `[confirmed: DB, 2026-09-18]`. It keys
rows in **steps 6, 11 and 12**, so one unresolved instrument blocks three steps. Resolution path: Q-05c
in `LEFT JOIN` form plus the unjoined `COUNT(*)`, then resolve the value directly; if it truly has no
row, that is a **source question** for `cib-boxfin-dbboxfe`, not a value to infer from the other five,
and never a name-similarity mapping.

#### Gate 0c is **not** released

Instruments were one of three answers it needs. Still outstanding: the **24 mandatory accrual values**
(four `NOT NULL` columns × six instruments — down from 36), the `LIMIT_ERRORS` decision, and book
scope. Question 2 still needs its reference query run first, so the SME is reacting to values rather
than column names.

#### The dry-run output had no introduction — fixed

`[stated: Edouard, 2026-09-21]` The prompt said *"your audience is a BOX FE developer who does not know
this repo"* and then sent him straight into walk step 1. `DRY-RUN-REVIEW.md` must now **open with a
five-part introduction** in plain language: what the agent is for, how it works in three sentences,
**what it will never do** (no database writes, no invented values, no DDL, no PR against his repos),
that this is a plan rather than a result with nothing executed, and what is needed from him plus how
long it should take. No repo jargon until after it.

### 2026-09-21 (late) — the charter cut: withdrawn modes moved to decision records

The FE agent's charter had grown to **1063 lines**, and a third of it described modes the agent must
*not* use. A prompt that spends 130 lines on withdrawn shapes competes for attention with the rules
that fire on every run. It is now **954 lines**, and **nothing was deleted — three sections were moved
into decision records, and every live rule inside them was relocated first.**

#### The three ADRs

| ADR | What moved | What stayed in the charter |
|---|---|---|
| [0001](docs/decisions/0001-withdraw-split-tier-runs.md) | **Split-tier runs** (~45 lines) — mine one environment, write another | (1) a step with unreachable evidence is a finding, not a run-stop — now a paragraph under *Deferred-verification* and an escalation rule; (2) never substitute one environment's data for another — now hard rule 6's second paragraph |
| [0002](docs/decisions/0002-deferred-pk-mode.md) | **Deferred-PK mode** (~25 lines) — PKs as named substitution variables | **`Gate 0b is narrowed, not withdrawn`** — a live gate rule that was buried inside this section. Moved into *Gates* before the cut. Deleting the section naively would have silently dropped it |
| [0003](docs/decisions/0003-gate-0f-demoted.md) | **Gate 0f** (~60 lines) — cross-environment reference check | (1) a run is never blocked on a `PGT_STC`/`PGT_SYS` value — that is a **platform escalation**; (2) *a PK is only meaningful with its table*, which now lives in `confirmed-joins.md` and `sigom-metamodel.md` §7 |

Reinstating any of the three means a new ADR superseding it, not quietly re-adding a section.

#### Compressed, not cut

The 2026-09-16 scope-correction block (49→17 lines), hard rule 3's `F___SEQUENCE` derivation (the
worked examples live in `sigom-reference.md` and three other files), hard rule 8's five prose
mechanisms → **a six-row table**, one rule and one incident per row, and the step 11/12 narratives.
Every rule survives; the storytelling around it does not.

#### Four rules the eval case tested and the charter never stated

Found by cross-checking every eval failure condition against the cut charter — and **all four predate
the cut**. The eval case had been growing rules the charter never absorbed, which is the propagation
gap this repo keeps hitting:

- **Every child of the MIS header is mined `WHERE FK_PARENT = <GBO config PK>`** — and a `MIN(PK)`
  subquery standing in for a missing filter is the tell. → hard rule 8
- **`FK_KIND` `6.1` is a flag and `11.1` is a screen filter parameter** — `11.1` is not a stored column
  at all. → hard rule 9, as a fourth column kind
- **`PGT_DOMAINS` is never enumerated without `FK_OWNER_OBJ`** — dozens of unrelated enumerations share
  that table. → hard rule 8
- ***Cannot mine* and *mined, needs sign-off* are different statuses** — a blocker with no rows behind
  it gives the reviewer nothing to disagree with. → *Escalation rules*

#### Two inconsistencies fixed while in there

- **The eval case asserted INSERT order `2→3→4→5→6→7→8→9→10→11→12`**; `validate_run_output.py` enforces
  `2…8,11,12` because **steps 9 and 10 are parked**. The eval was stale; it now matches the validator
  and names 4b, 9 and 10 as emitting nothing.
- **Stale step numbers** in the charter's notes — "Step 12 — not INSERT targets" is step 13, "Step 13 —
  two tables that look like branch config" is step 14 — plus the "Book last" sentence, which predates
  step 12, and the "four unverified joins" escalation, which now points at `confirmed-joins.md`'s
  live list instead of a fixed count. The frontmatter no longer claims a tab count.

#### Still open

`docs/reference/job-chains/box-fe-acc-batch-runtime.md` **does not exist** and is linked from four
files. Pre-existing, unrelated to this cut, not fixed here.

### 2026-09-21 (end of day) — dry-run mode, repo write-protection, and the summary rewritten

#### ⛔ The BOX deployment repos are read-only, and the charter now says so twice

`[stated: Edouard, 2026-09-21]` A Devin session can attach several repos, and **an attached repo can be
committed to or raised as a PR.** On `cib-boxfin-dbboxfe` and `cib-boxacc-dbboxacc` that must never
happen: no commit, branch, push, pull request, draft PR or **local edit**, including when the agent is
certain the code is wrong. A defect found there is a finding in `05-source-questions.md` with its
file:line, and an escalation.

Recorded in **hard rule 5** (extended from "never write GBO" to cover source) and as a prominent block
in *Source questions*, because a rule that only exists in one place is a rule that gets missed. The
practical note matters too: attaching a repo grants write by default, so a run's opening report must
state which repos were attached and in which mode. Belt and braces — the walk's output is always a file
a human executes, never an action the agent takes.

The automation repo is explicitly excluded: the agent writes its run folder there by design.

#### `RUN_MODE = dry-run` — the agent explains the walk instead of executing it

New mode, plus a Devin-ready prompt at
`agents/sigom-box-fe-configs-agent/prompts/dryrun-ny-sch.md`. **I had proposed this in the 2026-09-21
assessment and never built it; this is the build.**

Purpose: let a BOX FE expert review the agent's *reasoning* without anyone running a query — because
what an expert can usefully check is the **plan**, not the data, and sitting them through forty queries
wastes the scarcest resource in the project.

The deliverable is organised **by decision, not by query** — a query log is unreviewable by someone who
hasn't read the catalogue. Per walk step: what will be inserted and why that row count; where each value
comes from (mined / allocated / structural / `DERIVED`, each named); what the agent is unsure about, in
the reviewer's language; and what it needs from him.

Extra obligations, because a dry-run has no CSV behind it and nothing downstream catches a mistake:
every claim carries its evidence tag; the things that **cannot** be verified are stated loudly rather
than footnoted; and a gate is never presented as passing because the plan looks sound. The prompt also
carries a consequence table — *"what happens if a step-12 row is missing?"* — because that is what a
reviewer actually asks.

`validate_run_output.py` still applies: the illustrative SQL must pass the mechanical checks even though
it will never execute.

#### Executive summary rewritten, not amended — rev. 7

Six revisions of accumulated corrections had left it contradicting itself three times: a heading reading
"Five gates" over a six-row table that also omitted gate 0g, "five objects declare a pre-commit" over a
two-row table, and the **withdrawn** Tier-1 rehearsal described in the present tense. Patching that
again would have produced a seventh layer.

Rewritten from the current state. The revision history moved to this changelog, where it belongs. New
shape: the walk (15 objects), seven gates with honest state, **a section on what the source code
changed and why** — the committing pre-commit and the absence of FK constraints — then eight numbered
questions ranked, with gate 0c first and the `FEEFIRSTDAYSEL`-vs-`FeeCalcInterval` mapping flagged as
something we will not ask an SME to sign until it is confirmed.

### 2026-09-21 (later still) — the validator exists, and the agent can ask its own source questions

Assessment items 3 and 4. Both address the same finding: **this project's gates are prose a model
evaluates about its own output, and its source questions all had to be noticed by a human.**

#### `scripts/validate_run_output.py` — first runnable code in this repo

Deferred three times; now written and tested. ~380 lines, standard library only.

```bash
python3 scripts/validate_run_output.py runs/NY_SCH/tier2-pre/ [--strict] [--quiet]
```

**Every check encodes a defect this project actually produced.** Tested against a reconstruction of the
rejected 2026-09-18 draft: **17 FAIL, 8 WARN** — including `insert-select-from-gbo` (the `FK_OWNER_OBJ`
defect), `commit-vs-rollback` (hard rule 11), `step8-null-curves`, `insert-order`, `status-vocabulary`
(`CROSS_TIER_VERIFIED`) and eleven missing walk steps. Tested against a well-formed
deferred-verification run: **0 FAIL**.

Checks span SQL (DDL, literal PKs, `INSERT … SELECT FROM DEVENG`, missing column lists, hard-coded
identity constants, a single constant across three screens, committing-procedure conflicts, step 8's
null curves, ordering, statements for parked steps), the findings table (all 15 walk steps present,
canonical statuses, evidence tags) and cross-artifact state (preflight present, cited CSVs exist, no SQL
for an open SME decision).

**One design decision worth recording:** `EVIDENCE_REQUIRED` rows alongside *draft-marked* SQL report
`INFO`, not WARN — that is the designed state of a deferred-verification run, and a validator that cries
wolf on the mode the charter recommends would be switched off within a week. Unmarked SQL with
`EVIDENCE_REQUIRED` rows is a FAIL; an open `SME_DECISION_REQUIRED` is always a FAIL.

Wired into the charter's *Definition of done* (**a run with FAILs is not done**) and the procedure as
**Stage E8**, where a FAIL stops Stage F.

The constants at the top of the script — statuses, walk steps, INSERT order, identity constants,
committing procedures — **are the repo's facts expressed as code**, and the README says so. Allowed
Errors entering the walk as step 12 and not reaching several documents for weeks is the precedent this
is meant to avoid repeating.

#### `SOURCE_ACCESS_MODE` — a third evidence channel

The deployment repos appeared in agent-facing files only as a DDL source for gate 0e. `cib-boxacc-dbboxacc`
appeared in **none**. So every source question had to be noticed, composed and asked by a human — and the
2026-09-21 round, which overturned two hard rules, happened only because someone thought to ask.

New input alongside `DB_ACCESS_MODE`, with a new charter section carrying:

- **A channel-routing table** — what rows exist → the database; what the system declares → the metamodel
  (gate 0g); **what this code actually does** → the source repos; what the branch *should* have → an SME.
- **Six question shapes that must be raised rather than worked around**, headed by an unread pre-commit
  body and a column whose meaning cannot be stated (the live `FK_FEEFIRSTDAYSEL` vs `FeeCalcInterval`
  case).
- **The same contract shape as the query channel** — state the question, name the repo, say what the
  answer would change, say whether the run is blocked, stop and wait.
- A new run artifact, `05-source-questions.md`, where each answer carries a **file:line citation**. An
  answer without one is `[stated]`, not `[confirmed]`.

`SOURCE_ACCESS_MODE = none` is legitimate — questions accumulate and dependent findings stay
`EVIDENCE_REQUIRED`. **Guessing is not**: reasoning is precisely what the source round proved unreliable.

The NY_SCH kickoff sets it to `direct`, since Devin has both repos.

### 2026-09-21 (later) — the three dangerous contradictions fixed, and gate 0c made signable

Two targeted pieces of work, both from the 2026-09-21 repo assessment. Not a general cleanup — the wider
staleness (ten previously-reported defects still open, the coverage table's nine wrong step numbers, the
nine copies of `F___SEQUENCE`) is untouched and still queued.

#### 1. Three sites that would have made an agent do the dangerous thing

All three predated the source round and told an agent to treat a **committing** procedure as if it were
safe:

| Site | Was | Now |
|---|---|---|
| `03-fe-sigom-config-procedure.md` **E7** | *"Call each object's pre-commit procedure after its INSERT… affects steps 2, 3, 4, 5, 6"* | **Classify first, then place the call.** Three classes with a table; the committing one gets the populate-then-call treatment |
| `03-fe-sigom-config-procedure.md` **F3** + open items | prescribed *snapshot → INSERT → call → re-snapshot → `ROLLBACK`* with no carve-out | Method now depends on the procedure's class. New **F0** step: establish whether the script is reversible at all |
| `sigom-metamodel.md` §5 | restated the superseded hard rule 10 verbatim | Corrected with the same three-class table |

Also fixed: `runs/NY_SCH/tier2-pre/README.md` proposed running the rollback test **on
`p_check_Val_Curves_precommit` itself** — the one procedure it cannot be run on — and separately listed
"wrapped in `ROLLBACK`" as something the draft *got right*. Both corrected. And the eval case's
pre-commit condition now tests *classification*, not rote placement.

**Why this mattered more than its size.** The charter was already correct (hard rules 10 and 11), but
Devin reads the **procedure** doc for sequence. A correction that lives only in the charter is not a
correction — which is the repo's structural problem in one example.

#### 2. Gate 0c: a signable request instead of a standing blocker

New artifact: **`runs/NY_SCH/tier2-pre/00-gate-0c-signoff-request.md`**. Gate 0c has been the top blocker
for three weeks, and it has not moved because *"which instruments does NY_SCH get?"* asks an SME to
enumerate from memory. The request now presents **concrete lists to tick**:

- **Q1 — the instrument set**, proposed as SLB's nine, with the Credit-Derivatives / Bond-Return-Swap
  resolution gap flagged for whoever prepares it.
- **Q2 — the four `NOT NULL` accrual values** per instrument (`FK_FEEFIRSTDAYSEL`, `FK_INTFIRSTDAYSEL`,
  `INTCOMMONBASIS`, `BYTRIGGER`), which is the part that would otherwise surface at SQL-generation time.
  ⚠️ It carries an honest caveat: **the mapping from those physical column names to the screen labels
  the metamodel declares (`FeeCalcInterval`, `InterestCalcInterval`, `InCommonBasis`) is unconfirmed**,
  and a query is supplied to close it *before* the meeting. Asking an SME to sign values whose meaning
  we cannot state is not a sign-off.
- **Q3 — `LIMIT_ERRORS`** with its newly-discovered zero default (a missing row aborts the load on the
  first failed deal), and **book scope** with its unverifiability stated plainly rather than buried.

The charter's *Human checkpoints* now makes producing this artifact part of gate 0c, so the next branch
gets it by default rather than by memory.

### 2026-09-21 — eight questions to the source repos, and the walk is not what we thought it was

`cib-boxfin-dbboxfe` and `cib-boxacc-dbboxacc` interrogated via Devin. **`cib-boxacc-dbboxacc` is new to
this corpus** — only the FE repo was previously known. Full record in
[`sigom-metamodel.md`](docs/reference/sigom-metamodel.md) §5, §6c, §6d.

#### ⛔ A pre-commit procedure writes to another table and COMMITs

`[confirmed: source]` **`PKG_ENGPRECOMMIT.p_check_Val_Curves_precommit`**, passed the step-2 header PK,
UPDATEs **step 8's** `T_BOX_FIXING_BY_INSTR_S WHERE fk_parent = pk_in` — back-filling null fixing curves
from the header defaults — and issues an explicit **`COMMIT`** after each of three conditional UPDATEs.

Two distinct problems. **The cross-table write** means a raw INSERT set that skips it produces a
genuinely different end state — the "walk is incomplete" case, not the "walk skips a check" case. **The
COMMIT** destroys the script's safety model: it commits the entire outstanding transaction, so the
draft's trailing `ROLLBACK` is not a safety net and the snapshot→INSERT→call→rollback form of procedure
step F3 cannot be used on it.

**Hard rule 10 was wrong and is rewritten.** Not "call the procedure after each affected INSERT" but
*classify it first*: **no-DML** (call as a gate — `P_ENGFixingCurve_PreCommit` is validation only),
**same-row DML** (don't supply the columns it computes), **cross-table or committing** (never inside a
transaction you intend to roll back). **New hard rule 11** states the rollback position explicitly.

**The fix is elegant:** the UPDATEs fire only on *null* curves, so step 8 now emits populated values —
filling any GBO null from the header and tagging it `DERIVED` with a source citation — and *then* calls
the procedure. Updating nothing commits nothing, and finding nothing to do is positive evidence the
INSERT set matched SIGOM. **That is procedure step F3, solved**, after months as the biggest
unmitigated risk with no defined method.

#### ⛔ There are no foreign key constraints. Anywhere.

`[confirmed: DDL]` Across all thirteen FE walk and ACC config tables: **no `FOREIGN KEY`, no `CHECK`, no
`DEFAULT`.** Every `FK_*` is a plain `NUMBER`; integrity is entirely application-layer.

**New hard rule 12.** The metamodel is the *only* source of truth for the join graph — there is no
dictionary copy to check against, which retroactively explains why every relationship in this project
has had to be inferred, and makes gate 0g load-bearing rather than convenient. And **a wrong FK inserts
cleanly**, failing silently later in a batch. The `pBranch → Branch Group` trap is unguarded.

What the DDL *does* constrain: `NOT NULL` sets (the minimum INSERT list per step) and unique indexes —
including **global** unique indexes on `T_BOX_ENGCONF_S.DESCRIPTION` and `T_BOX_ENGFCURVE_S.DESCRIPTION`,
so a mined description that already exists is a **hard failure**. New pre-flight on Q-02/Q-03.

#### Three step-level corrections

- **Step 6 has four `NOT NULL` accrual *values*** — `FK_FEEFIRSTDAYSEL`, `FK_INTFIRSTDAYSEL`,
  `INTCOMMONBASIS`, `BYTRIGGER`. They can't wait for an SME, so **gate 0c is "which instruments *and*
  these four values for each"**, a bigger ask than recorded. Its unique index `(FK_PARENT,
  FK_INSTRUMENT)` also *proves* the row-count-is-scope claim asserted since 2026-09-17.
- **Step 12 is more severe than recorded.** `LIMIT_ERRORS` defaults to **`0`** when no row exists for a
  `(FK_BRANCH, FK_INSTRUMENT)` — so the first failed deal aborts the whole load. One row per in-scope
  instrument is **mandatory**, same conclusion as step 11 for an unrelated reason. It is a per-run
  tolerance, not cumulative.
- **Steps 9, 10 and 4b are ordinary SIGOM-UI configuration** — nothing in either repo writes them.
  Neither derived nor batch-populated. The SME question sharpens from "what are these?" to "does NY need
  them?"

#### Step 11 proven from source; step 5 is a runtime prerequisite

`PKG_ENGGNCP_OPTZ.p_create_process_queues_optz` reads `T_BOX_CONF_BY_BOOK_S` joined to
`T_BOX_ENGCONF_X` by `(FK_BRANCH, FK_INSTRUMENT)` and **inserts one queue row per distinct `FK_LABEL`**.
`CIBAUKI-4704` introduced that cursor in r0.0.27 *specifically* to drive queue creation from the book
configuration. The join to `T_BOX_ENGCONF_X` makes **step 5 a runtime prerequisite** — without it
nothing is queued at all.

#### ✅ Grants have names — the longest-standing blocker gets a precise ask

`[confirmed: deployment scripts]` **`BOX_FE_RD`** (read) / **`BOX_FE_WR`** (full DML), and
**`BOX_ACC_RD`** / **`BOX_ACC_WR`**. No `CREATE ROLE` in either repo — the roles pre-exist. Ask the DBA
for those **by name** rather than for "Tier 2 BOX_FE access", which reads as already-granted because for
GBO it is. **`F___SEQUENCE` is in the same grant set**, so this also discharges Q-G3b. FE creates **no
synonyms**, so every query must stay schema-qualified.

#### BOOK vs LABEL — a correction to `book-and-folder.md`

`[confirmed: source]` That page treated Book and Label as one word for one thing. **They are three
things.** The **process LABEL** is the BOX configuration concept (`PGT_DOMAINS`, `FK_OWNER_OBJ =
17910.4`) — what `FK_LABEL` holds and what batch procedures take as `P_Label`. **`BOOK`** is the
trading-book identifier string on datalake rows, part of the raw unique key. **raw `LABEL` /
`DEAL_LABEL`** are datalake attributes that drive nothing. The bridge is a function:
**`BOX_SYS.PKG_BOXUTILITY.f_GetBookByLabel(P_Label)`** → a book string → filter of raw rows.

The B4 derivation survives and is now better grounded: use the **DATADEAL** family (`FK_LABEL` +
`FK_FOLDER`, both resolved) rather than the RAW strings. `[open-question]` whether one label maps to one
book or many — if many, "the desk" is the label, not the book.

#### ACC: the topic/condition lists are generated, not inserted

`[confirmed: source]` **`PKG_ACCTPROP.f_GenTopicCond`** reads a portfolio property's
instrument/branch/date, finds the matching `T_BOX_CONF_LO_PROP_S`, and **inserts the missing
`T_BOX_ACCT_LIST_TOPIC_S` / `T_BOX_ACCT_LIST_COND_S` rows** from that config's three topic arrays, then
clears de-registered rows and re-validates. So the ACC walk is *configure the local-properties arrays →
insert the portfolio property → call the generator*, **not** "insert the junction rows" — and an agent
that hand-inserts them fights `p_ClearList`. It closes a loop with the metamodel, whose
`apLocalTopicArray` / `apGlobalTopicArray` / `apInternalTopicArray` are exactly what the procedure walks.

All three ACC pre-commit bodies write **only to their own row**, but each computes columns the agent must
not supply: `STATUS`/`MESSAGE` (a built-in validation oracle), the GLTA denormalised date/location
fields, and audit columns. **Audit stamping uses three different mechanisms across ACC** — a trigger, a
procedure, and an in-procedure `UPDATE` — so no single pattern can be assumed.

#### Triggers, and an operational step nobody owned

**No triggers on any of the nine FE walk tables.** ACC has exactly one:
`G_T_BOX_ACCT_PORT_PROP_S_BIU`, an audit stamp. (`T_BOX_BOOK_CONFIG_S` — the *second* Book object —
has one too, which is further evidence it is real and in use.)

**There is no "provision a new branch" script** in either repo. But `PKG_BOXTOOLS.p_Scheduling_Monitor`
generates a branch's processing calendar, and **someone has to run it** — an onboarding action outside
the FE config walk that no checklist owned. Now flagged in the orchestrator. Logging self-seeds via
`PKG_BATCHPROCESS_MBJ.p_ReadLog`, so that needs nothing.

### 2026-09-21 — BOX ACC read from the metamodel before its agent is written, and Book/Folder recorded

Two additions. The first applies the 2026-09-18 metamodel technique to **BOX ACC**, so the ACC agent
inherits declared facts instead of discovering them. The second records the **BOOK / FOLDER**
distinction and the gap between them.

#### BOX ACC — declared scope, and one trap that would have cost a draft

`[confirmed: DB via Edouard]` The ACC configuration module is **`35000006.65`** — 31 objects, 269
declared fields — with ACC content spread across five more modules (settlement, deal data, platform,
account/SSI standing data, and an **AUKI migration** module nobody had recorded). Module names are
*inferred from membership*, never read: `FK_PARENT` does not resolve in `T__OBJ_DEF_S`.

**⚠️ `pBranch` does not always mean branch.** Twelve ACC objects declare `pBranch → T_PGT_BRANCH_S`.
**Two do not** — `BOX - Acct Port Property` (portfolio properties, the first thing the ACC agent
configures) and `BOX - Config LOC Property` declare `pBranch → **T_PGT_BRANCH_GROUP_S**`. Same field
name, different target. For NY_SCH that is `FK_LOCALGROUP = 21447.4` against `BRANCH_PK = 20007.4` —
both valid PKs, and the wrong one fails silently.

This **corrects an over-generalisation in the ACC charter**, which read ACC as group-keyed throughout.
It is not: two objects are group-keyed, twelve are branch-keyed, and assuming either way for all of
them is wrong. It also promotes the orchestrator's Phase 0 branch-group resolution from a checklist
item to a **hard prerequisite for ACC**.

**⚠️ `T_BOX_LINK_ARRAY_X` is not one relationship — it is seventeen.** Where FE gives each object its
own bridge, ACC puts **nine objects and 17 relationships** into one generic table, `FK_BS` pointing at
**nine different target tables** depending on `(FK_OWNER_OBJ, FK_EXTENSION)`. `BOX - Config LOC
Property` alone puts four arrays in it, three targeting the same table — so owner *and* target still
don't disambiguate; only `FK_EXTENSION` does. `confirmed-joins.md` recorded exactly one of the
seventeen, confidently. **Never filter a shared bridge on `FK_PARENT` alone.**

**Pre-commit is systemic, not a quirk.** **857 objects in 172 packages** declare one. Hard rule 10 is
restated accordingly: *assume an object runs code on save until you have checked that it does not*, and
check **both** `PRE_COMMIT_PROC` and `FK_PRECOMMIT`, since either can be null while the other is set.
For FE and ACC together, only **three packages** and nine procedures matter — `PKG_ENGPRECOMMIT`,
`PKG_ACCTPRECOMMIT`, `PKG_SYSPRECOMMIT` — which makes reading the source a bounded job. **Three of the
most consequential ACC objects declare one: portfolio properties, topics, and GL accounts** — the
object where this repo's never-invent rule is most absolute.

Also: the FE `p_check_Val_Curves_precommit` fires on the *Config screen*, so it probably covers walk
steps **7–11** as well as the 2/5/6 already confirmed — one Q-G6 measurement settles it. New field kind
**`11.1`** (`sql…`) is a **screen filter parameter, not a stored column**; excluding it and `6.1` from
INSERT column lists is now a rule. `[open-question]` ~40 of the 172 packages carry a `PKG_MAD_` prefix,
mostly Spain/EU regulatory — **does a branch in a new jurisdiction need its own?**

#### BOOK and FOLDER — new page

`[stated: Edouard]` **BOOK** (Libro, Label) is **the desk**, and contains many **FOLDERS**; a folder is
an **aggregation of trades / Murex portfolios**, owned by the external system **GER** and distributed
to BOX. Book lives in `PGT_SYS.PGT_DOMAINS` where `FK_OWNER_OBJ = 17910.4`; folder in
`PGT_STC.T_PGT_FOLDER_S`. **BOX FE and BOX ACC both partition processing on (BOOK, INSTRUMENT, BRANCH)
to parallelise jobs.**

**This resolves walk step 11's standing open question.** `T_BOX_CONF_BY_BOOK_S` is a **batch-partitioning
table, not business configuration** — which the developer himself said was not fully understood. Its ACC
twin `T_BOX_MBJ_PROPERTIES_S` carries the same triple *plus* `Workers`, `Task_per_worker` and
`Concurrence`, which is the proof. The `0 - EMPTY` row is a **partition placeholder**; a missing row is
a **missing partition**, which is why the failure is silent.

**No BOOK↔FOLDER mapping exists in BOX** — evidenced three ways over the metamodel rather than
asserted, per hard rule 8. Stronger than "nobody built the screen": the dimensions attach to different
*kinds* of object, Folder to movements and keys, Book to job configuration. **Named risk on step 11:**
book scope cannot be verified the way gate 0c verifies instrument scope, and a missing book row means
work that is silently never scheduled.

**But it is derivable.** 41 tables carry both dimensions and **every one is a deal, RAW or MIS-view
table** — `T_BOX_DATADEAL_S` and its per-product twins carry resolved `FK_FOLDER`/`FK_LABEL`; the RAW
tables carry the pre-resolution strings. So something already resolves the pair per deal, and a
coverage check is possible for a live branch: the books appearing on actual deals, diffed against
`T_BOX_CONF_BY_BOOK_S`. Observed, not authoritative — and the natural starting point for the mapping
the team wants in future.

Two things closed along the way: **`apPortfolio` is declared as `PGT - Folders`**, so SIGOM itself
treats Folder and portfolio as the same thing; and the **BOX folder master question** — `Net
Contract.pFolder` is declared as `PGT_STC.T_PGT_FOLDER_S`, so **there is no BOX twin**.

`[open-question]` RAW carries `BOOK` *and* `LABEL` as separate columns. If Book = Label, why two?

#### Scope correction, same day — ACC content removed from the FE agent's catalogue

`[stated: Edouard, 2026-09-21]` The first pass put ACC module guidance inside
`queries/fe-config-mining.md`, which the **FE** agent reads. Each agent has its own purpose, its own
evidence base and its own catalogue; mixing them couples two agents that are deliberately separate and
puts noise in a prompt that is already long.

Fixed by separating **technique** from **instance**: `sigom-metamodel.md` gains **§11**, the
module-parameterised forms of the object, field and shared-bridge queries, owned by no agent.
`fe-config-mining.md` keeps its FE-only instance with the module hard-coded and a one-line pointer.
The ACC charter gains a *Queries* section stating that its catalogue will be
`queries/acc-config-mining.md` when built, and that it does not read the FE file. One FE eval condition
was re-worded to state the general rule rather than cite ACC objects.

### 2026-09-18 — SIGOM declares itself: the metamodel, and the end of inferred joins

`[confirmed: DB via Edouard]` `GOM_GLB_SYS` holds a self-describing object catalogue. **Every
relationship this repo has been inferring one incident at a time is declared there.** New document:
[`docs/reference/sigom-metamodel.md`](docs/reference/sigom-metamodel.md). New gate **0g** (Q-G7),
which needs no `BOX_FE` access and runs before the walk.

Two tables carry it. `T__OBJ_DEF_S` — one row per SIGOM object, naming its `BASIC_STORAGE`,
`EXT_STORAGE` and what runs on save. `T__EXT_DEF_S` — one row per field, naming **what that field
points at**. `T__OBJ_DEF_S` describes itself (`PK 1.1` = `_OBJ_DEF`, stored in `T__OBJ_DEF_S`), so it
is authoritative rather than documentation that drifted.

**What it closed**

- ✅ **The product-shaped-branch question — the oldest open item in the FE model.** Accrual Exceptions
  and Allowed Errors both declare `pBranch → PGT_STC.T_PGT_BRANCH_S`, the geographic branch master. The
  `BOX CCS` / `BOX FX` / `BOX IRS` values seen in BOX-DEV are rows *inside* that overloaded table
  (~137 rows: entities, SPVs, counterparties, test records). The walk's grain is correct, and the
  kickoff's *stop the run* condition is withdrawn. This was question A of the executive summary.
- ✅ **`FK_INSTRUMENT`, declared across the walk.** `T_PGT_SUB_PRODUCT_S` on six objects;
  **`V_BOX_PROC_INSTR_S`** on the two *fixing* objects (steps 8, 13). That is why Q-05c was wrong and
  why Q-07 legitimately differs from its neighbours — one table, mechanically.
- ✅ **Q-08 and Q-09's `FK_PARENT`**, `[open-question]` since the tables were named and unvalidatable
  against tables empty in Tier 1 PRE. Declared as `amZeroCoupon` / `amCurrencyBasis`, owned collections
  of `BOX_ENG_Config` — so the parent *is* the header. An empty table cannot validate a join; a
  declaration does not need to.
- ✅ **The `_X` convention**, promoted from `[inferred]` to `[confirmed]`. It is `FK_KIND = 4.1`, a link
  array whose `_X` table is the field's `EXT_STORAGE`. A `3.1` owned collection gets no bridge because
  its rows belong to the parent — which is the whole distinction.
- ✅ **Step 11 and step 12's complete column lists**, and steps 9/10's, which were unknown.
- ✅ **Step 14's `NOT_BRANCH_SCOPED`**, now evidenced by declaration: `BOX_ENG_Setup` and
  `BOX_ENG_Days_Matured` declare no branch field at all.

**What it opened, and the second is serious**

- ⚠️ **A declared tab with no walk step.** `BOX_ENG_FixingCurve.apYieldCurve` → `T_BOX_ENGFIXDISC_S`.
  Now **step 4b**, `EVIDENCE_REQUIRED`, parked with steps 9/10 — empty in Tier 1 PRE, which is not
  evidence it is unnecessary. **Not** step 9's Yield Curve (`T_BOX_ENGZCCONF_S`); two "yield curve"
  objects at two levels, which is exactly how a step goes missing. Found by set difference rather than
  by someone noticing — which is what gate 0g is for. Allowed Errors went unnoticed for weeks.
- ⛔ **Pre-commit procedures on the spine of the walk.** Five objects declare `PRE_COMMIT_PROC`, covering
  steps 2, 3, 4, 5 and 6 — `p_check_Val_Curves_precommit` on `BOX_ENG_Config`,
  `P_ENGFixingCurve_PreCommit` on `BOX_ENG_FixingCurve`. **A raw INSERT is not the whole operation.**
  New **hard rule 10**: the script calls the procedure after each affected INSERT, using the PK variable
  it already holds. The draft is non-executable until the bodies are read — committed in
  `cib-boxfin-dbboxfe` `[stated: Devin]`; `ALL_SOURCE` and `ALL_OBJECTS` return the spec only, because
  `EXECUTE` privilege never reveals a package body.

  **This also gives procedure step F3 its first method** — flagged since the procedure was written as
  the step most likely to catch a real defect and the one with no defined comparison. Snapshot, INSERT,
  call the procedure, re-snapshot, `ROLLBACK`.

**`FK_OWNER_OBJ` corrected, for the second time in one day.** It is **the screen the row is edited
through**, not the owning module — `35000126.65` is `BOX_ENG_Config`; the module is `35000005.65`. And
it is **not one constant across the walk**: the walk spans three screens, so a single value is wrong for
steps 3, 4 and 12. The derivation (base table → object PK, NULL extension; extension table → the
extension's `FK_PARENT` and own PK) validates **four for four** against live Tier 1 rows and needs no
`BOX_FE` read — so **Q-G6 comes off the deferred list**.

The morning's reading was built from two tables that happened to share a screen. `T_BOX_ENGACCRCONF_S`
is the case that breaks it: registered as `BOX_ENG_AccrualConfig`'s own storage, yet its rows carry
Config's identity, because the Accrual tab is a *composition extension* of the Config screen.

**A near miss worth recording.** Read as if `T__OBJ_DEF_S.FK_CONNECTION` pointed at `T__OBJ_DEF_S`,
`35000007.65` resolves to **"BOX - Colour Config"** — a plausible-sounding row from an unrelated
registry. Same failure as `6401.4` naming two different quote references. **A PK is only meaningful with
its table**, and `35000005.65` — the module every BOX FE object hangs off — does not exist in
`T__OBJ_DEF_S` at all.

**`confirmed-joins.md` got shorter, deliberately.** The instrument map, the `_X` convention and the
identity columns are no longer patterns this repo maintains by hand; they are lookups. That page keeps
what the metamodel does not cover — cross-environment rules, branch identity, PK allocation, the
known-broken list — and cites the metamodel for the rest. Two copies of a fact is how the fact drifts.

Also corrected while in the files: `03-fe-sigom-config-procedure.md`'s Stage E still ordered statements
`2→…→11` and classified steps 12/13 under the pre-Allowed-Errors numbering, so following it literally
would have dropped step 12 and misclassified two more; and its open-items list still declared gate 0d
unresolved and the procedure stopped at Stage D, both stale since 2026-09-17.

### 2026-09-18 — first full draft SQL reviewed and rejected: a BOX row is not a GBO row re-addressed

The agent produced `NY_SCH-tier2-pre-draft.sql` end to end. **The PK mechanism worked perfectly** —
every PK a `F___SEQUENCE(<table>,'X')` call on a declared variable, children referencing their parents,
draft header present, `ROLLBACK` at the end. The gate that was open longest is closed in practice, not
just on paper.

Five defects, three of them one defect wearing three hats.

**1. SIGOM identity columns copied from the source.** `[confirmed: DB via Edouard]` The INSERT carried
`FK_OWNER_OBJ` from `DEVENG.T_PGT_ENGCONF_S` — where every row holds `12198.4`, the **GBO** Financial
Engine module — into `BOX_FE.T_BOX_ENGCONF_S`, where every row holds `35000126.65`, the **BOX** one.
`FK_EXTENSION` behaves the same and varies per table (`35001114.65` Accrual, `35001566.65` branch
bridge). These are **constants of the destination table**, read with the new **Q-G6**.

→ **Charter hard rule 9**, which generalises past the two columns: a GBO row and its BOX twin differ in
three kinds of column — **mined** (from GBO), **allocated** (`F___SEQUENCE`), **structural** (from the
target). `INSERT … SELECT` collapses all three, so every INSERT now needs an explicit column list and a
per-column classification.

The evidence was already in the repo: Q-05c's own result note recorded these as `.65` BOX-DEV values
*while the same row's mined FKs were `.4` and `.21`*. Written to corroborate the auth-code finding,
never read as the rule it implies. Fourth instance of "the answer was already here".

**2. Q-07 had no `FK_PARENT` filter** and was narrowed with a `MIN(PK)` subquery — an arbitrary row, not
NY's. Corrected to `WHERE FK_PARENT = &&GBO_CONFIG_PK`, the predicate steps 6, 8, 9 and 10 already use.
**Second instance of a catalogue join missing its mining predicate and a run filling the blank** (Q-04
was the first, three days earlier). Every remaining unfiltered `SELECT *` in the catalogue has now been
checked against its step.

**3. Step 5 blocked for want of the values in defect 1.** `T_BOX_ENGCONF_X` "requires BOX-specific
`FK_OWNER_OBJ` and `FK_EXTENSION` values not present in the supplied GBO evidence" — correct observation,
wrong conclusion, and **internally inconsistent with the same draft silently copying those columns
elsewhere.** That inconsistency is the clearest signal in the draft. New **Q-01c** documents step 5's
four values; the charter now calls a step-5 block run-stopping, since a configuration with no branch
association belongs to nobody while looking complete.

**4. Q-06 blocked on `FK_BRANCH` semantics** — conflating *cannot mine* with *mined, needs sign-off*.
The mine works (`FK_PARENT = 64408.35`); `FK_BRANCH` resolves into shared `PGT_STC`; and the GBO
evidence on `T_PGT_ERRORS_FE_S` points to geographic branches. Mine it, status `EVIDENCE_REQUIRED` with
the product-shaped-branch question attached.

**5. Attribution.** Six instruments and `LIMIT_ERRORS` 115/100 recorded as confirmed / "User decision"
with no name or date, while gate 0c is still ⛔.

**Blocks 8, 9, 11 and 12 were correct** and stand.

### 2026-09-18 — environment suffixes are queryable, not inferred

`[stated: Edouard]` `PGT_SYS.T_PGT_SOURCE_S.SIGOMID` maps auth-code suffixes to named environments
(`4` = global, `21` = Tier 1 Madrid). `PGT_SYS` is a shared schema, so **one query in any environment
returns the whole registry**, with no `BOX_FE` access needed. New **Q-G5**.

This turns the repo's suffix model from pattern-matching into lookup, and should settle three things on
first use: **`.44`**, sighted twice and never explained; **`.65` = BOX-DEV**; and **`.35` = NY Tier 2** —
the last two asserted here on circumstantial evidence since the corpus began.

### 2026-09-18 — Q-G4 was missing a walk table

`T_BOX_ERRORS_FE_S` entered the walk as step 12 on 2026-09-17 and was never added to the gate 0e
presence list. The gate would have passed on an environment missing it. Now 15 tables, not 14.

### 2026-09-18 — a quote reference decoded: it is a tuple, not an opaque id

`[confirmed: DB via Edouard]` A supplied query settles what
`PGT_MRK.T_PGT_QUOTE_REFERENCE_S` actually contains. Two of its joins were already in this repo; **two
were not**, and three FK columns had never been seen.

| Column | → | Schema | Status |
|---|---|---|---|
| `FK_QUOTESOURCE` | `PGT_MRK.T_PGT_QUOTE_SOURCE_S.PK` | `PGT_MRK` | Already known |
| `FK_QUOTETYPE` | `PGT_SYS.PGT_DOMAINS.PK` | `PGT_SYS` | Already known |
| **`FK_QUOTEINSTRUMENT`** | **`PGT_STC.T_PGT_CURR_PAIR_S.PK`** — currency pair (`SHORTNAME`) | `PGT_STC` | **New** |
| `FK_QUOTEDIRECTION`, `FK_MATURITY`, `FK_PARENT` | targets unconfirmed | — | **New columns** `[open-question]` |

`T_PGT_CURR_PAIR_S` is new to this repo — a currency-pair master in `PGT_STC`, therefore shared and
identical in every environment. The columns above are a subset; the table's full shape is unconfirmed.

**Two things follow, and both are useful.**

**Step 4's findings become reviewable.** An SME cannot meaningfully sign off `6401.4`. They can sign off
*"Santander NY spot closing prices, EUR/USD"*. New query **Q-04b** decodes a quote reference into
(currency pair, source, type) for exactly that purpose — a **comprehension and review** query, explicitly
not a mining one. Worth stating plainly in the catalogue: **this agent never creates a quote reference.**
They are pre-existing market-data objects; step 4 writes the *bridge* row pointing at them. A required
reference missing from the target is a market-data provisioning escalation, never a row to create.

**It explains the `6401.4` collision structurally.** A quote reference's three identity components split
across schemas: currency pair (`PGT_STC`) and quote type (`PGT_SYS`) are **shared**, the quote **source**
(`PGT_MRK`) is **not**. The same PK naming a different feed in two environments is therefore exactly what
the structure predicts, rather than an anomaly. Cheap confirmation, recorded as a follow-up: run Q-04b
for `6401.4` in both environments and read which component diverges — pair and type should match, source
should differ.

**A smaller generalisation, recorded with its caveat.** `FK_PARENT` means "the owning object" beyond
`_X` bridges — it holds on `_S` tables too (`T_*_ENGACCRCONF_S.FK_PARENT` → the configuration header).
So an unfamiliar `FK_PARENT`, such as the one on `T_PGT_QUOTE_REFERENCE_S`, is best read as *"what owns
this row?"*. Flagged `[inferred]`, not stated — and one `FK_PARENT` in this corpus is **proven wrong**
(`T_PGT_BRANCH_INST_S`), which is precisely why it stays a hypothesis to check rather than a rule.

### 2026-09-18 (latest) — the rehearsal is withdrawn: run against the real target and defer the reads

`[stated: Edouard, 2026-09-18]` **Target Tier 2 PRE — the real target — and defer only what access
blocks**, rather than substituting Tier 1 PRE as a stand-in destination. The split-tier rehearsal is
withdrawn.

**Why it is better, in one line:** it replaces an arbitrary deferred set with a nameable one.

| | Deferred-verification (new) | Split-tier (withdrawn) |
|---|---|---|
| Target | **The real one** | A substitute |
| Reference FKs | **Native — no portability question** | Every one needs cross-environment checking |
| Gate 0f | **Not applicable** | Required |
| Step 4 (quote references) | **In scope** — `PGT_MRK` resolves natively | Blocked; NY's references are Tier-2-local |
| Output | **The real deliverable**, one verification pass from executable | Never executable anywhere |
| Writes to a shared pre-prod environment | **No** | Yes, and needed an owner's sign-off |
| Deferred set | The BOX-side existence reads, and gate 0e | Whatever reference data happened to be local |

**What is deferred, precisely:** procedure step **C2** (*"does a row already exist on the BOX side?"*)
for every walk step, plus **gate 0e**. Nothing else — mining, walk order, dependency graph, value
derivation and SQL generation all run completely.

**What that costs, stated rather than glossed.** Every BOX-side status becomes assumed rather than read,
so:

- Findings are `EVIDENCE_REQUIRED`, never `CONFIRMED_ABSENT` on an assumption. NY almost certainly has no
  `BOX_FE` rows — that is the precondition for the job — but near-certain is not confirmed, and this repo
  does not let those collapse.
- **The SQL is a marked draft and does not execute.** If a row does already exist — a partially
  configured branch, or a shared configuration NY should reuse rather than recreate — an `INSERT` would
  be wrong.
- **Gate 0e becomes the single release gate.** One Q-G4 run plus the deferred C2 reads, and the draft
  becomes executable **without regeneration**. That is the whole point of targeting the real environment.

**The structural assumption**, recorded as `[stated]` not confirmed: Tier 2 PRE's `BOX_FE` has the same
tables and columns as Tier 1 PRE's. It has a validated reference — the Tier 1 run confirmed all 15 walk
tables and `V_BOX_PROC_INSTR_S` present, 80 objects visible — and is discharged by the same Q-G4 run that
closes gate 0e. **Structure, never values:** reading Tier 1's column list is fine; reading a Tier 1 row
into NY's configuration is hard rule 6.

**The blocker from the previous run dissolves.** NY's 38 quote references are Tier-2-local (`.35`), which
is exactly why they were absent from Tier 1. Targeting Tier 2 makes them native — `PGT_MRK` is shared
between BOX and GBO within an environment — so **step 4 is fully in scope** rather than
`not rehearsable`.

**The Tier 1 rehearsal folder is kept, not deleted.** It produced real findings that the Tier 2 run
cites: `PGT_MRK` environment-specificity, the `6401.4` collision, the Tier 1 structural reference, and
four query defects. Marked superseded with the reasoning.

The charter gains a **Deferred-verification runs** section stating this as the *preferred* answer to a
read-blocked target, with split-tier retained below it for cases where the real target cannot be
targeted at all. Gate 0f is marked not-applicable to same-environment runs; gate 0e's row records its
release-gate role; the procedure marks C2 deferrable and Stage D0 not-applicable. Three new eval failure
conditions cover assumed `CONFIRMED_ABSENT`, unmarked or executed draft SQL, and Tier-1 values entering
via a structure lookup.

### 2026-09-19 — `PGT_MRK` is environment-specific; step 4 is not rehearsable, and that is a finding

The rehearsal's second run produced one genuinely new fact about the platform and three more query
defects of familiar shapes.

#### 🔑 `PGT_MRK` does not replicate across environments — the open question, answered

`[confirmed: DB via Edouard]` NY_SCH's fixing curve references **38 quote references**; only **2** exist
in BOX Tier 1 PRE. The suffixes explain it entirely: **35 of the 38 carry `.35`**, NY's own Tier 2 auth
code. They were allocated locally. Quote references are largely *local market-data objects*, not shared
reference data, and Tier 1 has never had reason to hold Santander NY spot closing prices.

**One PK collides, and it is instructive.** `6401.4` resolves to **SANTANDER NY SPOT CLOSING PRICES** in
GBO Tier 2 and **EUROPEAN CENTRAL BANK FIXING** in BOX Tier 1 PRE. Same PK, different object — and it
carries the `.4` "global" suffix. So **`.4` does not guarantee identity inside `PGT_MRK`** the way it
does inside `PGT_STC`/`PGT_SYS`. That is a real caveat on the auth-code model, recorded as such.

#### The blocker is an artifact of the rehearsal, and provably absent from the real run

The run stopped and asked whether to refresh Tier 1 PRE with the missing references or adopt a
"target-approved quote-reference mapping". **Neither.** `PGT_MRK` is confirmed shared between BOX and
GBO *within* one environment; all 38 references were read from GBO Tier 2's `PGT_MRK`, so **BOX Tier 2
sees the same 38 rows**. Step 4 resolves natively in the real target.

So **step 4 is `EVIDENCE_REQUIRED`, annotated *not rehearsable cross-environment*, with no SQL emitted —
and the other thirteen steps continue.** The charter gains a *Some steps are not rehearsable* section
stating that this is a finding rather than a failure, and naming the two things that must not happen:

| Tempting | Why not |
|---|---|
| Load the source environment's market data into the target | Polluting a shared pre-production environment to satisfy a test |
| Substitute the target's equivalents so the curve resolves | Hard rule 6. It would point NY's curve at ECB fixings instead of Santander NY closes — an error nothing downstream catches until the numbers are wrong |

**Stopping was the right instinct; stopping the whole run was not.** The eval case gains a failure
condition for each.

#### Three query defects, two of them familiar shapes

**A diagnostic filtered by its own expected answer.** `ALL_TAB_PRIVS … AND GRANTEE IN
('BOX_ADMIN','BOX_FE','PUBLIC')` found no grant and was reported as a gate still open. Unfiltered, the
same query returns **seven grantees** — `F___SEQUENCE` is reachable. A filter on the column holding the
answer can only confirm or fail to confirm a guess. **Hard rule 8 gains a fifth mechanism:** for a
discovery question, `SELECT *` and read the result. New query **Q-G3b** (function reachability), written
unfiltered, with owner and synonym lookups alongside.

**A branch code guessed for the third time.** `LONDON`, after `SLB` and `ESP`. The values are `MADRID`
and `LND BRANCH`. Correcting the string again would be the fourth patch on one value, so the fix is
structural: new **Q-G1b** lists `PK, CODE, DESCRIPTION` from the ~137-row registry — **enumerate and
pick, never predicate on a guessed string**. Reference branches now have the same
never-typed-by-hand discipline `&&BRANCH_PK` always had.

**A comparison query with a narrow column list.** Q-14 compared two environments on two columns; "same
object" is otherwise a claim about the fields you happened to select. Now `SELECT *`.

### 2026-09-18 (late) — the purpose restated, and gate 0f demoted to a spot check

Two clarifications from Edouard, one of which shrinks a gate I over-built.

#### The job, stated plainly — and a paragraph added so no gate misreads it again

`[stated: Edouard, 2026-09-18]` A branch live in GBO already has its Financial Engine configuration
there as real rows — MIS header `DEVENG.T_PGT_ENGCONF_S` `PK = 64408.35`, fixing curve
`DEVENG.T_PGT_ENGFCURVE_S` `PK = 1.35`, and so on. **The agent reads those rows and creates the
equivalent rows in `BOX_FE`.** The twin tables are similar but not identical, so some values map across
directly and some need a stated rule — which is what `DERIVED` exists for.

**Finding nothing for the branch in `BOX_FE` is the precondition for the job, not a problem.** Every
walk step expects `CONFIRMED_ABSENT` on the BOX side against `CONFIRMED_PRESENT` on the GBO side, and
that pairing *is* the work.

This is not new policy — it is what the charter has always described. But gate 0f drifted far enough
from it to stop a run on exactly the condition that should have started one, so it is now stated
explicitly under *Goal*, with the instruction to **check every gate, status and query against it**. The
kickoff carries the same paragraph. The eval case gains a failure condition for treating a missing BOX
row as an obstacle.

#### 📉 `PGT_STC` and `PGT_SYS` are shared — gate 0f becomes a spot check

`[stated: Edouard, 2026-09-18]` **Those two schemas hold identical rows in every environment.** That is
most of the reference data this walk touches: calendars, currencies, the branch master, Sub-Product
instruments, all `PGT_DOMAINS` values. Checking them across environments verifies a design guarantee
rather than a risk — and it explains why the first Q-14 run matched *exactly*. It also fits the
auth-code finding, since shared reference data is allocated in the global environment and carries `.4`.

| Mined FK | Schema | Cross-environment check? |
|---|---|---|
| `FK_CALENDAR`, `FK_CURRENCY`, branch `FK_BS` | `PGT_STC` | ❌ Shared |
| `FK_INSTRUMENT`, `FK_*DAYSEL`, `FK_LABEL`, domain values | `PGT_SYS` | ❌ Shared |
| **Quote references** (step 4) | `PGT_MRK` | ✅ **The one genuine item** `[open-question]` |
| FKs to walk-created objects | `BOX_FE` / `DEVENG` | ❌ Apply-time |

So gate 0f is now **one check per environment pair, scoped to `PGT_MRK`** — not a per-run gate. It is
kept rather than deleted because "identical in every environment" is a stated design intent and real
systems drift; but it should cost one query, not a round every walk. And **a run must never be blocked
on a `PGT_STC`/`PGT_SYS` value**: an out-of-sync shared schema is a platform escalation, far bigger than
one branch onboarding.

The practical effect is immediate — the agent had been asking for exactly those comparisons, and the
kickoff now tells it to stop.

**One working assumption is thereby answered.** "`.4` reference data is genuinely replicated across
tiers rather than coincidentally numbered" was recorded as untested; it was never an assumption, it is
a shared schema. The remaining one — that `BOX_FE` table structures are identical across tiers — stands
until someone with Tier 2 grants runs the Q-G4 diff.

**Recorded where it will be found:** `confirmed-joins.md` gains a *Which schemas are shared across
environments* section. This is the second time in a week that an unwritten but knowable fact cost a
round of queries, which is precisely what that page exists to stop.

### 2026-09-18 (evening) — gate 0f blocked on a false positive; two real findings alongside it

**Gate 0f's scope was wrong, and it stopped a run that should have proceeded.** The rehearsal reported
gate 0f blocked because GBO Tier 2's fixing curve `PK = 1.35` has no row at `PK = 1.35` in BOX Tier 1
PRE. That is not a gate failure — `1.35` is the **source object's own PK**, the identity of the row
being *read*, not an FK the `INSERT` will carry. **Its absence in the target is expected and is the
reason the walk exists**; the new BOX curve gets its PK from `F___SEQUENCE`.

The gate's own output showed it **passing**: calendars, currencies, branches and all sixteen
Sub-Product descriptions matched exactly across tiers. Gate 0f now distinguishes three kinds of mined
value, with only the first in scope:

| Kind | Gate 0f? |
|---|---|
| **Reference FK** — a pre-existing shared object the new rows point at | ✅ Yes |
| **Source-object PK** — the identity of the GBO row being read | ❌ No — absence expected |
| **Intra-config FK** — points at something this walk creates | ❌ No — resolved at apply time |

Corrected in the charter's gate 0f section, in Q-14, in the kickoff and in the run log. **The run's
refusal to substitute a Tier 1 curve was correct and is preserved** — and it is more correct than it
knew: SLB's and Madrid's curves are both `FK_CURRENCY = 160.4` against NY's `159.4`, so they differ in
currency, not just in PK. Hard rule 6 held exactly as designed; the error was in what the gate checked,
not in how cautiously the agent behaved.

One **real** gate 0f item was surfaced by the correction: the **quote references** behind the curve
(step 4, via `T_*_ENGLKFC_X.FK_BS` → `PGT_MRK.T_PGT_QUOTE_REFERENCE_S`). `PGT_MRK` is documented as
shared between BOX and GBO *within* a tier; whether it replicates *across* tiers is unrecorded.
`[open-question]`

**Step 12 has a GBO source after all.** `[confirmed: DB via Edouard]` `DEVENG.T_PGT_ERRORS_FE_S`, keyed
by **`FK_BRANCH`**. The naming-rule prediction was right, so Allowed Errors is an **ordinary
mine-and-propose step**, not a step-11-style BOX-only one — error limits come from the branch's own GBO
configuration rather than a reference branch or an SME guess. The GBO column holding a *geographic*
branch PK is mild evidence against the product-shaped-branch worry on the GBO side; it settles nothing
about the BOX side.

**`SLB` and `ESP` are not branch codes.** A branch lookup searched `CODE IN ('SLB','ESP')` and found
nothing. Those are abbreviations inside *configuration descriptions*; the `CODE` values are `MADRID`
(`22.21`) and `LND BRANCH` (`20087.4`). **This repo already carried both mappings** — its own baseline
table pairs *"Configuracion -SCH (ESP)"* with branch **MADRID**. The column is confirmed to be `CODE`,
with `DESCRIPTION` alongside, which also closes Q-G1's long-standing `<CODE_COLUMN>` placeholder.

#### New: `docs/reference/confirmed-joins.md`

Four query defects in three days, and **three asserted a relationship this repo had already confirmed
somewhere else**. The information was never missing — it was scattered across thirty documents, so
"check before you assume" cost more than guessing did. One page now holds every confirmed FK
relationship and identifier, plus the known-broken and known-unconfirmed ones, and the charter and
query catalogue both point at it. **Recording a newly confirmed relationship there is now part of
confirming it** — a fact stored only where it was discovered gets missed again.

This is the first structural response to that pattern rather than another note appended to hard rule 8.

### 2026-09-18 (latest) — ⛔ Q-04 had no curve filter, and the improvised one contradicted its own join

Second defect found by the rehearsal, and again **in this repo rather than in the agent**.

**What happened.** Step 4 mines the quote-reference array behind one fixing curve. Q-04's join was
`[confirmed: DB via BOX Lead, 2026-09-10]` and correct — but it was recorded **with no `WHERE` clause
at all**, so as written it returns every linkage row in the schema. Asked to mine one curve, the agent
added a predicate on the only `t1` column the query mentioned: `WHERE t1.FK_BS IN (1.35)`.

**Why that is wrong, provable without a database.** The query's own second line asserts
`t1.FK_BS = t3.PK` where `t3` is `T_PGT_QUOTE_REFERENCE_S` — so `FK_BS` is a **quote-reference** FK.
The improvised filter then treats the same column as the **curve** PK. One column cannot be both sides
of a bridge; the query contradicts itself. The correct filter is
`WHERE t1.FK_PARENT = &&CURVE_PK` `[confirmed: DB via Edouard, 2026-09-18]`, with `&&CURVE_PK` resolved
by Q-03 rather than typed.

**The generalisable win: the `_X` bridge-table convention is now documented.** Tables ending `_X` are
bridges with two FKs in fixed roles — **`FK_PARENT` points up to the owner, `FK_BS` points across to
the linked object**. So on any `_X` table: **filter on `FK_PARENT`, join on `FK_BS`.** Already
evidenced on three tables before today:

| Bridge | `FK_PARENT` → | `FK_BS` → |
|---|---|---|
| `T_BOX_ENGCONF_X` | FE configuration header | GBO branch |
| `T_BOX_LINK_ARRAY_X` | `T_BOX_CONF_LO_PROP_S` | `T_BOX_CONDPAR_PROP_S` |
| `T_*_ENGLKFC_X` | fixing curve | quote reference |

The convention was findable and was not checked — the same failure as the Q-05c join defect earlier the
same day.

**A misleading sentence, corrected.** `fe-branch-configuration.md` read *"each linkage row's `FK_BS` —
**not a generic `FK_PARENT`** — is the join key"*. True about the join, and easily read as "`FK_PARENT`
is unused on this table." It is not: `FK_PARENT` is the curve. That phrasing is a plausible source of
the defect and is rewritten, with both roles stated.

**Two new hard-rule 8 mechanisms**, bringing it to four:

> **A catalogue query recorded as a *join* is not thereby a *mining query*.** If it lacks the predicate
> a step needs, that is a gap to report — not a blank to fill with the nearest available column.

The eval case gains two matching failure conditions. Q-04's coverage-check row is downgraded from
"Full join confirmed" to record that the join is confirmed and the *filter* was missing.

**Pattern worth noting across three days.** Three of the four join defects found so far share a shape:
a relationship that was documented somewhere in the repo, and a query written without checking. The
agent is behaving correctly each time — it uses the catalogue rather than improvising — which is why
these surface in rehearsal against branches with known answers.

### 2026-09-18 (later) — split-tier runs: mine the tier where the branch is live, write the tier you can reach

`[stated: Edouard, 2026-09-18]` Access turns out to be asymmetric: **Tier 2 PRE** has GBO only (no
`BOX_FE`) and is where NY_SCH is actually live; **Tier 1 PRE** has full access including `BOX_FE` and
has no NY_SCH. The rehearsal is reshaped around that — **mine GBO Tier 2, write BOX Tier 1 PRE.**

**This corrects an instruction I wrote on 2026-09-16.** The original rehearsal set `GBO_SOURCE = Tier 1`
alongside `TARGET_ENV = Tier 1`. That was wrong: NY_SCH is live in GBO Tier 2, so a Tier 1 GBO read
returns either nothing or another branch's configuration. A well-formed findings table built on the
wrong branch's data is worse than none, because it looks correct. **Mine where the branch is real;
substitute only the target.**

**The charter already allowed this.** `GBO_SOURCE` and `TARGET_ENV` are separate inputs, deliberately,
and the charter says in as many words that *"a Tier 1 read is not evidence about a Tier 2 branch."* The
rehearsal instructions collapsed two inputs the contract had kept apart. The charter's *Split-tier runs*
section now states the principle rather than leaving it implicit in the input table.

**What the reshaped run buys:** every mined value is NY_SCH's **real** configuration — the actual MIS
header, the actual Fixing Curve — so the findings table it produces is the one that goes to the SME for
the real run, not a throwaway. Only the destination is a stand-in. The rehearsal stops being a shape
test and becomes a genuine dry run.

**New: gate 0f — cross-tier FK resolution (query Q-14).** The catch, and the interesting part. Every FK
mined from Tier 2 is a **Tier 2 PK**; an `INSERT` into Tier 1 carrying `FK_CALENDAR = 83.4` is only
correct if `83.4` names the same calendar there. Three outcomes, deliberately not collapsed:

| Result | Action |
|---|---|
| Resolves in both, same description | Use it; tag `CROSS_TIER_VERIFIED` |
| Absent in target | `EVIDENCE_REQUIRED`, no statement — a portability finding |
| Resolves to a **different** object | **Stop and escalate** — silent wrong value, the failure this agent exists to prevent |

Gate 0f is the first gate evaluated **after** mining rather than before the walk, because it tests
values the walk produces. It gets its own procedure stage (**D0**, between mining and findings review).
The auth-code finding supplies a strong prior — `.4` PKs were allocated in the global reference
environment, so `FK_CALENDAR = 83.4`, `FK_CURRENCY = 159.4` and the Sub-Product instrument FKs are the
most likely to hold in both tiers — and the catalogue is explicit that this is **a prior, not a
conclusion**: "it ends in `.4` so it's global" is exactly the reasoning hard rule 8 forbids.

**Its answer outlives the rehearsal.** The share of FKs that verify tells you how much of the eventual
Tier 2 run is a straight replay of these findings and how much has to be re-resolved.

**Also recorded: this writes into a shared pre-production environment.** NY_SCH does not exist in Tier 1
PRE and the run creates it there. The run log now says to get an owner's OK first, keep the rollback
`DELETE`s, and label the configuration so nobody mistakes it for a real Tier 1 onboarding.

The run folder is renamed `runs/NY_SCH/tier1-rehearsal/` → **`runs/NY_SCH/tier1-pre-rehearsal/`**, which
matches the `runs/<branch>/<target-env>/` convention while keeping the rehearsal marker. The eval case
gains two failure conditions: a cross-tier FK used without gate 0f, and a split-tier run that mines the
reachable tier instead of the live one.

### 2026-09-18 — ⛔ Q-05c joined the wrong table, and an inner join was hiding two instruments

The first live rehearsal caught a defect **in this repo, not in the agent**: Devin ran Q-05c exactly as
the catalogue specified it, and the catalogue was wrong.

**The join was wrong.** `[confirmed: DB via Edouard]` `T_BOX_ENGACCRCONF_S.FK_INSTRUMENT` resolves to
**`PGT_SYS.T_PGT_SUB_PRODUCT_S.PK`** — the Sub-Product level of the Family→Product→Sub-Product
hierarchy — not to `BOX_FE.T_BOX_ENGINSTRUMENTS_S`. The key spaces are visibly different: SLB's
`FK_INSTRUMENT` values are `20111.4`, `20.4`, `20092.4`, `20330.4`, `2.4`, `20314.4`, `20213.4`, while
Processed Instruments PKs are `1.65`, `2.65`, `3.65`.

**This repo already held the answer, and the warning.** `T_BOX_CONF_BY_BOOK_S.FK_INSTRUMENT →
T_PGT_SUB_PRODUCT_S.PK` was confirmed on 2026-09-11 and written into `box-data-model.md`, in a
paragraph ending *"an 'instrument' FK is not self-evidently pointing at the same table every time."*
Q-05c was written on 2026-09-17 with a different join, flagged as assumed. **Flagging an assumption is
not a substitute for checking what is already confirmed** — that lesson is now recorded in hard rule 8
and in the data-model paragraph itself.

**The more valuable finding: an `INNER JOIN` that drops rows is a new failure mode.** SLB's Accrual tab
shows **nine** instruments on screen; the inner-join query returned **seven**, silently omitting
**Credit Derivatives** and **Bond Return Swap**, whose `FK_INSTRUMENT` values do not resolve to a
Sub-Product row. Nothing about the result looked wrong. Hard rule 8 previously covered queries that
return *nothing*; it now also covers queries that return *almost everything*:

> When a query's job is to enumerate a set, **count the base table first with no join at all**, then
> `LEFT JOIN` for labels and flag unmatched rows. A row that cannot be labelled is a finding, never a
> row to drop.

Q-05c is rewritten as two steps on that pattern. The eval case gains two failure conditions.

**It also largely explains the 7-vs-9 discrepancy** recorded on 2026-09-17: the repo's Tier 1
calibration baseline says 7 Accrual rows for SLB, and 7 is exactly what this join produces. The
baseline was very likely measured the same way. One unjoined `COUNT(*)` settles it; until then, treat 9
as the branch's instrument set. `[inferred]` The two unresolved instruments may be newer products —
Bond Return Swap is still in development — whose Sub-Product rows were allocated elsewhere; every
resolved `FK_INSTRUMENT` carries the `.4` global-reference suffix.

**A quiet corroboration of the auth-code finding.** One SLB Accrual row carries PK `.21` (this Tier 1
environment), `FK_INSTRUMENT` `.4` (global reference data) and `FK_OWNER_OBJ`/`FK_EXTENSION` `.65`
(BOX-DEV) — three different origin environments in a single row, which is what "the suffix records
where a row was allocated" predicts and what "the suffix marks an owner" does not.

**On the agent's behaviour: this is a good result.** It used the catalogue query rather than improvising
one, which is exactly the designed behaviour and is why the defect surfaced in a rehearsal against a
known branch instead of in Tier 2 against a branch with no answer key.

### 2026-09-17 (later) — 🔑 gate 0d resolved, and a missing walk step found

A BOX FE Developer answered six of the eight questions in the executive summary. Two answers are
significant, two close open questions, one adds a step, and one is an admitted gap.

#### ✅ Gate 0d is closed — PKs come from `F___SEQUENCE`

`[confirmed: source via BOX FE Developer]` The function takes `NEXTVAL` from a **shared sequence**
(`SQ_BOX_FINANENG1` for every table in this walk; `SQ_BOX_FINANENG3` serves only `T_BOX_ENGPROCESS_S`
and `T_BOX_ENGDOM_S`) and, when `seq_range = 'X'`, adds the environment's auth code as a fractional
part: `auth_code / 10^length(auth_code)`, read from the single global row in
`gom_glb_sys.t__CORE_INFO_S`.

**This explains every PK the corpus has ever recorded** — `20007.4`, `141.35`, `24.095.416,21`,
`333105.21`, `113.65` — and closes the `<integer>.<integer>` convention that has been flagged as
unexplained since the corpus began. The 2026-09-17 inference from SLB's Accrual `InternalID`s (shared
sequence, environment suffix) was correct.

**Three consequences.**

- **The agent calls the function; it never computes a PK.** `v_pk := F___SEQUENCE('T_BOX_ENGCONF_S','X')`
  assigned to a declared variable, children referencing the variable. A literal PK is still a hard
  failure — and so is a bare `SQ_BOX_FINANENG1.NEXTVAL`, which would drop the auth-code fraction. Hard
  rule 3 is satisfied not by knowing a number but by delegating allocation to the database, which is
  strictly safer than anything the agent could construct.
- **The generated SQL is environment-portable.** `auth_code` is read from the *target* at execution
  time, so a script written against Tier 1 produces correctly-suffixed Tier 2 PKs unchanged. The Tier 1
  rehearsal's `&PK_nn_*` placeholders map one-to-one onto declared variables — convert, don't
  regenerate.
- **The auth-code suffix means environment, not owner.** The corpus has read `.21` as "Madrid-owned",
  `.4` as "global/shared", `.65` as "BOX-DEV". The causal story is different: a suffix records **which
  environment allocated the row**. The Madrid correlation is real but incidental. `[inferred]` — rows
  with different suffixes coexist in one database because they were allocated elsewhere and replicated
  or imported, which also fits the runbook's "export with dynamic pk" path. Corrected in
  `sigom-reference.md`, `04-add-book-procedure.md` and `05-add-product-procedure.md`.

**Also vindicated: "finding nothing is a finding."** Q-G3's dictionary queries showed no triggers and
no defaults, and the catalogue said that pointed at application-side allocation rather than being
inconclusive. It did — the allocation lives in a function.

#### 🔴 A missing walk step: Allowed Errors

`[stated: BOX FE Developer via Edouard]` **`BOX_FE.T_BOX_ERRORS_FE_S`** — SIGOM
`BOX - Financial Engine > Process Management > Allowed Errors` — defines the **error limit before a
process crashes**, **per instrument and per branch**. It was absent from the walk entirely. The walk
is now **14 steps**, with Allowed Errors as step 12 (blocked by gate 0c like steps 6 and 11), new query
**Q-13**, and a new row in `fe-branch-configuration.md` §2.

This is the answer to *"is anything missing from the 13?"* — the question written into the executive
summary precisely because an unknown table is the failure you only discover when the batch misbehaves.
Its GBO twin, its column names and its branch grain are all **unconfirmed**; Q-13 leads with a column
query rather than assuming.

⚠️ **It also raises the priority of the unanswered product-shaped-branch question.** Allowed Errors is
one of the two BOX-DEV screens showing `Branch` values like `BOX CCS` / `BOX FX`. That oddity now sits
**inside** the walk rather than beside it: if "branch" means a product there, step 12's grain is wrong.
The developer did not answer this one — re-ask it.

#### Confirmations, a park, and an admitted gap

- **Accrual tab confirmed** as the right place to read a branch's instrument set. Upgraded to
  `[confirmed: BOX FE Developer]`.
- **Steps 9 and 10 (Yield Curve, Currency Basis) parked, not resolved.** Both are empty in Tier 1 PRE,
  and the developer's read that they therefore don't matter was explicitly offered as a guess. They are
  `EVIDENCE_REQUIRED` with no INSERT emitted — deliberately not `CONFIRMED_ABSENT`, because nobody has
  said they are unnecessary, and the assumed `FK_PARENT` join cannot be validated against an empty
  table. Cheapest next check: Tier 1 **PRO** rather than PRE.
- **Step 14 (not-branch-scoped) confirmed** — `T_BOX_ENGDAYS_MATURED_S` and `T_BOX_ENGSETUP_S` are
  global; a new branch needs nothing in them.
- **Step 13 split.** `T_BOX_BRPROCCAL_S` is confirmed derived; `T_BOX_FIXING_ASSIGNMENT_S` is only *to
  be confirmed*, so it stays `EVIDENCE_REQUIRED`. The agent writes to neither either way.
- **The Book table (step 11) is still not fully understood — by the developer either**, which is worth
  recording plainly rather than smoothing over. Two concrete rules did come out of it: **at least one
  row per instrument is required** (hence the `0 - EMPTY` placeholder rows), and the safest source is a
  **reference branch that trades the same instrument** — row set from the reference, Book/Label values
  still to be confirmed. Same shape-not-values split as Q-05c; hard rule 6 is unaffected.

### 2026-09-17 — the Accrual tab *is* the branch's instrument list

`[confirmed: DB via Edouard, 2026-09-17]` **A sharpening of the 2026-09-16 instrument-scope correction,
and a genuine improvement to gate 0c.** The 16th's entry said instruments are chosen from BOX's live
catalogue and pointed at `T_BOX_ENGINSTRUMENTS_S` as "the menu." That was right about the menu and
wrong if read as the place to look up what a *branch* has. Two tables, two questions:

| Question | Table |
|---|---|
| What does BOX have at all? — **the menu** | `T_BOX_ENGINSTRUMENTS_S` (Processed Instruments). Global, 18 rows, no branch dimension |
| What does **this branch** have? — **the selection** | `BOX_FE.T_BOX_ENGACCRCONF_S`, the MIS configuration's **Accrual tab**. One row per instrument |

Observed directly for **SLB in Tier 1**: nine Accrual rows — OTC Option, Cross Currency Swap, Swap,
Cash Flow Matching, Deposit & Loan, Credit Derivatives, Forward Rate Agreement, Caps And Floors, Bond
Return Swap.

**Why this is more than a table-name fix.**

- **Gate 0c becomes verifiable.** "NY_SCH gets the same set as SLB" has been the working hypothesis for
  weeks with no way to check it. It is now a query. The SME is asked to confirm a **concrete
  enumeration** — *"these nine, or which subset?"* — instead of enumerating from memory, which is both
  a better question and a much cheaper one to answer. New query **Q-05c** added for exactly this, with
  its `FK_INSTRUMENT → PK` join flagged as **assumed**, not confirmed.
- **Walk step 6 is the instrument scope.** `T_BOX_ENGACCRCONF_S` was labelled "Accrual defaults." Its
  row count **is** `PRODUCT_BOOK_SCOPE` — one row per instrument. That explains why step 6 is blocked
  by gate 0c and makes the dependency far more load-bearing than "defaults" suggested. The FE walk eval
  gains two failure conditions: a step-6 row count not matching the confirmed scope, and a reference
  branch's accrual *values* copied rather than just its *set*.
- **Hard rule 6 is untouched.** Reading a reference branch's set is a proposal aid. It does not
  authorise copying SLB's accrual values into a USD/New York branch.

**A row-count discrepancy, recorded not resolved.** The repo's Tier 1 calibration baseline records
**7** Accrual rows for SLB; the direct 2026-09-17 read shows **9**. The 7's provenance isn't recorded.
Both are kept in `fe-branch-configuration.md` §3 and on Q-05, with the direct observation treated as the
better evidence, until someone re-runs the count. Neither is a target for a new branch.

**Incidental evidence for gate 0d, and it is the first from a `BOX_FE` table rather than GBO.** SLB's
nine `InternalID`s — `24.095.416,21`, `19.146.735,21`, `2.884.060,21`, `22.085.977,21`, `44.552,21`,
`31.874.132,21`, `23.029.079,21`, `26.216.212,21`, `31.874.121,21` (Spanish locale: `.` thousands, `,`
decimal). `[inferred]` The `<integer>.<authcode>` PK shape holds inside `BOX_FE`; all nine share suffix
`.21`; and the integer parts are large, scattered (44,552 → 31,874,132) with one pair 11 apart — which
looks like a **sequence shared across many tables** rather than a per-table one. If so, the allocator is
one `ALL_SEQUENCES` row with `LAST_NUMBER` above ~31.9 M. A lead to test in the Tier 1 rehearsal, not a
finding, and nothing to construct a PK from before 0d is signed off.

### 2026-09-16 (later) — 🔴 "Tier 2 PRE is missing BOX_FE tables" was a permissions artifact

`[confirmed: DB, 2026-09-16]` **The most alarming claim in this repo is withdrawn.** The Tier 2 account
used to run Q-G4 had **no grants on the `BOX_FE` schema**. An Oracle session without privileges does
not see missing tables — it sees no rows in `ALL_TABLES`, which is byte-for-byte identical to absence.
The tables were invisible, not absent.

**What this retracts.** That Tier 2 PRE is missing a substantial number of `BOX_FE` tables. That gate
0e will fail. That the provisioning artifact is expected. And — the big one — the instruction to
"establish whether `BOX_FE` was ever deployed to Tier 2 at all," flagged in the kickoff as a possible
project-resizing prerequisite belonging to the orchestrator's Phase 0. **That alarm is stood down; it
was never evidence about provisioning.** Nothing is now known about Tier 2 PRE's schema completeness
in either direction. Gate 0e for Tier 2 is `EVIDENCE_REQUIRED — blocked on access, not on schema`.

**The generalisable failure, which is the real content here.** This is the **second** time in this
project an "absence" turned out to be an access path nobody validated. Q-G2 was the first: the join
returned nothing for NY_SCH, was recorded as a real absence, and then returned nothing for Madrid too
— proving the join wrong, not the data missing. Same shape, different mechanism, eight days apart.
Once is a bug; twice is a missing rule.

So hard rule 8 is rewritten from *"never let a zero-row result mean absent when the query might be
wrong"* to **"before recording an absence, prove the query could have returned a presence"** — with two
named ways to discharge it (a known-good control, or a visibility preflight) and both incidents written
in as worked examples. A **mandatory preflight** is added to the query catalogue and the kickoff:

```sql
SELECT USER, SYS_CONTEXT('USERENV','DB_NAME'),
       (SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER='BOX_FE'),
       (SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER='DEVENG') FROM dual;
```

A result set whose preflight was not run is no longer evidence. This also happens to answer the
external review's environment-assertion suggestion, which it filed as a *minor* — it now has two real
incidents behind it, and it doubles as the first mechanical check in a repo the same review criticised
for having none.

**Rehearsal mode — gate 0d no longer blocks testing the walk.** `[stated: Edouard, 2026-09-16]` With
Tier 2 `BOX_FE` access pending and gate 0d unresolved (ten PK columns with empty `DATA_DEFAULT`, no
triggers, seven sequences unmapped to the walk tables), the run moves to a **Tier 1 rehearsal**. The
insight: hard rule 3 forbids *fabricating* a PK, not *deferring* one. The agent emits every PK as a
named substitution variable (`&PK_02_ENGCONF`) with an undefined `DEFINE` block, children referencing
their parent's variable by name — so the dependency graph becomes explicit and auditable, which is
precisely what a rehearsal tests. The file is deliberately not runnable until a human binds the
DEFINEs, and becomes runnable without regeneration once 0d resolves.

Guardrails kept: no literal PKs, no unmapped sequences, no PK copied from a live row, every other gate
and hard rule unchanged, separate `RUN_FOLDER` (`runs/NY_SCH/tier1-rehearsal/`), and every output
headed *"Tier 1 rehearsal — structure validated; values are Tier 1 and must not be carried to Tier 2."*
A rehearsal produces a validated **shape**, never a draft to promote. The working assumption that
`BOX_FE` structures are identical across tiers and differ only in content is recorded as an
**assumption**, untested until someone with Tier 2 grants runs the Q-G4 diff.

**An open lead on gate 0d, worth running while Tier 1 access exists.** Every observed PK has the form
`<integer>.<authcode>` — `141.35`, `20007.4`, `4.21`, `64408.35` — and a bare sequence cannot produce
that suffix. If `DATA_SCALE` is 2 and some sequence's `LAST_NUMBER` tracks the integer part of a
table's `MAX(PK)`, the mechanism is *sequence for the integer, application or import tooling for the
suffix*, which would resolve 0d and establish that the suffix is a stated rule or an SME input, never
the agent's to choose.

### 2026-09-16 — external review: coherence fixes before the first Tier 2 run

An external model reviewed the repo. Its critical findings (prose-only enforcement of the hard rules;
correction blocks layered across charters that an LLM operator has to reconcile mentally) are real and
are deliberately **deferred** — they are follow-up work, not pre-run blockers. What follows is the
subset that was verified against the files, is cheap, and would actively misdirect a Devin session if
left as-is.

**The orchestrator disagreed with itself about when the job is done.** *Exit conditions* said "all
**four** Definition of done criteria met" while the DoD lists **five** — and thirty lines earlier the
same file argues at length that criteria 1–4 passing must not be treated as the end. The exit
condition licensed exactly the failure the file predicts: declaring success with criterion 5
(knowledge capture) unmet. Corrected to five.

**The orchestrator didn't know its most important delegate existed.** Its delegate table listed only
`box-datalake-expert` and `branch-config-agent`, and the W2 workstream row routed all SIGOM config to
`branch-config-agent` — so a session following the charter literally would run the FE work through a
sequence with no gates 0d/0e, different statuses and no SQL deliverable. `sigom-box-fe-configs-agent`
added to the table, W2 split FE/ACC, and an **interim routing note** records that the FE walk runs via
`sigom-box-fe-configs-agent` until the BOX Lead resolves the documented overlap. The open decision is
unchanged — it is now just answered *for today* in the place someone executing would look.

**The status vocabulary was defined twice, inconsistently.** `sigom-box-fe-configs-agent` uses eight
statuses; `branch-config-agent` listed six, missing `DERIVED` and `NOT_BRANCH_SCOPED`. Since
`propose-branch-config` feeds **both**, a matrix row could silently change meaning depending on which
agent read it — and the status at risk is `DERIVED`, the one the entire never-invent regime rests on
(a `DERIVED` value collapsing into `PROPOSED` is exactly what hard rule 2 exists to prevent).
`branch-config-agent`'s list aligned to the canonical eight, with the `DERIVED` ≠ `PROPOSED`
distinction stated explicitly. Full canonicalisation into a single reference doc — which also means
de-duplicating the never-invent rule from its six restatements — is deferred with the rest.

**Two eval cases encoded superseded architecture.** The orchestrator's only case still said "all three
experts' proposals" (three delegates was the pre-2026-09-09 architecture). The FE walk case's *Given*
was worse and was **not** caught by the external review: it described gate 0b in its pre-narrowing
form ("a complete GBO config tree"), gate 0c in its pre-correction form ("product and book scope"
rather than instrument scope from BOX's live catalogue), and **omitted gate 0e entirely** — while its
failure conditions blocked SQL on gate 0d only, though the charter refuses SQL until 0d *and* 0e pass.
Both cases corrected; a gate 0e failure condition added. This is a direct instance of the deferred
correction-layering finding: the dated overrides landed in the charters and the query catalogue, and
the eval cases were left behind holding the stale version.

**Not changed, deliberately.** No validator script was written. The proposed one parses a run-folder
format (`02-findings.md`, `03-sql/`) that has never been produced once, so it would encode assumptions
the first real run invalidates; the cheap grep-level subset (no `CREATE`/`ALTER`/`DROP`; no SQL while
`Q-G3-*`/`Q-G4-*` evidence is absent) is worth doing, and the parser is worth doing **after** run one.
`agents/sigom-box-fe-configs-agent/AGENT.md` was not touched at all — it is what Devin is reading right
now.

### 2026-09-16 (later) — instrument scope comes from BOX, not GBO

`[stated: BOX Developer via Edouard, 2026-09-16]` **A narrow but load-bearing correction to
`sigom-box-fe-configs-agent`.**

**What changes:** do not look up which *instruments* are configured for a branch in GBO. A branch is
onboarded in BOX with instruments chosen from **what is already created and live in BOX** — all of
them, or an SME-chosen subset. The branch's GBO instrument configuration is neither the source for
that choice nor a prerequisite for it.

**What does not change, and this is most of it.** The MIS configuration and the Fixing Curve are still
mined from their GBO (`DEVENG.T_PGT_*`) equivalents. The walk's GBO source column is still the input.
`GBO_SOURCE` is still a required input. Correctness still means the branch behaves like its GBO
counterpart. The hard rules, walk order, other gates, outputs and definition of done are untouched.
Jobs, BOX ACC config, Reporting, GL and FDH are all outside this and unaffected.

**Applied as:**

- **Gate 0b / Q-G2 narrowed to level 1, not withdrawn.** Level 1 resolves `FK_MISCONFIG` to the GBO MIS
  header — precisely the thing still being mined — so the gate stays and is load-bearing. Levels 2–3
  (`T_PGT_BRANCH_INST_S`, `T_PGT_BRANCH_INS_CONFIG_S`) are the *branch-instrument* tree and drop out.
- **`PRODUCT_BOOK_SCOPE` re-sourced:** instruments chosen from BOX's live catalogue by a named SME. The
  menu is the BOX FE Processed Instruments catalogue in `box-data-model.md`, which makes that table more
  operationally important than it looked.

**A useful coincidence:** the two levels that drop are exactly the two that were broken. The first live
NY_SCH run returned level 1 only — and levels 2–3 return nothing for **Madrid** too (`bc.PK = 4.21`,
absent from every populated `FK_PARENT` value), which is unambiguously live and fully configured. So
the join `T_PGT_BRANCH_INST_S.FK_PARENT = T_PGT_BRANCH_CONFIG_S.PK` is wrong, and the empty result was
a query defect, not a finding about NY_SCH. **An earlier entry in this session concluded "confirmed
real absence" — that is retracted.** What `FK_PARENT` actually references is recorded as open; it can't
be recovered from constraint metadata because this schema declares no foreign keys at all. Level 1
worked correctly throughout and is the level that stays.

**The generic lesson, now written into the catalogue:** always run a **known-good control** before
recording `CONFIRMED_ABSENT`. Requiring a Madrid run alongside the target branch would have surfaced
the broken join in one round instead of three.

**NY_SCH identity corrected from the live Q-G1 run** `[confirmed: DB Tier 2, 2026-09-16]`: `20007.4` is
the **branch PK**, not the entity as this repo previously recorded. Full row: `FK_ENTITY = 31398.4`,
`FK_CURRENCY = 159.4`, `FK_CALENDAR = 83.4`, `FK_LOCALGROUP = 21447.4` — that localgroup differs from
Madrid's `269.4`, a real input to the branch-group open question. NY_SCH's GBO branch-config row
(`141.35`) and FE/MIS header (`64408.35`, "Configuracion -NY") both exist and resolve.

### 2026-09-17 — filename collision resolved, and the auth-code question closed

**A name clash, caught by Edouard.** `docs/reference/job-chains/box-fe-acc-batch-runtime.md` was carried
as *pending — not yet imported* in eight places across this repo. That marker meant "this doc exists in
Devin's wiki, we haven't pulled it in here yet" — the filename was **reserved for a specific existing
document**. It was subsequently imported into the real repo. This scaffold, which never had it, wrote a
*different* document (built from the team's Confluence batch-process page) into that reserved name. Had
the scaffold been copied over the repo wholesale, Devin's document would have been overwritten.

**Resolution: keep both, under distinct names.** They are two layers of one stack, not duplicates, and
they were written from different evidence — merging them would flatten `[confirmed: repository
configuration]` together with `[stated: team page]`.

- `box-fe-acc-batch-runtime.md` (Devin's, **unchanged, not in this scaffold**) — the **scheduler**
  layer: Control-M job families, subapplications, the `T_BOX_MBJ_PROPERTIES_S` binding, FE→ACC handoff.
  Covers FE *and* ACC.
- **Renamed:** the scaffold's doc → `fe-batch-event-groups.md` — the **inside-Oracle** layer: the nine
  ordered FE event groups and the procedures inside two of them. FE only.
- **The seam between them:** Devin's doc records the dispatcher signature `f_ExecuteGroup(group, branch,
  process-date, instrument, mode, label, sub-label)` and flags the `group` values as an open question.
  The renamed doc is the list of those values. Each is the other's missing half; both now say so.

**Three of the renamed doc's four *Still pending* items are closed by Devin's**, and are recorded as a
reconciliation table rather than silently deleted: the BOX_ACC batch topology, the FE→ACC completion
contract (FE and ACC are separate Oracle batch layers joined through **Control-M events**), and the
shape of per-branch scoping. Only failure/restart behaviour stays open in both.

**🔑 `.21` is Madrid's auth-code — and the PK suffix and the SIGOM status bar are the same number.**
`sigom-reference.md` has carried "*is `Current auth-code` a fixed numeric code per branch (Madrid = 21)?*"
open since the first screen walk. Devin's `T_BOX_MBJ_PROPERTIES_S` extract records Madrid's branch as PK
**`22.21`**, matching the `Current auth-code: 21 - Madrid` shown on six separate Madrid-filtered screens.
His job-to-MBJ table is also the first place all three suffixes appear as typed columns of one row —
branch `22.21`, instrument `20.4`, MBJ group `3375.65`. New `[inferred]` hypothesis recorded: the
auth-code marks **which installation owns the row**, not which environment it lives in, which is the
first reading that explains one row carrying three different suffixes. **NY_SCH's auth-code is now a
Phase 0 question** — a PK written under the wrong one would be invisible to the delete-guard pattern.

**Correction logged, not overwritten.** `sigom-reference.md`'s MBJ Config note concluded the decimal
part was "not a meaningful separate code… a documentation formatting artifact". The European-number
reading was right; that inference was wrong. Both are now on the page, with the error marked.

**Two more structural findings** from putting the two docs side by side, both `[inferred]`: FE event
groups and ACC MBJ groups interleave in one numbering space (so the ACC half of a branch walk may be
minable the same way as FE — worth one query before building two paths); and **CES has an FE Deal Data
group but no ACC accounting**, so "is this product supported?" has to be asked per engine, not once.

**`MIC_FLOW_MODE = On-Line` on a batch job row** — flagged as a lead, not a finding. The online
(CROSS_REF) arrival path still has no document; this is the first place batch configuration and the
online idea touch.

**Five repos upgraded from hearsay to evidence.** `cib-boxfin-t1mdesfe`, `cib-boxfin-t1mdalmfields`,
`cib-boxfin-mdfinancialcheck`, `cib-boxacc-t1mdesac`, `cib-boxacc-t1mdacccheck` were tagged
`[stated: BOX Developer, not yet doc-evidenced]`. Now `[confirmed: repository configuration]`, and the
BOX Developer's descriptions survived contact with the repos. New open question in their place: job
configs name scripts under `/appl/gm/scripts`, and **none of the five repos contains that path**.

### 2026-09-11 — BOX Lead scoping meeting intake (2026-09-10)

- `docs/examples/ny-sch-branch-onboarding.md` restructured around the **six agreed workstreams**
  (Software · SIGOM configs · Jobs · Reporting · GL · FDH) and promoted to the main reference for what's
  done. Repo coverage and work status tracked as separate columns.
- **Testing does not require booking trades in Murex** — a branch live in GBO has its trades in the Data
  Lake and can feed RAW manually. Documented in `fe-raw-data-stage.md` and `system-overview.md`; checklist
  item 2.1 updated to separate "online as a production capability" from "getting test data in".
- **Correction:** `status_vr = BOValidated` was recorded as batch-job boilerplate in
  `control-m-batch-layer.md`. It is the AUKI status — for a branch still on GBO the standard job selects
  no rows. Now flagged as a per-branch parameter, not a constant to copy from the analogue.
- **New:** an existing GBO→BOX **Topics mapping tool** recorded in `sigom-box-acc-configs-agent`; changes
  that agent's topic work from derive-and-propose to apply-and-verify.
- NY_SCH's GL confirmed as **Equation** (same as SLB) in `system-overview.md`; **FDH registered as a
  documentation gap** — it appeared nowhere in the repo before this.
- Scope reconciliation: workstream↔layer mapping added to the master checklist; coverage note added to
  `branch-onboarding-orchestrator` recording that four of six workstreams have no delegate.

### 2026-09-16 (later still) — the FE batch process overview

- **New doc: `docs/reference/job-chains/box-fe-acc-batch-runtime.md`** — a file **eight other documents
  already cited as "pending — not yet imported"**. The **FE half** is now filled: nine event groups in
  order with their PKs, the two before-batch prerequisites, the eight per-product Deal Data inserts, and
  the procedure-by-procedure execution order inside groups `2629.65` and `2630.65`. The **ACC half and
  the FE→ACC barrier remain undocumented**, and the doc says so rather than implying completeness.
- **Upgraded an inference to named facts.** Two turns ago the add-book runbook's `f_ExecuteGroup(<pk>,…)`
  arguments were `[inferred]` to be event-group PKs from two coincidental matches. Seven of the fifteen
  `db.conf` lines can now be named outright, and it's confirmed that one book's block spans **both** the
  FE and ACC batches.
- **Resolved the Fixing Curve two-location trap** (Q-03): `Control > Configuration` is the batch's
  **input**, `Control > Historical Data` is its **output**. Mine Configuration; an empty Historical Data
  on a new branch means the batch hasn't run, not that config is missing.
- **Named the RAW Deal → DATADEAL transformer:** `PKG_FE_DEAL_CALCULATION.p_Import_Deal_Data`, step 1 of
  group `2629.65`. Doesn't close that open question but shortens it to "read this procedure".
- **Placed `p_Import_Flow_Data` in sequence** (step 2 of the same group) and surfaced a third package
  family, `PKG_FE_PROPAGATION_DATA`, which is what sets the `PROPAGATION` column already observed on
  processed Flow.
- ⚠️ **The product-shaped-branch question got materially stronger.** The runtime **Process Calendar**
  schedules against Branch `BOX COMMODITIES` / instrument `COMM_SWAP`, so product-shaped branches are
  **the unit the batch processes**, not a config-screen label. The "harmless dev convention" reading is
  now the weaker one. Still unresolved; still one query away.
- Partially answered an earlier lead: a BOX-side **`Branch - MIS`** exists under `Control \ Historical
  Data` — it is **generated** by event group `2388.65`, which is why it never appeared in the config
  surface.

### 2026-09-16 (later) — the add-a-product runbook

- **New doc: `docs/process/05-add-product-procedure.md`** — the **Product axis**, completing the set
  alongside Book (04) and Branch (the master checklist). Covers BOX API, BOX FE and BOX ACC. Marked
  `DOC IN PROGRESS` at source, so absences are recorded as unwritten rather than as "not required".
- 🔑 **The `.65` PK suffix is an "authcode".** BOX-DEV is the `.65` authcode, and topics/conditions are
  created "as `.65`". Names a convention this corpus has flagged as unexplained for weeks. Recorded with
  what it still doesn't settle — `.65` PKs appear in production-copy extracts too, and branches carry
  both `.21` and `.4`.
- **`CES` identified as Commodity Swap**, closing a BOX-only unknown in the Financial Status product set.
- **"False friend" resolved.** The SIGOM object for the BOX MtM view is named
  `BOX_ENG_Interfaz <product> MIS-MDR` — so BOX's object *is* a MIS-MDR interface like GBO's; only the
  menu label differs. A GBO↔BOX mapping across that row is now justified.
- ⚠️ **Open question raised against the branch-keyed FE model.** BOX-DEV's Accrual Exceptions and
  Allowed Errors screens show `Branch` values like `BOX CCS`, `BOX FX`, `BOX IRS` — **product-shaped,
  not geographic**. Three possible readings recorded, none chosen; flagged in
  `fe-branch-configuration.md` and added to the NY_SCH kickoff prompt as an early check, since it could
  change the shape of the FE walk.
- **New reference table:** the full 18-instrument Processed Instruments catalogue with codes, which
  **refines** the earlier "BOX covers 11 products vs GBO's ~28" framing — BOX recognises more
  instruments than it gives Financial Status screens to.
- **Qualified the universal-engine "zero new PL/SQL" claim** on `acc-add-product-checklist.md`: true for
  ACC accounting logic, but BOX FE demonstrably needs per-product packages and the API needs a function
  change.
- **Flagged:** Days Matured is 2 in BOX-DEV against the documented 30 across Tier 1 — `NUM_DAYS` varies
  by environment and shouldn't be carried as a default.
- Corroborations worth noting: `cinstrument_if → CFM` confirms GBO's odd `IF` code for CFM a second
  time; the MTM import's `CURR`/`OPT` family/group pair matches Control-M's `mfamily`/`mgroup` exactly.

### 2026-09-16 — `T_BOX_CROSS_REF_S` and instrument mappings

- **New doc: `docs/reference/tables/t-box-cross-ref-s.md`** — the **first real per-table deep-dive**,
  filling a folder `docs/README.md` described as "none written yet". Covers the five `MAP_TYPE`s,
  column names `[confirmed: DML]`, the IC→GBO instrument mappings, the five-rows-per-instrument
  checklist, and the `cib-box-cntdblite` script convention.
- **Reframing flagged, not forced.** The repo names a topic category "Online arrival (CROSS_REF)" and
  treats this table as part of the real-time path. The team's page documents its purpose as
  **Integrity Check → GBO Static-Data** translation. Qualified in `topic-index.md` and
  `branch-trading-readiness.md`; the Known-gap note now says Online research has **two** open
  questions where it implied one.
- **Open question resolved:** `fe-raw-data-stage.md` flagged the Pay/Receive → Loan/Borrower
  transformation as unexplained. It is configured here as `Direction` mappings
  (`RECEIVE→BOR`, `PAY→LOA`), instrument-filtered — configuration, not hardcoded logic.
- **Open question resolved:** the add-book runbook's unexplained `f_ExecuteGroup(<pk>, …)` arguments
  are `T_PGT_BR_EVE_S` event-group PKs — two of them (`2735.65`, `2755.65`) appear verbatim in
  `acc-add-product-checklist.md` §4's independently-sourced event-group list.
- 🔑 **A second PK mechanism, contradicting any single answer to gate 0d.** These scripts assign PKs as
  **hand-written literals** in versioned SQL, where the Book tab exports a file with a *dynamic* PK.
  Q-G3 guidance updated: answer the PK question **per table**, not once for the walk.
- **First hard evidence that the `<int>.<int>` PK suffix is load-bearing**: the scripts' delete guard
  `trunc(PK)=sign(PK)*(abs(PK)-.65)` is an assertion that the fractional part is exactly `.65`. What it
  denotes is still open, but it is relied on by code.
- Added the **`BOX_SYS` schema** to the Schema Overview (it was entirely absent) and the
  **`cib-box-cntdblite`** repo to `repo-index.md` under a new *Configuration-as-code repos* section.

### 2026-09-15 (later still) — the add-a-book runbook

- **New doc: `docs/process/04-add-book-procedure.md`** — the team's own Confluence runbook for adding a
  Book, imported and translated from Spanish. Two parts: Data-Lake/Control-M job creation, then BOX FE +
  ACC configuration. This is the repo's **third axis** (branch / product / book) and the first procedure
  written by the people who run it rather than reverse-engineered from code.
- 🔑 **Lead on the FE walk's biggest blocker.** The runbook's MIS-book step says to *"export the book
  configuration file with dynamic pk to insert it into the environments"* — an export/import path, not
  an `INSERT` path. If it generalises, hand-written INSERTs are the wrong deliverable shape for at least
  some config objects. Flagged in the agent charter, Q-G3, and the Book section of
  `fe-branch-configuration.md`; **not** treated as settled.
- **Retraction.** The 2026-09-11 hypothesis that `PGT_SYS.PGT_DOMAINS` might be the missing
  `<BOOK-ABBREV>` lookup table is **withdrawn**. The runbook shows the two live at different layers:
  `PGT_DOMAINS` holds the book's label code + description; the Control-M abbreviation is an informal
  hand-made contraction of that description. They correspond by shared ancestry, not by lookup.
- **`<BOOK-ABBREV>` open question resolved** the other way — it is a convention chosen by the job's
  creator, so there was never a table to find.
- **Three unresolved discrepancies recorded** between `control-m-batch-layer.md` (repo-derived) and the
  runbook (practice): 6 vs 4 jobs per book, region token present vs absent in job names, and two
  apparently different job families. Recorded as contested rather than reconciled by picking one.
- New findings for branch onboarding: the batch package binds the branch as a **compile-time constant**
  (`CST_PK_BRANC_MAD`), suggesting a new branch is a code change here; and the Calypso DUMMY jobs exist
  for ES/LB only, with no US family.

### 2026-09-15 (later) — Folders, and two more GBO↔BOX equivalents

- **New table surfaced: `PGT_STC.T_PGT_FOLDER_S`** (SIGOM `GBO > Static Data > Environment > Config >
  Folders`). It was already listed in `box-data-model.md` as "Folder/portfolio data" with no schema and
  no detail; now has its schema, branch-keying, columns, and a working query. **Folder is branch-keyed**,
  so it is flagged as candidate item **1.6** on the onboarding checklist — `open-question`, not a
  confirmed requirement.
- Recorded the **Folder vs Book** distinction explicitly (portfolio-side vs Data-Lake processing-side);
  both travel with a deal and are easy to conflate.
- **Two more naming-rule confirmations:** `T_BOX_ENGINSTRUMENTS_S` ↔ `T_PGT_ENGINSTRUMENTS_S` and
  `T_BOX_ENGDOM_S` ↔ `T_PGT_ENGDOM_S`.
- **`ENGDOM` backs several codes screens at once**, not one per screen — the same many-screens-one-table
  shape as `T_BOX_DATADEAL_S`. Also recorded that it is **not** `PGT_SYS.PGT_DOMAINS` (module-owned vs
  shared), since both are "domain" tables.
- **`PGT_DOMAINS` now has four confirmed, unrelated uses** (quote type, book label, folder coverage type,
  folder coverage list) across three schemas — two of them on the same folder row. Documented as its own
  section.
- **Flagged for confirmation:** the supplied `ENGDOM` screenshot has its two schemas swapped relative to
  every other confirmed mapping. Recorded in corrected orientation with the reasoning stated, pending one
  word from the developer.
- Partially expanded GBO's `Static Data` tree branch, previously recorded as wholly unexplored.

### 2026-09-15 — Financial Status surfaces, GBO and BOX FE

- **Resolved a standing caveat:** `sigom-reference.md` had confirmed only CCS's Financial Status tables
  by name, with the other ten products derived from a stated pattern. All 11 BOX products are now
  confirmed by name, along with a **correction** — the table code is not always the folder label
  (`C&F`→`CF`, `Depo`→`MM`, `Swap`→`IR`), so the previously written rule would have produced three wrong
  table names.
- **New:** GBO's Financial Status product list and per-product triad (`DATAMIS`/`FINANCST`/`RISK`,
  plus the `MIS-MDR Interface` view) — previously an undocumented folder. Also GBO's `Static MIS Data`
  tables, including the branch-keyed `T_PGT_BRANCH_MIS_S`, flagged as a possible gap in the FE walk.
- **Structural finding:** GBO has one Deal Data table per product; BOX routes all 11 products through the
  single shared `T_BOX_DATADEAL_S` — a second, independent confirmation of what `fe-raw-data-stage.md`
  had concluded from row sampling alone.
- **Trap recorded:** `V_*_ENG<CODE>DATAMIS_S` is labelled *MIS-MDR Interface* in GBO but *MtM Data* in
  BOX. Same naming convention, different stated role.
- **Scope-qualified the GBO↔BOX FE naming rule** in `fe-branch-configuration.md`: confirmed for the
  configuration surface, does not generalise to Financial Status data tables.
- **Product-set divergence** (BOX 11 vs GBO ~28, with FX and OTC consolidated and a dozen GBO products
  having no BOX counterpart) recorded as a hard constraint on `PRODUCT_BOOK_SCOPE` in the NY_SCH record.
- **Flagged, not reconciled:** `box-data-model.md`'s existing `T_BOX_IRDATADEAL_S` / `T_BOX_MMDATADEAL_S`
  rows appear to contradict the shared-DATADEAL finding. Needs a query, not a judgment call.

### Earlier

- Repo scaffold created: docs/skills/agents/evals structure.
