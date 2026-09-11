# Onboarding Process — Overview

Branch onboarding: bringing a branch that already exists in **GBO** live in **BOX** — configured (BOX_FE + BOX_ACC), batch-fed (Control-M/Data-Lake + internal BOX_FE/ACC jobs), and producing accounting that reconciles against what GBO already produces for it today. Current live case: **NY_SCH** (GBO Tier 2). This file is the map; the detail lives in `01-current-state.md` (today, manual) and `02-target-state.md` (target, agent-assisted) plus `../reference/branch-config/`.

This repo's scope was narrowed from a broader "entity onboarding" origin to branch onboarding specifically — see the root README's Status section. The old entity-onboarding process docs (`00-02-*.md` under the original numbering, now superseded by this file) are kept only as generic convention examples (`skills/example-create-legal-entity/`, `agents/example-entity-onboarding-agent/`), not as active scope.

## Scope

- **What counts as "onboarding a branch" here**: the branch already exists in GBO (Tier 1 or Tier 2); the job is building its BOX_FE and BOX_ACC configuration and its batch jobs, so that trades booked to it produce correct BOX accounting instead of (or ahead of) GBO's.
- **What triggers it**: the bank assigns a branch to be brought onto BOX (NY_SCH today). Who raises the request and how it's scoped up front is `[open-question]` — not yet documented, worth confirming with the BOX team.
- **Systems touched besides BOX**: GBO (read-only source of the branch's existing config), SIGOM (the UI for both GBO and BOX_FE/BOX_ACC configuration), Murex/Data Lake/Control-M (the batch feed), and a deployment pipeline that promotes config/job changes toward production (see the PRE/pre-production note in `01-current-state.md` — its exact identity isn't confirmed yet).
- **What "done" means**: see the Definition of done in `agents/branch-onboarding-orchestrator/AGENT.md` — the branch is configured, its batch jobs run, the full readiness trace resolves, and its BOX postings reconcile against GBO's for the same trade population.
- **A branch's product scope is part of this, not separate from it**: onboarding NY_SCH means onboarding whatever products it trades — see the root README's Status section and `agent-architecture.md`.

## Out of scope (for now)

- **A product genuinely new to BOX** (not just new to this branch) — that's `checklists/acc-add-product-checklist.md`'s process. A real dependency of branch onboarding when it happens, but a different checklist.
- **Entity (legal entity) onboarding** — this repo's original, broader scope. Dormant; kept only as the generic agent/skill convention example (root README Status).
- **Online/BOX_TRD real-time onboarding.** No doc, no agent yet — `branch-trading-readiness.md` already names the role (`branch-trd-agent`) but nobody has built it. Whether NY_SCH even needs this for v1 (vs. batch-only) is an open Phase-0 question in `agent-architecture.md` — don't assume either answer.

## High-level flow

Canonical phase numbering lives in `../reference/branch-config/agent-architecture.md` — don't re-derive a different scheme here or in the two files below; map onto it instead.

1. **Phase 0 — Gate.** Confirm Tier 2 DB access, resolve the branch's group (existing vs. new), confirm product scope with the business/FO SME.
2. **Phase 1 — Build, config track.** Mine GBO's existing FE + ACC configuration for the branch, propose the BOX-schema equivalent. See `01-current-state.md` step "Configs" and `02-target-state.md`.
3. **Phase 1 — Build, jobs track.** Identify the batch jobs an analogous branch runs (Data-Lake ingestion + internal FE/ACC batch), propose the equivalent set for the new branch. See `01-current-state.md` step "Jobs" and `02-target-state.md`.
4. **Phase 2 — Sign-off.** SME confirms every proposed value (GL accounts, portfolio properties, job wiring) before anything is applied — nothing in Phase 1 is invented, only proposed.
5. **Phase 3 — Apply.** Deploy the confirmed config and jobs into the pre-production environment.
6. **Phase 4 — Validate.** Run the readiness trace end to end and reconcile against GBO. See `01-current-state.md` step "Test".

## Related docs

- Current (manual) process: `01-current-state.md`
- Target (agent-assisted) process: `02-target-state.md`
- Master checklist: `checklists/branch-onboarding-checklist.md`
- Agent workflow and design: `../reference/branch-config/agent-architecture.md`
- BOX overview: `../reference/system-overview.md`
- Live case: `../examples/ny-sch-branch-onboarding.md`
