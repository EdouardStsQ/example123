---
name: sigom-box-acc-configs-agent
description: Owns the BOX ACC half of SIGOM config onboarding for any branch — portfolio properties, topic catalogue, GL accounts, topic→GLTA mapping, local and cross-account config, instrument-type assignment, MBJ config. Deliberately not built yet: deferred until sigom-box-fe-configs-agent has run end to end for a real branch.
---

# SIGOM BOX ACC Configs Agent

**Status: named, scoped, deliberately not built.** This is a placeholder with a real scope, not a
work in progress.

Owns the **BOX ACC** half of the CONFIGS step. Its FE counterpart is
[`sigom-box-fe-configs-agent`](../sigom-box-fe-configs-agent/AGENT.md), which is built and is the
priority.

## Why deferred rather than written now

The FE agent's structure — input contract, evidence loop, ordered FK-dependency walk, four-part
deliverable, hard rules — is a *hypothesis* about how this work goes. None of it has survived contact
with a real Tier 2 run yet, and two of its gates (PK generation mechanism, target schema
completeness) are expected to fail on first attempt.

Duplicating an unvalidated structure doubles the cost of being wrong about it. So: run FE once for
real, learn which parts of that shape were right, then mirror the corrected version here.

## Why this is a separate agent from FE at all

Three substantive differences, not just size:

**Different keying.** FE config is branch-keyed (`T_BOX_ENGCONF_X.FK_BS = branch PK`). ACC's manual
config is keyed to the branch **group** (`T_PGT_BRANCH_S.FK_LOCALGROUP`) — proven at the DB level in
`branch-config-surface.md`, where Madrid (`22.21`) and London (`20087.4`) each resolve to **0**
portfolio properties by their own PK but 80 and 101 respectively by their `FK_LOCALGROUP`. The
practical consequence is large: a branch joining an existing group may need **no ACC INSERTs at all**,
and the real decision is group membership — resolved upstream, at the orchestrator's Phase 0 gate,
not here.

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
| Topic → GLTA mapping | `T_BOX_ACCT_LIST_TOPIC_S` | The junction: `FK_PARENT` → portfolio property, `FK_TOPIC` → topic, `FK_GLTA` → GL account |
| Local properties config | `T_BOX_CONF_LO_PROP_S` | |
| Cross-account config | `T_BOX_CROSS_ACCTCONF_S` | |
| Instrument-type assignment | `T_BOX_CONF_INSTRUM_TYPE_S` | Conditional — Tier 1 proves a row is **not** universally required; several active products resolve an effective instrument type with no row at all |
| MBJ config | `T_BOX_MBJ_PROPERTIES_S` | |

Known ordering constraint already established: portfolio properties and GL accounts both precede the
topic→GLTA mapping, since the mapping references both.

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

## Eval case

None yet — an eval for an unbuilt agent would encode the same unvalidated assumptions the deferral is
meant to avoid.
