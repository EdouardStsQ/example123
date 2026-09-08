# Branch Onboarding — Agent Architecture

This is the workflow and agent design behind branch onboarding, written against the first live case — `NY_SCH`, which exists in **GBO Tier 2** but not yet in BOX. Where a decision is genuinely NY_SCH-specific (Tier 2, no BOX-side analogue yet) that's called out rather than silently generalized; everything else is meant to hold for the next branch too.

See [`../../topic-index.md`](../topic-index.md) for the subsystem breakdown these agents map onto, and [`README.md`](README.md) for the "scope templatable, values not" rule they all follow.

## Two phases, not one chain

`branch-trading-readiness.md` gives a workflow order: source arrival → instrument type → FE status → ACC movement. That's the right order to **validate** an onboarded branch — it's literally the trace `accounting-resolution-chain.md` runs as the acceptance test. It is not the order in which NY_SCH gets **built**.

NY_SCH's build order is different because the branch already exists somewhere: GBO Tier 2. The job isn't "stand up online arrival, then instrument type, then FE, then ACC" from a blank slate — it's "GBO Tier 2 already has this branch's configuration; mine it per domain; propose the BOX equivalent; get SME sign-off; apply." Only once that's done does the readiness chain get run, as validation, not construction.

So the architecture below has a **Build phase** (mine → propose → sign-off → apply, per domain, mostly parallel) and a **Validate phase** (the existing readiness chain, run once, at the end).

## The four agents

| Agent | Status | Scope | First NY_SCH deliverable | Primary docs |
|---|---|---|---|---|
| `branch-onboarding-orchestrator` | New. Name adopted from `branch-trading-readiness.md`, which already names this role — not coining a new one. | **Accountable for the outcome**: NY_SCH onboarded into BOX, per the Definition of done in its `AGENT.md`. Delegates all domain work to the three experts; owns the Phase 0 gate, the Phase 4 validation run, and the current-state record. | Runs the Gate checklist, delegates Build, blocks Apply until all three are signed off, runs Validate + reconciliation. | `branch-trading-readiness.md`, `../../process/checklists/branch-onboarding-checklist.md` |
| `box-datalake-expert` | New. | Murex → Data Lake → BOX RAW-table batch routing. Does **not** cover the Murex → online (CROSS_REF) real-time path — no doc exists for that yet (see Known gap in `topic-index.md`). | Confirm/extend NY_SCH's `source_system`/country-code routing in the Control-M/`diaria.json` config so its data lands in the expected RAW tables. | `control-m-batch-layer.md`, `../fe-raw-data-stage.md` |
| `box-fe-expert` | New. | BOX_FE config (the eight SIGOM tabs, fixing curves/QR FX) and FE batch topology. | Mine GBO Tier 2's FE-equivalent config for NY_SCH and propose the BOX_FE equivalent, flagged for SME. | `fe-branch-configuration.md`, job-chain doc pending `box-fe-acc-batch-runtime` |
| `box-acc-expert` | Renames/absorbs the existing `branch-config-agent` (external — lives in Devin's generated repos with real scripts `extract_branch_config.py`, `diff_branches.py`), extended with a new capability. | BOX_ACC config (portfolio properties, topic→GLTA, GL accounts, branch-group dual-keying) and ACC batch topology. | Mine GBO Tier 2's ACC-equivalent config for NY_SCH and propose the BOX_ACC equivalent. This is genuinely new capability: `branch-config-agent`'s existing scripts diff one **BOX** branch against another (validated Tier 1, Madrid vs. London) — NY_SCH has no BOX side to diff against yet, so the extraction has to read GBO Tier 2 instead. | `branch-config-surface.md`, `accounting-resolution-chain.md`, `branch-config-madrid-london-diff.md` (Tier 1 evidence only, see its Evidence boundary) |

Instrument-type resolution isn't a fifth agent — per `topic-index.md` it's a concern both `box-fe-expert` and `box-acc-expert` already have to carry (per-product instrument identity), not an independent domain with its own build step.

## The workflow

**Phase 0 — Gate** (blocking; orchestrator-owned; nothing below starts until this clears)

- Tier 2 DB access confirmed.
- NY_SCH's branch group resolved: existing group or new (`FK_LOCALGROUP`).
- Product scope confirmed by SME.
- **Open question, not yet answered**: does NY_SCH need the online (CROSS_REF) real-time path configured for v1, or is it batch-only initially? If the answer turns out to be "yes, online is in scope," that work currently has no doc and no agent — stop and flag it for research before committing to build it blind.

**Phase 1 — Build** (parallel — the three experts' mining/proposal steps are independent per domain)

- `box-datalake-expert` extends routing.
- `box-fe-expert` mines GBO Tier 2 and proposes FE config.
- `box-acc-expert` mines GBO Tier 2 and proposes ACC config.

Each stops at "proposed, pending SME" — nothing is applied on the strength of a mined value alone.

**Phase 2 — Sign-off** (orchestrator-owned)

Collects all three proposals, routes to SME, blocks progression until every one is confirmed. This is the same golden rule as the rest of the corpus (propose + flag, never invent), applied at the orchestration level rather than left to each expert individually.

**Phase 3 — Apply**

Each expert applies its own confirmed config. No cross-domain dependency here — FE and ACC config can be applied independently; the FE-output-feeds-ACC dependency is a *runtime* dependency (Phase 4), not a config-build one.

**Phase 4 — Validate** (orchestrator-sequenced)

Runs `accounting-resolution-chain.md`'s trace end to end: source arrival → instrument type → FE status → ACC movement posted. A failure here stops and surfaces which stage broke — it does not fall back into Phase 3 automatically.

## Deliberately not built yet

- **Online/BOX_TRD onboarding.** No doc, no agent. `topic-index.md`'s Known gap. Phase 0 has to establish whether this is even in scope for NY_SCH before anyone spends time speccing an agent for it.
- **The FE→ACC completion-event contract** (the `mdfinancialcheck`-style barrier between FE and ACC batch). Procedurally owned by the orchestrator's Phase 3→4 transition, but the actual technical signal — what `box-fe-expert` emits, what the orchestrator checks before calling Phase 4 — isn't written yet. Needs `box-fe-acc-batch-runtime` once Devin's analysis of it is shared.

## Evidence boundary

This section is expected to change as NY_SCH progresses — keeping it accurate is the orchestrator's standing obligation (see its `AGENT.md`), and a Tier 2 finding that contradicts something below should be drafted as a correction here rather than worked around in a session.

Same caveat as the rest of `branch-config/`: everything empirical here is Tier 1 unless stated otherwise. But there's a second, sharper boundary specific to this architecture — **mining GBO Tier 2 is genuinely new ground**. Every existing validated extraction (`branch-config-agent`'s scripts, the Madrid/London diff) is BOX-to-BOX. Nothing has been proven yet for BOX-from-GBO. Treat every "propose" step in Phase 1 as unvalidated until a full Phase 4 run passes for NY_SCH.
