# Procedure — BOX FE SIGOM config for a new branch

The step-by-step procedure `sigom-box-fe-configs-agent` follows to produce the BOX FE configuration SQL for
a new branch. The agent's **rules** live in its charter,
[`agents/sigom-box-fe-configs-agent/AGENT.md`](../../agents/sigom-box-fe-configs-agent/AGENT.md); this file holds
the **sequence**. When the two disagree, the charter wins — a procedure step can never authorise
something the hard rules forbid.

Kept separate from the charter on purpose: this document is expected to change repeatedly as Tier 2
work reveals what the steps actually are. The charter is not.

> **⚠️ Scope correction, 2026-09-16 — narrow.** `[stated: BOX Developer via Edouard]` Do **not** look
> up which *instruments* are configured for the branch in GBO: instrument scope is chosen from what is
> already created and live in **BOX**, by a named SME. **Everything else here stands** — the MIS
> configuration and Fixing Curve are still mined from their GBO equivalents, exactly as written below.
> The only step affected is **A2**, narrowed to level 1 (resolve `FK_MISCONFIG`); its two lower
> branch-instrument levels drop. Full correction at the top of
> [the charter](../../agents/sigom-box-fe-configs-agent/AGENT.md).

**Status:** first draft, written from Tier 1 evidence and the walk in the charter, then partly
corrected after the first live NY_SCH run (2026-09-16). Not yet executed end to end against Tier 2 —
every step below should be treated as provisional until it has been. `[inferred]` unless a step cites
otherwise.

**Scope:** BOX FE only. ACC follows once this has run once for real — see
[`agents/sigom-box-acc-configs-agent/AGENT.md`](../../agents/sigom-box-acc-configs-agent/AGENT.md)
for why that one is deliberately deferred rather than written in parallel.

**The queries** each step runs live in
[`docs/reference/queries/fe-config-mining.md`](../reference/queries/fe-config-mining.md), keyed by ID
(`Q-G1`, `Q-01`, …). Step tables below cite those IDs rather than repeating SQL.

**Where output goes:** `runs/<BRANCH_CODE>/<ENVIRONMENT>/` — layout and the evidence-filename contract
in [`runs/README.md`](../../runs/README.md).

---

## Stage A — Gates (no SQL is written during this stage)

*Gates 0a–0e and **0g** run here, before the walk. A **split-tier** run adds **gate 0f**, which cannot
run here because it tests mined values — see Stage D0.*

| Step | Action | Output | Blocks on failure |
|---|---|---|---|
| A0 | Write `00-inputs.md` — the filled-in input contract. Before any query runs | Run inputs, recorded | Yes — a missing input is a blocked start |
| A0b | **Q-G7 — gate 0g, the metamodel read** *(new 2026-09-18)*. `GOM_GLB_SYS` declares every object's storage, identity constants, FK targets and pre-commit procedures. Needs no `BOX_FE` access, so it runs first and parameterises Stage E | Object + field catalogue; completeness diff | No — but a join asserted without it is a defect |
| A1 | **Q-G1** — resolve the branch in GBO: PK, entity, currency, calendar, `FK_LOCALGROUP` | Branch profile; `BRANCH_PK` | Yes — propose GBO handoff, wait for `GBO-created` |
| A2 | **Q-G2** — resolve `FK_MISCONFIG` on the branch-config row to the GBO MIS header. **Narrowed 2026-09-16 to level 1**; the two branch-instrument levels below it are dropped (and their join is proven wrong — see the catalogue) | GBO MIS header resolved | Yes |
| A3 | Get product and book scope from a named SME, in writing — instruments chosen from **BOX's live catalogue**, not from the branch's GBO instrument config. **Run Q-05c against a reference branch first** (its Accrual tab, `T_BOX_ENGACCRCONF_S`, is that branch's instrument list) so the SME confirms a concrete enumeration rather than a phrase | Scope statement, attributed | Yes |
| A4 | **Q-G3** — ✅ **resolved 2026-09-17**: PKs come from `F___SEQUENCE(<table>,'X')` (shared sequence `SQ_BOX_FINANENG1` + the environment's auth code as a fraction). Re-run only to confirm the function exists in the target environment | PK mechanism — known | Satisfied |
| A5 | **Q-G4** — compare the target environment's `BOX_FE` schema against the reference environment, per walk table | Provisioning gap list | Yes — see Stage B |

Stage A produces no configuration. Its output is the evidence base everything else cites, and any
gate failing is a reportable end state — a partially-gated run is not "in progress", it's blocked.

**One exception, added 2026-09-18: gate 0e may be *deferred* rather than failed.** In a
**deferred-verification** run — the real target, read access not yet granted — A5 cannot run. That does
not block the walk: mining and SQL generation proceed, the SQL is marked **not executable**, and gate 0e
becomes the **release gate**. Nothing runs against a database until it passes. See the charter's
*Deferred-verification runs*.

**A4 returning nothing was a result, and it was the right one.** No sequence, no trigger and no column
default pointed at allocation in application code — and that is exactly what it turned out to be: a
function, `F___SEQUENCE`. `[confirmed: source via BOX FE Developer, 2026-09-17]` The consequence is not
that `INSERT` is unsafe, but that **the PK value in every INSERT must be `F___SEQUENCE('<TABLE>','X')`
assigned to a declared variable**, never a literal and never a bare `NEXTVAL`. Keep the original logic
for the next schema: finding nothing in the dictionary is a finding, not an inconclusive result.

## Stage B — Provisioning (only if A5 found gaps **under a passing visibility preflight**)

> **Retraction, 2026-09-16.** `[confirmed: DB]` "Tier 2 PRE is missing a substantial number of
> `BOX_FE` tables" was **wrong and is withdrawn** — the account used had no grants on `BOX_FE`, so the
> query measured visibility, not existence. Nothing is known about Tier 2 PRE's schema completeness.
> This stage is not currently expected to be needed, and must never be entered off a zero-visibility
> result: that is an **access** escalation, not a provisioning one. Run the Q-G4 preflight
> (`SELECT USER, SYS_CONTEXT('USERENV','DB_NAME'), COUNT(*) … WHERE OWNER='BOX_FE'`) before A5 is
> interpreted at all.

| Step | Action | Output |
|---|---|---|
| B1 | List every missing object, with the query that proves it missing | Schema diff artifact |
| B2 | Locate each object's authoritative DDL in `cib-boxfin-dbboxfe` and cite the file path | DDL source index |
| B3 | Order the missing objects by dependency | Runnable sequence for a DBA |
| B4 | Establish first whether this is an *incomplete environment* or an *undeployed module* — the corpus says NY is live in GBO Tier 2, not BOX, so `BOX_FE` may never have been deployed there at all | Answer, escalated to the orchestrator's Phase 0 either way |
| B5 | Hand off to the named release/DBA owner and block | Provisioning request |
| B6 | Once the objects exist, re-run A5 to verify — do not assume the handoff landed correctly | Confirmed-complete schema |

The agent never authors DDL and never runs it. See the charter's *Schema gaps* section for why
sourced-not-authored is a hard boundary and not caution.

## Stage C — Mining (read-only)

Worked one config object at a time, in the walk order (charter steps 1–14; **step 12, Allowed Errors /
`T_BOX_ERRORS_FE_S`, was added 2026-09-17**). For each object:

| Step | Action |
|---|---|
| C1 | Read the **GBO** side: the object's `Q-nn` query against its `DEVENG.T_PGT_*` counterpart (mapping in [`fe-branch-configuration.md`](../reference/branch-config/fe-branch-configuration.md) §2) |
| C2 | Read the **BOX** side (`Q-nnb`): does a row already exist for this branch? **Deferrable** — in a deferred-verification run this is the step that waits on target read access. Status the finding `EVIDENCE_REQUIRED` and carry on; never write `CONFIRMED_ABSENT` on an assumption |
| C3 | Classify: `CONFIRMED_PRESENT` (exists and correct), `CONFIRMED_ABSENT` (needs creating), or a gap status if neither can be established |
| C4 | For anything absent: identify each column's value source — read / SME / constant / derived |
| C5 | For derived values: state the rule, the GBO row it came from, and where the rule came from. Tag `DERIVED` |

**In `assisted` mode** (no DB connection), each query is handed over with: its ID, purpose, target
database, resolved parameters, runnable SQL, the exact output path
(`01-evidence/Q-05-accrual-gbo.csv`) and the expected row count — then the agent stops and waits.
Ask in **dependency batches**, not all at once: Q-G1 parameterises everything, and a gate failure can
make twenty queries irrelevant. Validate an arriving CSV's shape before using it; a mismatch is a
re-run request, not data to interpret creatively.

**Never let a zero-row result mean "absent" when the query itself may be wrong.** Four catalogue
queries rest on an assumed join column (see the catalogue's Coverage check) — Q-08 and Q-09 in
particular. A zero-row result from a wrong join column is indistinguishable from a genuine absence,
and is the most plausible way this procedure produces a confidently wrong answer. Verify the join
before recording `CONFIRMED_ABSENT`.

**Order matters even here.** Charter step 1 (does an FE configuration association exist at all?) is
the fork that decides whether the rest is "adapt an existing configuration" or "build a new one".
Do not mine children before it's answered.

## Stage D0 — Cross-tier FK resolution (split-tier runs only) `[new 2026-09-18]`

**Not applicable when source and target are the same environment** — including a deferred-verification
run against the real target, which is the preferred shape when target access is missing. Applies only to
a split-environment run, once per environment pair rather than once per run.

`[stated: Edouard, 2026-09-18]` `PGT_STC` and `PGT_SYS` hold **identical rows in every environment**, so
calendars, currencies, the branch master, Sub-Product instruments and domain values need no
cross-environment check at all. The only reference values worth comparing are **`PGT_MRK` quote
references**. Never block a run on a `PGT_STC`/`PGT_SYS` value — an out-of-sync shared schema is a
platform escalation, not a walk finding.

| Step | Action | Output |
|---|---|---|
| D0-1 | List every FK value that will appear in a statement, from the findings table | FK inventory |
| D0-2 | **Q-14** — resolve each one in both environments, compare descriptions | Two CSVs, diffed |
| D0-3 | Tag each: `CROSS_TIER_VERIFIED`, `EVIDENCE_REQUIRED` (absent in target), or **escalate** (resolves to a different object) | Gate 0f result |

A value that is absent in the target gets no statement. A value that resolves to a **different** object
stops the run — that is the silent-wrong-value failure the whole agent exists to prevent, and it will
not announce itself any other way. See the charter's *Gate 0f* section.

## Stage D — Findings review (human gate)

| Step | Action |
|---|---|
| D1 | Assemble the findings table — every walk step present, every one statused |
| D2 | Separate `DERIVED` rows out for individual sign-off; they may not ride along in a batch approval |
| D3 | Route to the SME(s) named in A3 |
| D4 | Block until every row is confirmed, rejected, or explicitly deferred |

Deliverable parts 1 and 2 (evidence trail + findings table) are worth handing over at this point
even if no SQL is ever generated. A gap list with evidence is useful on its own; INSERTs without one
are worse than nothing.

## Stage E — SQL generation

Only for findings rows that are signed off. Gates A4 (PK mechanism) and A5 (schema complete) must both be satisfied — Stage E cannot start on a provisional answer to either.

| Step | Action |
|---|---|
| E0 | **Bind the SIGOM identity constants from gate 0g** — `FK_OWNER_OBJ`/`FK_EXTENSION` per target table, derived from the metamodel (Q-G7/Q-G6). Three screens, not one *(added 2026-09-18)* |
| E1 | Generate statements in FK-dependency order (charter steps 2→3→4→5→6→7→8→9→10→11→12) *(corrected 2026-09-18 — this list stopped at 11 and silently dropped Allowed Errors, added as step 12 on 2026-09-17)* |
| E2 | Annotate each statement: which GBO row it derives from, which findings row authorises it, and for `DERIVED` values the rule |
| E3 | Pair each statement with its verification `SELECT` and its rollback `DELETE` |
| E4 | State which SIGOM screen and action each statement set reproduces |
| E5 | Scope the file to **PRE**. A PRO file is generated separately, after PRE is verified |
| E6 | Emit no statement for a read-only step (1), a derived-data step (**13**), a not-branch-scoped step (**14**), or a parked step (9, 10, 4b) *(numbering corrected 2026-09-18 — it still used the pre-Allowed-Errors walk)* |
| E7 | **Classify each object's pre-commit procedure, then place the call accordingly** — charter hard rules 10 and 11. ⛔ *Corrected 2026-09-21: this step previously said "call it after its INSERT", which is wrong for step 2's procedure and unsafe for the script.* See the table below |

### E7 in detail — the placement depends on what the procedure does

`[confirmed: source via Devin, 2026-09-21]` **Read the body before deciding where the call goes.**

| Class | Walk objects | Placement |
|---|---|---|
| **No DML** — SELECTs, raises on failure | `P_ENGFixingCurve_PreCommit` (steps 3, 4) | Call it straight after the INSERT, as a validation gate. Safe anywhere |
| **Same-row DML** — computes columns on its own row | the ACC procedures; none in the FE walk | Do **not** supply the columns it computes; call it, then read the row back |
| ⛔ **Cross-table DML, and it `COMMIT`s** | **`p_check_Val_Curves_precommit`** (steps 2, 5, 6 — and probably 7–11) | See below. **Never inside a transaction you intend to roll back** |

**`p_check_Val_Curves_precommit`, passed the step-2 header PK, UPDATEs step 8's
`T_BOX_FIXING_BY_INSTR_S WHERE fk_parent = pk_in`** — back-filling null fixing curves from the header
defaults — and issues an explicit **`COMMIT`** after each of its three conditional UPDATEs.

**The correct handling, per hard rule 10:**

1. **Emit step 8's rows with their curve values already populated.** Where the GBO row is null, fill from
   the configuration header and tag it `DERIVED`, citing `023-pkg_engprecommit_body.sql:413-438`.
2. **Then call the procedure.** With no nulls left, its UPDATEs do not fire, so it commits nothing —
   and its finding nothing to do is positive evidence the INSERT set already matched SIGOM.

Calling it early (right after step 2, before step 8's rows exist) is a harmless no-op but proves
nothing. Calling it late on unpopulated rows commits the whole outstanding transaction.

### E8 — run the validator before anything leaves this stage *(added 2026-09-21)*

```bash
python3 scripts/validate_run_output.py <RUN_FOLDER>
```

Mechanical checks on everything Stage E produced: literal PKs, `INSERT … SELECT FROM DEVENG`, missing
walk steps, non-canonical statuses, INSERT ordering, statements emitted for parked steps, a missing
preflight, and the committing-procedure/rollback conflict from E7. **A FAIL stops Stage F** — it is not
advisory, and the findings table is not signed off while one stands.

It is a linter, not a reviewer: it cannot judge whether a *value* is right. It exists so the human
review in Stage D spends its attention on judgement rather than mechanics. See
[`../../scripts/README.md`](../../scripts/README.md).

## Stage F — Apply and verify

| Step | Action |
|---|---|
| Step | Action |
|---|---|
| F0 | ⛔ **Establish whether this script is reversible at all** — see the warning below. If any statement set contains a committing procedure, the trailing `ROLLBACK` is not an undo and the rollback `DELETE`s from E3 are the only one *(added 2026-09-21)* |
| F1 | A human runs the PRE script. The agent never holds write access |
| F2 | Run the verification `SELECT`s. Any unexpected result → stop, do not continue to the next object |
| F3 | Check the INSERT set against what SIGOM would have produced — method below |
| F4 | Report what was applied, what verified, and what didn't |
| F5 | Only then generate and hand over the PRO script |

> ## ⛔ The script's trailing `ROLLBACK` is not a safety net
>
> `[confirmed: source, 2026-09-21]` `p_check_Val_Curves_precommit` issues an explicit **`COMMIT`**. A
> committing procedure commits **the entire outstanding transaction**, including every INSERT the script
> has performed to that point. Charter hard rule 11.
>
> So: **the rollback `DELETE`s (E3) are the real undo**, and they must be correct and tested. Any run
> plan phrased as *"execute it, look at it, roll back"* is valid **only** for a statement set proven to
> contain no committing procedure — and that has to be stated, not assumed.

**F3's method, corrected 2026-09-21.** The earlier form — *snapshot → INSERT → call the procedure →
re-snapshot → `ROLLBACK`* — **cannot be used on a committing procedure**; it would commit the test. Use
whichever applies:

| Procedure class | Method |
|---|---|
| **No DML** (`P_ENGFixingCurve_PreCommit`) | The snapshot/rollback form is safe. Any change means the walk is incomplete |
| ⛔ **Committing** (`p_check_Val_Curves_precommit`) | **Make it a no-op and call it.** Populate step 8's curve values at INSERT time; the procedure's UPDATEs then don't fire, it commits nothing, **and finding nothing to do is the evidence.** No rollback needed because nothing changed |
| Either | Where a reference branch allows it, diff a script-created row against the equivalent row created through SIGOM |

Stage F3 is the one most likely to be skipped and the one most likely to catch a real defect. SIGOM
writes audit columns, validates, and — now proven — **may write to a different table than the one you
inserted into**; a clean-running INSERT is not evidence that it did the same thing.

---

## Open items in this procedure

- ~~**A4 (PK generation)** is unresolved for every table.~~ ✅ **Resolved 2026-09-17** — `F___SEQUENCE`;
  see A4 above. This item said the procedure "stops at Stage D," which stopped being true that day and
  was stale here until 2026-09-18.
- ✅ **F3 has a method** *(2026-09-18; corrected 2026-09-21)*. Five walk objects declare a
  `PRE_COMMIT_PROC` and their bodies have now been read. The comparison is no longer freeform — but
  **the method depends on the procedure's class**, because `p_check_Val_Curves_precommit` COMMITs and
  therefore cannot be tested by the snapshot-and-rollback form. See Stage F above.
- **B4** — incomplete environment vs. undeployed module — changes the size of the whole project and
  should be answered before Stage C effort is spent.
- ~~**four of its queries rest on an assumed or unconfirmed join/column** — Q-G1's branch-code column,
  Q-08's and Q-09's `FK_PARENT`, and Q-10's GBO table name.~~ ✅ **All four resolved.** Q-G1's column is
  `CODE` (2026-09-18); Q-08's and Q-09's `FK_PARENT` are declared owned collections of `BOX_ENG_Config`
  (2026-09-18); Q-10's "missing GBO table" was resolved 2026-09-11 as a confirmed *absence*. **The
  general fix is gate 0g** — SIGOM declares its relationships in `GOM_GLB_SYS`, so a join in this
  catalogue should cite a declaration rather than an assumption. See
  [`../reference/sigom-metamodel.md`](../reference/sigom-metamodel.md).
- The mechanised version of the catalogue belongs in the `generate-fe-config-sql` skill, which doesn't
  exist yet — still the largest missing piece.
- Nothing here is validated against a real Tier 2 run. Expect the stage boundaries to move.
