# Branch Onboarding — Agent Architecture

This is the workflow and agent design behind branch onboarding, written against the first live case — `NY_SCH`, which exists in **GBO Tier 2** but not yet in BOX. Where a decision is genuinely NY_SCH-specific (Tier 2, no BOX-side analogue yet) that's called out rather than silently generalized; everything else is meant to hold for the next branch too.

See [`../../topic-index.md`](../../topic-index.md) for the subsystem breakdown these agents map onto, and [`README.md`](README.md) for the "scope templatable, values not" rule they all follow.

## Two phases, not one chain

`branch-trading-readiness.md` gives a workflow order: source arrival → instrument type → FE status → ACC movement. That's the right order to **validate** an onboarded branch — it's literally the trace `accounting-resolution-chain.md` runs as the acceptance test. It is not the order in which NY_SCH gets **built**.

NY_SCH's build order is different because the branch already exists somewhere: GBO Tier 2. The job isn't "stand up online arrival, then instrument type, then FE, then ACC" from a blank slate — it's "GBO Tier 2 already has this branch's configuration; mine it per domain; propose the BOX equivalent; get SME sign-off; apply." Only once that's done does the readiness chain get run, as validation, not construction.

So the architecture below has a **Build phase** (mine → propose → sign-off → apply, per domain, mostly parallel) and a **Validate phase** (the existing readiness chain, run once, at the end).

## The three agents

**Correction (2026-09-09):** an earlier version of this doc split Build-phase config work into two agents, `box-fe-expert` and `box-acc-expert`. That was wrong — it was designed before we'd actually looked inside the existing `branch-config-agent` (real, already-built code at `plugins/agent-plugins/branch-config-agent/`, not a proposal). Its `propose-branch-config` skill already emits **one** combined decision matrix spanning GBO + BOX_FE + BOX_ACC + Control-M, fed by two independent mining skills (`mine-fe-branch-config`, `mine-branch-config`). Splitting that into two agents would mean forking a skill that already reconciles FE and ACC correctly, for no functional gain — so the design below folds `box-fe-expert` into `branch-config-agent` rather than keeping the split. See `agents/branch-config-agent/AGENT.md` for the merged agent.

**Correction (2026-09-11) — the count below is stale, and one decision is still open.** Two agents
have since been added, organised by *config surface* rather than by mining mechanics:
`sigom-box-fe-configs-agent` (built — owns the BOX FE walk, produces the config SQL, branch-agnostic)
and `sigom-box-acc-configs-agent` (named, deliberately deferred until FE has run once for real). They
were split from each other because FE is branch-keyed while ACC is branch-**group**-keyed, and
because GL accounts carry an absolute never-derive rule that shouldn't sit alongside FE tabs where
labelled `DERIVED` values are legitimate.

That leaves an **open decision**: `branch-config-agent` (below) and `sigom-box-fe-configs-agent`
overlap on BOX FE config. The recommendation is that `branch-config-agent` becomes a **skill host**
— its three real skills (`mine-fe-branch-config`, `mine-branch-config`, `propose-branch-config`) stay
and are called by the two SIGOM config agents — rather than remaining a peer agent with its own
claim on FE config. That is a decision for the BOX Lead, not a change to make quietly, so both are
still listed as peers here. Until it's resolved, treat `branch-config-agent`'s `AGENT.md` as
describing *the skills*, and `sigom-box-fe-configs-agent`'s as describing *the step*.

| Agent | Status | Scope | First NY_SCH deliverable | Primary docs |
|---|---|---|---|---|
| `branch-onboarding-orchestrator` | New. Name adopted from `branch-trading-readiness.md`, which already names this role — not coining a new one. | **Accountable for the outcome**: NY_SCH onboarded into BOX, per the Definition of done in its `AGENT.md`. Delegates all domain work to the two delegates below; owns the Phase 0 gate, the Phase 4 validation run, and the current-state record. | Runs the Gate checklist, delegates Build, blocks Apply until both are signed off, runs Validate + reconciliation. | `branch-trading-readiness.md`, `../../process/checklists/branch-onboarding-checklist.md` |
| `box-datalake-expert` | New. | Murex → Data Lake → BOX RAW-table batch routing. Does **not** cover the Murex → online (CROSS_REF) real-time path — no doc exists for that yet (see Known gap in `topic-index.md`). | Confirm/extend NY_SCH's `source_system`/country-code routing in the Control-M/`diaria.json` config so its data lands in the expected RAW tables. | `control-m-batch-layer.md`, `../fe-raw-data-stage.md` |
| `branch-config-agent` | Renamed and adopted as-is from the existing external agent (`plugins/agent-plugins/branch-config-agent/`, real scripts `extract_branch_config.py`, `extract_fe_branch_config.py`, `generate_branch_plan.py`), extended with a new capability. | BOX_FE **and** BOX_ACC config for **this branch**, as one combined proposal: the eight SIGOM tabs, portfolio properties, topic→GLTA *mapping* and *values*, GL accounts, branch-group dual-keying. Does **not** own the topic/event vocabulary itself — `accounting-resolution-chain.md` §10 names a `Matrix Agent` that "proposes universal events/topics only" as a product-axis (cross-branch) concern; this agent consumes that vocabulary as an input rather than inventing it. | Mine GBO Tier 2's FE- and ACC-equivalent config for NY_SCH and propose the combined BOX_FE + BOX_ACC decision matrix. This is genuinely new capability: the existing scripts diff one **BOX** branch against another (validated Tier 1, Madrid vs. London) — NY_SCH has no BOX side to diff against yet, so the extraction has to read GBO Tier 2 instead. | `fe-branch-configuration.md`, `branch-config-surface.md`, `accounting-resolution-chain.md`, `branch-config-madrid-london-diff.md` (Tier 1 evidence only, see its Evidence boundary), job-chain doc pending `box-fe-acc-batch-runtime` |

Instrument-type resolution isn't a fourth agent — per `topic-index.md` it's a concern `branch-config-agent` already has to carry (per-product instrument identity), not an independent domain with its own build step.

## The workflow

**Phase 0 — Gate** (blocking; orchestrator-owned; nothing below starts until this clears)

- Tier 2 DB access confirmed.
- NY_SCH's branch group resolved: existing group or new (`FK_LOCALGROUP`).
- Product scope confirmed by SME.
- **Open question, not yet answered**: does NY_SCH need the online (CROSS_REF) real-time path configured for v1, or is it batch-only initially? If the answer turns out to be "yes, online is in scope," that work currently has no doc and no agent — stop and flag it for research before committing to build it blind.

**Phase 1 — Build** (parallel — the two delegates' mining/proposal steps are independent)

- `box-datalake-expert` extends routing.
- `branch-config-agent` mines GBO Tier 2 (FE and ACC) and proposes the combined BOX_FE + BOX_ACC config.

Each stops at "proposed, pending SME" — nothing is applied on the strength of a mined value alone.

**Phase 2 — Sign-off** (orchestrator-owned)

Collects both proposals, routes to SME, blocks progression until every one is confirmed. This is the same golden rule as the rest of the corpus (propose + flag, never invent), applied at the orchestration level rather than left to each delegate individually.

**Phase 3 — Apply**

`branch-config-agent` applies FE and ACC config independently — no cross-domain dependency here, since the FE-output-feeds-ACC dependency is a *runtime* dependency (Phase 4), not a config-build one.

**Phase 4 — Validate** (orchestrator-sequenced)

Runs `accounting-resolution-chain.md`'s trace end to end: source arrival → instrument type → FE status → ACC movement posted. A failure here stops and surfaces which stage broke — it does not fall back into Phase 3 automatically.

The chain resolving is **not sufficient on its own**. NY_SCH's legacy system (GBO Tier 2) is live and already producing correct movements, so the real test is that BOX's postings for a given trade population **reconcile against GBO's**, with every break explained or accepted by an SME — see the orchestrator's Definition of done. That reconciliation step has no owner and no skill yet (see below); until it does, a chain that resolves cleanly proves the plumbing works, not that the numbers are right.

## Deliberately not built yet

- **Online/BOX_TRD onboarding.** No doc, no agent — but not nameless: `branch-trading-readiness.md` already names `branch-trd-agent` alongside `branch-onboarding-orchestrator` as the role that owns this. Adopt that name if this is ever built, rather than coining a new one. `topic-index.md`'s Known gap. Phase 0 has to establish whether this is even in scope for NY_SCH before anyone spends time speccing it.
- **The FE→ACC completion-event contract** (the `mdfinancialcheck`-style barrier between FE and ACC batch). Procedurally owned by the orchestrator's Phase 3→4 transition, but the actual technical signal — what `branch-config-agent` emits on the FE side, what the orchestrator checks before calling Phase 4 — isn't written yet. Needs `box-fe-acc-batch-runtime` once Devin's analysis of it is shared.
- **Reconciliation against GBO Tier 2.** Required by the orchestrator's Definition of done, but scope and tolerance are unconfirmed with SMEs and no skill (`reconcile-against-gbo`) is scoped, let alone implemented. The corpus names a *Reconciliation & Acceptance Agent* that has never been placed in this architecture — this is very likely its job, and a fifth agent may turn out to be warranted here once the scope is confirmed, unlike the ones this doc argued against elsewhere.

## Evidence boundary

This section is expected to change as NY_SCH progresses — keeping it accurate is the orchestrator's standing obligation (see its `AGENT.md`), and a Tier 2 finding that contradicts something below should be drafted as a correction here rather than worked around in a session.

Same caveat as the rest of `branch-config/`: everything empirical here is Tier 1 unless stated otherwise. But there's a second, sharper boundary specific to this architecture — **mining GBO Tier 2 is genuinely new ground**. Every existing validated extraction (`branch-config-agent`'s scripts, the Madrid/London diff) is BOX-to-BOX. Nothing has been proven yet for BOX-from-GBO. Treat every "propose" step in Phase 1 as unvalidated until a full Phase 4 run passes for NY_SCH.
