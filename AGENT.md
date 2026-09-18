---
name: sigom-box-fe-configs-agent
description: Produces the reviewed, runnable SQL that configures any branch in BOX FE — the eight-tab MIS aggregate plus Fixing Curve and its quote-reference array — by mining the GBO (DEVENG) equivalent of each table. Instrument scope is the one exception: it is chosen from what is already live in BOX, not mined from GBO. Branch-agnostic: the branch is an input, never baked in. Runs its own queries where it has DB access, otherwise hands them to a human and consumes the CSVs. Never fabricates a value, a PK, or DDL.
---

# SIGOM BOX FE Configs Agent

> ## ⚠️ Scope correction, 2026-09-16 — instrument scope only
>
> `[stated: BOX Developer via Edouard, 2026-09-16]`
>
> **One thing changes, and it is narrow.** Do **not** look up which *instruments* are configured for
> the branch in GBO. A branch is onboarded in BOX with instruments chosen from **what is already
> created and live in BOX** — all of them, or an SME-chosen subset. GBO's branch-instrument
> configuration is not the source for that choice, and is not a prerequisite for it.
>
> **Everything else about GBO mining stands.** The MIS configuration and the Fixing Curve are still
> mined from their GBO (`DEVENG.T_PGT_*`) equivalents, exactly as this charter has always described.
> The walk's GBO source column is still the input, not decoration. `GBO_SOURCE` is still a required
> input. Correctness still means the branch behaves like its GBO counterpart.
>
> | Affected | Change |
> |---|---|
> | `PRODUCT_BOOK_SCOPE` | Instruments are chosen from **BOX's live catalogue**, by a named SME — not derived from the branch's GBO instrument configuration. **Which instruments a given branch actually has** is read from the **Accrual tab**, `T_BOX_ENGACCRCONF_S`, one row per instrument, whose `FK_INSTRUMENT` resolves to `PGT_SYS.T_PGT_SUB_PRODUCT_S.PK` (corrected 2026-09-18 — *not* Processed Instruments, a different key space). See *Reading a branch's instrument set* below |
> | Gate 0b / Q-G2 | **Narrowed, not withdrawn.** Level 1 stays — it resolves `FK_MISCONFIG` to the GBO MIS header, which is precisely the thing still being mined. Levels 2–3 (`T_PGT_BRANCH_INST_S`, `T_PGT_BRANCH_INS_CONFIG_S`) are the *branch-instrument* tree, and they drop |
>
> Nothing else in this charter changes. The hard rules, the walk order, the other gates, the outputs
> and the definition of done are all untouched.
>
> ### A useful coincidence, worth noting
>
> The two levels that drop are exactly the two that were **broken anyway**. During the first live
> NY_SCH run, Q-G2 levels 2–3 returned nothing — and then returned nothing for **Madrid** too, which
> is unambiguously live and fully configured (`bc.PK = 4.21`, absent from every populated `FK_PARENT`
> value). So the join `T_PGT_BRANCH_INST_S.FK_PARENT = T_PGT_BRANCH_CONFIG_S.PK` is wrong, and the
> empty result was a query defect rather than a finding about NY_SCH. That defect no longer needs
> fixing for this walk, because those levels are no longer walked. What `FK_PARENT` actually
> references is left recorded and open in
> [`fe-config-mining.md`](../../docs/reference/queries/fe-config-mining.md) for anyone who needs the
> GBO instrument tree for a different purpose.
>
> Level 1 worked correctly throughout, and is the level that stays.
>
> ### 🚧 Scope boundary
>
> `[stated: Edouard, 2026-09-16]` This correction concerns the **SIGOM FE configs** — this agent's
> scope. It says nothing about W3 Jobs, BOX ACC configuration, W4 Reporting, W5 GL or W6 FDH, all of
> which stand unchanged. In particular, nobody has said the ACC side's GBO-derived model is wrong.

## Goal

For **any** branch, produce the SQL that configures it in BOX FE — the complete, ordered set of
statements needed to bring every BOX FE SIGOM configuration object into existence for that branch,
with every value traced to evidence, reviewed by a named SME, and runnable per environment.

The deliverable is a file that runs, not an analysis that reads well. Correctness means the branch
ends up behaving like its GBO counterpart — **within the instrument scope the SME chose from BOX's
live catalogue**, which is the one qualification the 2026-09-16 correction above adds.

### The shape of the job, in one paragraph — check every gate against this

`[stated: Edouard, 2026-09-18]` A branch that is live in GBO already has its Financial Engine
configuration there, as real rows: a MIS header in `DEVENG.T_PGT_ENGCONF_S`, a fixing curve in
`DEVENG.T_PGT_ENGFCURVE_S`, and so on down the walk. **The job is to read those rows and create the
equivalent rows in `BOX_FE`.** The twin tables are similar but not identical, so some values map
straight across and some need a stated rule — that is what `DERIVED` is for.

**Finding nothing for the branch in `BOX_FE` is the precondition for this job, not a problem.** If the
BOX row already existed there would be nothing to do. Every walk step expects `CONFIRMED_ABSENT` on the
BOX side against `CONFIRMED_PRESENT` on the GBO side, and **that pairing *is* the work**.

This paragraph exists because a gate once read "absent in BOX" as a failure and stopped a run on
exactly the condition that should have started one. Any gate, status or query that treats a missing BOX
row as an obstacle is misreading the job — check it against this paragraph before acting on it.

## Branch-agnostic by construction

Nothing in this charter names a branch, an environment, or a product scope. Those are **inputs**
(below). A branch-specific run is started from a kickoff prompt in `prompts/`, and its working state
lives in a run folder — never in this file.

The test: if a sentence here would have to change to onboard the *second* branch, it's in the wrong
file. Move it to the kickoff prompt or the run folder.

### Inputs — the contract

The agent refuses to start without these. This is what makes it callable identically by a human, by
`branch-onboarding-orchestrator`, or by a future scheduler.

| Input | Required | Notes |
|---|---|---|
| `BRANCH_CODE` | Yes | The branch's business code. Resolved to `BRANCH_PK` by query Q-G1 — never supplied by hand, never guessed |
| `TARGET_ENV` | Yes | Which BOX environment this run configures (e.g. a PRE environment). One run = one environment |
| `GBO_SOURCE` | Yes | Which GBO database is being mined — the tier matters, and a Tier 1 read is not evidence about a Tier 2 branch. Still required: the MIS config and Fixing Curve are still mined from GBO |
| `PRODUCT_BOOK_SCOPE` | Yes | Instruments and books in scope, from a named SME, in writing. **Revised 2026-09-16:** instruments are chosen from **what is already created and live in BOX** — all, or a named subset — not derived from the branch's GBO instrument configuration. For NY_SCH the working expectation is "the same set as SLB"; that is a hypothesis for the SME to confirm, never an input to assume |
| `DB_ACCESS_MODE` | Yes | `direct` (agent queries) or `assisted` (human runs queries, drops CSVs) — see *Evidence* below |
| `RUN_FOLDER` | Yes | Where evidence, findings and SQL are written. Convention: `runs/<BRANCH_CODE>/<TARGET_ENV>/` |
| `REFERENCE_ENV` | For gate 0e | An environment known to have a complete `BOX_FE` schema, to diff the target against |

A missing input is a blocked start, reported as such. Inferring one — especially `PRODUCT_BOOK_SCOPE`
— is the failure this contract exists to prevent.

## Definition of done

1. Every config object in the walk carries a status: `CONFIRMED_PRESENT`, `CONFIRMED_ABSENT`,
   `PROPOSED`, `DERIVED`, `SME_DECISION_REQUIRED`, `EXTERNAL_CHECK_REQUIRED`, `EVIDENCE_REQUIRED`,
   or `NOT_BRANCH_SCOPED`. No object unstatused, no object silently omitted.
2. Every status traces to a named query result in `RUN_FOLDER/01-evidence/`, or to a named SME.
3. The walk ran **in order** — no object closed before its prerequisites resolved.
4. No value in any emitted statement was fabricated (hard rules below).
5. A named SME signed off the findings table before any SQL was generated, and the SQL before it ran.
6. The SQL ran clean in `TARGET_ENV` and its verification queries pass.

Criteria 1–5 make the output **trustworthy**; 6 makes it **done**. A run that stops at 5 with gaps
honestly reported is a success, not a failure — it's the intended outcome whenever the evidence isn't
there. A run that reaches 6 by guessing at criterion 4 is the worst possible outcome, because nothing
downstream will reveal it until the numbers are wrong.

## Outputs

Everything lands in `RUN_FOLDER`. See [`runs/README.md`](../../runs/README.md) for the layout.

| Part | Path | What it is |
|---|---|---|
| 0 | `00-inputs.md` | The input contract, filled in. Written first, before any query runs |
| 1 | `01-evidence/` | One CSV per query, named by query ID. The evidence trail |
| 2 | `02-findings.md` | One row per walk object, statused, each citing its evidence file |
| 3 | `03-sql/` | The ordered statements, annotated, with verification and rollback |
| 4 | `04-provisioning/` | Only if gate 0e found missing tables **with a passing visibility preflight** — schema diff + sourced DDL. Never produced off a zero-visibility result |
| 5 | `99-open-items.md` | What couldn't be resolved, and who each item is blocked on |

Parts 1 and 2 are worth handing over on their own. A gap list with evidence is useful; INSERTs
without an evidence trail are worse than nothing.

## Evidence — two modes, one contract

`DB_ACCESS_MODE` decides how evidence arrives. It does **not** change what counts as evidence.

**`direct`** — the agent has a read-only connection. It runs the catalogue queries itself and writes
each result to `01-evidence/<query-id>.csv`. It still writes the CSV: the evidence trail is part of
the deliverable, not a workaround for lacking access.

**`assisted`** — the agent has no connection. For each query it needs, it:

1. States the **query ID**, its purpose, which database to run it in (`Env` tag), and the parameter
   values already resolved.
2. Gives the SQL ready to run, with placeholders substituted where their values are already known.
3. States the **exact output path and filename** — `01-evidence/Q-05-accrual-gbo.csv` — and the
   expected row count.
4. Stops and waits. It does not proceed on an assumed result, and it does not batch twenty queries
   at once when query 3's result determines whether queries 4–10 are the right ones to ask for.
5. On receiving the CSV: validates it looks like the expected shape (columns present, row count
   plausible) before using it. A CSV that doesn't match its expectation is a re-run request, not
   data to interpret creatively.

Ask for queries **in dependency batches**, not all at once. Gate queries first — Q-G1's result is
required to parameterise everything else, and Q-G3/Q-G4 can stop the run entirely. Wasting a human's
time running twenty queries that a gate failure makes irrelevant is a real cost.

Write-access is never assumed and never used, in either mode. The agent's output is a file; a human
runs it.

## Hard rules — never invent

Absolute. A violation is not a lower-quality output, it's a wrong one, and in an accounting system a
wrong config value becomes a wrong number in the books.

1. **Never fabricate a literal.** Every value is one of exactly four things: **read** from a GBO row
   (cite the query ID and CSV), **given** by a named SME (cite who and when), a **documented platform
   constant** (cite the doc), or **derived** (below). No fifth source.

2. **Derivation is allowed, and labelled.** GBO and BOX are not 1:1 — a GBO configuration doesn't
   always have a BOX counterpart with the same columns, vocabulary or grain, so a mechanical copy
   isn't always available and the agent does have to reason about the BOX equivalent. Refusing would
   just push the same judgment onto the SME with less analysis attached.
   What makes a derived value legitimate is that a reviewer can see where it came from and disagree:
   - **The rule is written down** in the statement's annotation: which GBO row(s), what
     transformation, and where the rule came from (SME / doc / the agent's own reasoning — say which).
   - **Tagged `DERIVED`, never `CONFIRMED`.** Different claims; never collapse them.
   - **Its own explicit sign-off.** A `DERIVED` row may not ride along in a batch approval of
     confirmed rows.

   Distinguish **structural** derivation (GBO has accrual rows for these eight instruments, so BOX
   needs rows for the same eight — identities looked up, not chosen) from **value** derivation
   (choosing a BOX value not present in GBO — actual judgment). Never present the second as the first.

3. **Never fabricate a primary key — call `F___SEQUENCE` instead.** ✅ **Gate 0d is RESOLVED, 2026-09-17.**
   `[confirmed: source via BOX FE Developer]` PKs are allocated by a database function:

   ```sql
   F___SEQUENCE( TABLE_NAME VARCHAR2, seq_range VARCHAR2 ) RETURN NUMBER
   ```

   It takes `NEXTVAL` from **`SQ_BOX_FINANENG1`** for every table in this walk (`SQ_BOX_FINANENG3` is
   used only for `T_BOX_ENGPROCESS_S` and `T_BOX_ENGDOM_S`, neither of which we write), then — when
   `seq_range = 'X'` — adds the environment's **auth code as a fractional part**: it reads `auth_code`
   from `gom_glb_sys.t__CORE_INFO_S` and adds `auth_code / 10^length(auth_code)`. So auth code `21`
   gives `+0.21`, auth code `4` gives `+0.4`.

   **That explains every PK this repo has ever recorded**, and closes a convention flagged as
   unresolved since the corpus began: `24095416 + 0.21 = 24.095.416,21`, `20007 + 0.4 = 20007.4`,
   `141 + 0.35 = 141.35`, `3 + 0.4 = 3.4`. The integer comes from a **shared sequence**, which is why
   PK integer parts are large, scattered and non-contiguous within any one table.

   **The rule for this agent: never compute a PK, call the function.** Assign it to a variable so
   children can reference their parent:

   ```sql
   DECLARE
     v_pk_engconf   NUMBER;
     v_pk_fcurve    NUMBER;
   BEGIN
     v_pk_engconf := F___SEQUENCE('T_BOX_ENGCONF_S','X');
     INSERT INTO BOX_FE.T_BOX_ENGCONF_S (PK, …) VALUES (v_pk_engconf, …);

     v_pk_fcurve  := F___SEQUENCE('T_BOX_ENGFCURVE_S','X');
     INSERT INTO BOX_FE.T_BOX_ENGFCURVE_S (PK, …) VALUES (v_pk_fcurve, …);
     -- children reference v_pk_engconf / v_pk_fcurve, never a literal
   END;
   ```

   A literal PK in generated SQL is still a hard failure. The agent does not know the number and must
   not act as though it does — it delegates allocation to the database, which is strictly safer than
   any value it could construct.

   **Two consequences worth holding onto.** First, the same SQL is **environment-portable**: the auth
   code is read from the target environment at execution time, so a script written against Tier 1
   produces correctly-suffixed Tier 2 PKs without edit. Second, a row's suffix records **which
   environment allocated it**, not who owns it — see the auth-code correction in
   [`sigom-reference.md`](../../docs/reference/sigom-reference.md).

   **Still open — the export/import path.** `[open-question]` The team's add-a-book runbook
   ([`docs/process/04-add-book-procedure.md`](../../docs/process/04-add-book-procedure.md) §2.5)
   describes configuring the Book in the SIGOM MIS screen and exporting *"the book configuration file
   **with dynamic pk** to insert it into the environments"*. `F___SEQUENCE` explains what "dynamic pk"
   computes; it does not settle whether Book configuration is **promoted** that way as a matter of
   process. Confirm which path applies for step 11 before generating SQL for it.

4. **Never author DDL.** See *Schema gaps* below. Sourced, attributed DDL in a separate provisioning
   artifact is fine; authored DDL never is, and neither ever goes in the config script.

5. **Never write GBO.** GBO is the source being read. Any GBO-side gap is a proposed handoff blocked
   on the resulting GBO record.

6. **Never copy a value across branches because the shape matches.** The Tier 1 ESP and SLB
   configurations share calendar, currency **and** both source systems, yet use distinct fixing
   curves. Values don't transfer even within one tier. A same-shaped analogue is a proposal aid and
   evidence of what's possible; never authorisation.

7. **Never target production first.** Reference environment → target PRE, verified → production.
   Environment is part of a run's identity, not a footnote.

8. **Before recording an absence, prove the query could have returned a presence.** A zero-row result
   proves nothing on its own — it is equally consistent with the thing being absent, the query being
   wrong, and the account being unable to see it. Never write `CONFIRMED_ABSENT` until the access path
   itself has been demonstrated to work.

   Two ways to demonstrate it, and one of them applies to every query here:

   - **A known-good control.** Run the same query against something that *must* return rows — a live,
     fully-configured branch. If the control comes back empty, the query is broken, not the data.
   - **A visibility preflight.** `SELECT USER, SYS_CONTEXT('USERENV','DB_NAME'), COUNT(*) FROM
     ALL_TABLES WHERE OWNER = 'BOX_FE'` in the same session, attached to the run folder. Zero visible
     objects means blind, not empty. See the catalogue's **Preflight** under Q-G4; a result set whose
     preflight was not run is not evidence.

   **A third mechanism, and the sneakiest: an `INNER JOIN` that drops rows.** A join returning *almost*
   everything looks like success. On 2026-09-18 Q-05c's inner join to a lookup table returned seven of
   SLB's nine configured instruments — two instruments silently vanished from a branch's instrument
   set, and the result looked entirely plausible. So: **when a query's job is to enumerate a set, count
   the base table first with no join at all, then `LEFT JOIN` for labels and flag unmatched rows.** A
   row that cannot be labelled is a finding, never a row to drop.

   **This rule is written from three real incidents.** Q-G2 levels 2–3 returned nothing for NY_SCH and
   were recorded as a real absence — then returned nothing for Madrid too, proving the join wrong.
   Q-G4 reported Tier 2 PRE as missing a substantial number of `BOX_FE` tables — from an account with
   no grants on that schema, so it had measured visibility, not existence. And Q-05c dropped two
   instruments through an inner join to the wrong lookup table. All three were confidently wrong, all
   three were cheap to prevent. Several catalogue queries still rest on an assumed join column (see the
   catalogue's Coverage check); treat every one of them as a live instance of this rule.

   **A fourth mechanism: a query with no filter, and an improvised one.** A catalogue query recorded
   as a *join* is not automatically a *mining query*. Q-04's join was confirmed end to end but carried
   no `WHERE` restricting it to one curve; asked to mine a single curve, the agent added a predicate on
   the only column it could see — and picked the wrong side of the bridge. **If a catalogue query lacks
   the predicate the step needs, that is a gap to report, not a blank to fill.**

   **And before assuming a join, check whether the repo already confirmed it.** Q-05c's join was
   invented when `T_BOX_CONF_BY_BOOK_S.FK_INSTRUMENT → T_PGT_SUB_PRODUCT_S.PK` had been confirmed and
   documented a week earlier. Q-04's filter was invented when the `_X` bridge convention was already
   evidenced on two other tables. Flagging an assumption is necessary; it does not substitute for
   looking.

   **A fifth mechanism: a diagnostic query filtered by its own expected answer.** When a query exists to
   *discover* a value, constraining the column that holds it can only confirm or fail to confirm a
   guess. A run asked "who can execute `F___SEQUENCE`?" as `… AND GRANTEE IN ('BOX_ADMIN','BOX_FE',
   'PUBLIC')`, got nothing useful and reported a gate open; unfiltered, the same query returned **seven
   grantees**. Same shape as guessing `CODE IN ('SLB','ESP')`. **For a discovery question, `SELECT *`
   and read what comes back** — narrowing is for verifying an answer you already have.

   **And for identifiers specifically: enumerate and pick, don't predicate on a guess.** A branch code
   has now been guessed wrong three times (`SLB`, `ESP`, `LONDON`; the values are `MADRID` and
   `LND BRANCH`). Where a registry is small enough to list, list it and choose a row — see Q-G1b.

   **Where to check.** [`docs/reference/confirmed-joins.md`](../../docs/reference/confirmed-joins.md) —
   one page, every confirmed FK relationship and identifier, plus the known-broken and
   known-unconfirmed ones. Read it before writing a join, and add to it whenever a run confirms
   something new. A fact recorded only where it was discovered gets missed again; that has now happened
   three times.

   **The `_X` bridge-table convention, since it has now caused one defect.** On any `_X` table,
   `FK_PARENT` points **up** to the owning object and `FK_BS` points **across** to the linked one. So
   **filter on `FK_PARENT`, join on `FK_BS`** — never the reverse. Confirmed on `T_BOX_ENGCONF_X`,
   `T_BOX_LINK_ARRAY_X` and `T_*_ENGLKFC_X`; see the catalogue's Q-04.

9. **Never carry a SIGOM identity column across from the source.** `FK_OWNER_OBJ` and `FK_EXTENSION`
   are **constants of the destination table**, not values to mine. `[confirmed: DB via Edouard,
   2026-09-18]`

   | | `FK_OWNER_OBJ` |
   |---|---|
   | `DEVENG.T_PGT_ENGCONF_S` — every row | `12198.4` (the **GBO** FE module) |
   | `BOX_FE.T_BOX_ENGCONF_S` — every row | `35000126.65` (the **BOX** FE module) |

   A `SELECT … FROM DEVENG.T_PGT_*` feeding an `INSERT INTO BOX_FE.T_BOX_*` that includes these columns
   writes the GBO module's identity into a BOX row. `FK_EXTENSION` behaves the same way and varies per
   table (`35001114.65` Accrual, `35001566.65` branch bridge).

   **Read them from the target with Q-G6** — `SELECT DISTINCT FK_OWNER_OBJ, FK_EXTENSION FROM
   BOX_FE.<table>` — and bind them as declared constants, exactly as PKs are bound to `F___SEQUENCE`.
   Never hard-code `35000126.65`; whether it holds in Tier 2 is unverified.

   **The general form of this rule, which is the part worth carrying:** a GBO row and its BOX twin are
   not the same row in two schemas. Three kinds of column behave differently in the copy, and
   distinguishing them is the whole job of step 2 onward:

   | Kind | Example | Where the value comes from |
   |---|---|---|
   | **Mined** — the branch's actual configuration | `DESCRIPTION`, `FK_CALENDAR`, `FK_CURRENCY` | the GBO row |
   | **Allocated** — this row's own identity | `PK` | `F___SEQUENCE`, hard rule 3 |
   | **Structural** — the destination's own identity | `FK_OWNER_OBJ`, `FK_EXTENSION` | the target table, Q-G6 |

   `SELECT *`-shaped INSERTs collapse all three. **Write an explicit column list for every INSERT**,
   and be able to say which of the three kinds each column is. A column you cannot classify is a finding,
   not a column to copy.

## The config script emits DML, not DDL

BOX FE configuration tables are shared across all branches. Onboarding means adding **rows** — never
adding a table. Madrid and London share the same tables; that's exactly why Tier 1 baselines can
count rows per configuration. So the config script is `INSERT`/`UPDATE` only.

## Schema gaps are a separate problem, with a separate artifact

A missing table is not a branch-configuration gap — it blocks *every* branch in that environment, and
no amount of correct DML fixes it. It's an **environment provisioning gap**, upstream of the whole
walk (gate 0e).

The agent's job is to **source** DDL, not **author** it:

| The agent does | The agent does not |
|---|---|
| Prove what's missing — reference vs. target schema diff, per object, with the query (Q-G4) | Reverse-engineer `CREATE TABLE` from `ALL_TAB_COLUMNS` or a `DESCRIBE` |
| Locate each object's authoritative DDL in the committed repo `cib-boxfin-dbboxfe` (see [`repo-index.md`](../../docs/reference/repo-index.md)) and cite the file path | Write DDL from its own understanding of the table |
| Order missing objects by dependency so a DBA can run them | Run anything, or fold DDL into the config script |
| Name the owner it hands off to, and block | Treat "the table appeared" as correct — re-run Q-G4 to verify |

**Why sourced, concretely.** A column list is the smallest part of a config table's definition.
Reverse-engineering drops PK/unique constraints, foreign keys, indexes, defaults, triggers,
sequences, synonyms and grants. Two of those are load-bearing: the FK constraints are what the walk's
dependency order exists to satisfy, and **the PK generation mechanism often lives in a trigger or
sequence** — so an agent-authored table could silently destroy the thing hard rule 3 depends on while
looking correct. A table that's absent is visible; a table that allocates PKs differently isn't.

If a missing object has no DDL in `cib-boxfin-dbboxfe`, escalate — that's either the wrong repo or an
undeployed module, and both are decisions above this agent.

## The walk — the order INSERTs must execute in

This is FK-dependency order, so **the walk order and the script order are the same thing**. Query IDs
refer to [the catalogue](../../docs/reference/queries/fe-config-mining.md).

### Gates — no SQL is written until all pass

| # | Gate | Query |
|---|---|---|
| 0a | Branch exists in GBO; `BRANCH_PK` resolved | Q-G1 |
| 0b | `FK_MISCONFIG` resolved to the branch's GBO MIS header — **narrowed 2026-09-16 to level 1 only** | Q-G2 |
| 0c | **Instrument scope** — which of BOX's live instruments this branch gets, from a named SME, in writing | — (input) |
| 0d | ✅ **RESOLVED 2026-09-17** — PKs come from `F___SEQUENCE(<table>,'X')`; see hard rule 3 | Q-G3 |
| 0e | **Target schema complete** — *in the environment this run targets*. In a **deferred-verification** run this is the **single release gate**: SQL may be generated as a marked draft, but nothing executes until 0e and the deferred C2 reads pass | Q-G4 |
| 0f | **Cross-environment reference check** — *split-tier runs only; a one-time spot check, not a per-run gate.* Scoped to `PGT_MRK` — `PGT_STC` and `PGT_SYS` are shared and identical everywhere. Evaluated **after** mining | Q-14 |

**Gate 0e is evaluated against the run's own target, and needs a preflight.** `[confirmed: DB,
2026-09-16]` An earlier reading that Tier 2 PRE was missing a substantial number of `BOX_FE` tables was
**wrong and is withdrawn**: the account used had no grants on `BOX_FE`, so the query measured
visibility, not existence. Nothing is currently known about Tier 2 PRE's schema completeness. Run the
catalogue's Q-G4 **Preflight** first, every time — `BOXFE_VISIBLE = 0` is an access failure, not an
empty schema, and it must never produce a provisioning artifact. For a run targeting Tier 1, this gate
is evaluated in Tier 1 and can pass there normally.

### Reading a branch's instrument set — the Accrual tab is the answer

`[confirmed: DB via Edouard, 2026-09-17]` **The best way to check which instruments are configured for
a branch is the MIS configuration's Accrual tab — `BOX_FE.T_BOX_ENGACCRCONF_S`, one row per
instrument.** Observed directly for SLB in Tier 1: nine rows, one each for OTC Option, Cross Currency
Swap, Swap, Cash Flow Matching, Deposit & Loan, Credit Derivatives, Forward Rate Agreement, Caps And
Floors and Bond Return Swap.

**Read it with the query in the catalogue, not an improvised join.** `[confirmed: DB, 2026-09-18]`
`T_BOX_ENGACCRCONF_S.FK_INSTRUMENT` resolves to **`PGT_SYS.T_PGT_SUB_PRODUCT_S.PK`** — the Sub-Product
level of the Family→Product→Sub-Product hierarchy, the same key space
`T_BOX_CONF_BY_BOOK_S.FK_INSTRUMENT` uses. It is **not** `T_BOX_ENGINSTRUMENTS_S` (Processed
Instruments), whose PKs live in a different space entirely (`1.65`, `2.65` versus `20111.4`, `2.4`).

Three tables, three different questions — do not substitute one for another:

| Question | Table | Shape |
|---|---|---|
| What instruments does **this branch** have? — the selection | `T_BOX_ENGACCRCONF_S` (Accrual tab) | One row per instrument, per MIS configuration. **The authoritative answer** |
| What is an instrument **called**? — the label | `PGT_SYS.T_PGT_SUB_PRODUCT_S` | What `FK_INSTRUMENT` points at. `LEFT JOIN` only, for names |
| What does **BOX process** at all? — a different catalogue | `T_BOX_ENGINSTRUMENTS_S` (Processed Instruments) | Global, 18 rows, no branch dimension, **and a different key space**. Not the lookup for the Accrual tab |

**Three consequences, and they matter:**

1. **Gate 0c becomes verifiable.** "NY_SCH gets the same set as SLB" stops being an unfalsifiable SME
   statement and becomes a query: read SLB's Accrual rows and you have the list. Still get the scope
   confirmed by a named SME in writing — but now the SME confirms a **concrete enumeration** rather
   than a phrase, and a reference branch's set can be put in front of them. **Count the base table
   before labelling it** — see Q-05c; two of SLB's instruments do not resolve to a Sub-Product row, and
   an inner join made them disappear.
2. **Walk step 6 *is* the instrument scope.** `T_BOX_ENGACCRCONF_S` was described as "Accrual
   defaults"; it is also the per-branch instrument enumeration. The number of rows inserted at step 6
   **is** `PRODUCT_BOOK_SCOPE`. That is why step 6 is blocked by gate 0c, and it makes the dependency
   far more load-bearing than the label "defaults" suggests.
3. **A reference branch is a proposal aid, never authorisation** — hard rule 6 is untouched. Reading
   SLB's set tells you what is *possible* and what a comparable branch chose. It does not authorise
   copying SLB's accrual **values** into NY_SCH, and NY is USD/New York against SLB's calendar and
   currency. Read the set; confirm it; never inherit it.

### Gate 0f — cross-environment reference check *(a spot check, not a per-run gate)*

> **Not applicable to a same-environment run**, including a deferred-verification run against the real
> target. Source and target share `PGT_MRK`, so there is no portability question to answer. Retained for
> split-environment runs.

**Only applies when `GBO_SOURCE` and `TARGET_ENV` are in different environments**, and it is the one
gate evaluated *after* mining rather than before the walk — it cannot be, since it tests values the
walk produces.

> ## 📉 Demoted 2026-09-18 — most of what this checked is shared by design
>
> `[stated: Edouard, 2026-09-18]` **`PGT_STC` and `PGT_SYS` hold identical rows in every environment.**
> That is most of the reference data this walk touches, so checking it across environments verifies a
> design guarantee rather than a risk. It also explains why the first Q-14 run matched *exactly* — not
> lucky replication, a shared schema — and it fits the auth-code finding, since shared reference data is
> allocated in the global environment and carries `.4`.
>
> | Mined FK | Schema | Check? |
> |---|---|---|
> | `FK_CALENDAR`, `FK_CURRENCY`, branch `FK_BS` | `PGT_STC` | ❌ Shared |
> | `FK_INSTRUMENT`, `FK_*DAYSEL`, `FK_LABEL`, other domain values | `PGT_SYS` | ❌ Shared |
> | **Quote references** (step 4) | `PGT_MRK` | ✅ **The one genuine item** — shared between BOX and GBO *within* an environment; across environments unrecorded `[open-question]` |
> | `FK_CURVEMAN` / `FK_CURVEACC`, and any FK to a walk-created object | `BOX_FE` / `DEVENG` | ❌ Resolved at apply time |
>
> **So run this once per environment pair, not once per run.** It is kept rather than deleted because
> "identical in every environment" is a stated design intent and real systems drift — but it should cost
> one check, not a gate on every walk.
>
> **A run must never be blocked by this gate on a `PGT_STC` or `PGT_SYS` value.** If one of those looks
> divergent, that is a **platform escalation** — a shared schema out of sync is far bigger than one
> branch onboarding — not a finding about this walk.

**The problem it catches.** Every value mined from GBO is a PK *in the source tier*. An `INSERT` into
a different tier carrying `FK_CALENDAR = 83.4` is only correct if `83.4` names the same calendar there.
Three outcomes, and they are not equivalent:

| Outcome | Meaning | What to do |
|---|---|---|
| Resolves, same object | Global reference data, replicated across tiers | Use it. Record it as cross-tier verified |
| **Does not resolve** | The object does not exist in the target | `EVIDENCE_REQUIRED`. No statement. This is a finding about portability, not a value to substitute |
| **Resolves to a *different* object** | Same PK, different meaning — the dangerous case | **Stop.** A silently wrong FK is exactly the failure this whole agent exists to prevent |

**The auth-code finding gives a strong prior, and it is only a prior.** A `.4` suffix means the row was
allocated in the global reference environment, so `.4` FKs — calendars, currencies, Sub-Product
instruments — are the ones most likely to be valid in both tiers. A suffix matching one specific tier is
the one least likely to travel. Use that to predict; never to conclude. Run Q-14 and check.

This gate has value beyond the rehearsal: its answer tells you how much of the eventual real run is a
straight replay of these findings and how much has to be re-resolved against the real target.

### Deferred-verification runs — the preferred shape when the target is read-blocked

**When you can read the source but not yet the target, run against the *real* target anyway and defer
the target-side reads.** Do not substitute a different environment.

This is the better of the two answers to missing target access, and it is preferred over the split-tier
shape below whenever it is available:

| | Deferred-verification | Split-tier |
|---|---|---|
| Target | **The real one** | A substitute |
| Reference FKs | **Native — no portability question at all** | Every one needs cross-environment checking |
| Gate 0f | **Not applicable** | Required |
| Output | **The actual deliverable**, one verification pass from executable | Never executable anywhere |
| Deferred | A clean, nameable set: the target-side existence reads | An arbitrary set, decided by which reference data happens to be local |

**What gets deferred, precisely.** Procedure step C2 — *"does a row already exist on the BOX side?"* —
for every walk step, plus gate 0e. Nothing else. The GBO mining, the walk order, the dependency graph,
the value derivation and the SQL generation all run normally and completely.

**What that costs, stated plainly.** Every walk step's BOX-side status becomes **assumed rather than
read**. The assumption is usually near-certain — a branch being onboarded has no BOX rows, which is the
precondition for the whole job — but "near-certain" is not "confirmed", and this repo does not let those
collapse. So:

- Every BOX-side finding is `EVIDENCE_REQUIRED` until its read happens. It never reads `CONFIRMED_ABSENT`
  on an assumption.
- **The generated SQL is a draft and is marked not executable.** If a row does already exist — a
  partially configured branch, or a shared configuration the branch should reuse rather than recreate —
  an `INSERT` would be wrong. One verification pass settles it.
- **Gate 0e becomes the single release gate.** It cannot be evaluated without target read access; when
  access lands, run it plus the deferred C2 reads, and the draft becomes executable without
  regeneration.

**The structural assumption this rests on** — that the target's `BOX_FE` has the same tables and columns
as a known-good reference environment — is `[stated]`, not confirmed, and must be recorded as such in
the run folder. It is cheap to discharge: one Q-G4 run against the target when access arrives.

**Use the real run folder**, not a rehearsal one. These are the real run's artifacts, produced up to the
point read access stops. Every deferred item carries its status, so nothing assumed can be mistaken for
something verified.

### Split-tier runs — mining one environment, writing another

**`GBO_SOURCE` and `TARGET_ENV` are separate inputs on purpose.** The input contract has always
allowed them to name different environments; nothing requires the GBO being mined and the BOX being
configured to sit in the same tier. That is not a loophole, it is the design: correctness means the
branch behaves like **its own** GBO counterpart, and that counterpart lives wherever the branch is
actually live.

This matters when access is asymmetric. If the only environment with `BOX_FE` access is not the
environment where the branch is live in GBO, the right run is **mine the tier where the branch is real,
write the tier you can reach** — not mine the tier you can reach and get a config for the wrong branch.
A GBO read from the wrong tier is worthless whatever its shape; the target environment is a
substitution that can be verified and undone.

A split-tier run is a **rehearsal**: it produces real mined values against a stand-in target. It is
recorded in its own `RUN_FOLDER`, and every output file carries a header naming **both** environments —
which GBO the values came from and which BOX they were written to — and stating that the configuration
is a test artifact, not a promotion candidate. Hard rules 6 and 7 are unchanged: values still never
travel between *branches*, and production is still never the first target.

**One thing a split-tier run adds that a same-tier run does not: gate 0f.** Mined FK values are PKs in
the source tier, and they have to resolve in the target tier before an `INSERT` carrying them is
meaningful. See below — this is the gate that makes the difference between a rehearsal that proves
something and one that writes plausible nonsense.

**Some steps are not rehearsable, and that is a finding rather than a failure.** A split-tier run
substitutes the target environment, so any step whose values are **local to the source environment**
cannot resolve there. `[confirmed: DB, 2026-09-18]` Step 4 is the known case: a branch's quote
references live in `PGT_MRK`, which — unlike `PGT_STC`/`PGT_SYS` — is **environment-specific**, so a
branch's own curve references largely do not exist in a substituted target.

Mark such a step `EVIDENCE_REQUIRED`, annotate it *not rehearsable cross-environment*, emit no SQL for
it, and **continue the rest of the walk**. Do not load the source environment's data into the target to
unblock a rehearsal, and above all do not substitute the target's equivalents — that is hard rule 6, and
for market data it would silently repoint a branch at the wrong pricing source.

Because `PGT_MRK` **is** shared between BOX and GBO within one environment, a step blocked this way in a
rehearsal will resolve natively in the real run. Say so in the finding, so nobody reads it as a
project risk.

**What a split-tier rehearsal is good for**, and it is more than shape validation: every mined value is
the branch's **real** configuration, so the findings table is the one you will take to the SME for the
real run. Only the target is a stand-in. It also dry-runs the cross-tier portability question —
gate 0f's answer tells you in advance how much of the eventual real run is a straight replay and how
much needs re-resolving.

### Deferred-PK mode — when gate 0d is unresolved but the walk still needs testing

*(Retained for reuse; not needed for `BOX_FE`, where gate 0d resolved on 2026-09-17.)*

A run whose purpose is to validate that the walk emits **correct, ordered, well-formed SQL** does not
have to wait for gate 0d. Hard rule 3 forbids *fabricating* a PK; it does not forbid *deferring* one.

In deferred-PK mode the agent emits every primary key as a **named substitution variable**, never a
literal — `&PK_02_ENGCONF`, `&PK_03_CURVE` — with an undefined `DEFINE` block at the top of the file,
and each child row referencing its parent's variable **by the same name**. That makes the dependency
graph explicit and auditable. The file is deliberately not runnable until a human binds the DEFINEs,
and says so in its header. The moment the mechanism resolves, the same file becomes runnable by filling
in that block — no regeneration.

What does not relax: no invented literal, no sequence that has not been mapped to its table, no PK
copied from an existing row, and every other gate and hard rule applies unchanged.

**Gate 0b is narrowed, not withdrawn.** It still has to resolve `FK_MISCONFIG` on the branch-config
row to the GBO MIS header — that header is the source for the MIS configuration this walk mines, so
the gate is load-bearing. What drops is the walk down into `T_PGT_BRANCH_INST_S` and
`T_PGT_BRANCH_INS_CONFIG_S`: those are the *branch-instrument* levels, and instrument scope now comes
from BOX's live catalogue via the SME. Conveniently, those are also the two levels whose join was
proven broken — see the correction block at the top.

### The sequence

**The GBO column is still the mining input** — the 2026-09-16 correction did not change that. What it
changed is where *instrument scope* comes from (BOX's live catalogue via the SME, not the branch's GBO
instrument tree). The `T_PGT_*` reads below stand.

| # | Config object | INSERT target (`BOX_FE`) | GBO source (`DEVENG`) | Query | Blocked by |
|---|---|---|---|---|---|
| 1 | FE configuration association — **read**: reuse or new? | `T_BOX_ENGCONF_X` | — | Q-01 | 0a, 0b |
| 2 | MIS Generic header | `T_BOX_ENGCONF_S` | `T_PGT_ENGCONF_S` | Q-02 | 1 |
| 3 | Fixing Curve header | `T_BOX_ENGFCURVE_S` | `T_PGT_ENGFCURVE_S` | Q-03 | 2 |
| 4 | Curve → quote reference linkage | `T_BOX_ENGLKFC_X` | `T_PGT_ENGLKFC_X` | Q-04 | 3 |
| 5 | Branch association row — **write** | `T_BOX_ENGCONF_X` | — (GBO side is `T_PGT_BRANCH_S`) | Q-01c | 2, 3, 4 |
| 6 | Accrual defaults | `T_BOX_ENGACCRCONF_S` | `T_PGT_ENGACCRCONF_S` | Q-05 | 0c, 5 |
| 7 | Accrual Exceptions | `T_BOX_CONFIG_ACCRUAL_S` | `T_PGT_CONFIG_ACCRUAL_S` | Q-06 | 6 |
| 8 | Fixing Exceptions | `T_BOX_FIXING_BY_INSTR_S` + `V_BOX_PROC_INSTR_S` | `T_PGT_FIXING_BY_INSTR_S` + `V_PGT_PROC_INSTR_S` | Q-07 | 3, 6 |
| 9 | Yield Curve | `T_BOX_ENGZCCONF_S` | `T_PGT_ENGZCCONF_S` | Q-08 | 2 |
| 10 | Currency Basis | `T_BOX_ENGCURRENCYBASIS_S` | `T_PGT_ENGCURRENCYBASIS_S` | Q-09 | 2 |
| 11 | Book — batch execution registration | `T_BOX_CONF_BY_BOOK_S` | **none — confirmed no GBO analogue** | Q-10 | 0c, 5, 6 |
| 12 | **Allowed Errors** — error limits per branch × instrument | `T_BOX_ERRORS_FE_S` | `[open-question]` — GBO twin unknown | Q-13 | 0c, 5, 6 |
| 13 | Derived — **verify, never INSERT** | `T_BOX_FIXING_ASSIGNMENT_S`, `T_BOX_BRPROCCAL_S` | — | Q-11 | 4, 11 |
| 14 | Not branch-scoped — **rule out with evidence** | `T_BOX_ENGDAYS_MATURED_S`, `T_BOX_ENGSETUP_S` | — | Q-12 | — |

> **Step 12 is new, 2026-09-17.** `[confirmed: BOX FE Developer via Edouard]` **Allowed Errors** —
> SIGOM path `BOX - Financial Engine > Process Management > Allowed Errors`, table
> `BOX_FE.T_BOX_ERRORS_FE_S` — defines **the error limit before a process crashes**, and it is defined
> **per instrument and per branch**. It was missing from this walk entirely: the developer's answer to
> *"is anything missing from the 13?"* That is exactly the failure mode the question existed to catch —
> an object a branch needs that nobody notices until the batch behaves wrongly. Being branch × instrument
> keyed, it is blocked by gate 0c like steps 6 and 11, and its row count should track the instrument
> scope. **✅ Its GBO counterpart exists** — `DEVENG.T_PGT_ERRORS_FE_S`, keyed by **`FK_BRANCH`**
> `[confirmed: DB via Edouard, 2026-09-18]`. The naming-rule prediction was right, so step 12 is an
> **ordinary mine-and-propose step**, not a step-11-style BOX-only one: the error limits come from the
> branch's own GBO configuration, not from a reference branch and not from an SME guess. The GBO column
> holding a *geographic* branch PK is also mild evidence against the product-shaped-branch worry on the
> GBO side — it settles nothing about the BOX side, whose column name is still unconfirmed.
>
> ⚠️ **This intersects the unanswered product-shaped-branch question.** Allowed Errors is one of the two
> screens where BOX-DEV showed the `Branch` column holding values like `BOX CCS` / `BOX FX` / `BOX IRS`
> rather than geographic branches. That oddity now sits **inside** the walk rather than beside it, which
> raises its priority: if "branch" means something different on this screen, step 12's grain is wrong.
> Still unanswered — re-ask.

### Why not the SIGOM tab order

SIGOM shows the tabs as Generic, Yield Curve, Accrual, Fixing Exceptions, Accrual Exceptions,
Currency Basis, Branch, Book. Working left to right would INSERT children before parents: `Branch`
sits seventh but its row ties the configuration to the branch, and `Yield Curve` sits second though
nothing depends on it. Above, the header and what it points at come first (2–5), then children in
dependency order (6–11), with Book last because it needs the association, the instrument scope and
the book scope all resolved.

### Notes on the steps that need them

**Step 1 is a read; step 5 is the write.** Both touch `T_BOX_ENGCONF_X`. Step 1 asks whether an FE
configuration already covers this branch (`FK_BS = BRANCH_PK`) — the fork deciding whether the rest
is "adapt existing" or "build new". Step 5 emits the association row. A script that writes the bridge
before the header exists fails on the FK.

> **Step 5 is not blockable on "BOX-specific values not in the GBO evidence" — 2026-09-18.** A run
> blocked this step reporting that `T_BOX_ENGCONF_X` needs `FK_OWNER_OBJ` and `FK_EXTENSION` values the
> GBO evidence does not supply. That is true and it is not a blocker: those two columns are **never**
> supposed to come from GBO (hard rule 9). All four values are available —
> `FK_PARENT` = the step-2 header variable, `FK_BS` = `&&BRANCH_PK` from Q-G1, `FK_OWNER_OBJ` and
> `FK_EXTENSION` from Q-G6 against the target (`35000126.65` / `35001566.65` in Tier 1). Step 5 is the
> row that ties the whole configuration to the branch; a walk that emits steps 2–4 and 6–12 but skips
> it has produced a configuration that belongs to nobody. **If step 5 cannot be emitted, that is a
> run-stopping finding, not a line item.**

**Steps 3–4: the curve is an array, not a header.**
`T_BOX_ENGCONF_S.{FK_CURVEMAN|FK_CURVEACC}` → `T_BOX_ENGFCURVE_S` → `T_BOX_ENGLKFC_X.FK_BS` →
`PGT_MRK.T_PGT_QUOTE_REFERENCE_S`, which resolves `FK_QUOTESOURCE` → `T_PGT_QUOTE_SOURCE_S` and
`FK_QUOTETYPE` → `PGT_SYS.PGT_DOMAINS`. So configuring a curve means configuring its quote-reference
rows too; step 4 is a real INSERT set, not a detail of step 3.

Step 4's *mining* is simpler than the rest of the walk: `PGT_MRK` and `PGT_SYS.PGT_DOMAINS` are
shared between BOX and GBO — one copy, read identically from either side — so there's no separate
"GBO version" to find. Only the `ENGLKFC_X` linkage rows are module- and curve-specific.

Also: `Fixing Curve` appears as a SIGOM leaf under **both** `Control > Configuration` and
`Control > Historical Data`. Confirm which is being read before comparing.

**Step 8 — two objects.** The tab is `T_BOX_FIXING_BY_INSTR_S` joined to the view
`V_BOX_PROC_INSTR_S` on `FK_INSTRUMENT = PK`. The view supplies the processed instrument; an exception
row alone carries only an FK.

**Step 12 — not INSERT targets.** `T_BOX_FIXING_ASSIGNMENT_S` is a *different table* from step 8's
`T_BOX_FIXING_BY_INSTR_S` (`box-data-model.md` lists both separately) and follows from the header's
curve selection via
`ENGCONF.{FK_CURVEACC|FK_CURVEMAN} → FIXING_ASSIGNMENT.{FK_FIXINGCURVE_ACC|FK_FIXINGCURVE_MAN}`; its
own `FK_PARENT` is a separate relationship and must never be invented. The runtime queue tables prove
branch/instrument *activity*, not configuration selection — in Tier 1 extracts zero rows had
`FK_CONFIG` or `FK_FIXCURVE` populated, so a null there is not a missing config.

**Step 11 — no GBO row to mine, confirmed by a BOX FE Developer (2026-09-11).** `T_BOX_CONF_BY_BOOK_S`
is new BOX functionality with no GBO precedent at all — not an unconfirmed name, an actual absence.
Functionally, a row here for `(branch, instrument)` is what registers that combination for the FE
batch to execute — in the developer's words, "the books which are created there for X branch and X
instrument are the ones that are executed." A missing row isn't an incomplete config value, it's that
combination never being processed, silently. Full explanation in
[`fe-branch-configuration.md`](../../docs/reference/branch-config/fe-branch-configuration.md)'s
"Book — batch execution registration" section.

This is the **first confirmed non-analogue object in the walk**, and it changes how the step is
evidenced — but "no GBO row" does not mean "no evidence at all." Three sources apply, none of them
GBO: (1) the **Data-Lake/Murex book enumeration** for this branch — the same developer confirmed
"the books are the books that we have in the Data Lake (Lago)," and that enumeration is the *same*
piece of evidence-gathering `control-m-batch-layer.md` §4 step 2 already requires for the batch build,
not a second exercise; (2) a **named SME decision** on which of those books need FE batch registration
specifically, since not every Data-Lake book necessarily needs one; (3) **structural reference** to an
existing BOX branch's Book rows (never copied — hard rule 6 still applies in full). Run Q-10's
canonical joined query (`fe-config-mining.md`) — it resolves `FK_INSTRUMENT` to the Sub-Product level
and `FK_LABEL` to `PGT_SYS.PGT_DOMAINS`, the book label — to see the current BOX-side fact; that fact
alone still isn't a proposal for NY_SCH without (1) and (2). Findings-table rows start from
`EVIDENCE_REQUIRED`/`SME_DECISION_REQUIRED` by default. Don't let step 11 default to
`CONFIRMED_ABSENT` the way an ordinary missing-mining-result would; absence of a *GBO* row here is the
*permanent, expected* state, not a gap to close by finding the right query — and a promising but
unverified match between `PGT_DOMAINS` labels and Control-M's `<BOOK-ABBREV>` naming
(`control-m-batch-layer.md` §3/§4) is worth flagging if seen again, not yet something to rely on.

**Step 13 — two tables that look like branch config and aren't.** `T_BOX_ENGDAYS_MATURED_S`
configures `NUM_DAYS` by instrument with **no branch column**; `T_BOX_ENGSETUP_S` is a generic/EAV
parameter store with no observed branch dimension. Neither needs a row for a new branch. They stay in
the walk because they sit in the same `Control > Configuration` folder as MIS and Fixing Curve, and an
agent that silently skipped them is indistinguishable from one that forgot them. Q-12 proves the
absence of a branch column rather than asserting it.

## Relationship to `branch-onboarding-orchestrator`

**Thin, one-directional delegation. This agent is invocable either way — standalone or as a
delegate — and the input contract is what makes that true.**

- The orchestrator owns the **branch-specific project**: which branch, what phase it's in, what's
  blocking it, and the cross-domain state in `docs/examples/<branch>-branch-onboarding.md`. Its own
  charter deliberately hard-codes its branch, which is right for something that owns one onboarding.
- This agent owns a **reusable capability**. It receives inputs, does the FE walk, and reports one
  status plus its `RUN_FOLDER` path.
- It does **not** read the orchestrator's state file, know about Phase 0–4, or track anything outside
  BOX FE. Cross-domain state is the orchestrator's job and duplicating it here would create two
  sources of truth for "where is this branch".
- Called standalone, a human supplies the same inputs directly. Nothing changes.

The formulation worth holding onto: **the capability is branch-agnostic, the run is branch-specific.**
Charter = capability. `prompts/kickoff-<branch>.md` = the bridge. `runs/<branch>/<env>/` = the run.

## Skills it may call

| Skill | Owner | Purpose here |
|---|---|---|
| `mine-fe-branch-config` | `branch-config-agent` | Emits read-only SQL for the GBO side and loads the results — already uses the emit-query → human-runs-it loop. Needs a variant reading the GBO tier this run targets |
| `propose-branch-config` | `branch-config-agent` | Produces the findings table from mined evidence |
| `generate-fe-config-sql` *(not yet implemented)* | this agent | **The net-new capability:** turns a signed-off findings table into ordered, annotated INSERTs with verification and rollback. Refuses any row not `PROPOSED` or better, and refuses entirely until gates 0d and 0e pass |

Nothing today emits SQL — `generate-fe-config-sql` is the first thing worth building. Until it exists,
the walk table is the checklist and a human writes the statements.

## Human checkpoints

- **Gate 0c** — product and book scope, before steps 6–11.
- **Gate 0d** — PK mechanism, before *any* INSERT is written.
- **The findings table as a whole**, before SQL is generated. The set, not object by object, so gaps
  are visible next to each other.
- **The SQL file**, before it runs anywhere including PRE — reviewed by someone who can answer "would
  SIGOM have done exactly this?" SIGOM writes audit columns, validates, and may write more than one
  table. A clean-running INSERT is not evidence it did the same thing.

## Escalation rules

- **A required value has no source** → `EVIDENCE_REQUIRED` / `SME_DECISION_REQUIRED`, and no statement
  is emitted for it.
- **A PK would have to be constructed** → stop. Gate 0d.
- **A walk table is missing in the target** → run the visibility preflight first. Zero visible `BOX_FE`
  objects is an **access** escalation, not a provisioning one — report it as such and block, producing
  no schema diff and no DDL. Only a genuine absence under a passing preflight is gate 0e: provisioning
  artifact, then block.
- **A missing object has no DDL in `cib-boxfin-dbboxfe`** → escalate.
- **Actual schema change needed** (a new column, an altered constraint — not a provisioning gap) →
  stop. That's a release.
- **A zero-row result on one of the four unverified joins** → verify the join before recording it as
  an absence.
- **Out-of-order execution** — record late-arriving evidence, but don't close a step before its
  prerequisites. In a script, out-of-order doesn't read badly, it fails.
- **A finding contradicts `fe-branch-configuration.md`** → the highest-value output available. Draft
  the correction against the specific doc and flag it loudly; never rewrite a `[confirmed]` claim on
  the agent's own authority.

## Eval case

See [`evals/cases/sigom-box-fe-configs-agent-walk.md`](../../evals/cases/sigom-box-fe-configs-agent-walk.md).
