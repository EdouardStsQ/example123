---
name: sigom-box-acc-configs-agent
description: Owns the BOX ACC half of SIGOM config onboarding for any branch — portfolio properties, topic catalogue, GL accounts, topic→GLTA mapping, local and cross-account config, instrument-type assignment, MBJ config. Deliberately not built yet: deferred until sigom-box-fe-configs-agent has run end to end for a real branch.
---

# SIGOM BOX ACC Configs Agent

**Status: named, scoped, deliberately not built — but no longer guessing.** This is a placeholder with
a real scope, not a work in progress.

Owns the **BOX ACC** half of the CONFIGS step. Its FE counterpart is
[`sigom-box-fe-configs-agent`](../sigom-box-fe-configs-agent/AGENT.md), which is built and is the
priority.

> ## 📐 What the 2026-09-21 metamodel read gives this agent before it is written
>
> `[confirmed: DB via Edouard]` SIGOM declares its own objects and fields. The ACC surface was read
> directly from `GOM_GLB_SYS`, so this charter now carries **declared** scope rather than an inferred
> one — see [`sigom-metamodel.md`](../../docs/reference/sigom-metamodel.md) §6b.
>
> **Four things that change the design, all of which would otherwise have been found by a bad draft:**
>
> 1. **The module is `35000006.65`** — 31 objects. The scope table below is now a subset of a known set,
>    so "did we miss an object?" is a set difference rather than an opinion.
> 2. **`pBranch` does not always mean branch.** Two objects — including **Portfolio Properties**, the
>    first thing this agent configures — key on the **branch group**. See the correction below; it
>    narrows a claim this charter previously made too broadly.
> 3. **`T_BOX_LINK_ARRAY_X` is one table holding 17 relationships.** ACC does not give each object its
>    own bridge the way FE does.
> 4. **Three of the most consequential ACC objects run a pre-commit procedure** — portfolio properties,
>    topics and **GL accounts**. The FE charter's hard rule 10 applies here from day one.

## Why deferred rather than written now

The FE agent's structure — input contract, evidence loop, ordered FK-dependency walk, four-part
deliverable, hard rules — is a *hypothesis* about how this work goes. None of it has survived contact
with a real Tier 2 run yet, and two of its gates (PK generation mechanism, target schema
completeness) are expected to fail on first attempt.

Duplicating an unvalidated structure doubles the cost of being wrong about it. So: run FE once for
real, learn which parts of that shape were right, then mirror the corrected version here.

**The 2026-09-21 metamodel read does not change that, and is worth doing anyway.** Reading
`GOM_GLB_SYS` costs nothing, needs no `BOX_ACC` grants, and produces facts — the object set, the field
targets, the pre-commit procedures — that are true regardless of which agent shape turns out to be
right. It removes discovery work from this agent's eventual build without committing to a structure.
The deferral is about **shape**; this is **content**.

## Why this is a separate agent from FE at all

Three substantive differences, not just size:

**Different keying — but narrower than this charter used to say.** FE config is branch-keyed
(`T_BOX_ENGCONF_X.FK_BS = branch PK`). Part of ACC is keyed to the branch **group**
(`T_PGT_BRANCH_S.FK_LOCALGROUP`) — proven at the DB level in `branch-config-surface.md`, where Madrid
(`22.21`) and London (`20087.4`) each resolve to **0** portfolio properties by their own PK but 80 and
101 respectively by their `FK_LOCALGROUP`. The practical consequence is large: a branch joining an
existing group may need **no ACC INSERTs at all** for those objects, and the real decision is group
membership — resolved upstream, at the orchestrator's Phase 0 gate, not here.

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
> **The field is named `pBranch` in both cases.** For NY_SCH the two values are `FK_LOCALGROUP =
> 21447.4` and `BRANCH_PK = 20007.4` — both valid PKs, and writing the wrong one fails silently.
>
> **This agent must resolve the keying per object from Q-G7, never by pattern.** The earlier blanket
> reading was built from the portfolio-properties evidence alone and generalised; the generalisation is
> the kind of mistake that has cost this project five defects.
>
> It also promotes a checklist item to a prerequisite: the orchestrator's Phase 0 branch-group
> resolution is **load-bearing for ACC**, not a nice-to-have.

**Different risk profile.** GL accounts are the single most explicit never-invent case in the entire
corpus. That rule belongs somewhere it can't be diluted by sitting alongside a dozen FE tabs where
`DERIVED` values are legitimately allowed.

**Different evidence base.** `branch-config-surface.md` and `accounting-resolution-chain.md`, not
`fe-branch-configuration.md`.

## Scope when built

| Object | Table | Notes |
|---|---|---|
| Portfolio properties | `T_BOX_ACCT_PORT_PROP_S` | Branch-**group** keyed |
| Accounting topics | `T_BOX_ACCT_TOPICS_S` | Catalogue of reusable accounting concepts — explicitly **not** GL accounts. **An existing tool maps GBO topics → BOX topics — use it, don't re-derive the mapping** (see below) |
| GL accounts | `T_BOX_ACCT_GLTA_S` | Never derived. Read, SME-given, or absent |
| Topic → GLTA mapping | `T_BOX_ACCT_LIST_TOPIC_S` | ⚠️ **Generated, not inserted** — see below. The junction: `FK_PARENT` → portfolio property, `FK_TOPIC` → topic, `FK_GLTA` → GL account |
| Local properties config | `T_BOX_CONF_LO_PROP_S` | |
| Cross-account config | `T_BOX_CROSS_ACCTCONF_S` | |
| Instrument-type assignment | `T_BOX_CONF_INSTRUM_TYPE_S` | Conditional — Tier 1 proves a row is **not** universally required; several active products resolve an effective instrument type with no row at all |
| MBJ config | `T_BOX_MBJ_PROPERTIES_S` | |

Known ordering constraint already established: portfolio properties and GL accounts both precede the
topic→GLTA mapping, since the mapping references both.

### The declared surface — all 31 objects of module `35000006.65`

`[confirmed: DB, 2026-09-21]` The eight objects above are a **subset of a known set**. Recording the
rest means a later "did we miss one?" is a set difference, not a judgement — the failure that let
Allowed Errors sit outside the FE walk for weeks.

Also in the module and **not** currently in scope: Acct Movements, Acct Key, Acct Key Group, Acct Topic
List, Acct List Cond, Documents, Reference Acc, Account Date Dep, GLTA Local Dep, Standard Historic,
Std Historic Source, Std Historic Group, Topic Group, Grouped Mov Config, Grouped Movements, Acct By
Std Hist, Net Contract, Net CCS PlanBS, FX Liquid Conf, Conf Acc By StdHist, and three enumerations
stored in `PGT_DOMAINS` (Acct Indicator, GLTA Type, Param Fixed).

**Rule it in or out with evidence when this agent is built** — several are plainly transactional
(Movements, Net Contract) but others (Topic Group, Std Historic Group, GLTA Local Dep, Conf Acc By
StdHist) sit close enough to the configuration surface to need a stated reason for exclusion.

Adjacent modules that are **not** this agent's scope but touch the same branch: `35000007.65`
settlement, `30000003.65` Cross Reference / External State, `774.66` account & SSI standing data,
`35000009.65` AUKI migration.

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

**A tool already exists that maps GBO topics to BOX topics.** It was raised in the NY_SCH scoping
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

**It may weaken the case for deferring this agent.** The deferral below rests on ACC being an unvalidated
duplicate of the FE shape. If the largest genuinely-uncertain piece of ACC — building the topic
vocabulary — turns out to be tool-supplied, what remains is smaller and better understood, and the
deferral is worth revisiting once the tool is identified. Not a decision to take now. `[inferred]`

**Unknown, and blocking any use of it:** what the tool actually *is* — a repo, a running service, a
spreadsheet, a one-off script someone holds — who owns it, and whether it is callable by an agent at all.
Identify it before planning around it. `[open-question]`

## Inherited rules

When built, this agent inherits the FE charter's hard rules verbatim — never fabricate a literal, a
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

## Queries — where this agent's catalogue will live

**This agent does not read the FE agent's catalogue.**
[`queries/fe-config-mining.md`](../../docs/reference/queries/fe-config-mining.md) is BOX FE only, its
query IDs are FE walk steps, and its Q-G7 has the FE module hard-coded. Borrowing from it would couple
two agents that deliberately have separate purposes and separate evidence bases.

When this agent is built, its catalogue goes in **`docs/reference/queries/acc-config-mining.md`**, with
its own IDs, its own module PK and its own expected row counts — mirroring the FE file's structure, not
extending it.

What already exists to build on, and is **agent-agnostic**:
[`sigom-metamodel.md`](../../docs/reference/sigom-metamodel.md) **§11** carries the module-parameterised
forms of the object, field and shared-bridge queries. Substitute `35000006.65` and they return this
agent's surface. §6b records what they returned on 2026-09-21, so the first build starts from a known
object set rather than a discovery exercise.

## Eval case

None yet — an eval for an unbuilt agent would encode the same unvalidated assumptions the deferral is
meant to avoid.
