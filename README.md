# BOX Onboarding — Automation Project

This repo is the working memory for automating onboarding into BOX (Derivatives Accounting system) — new entities, new branches, and new products are three related but distinct axes of the same problem (see `docs/reference/branch-config/README.md` for how they differ). It holds three kinds of things, kept deliberately separate:

- **`docs/`** — the wiki, split by kind of document (process / reference / examples / decisions — see `docs/README.md`), not by topic.
- **`skills/`** — narrow, reusable capabilities (e.g. "create legal entity in BOX", "map chart of accounts") that an agent invokes as a tool. A skill does one thing and can be tested on its own.
- **`agents/`** — the orchestrators. An agent composes skills to complete a job end-to-end (e.g. "onboard a new entity") and is what Devin (or another runtime) actually runs.
- **`evals/`** — test cases that prove a skill or agent behaves correctly, independent of any specific runtime.

## Why this split

Skills and agents get rewritten often as the process and the tooling change. Docs describe ground truth that outlives any one implementation. Keeping them apart means a change to one doesn't force a rewrite of the other, and any future agent (not just Devin) can be pointed at `docs/` and `skills/` without dragging in orchestration logic.

## Ground rules

1. **Docs first.** Before writing a skill or agent, make sure the step it automates is documented in `docs/process/`. If it isn't, write that up first — undocumented automation is a black box nobody can debug in six months.
2. **One skill, one job.** If a skill needs "and" in its description, split it.
3. **No real entity, counterparty, or portfolio names anywhere in this repo.** Use placeholders (`ENTITY_A`, `CPTY_X`) in every doc, prompt, and eval case — including ones sourced from screenshots or trade captures.
4. **Every agent and skill ships with at least one eval case.** No eval, no merge.
5. **Decisions get an ADR**, not a Slack thread. See `docs/decisions/`.

## Quickstart for a new contributor (human or agent)

1. Read `docs/reference/system-overview.md` for what BOX is, then `docs/process/00-overview.md` for the (entity) onboarding flow end to end.
2. Onboarding a **branch**, not an entity? Start instead with `docs/process/checklists/branch-onboarding-checklist.md` (the master checklist) and `docs/reference/branch-config/README.md`.
3. Read `docs/reference/box-data-model.md` for the BOX-specific facts you'll need.
4. Look at `skills/example-create-legal-entity/` as the template for a new skill.
5. Look at `agents/example-entity-onboarding-agent/` as the template for a new agent.
6. Add your eval case to `evals/cases/` before considering anything "done".

## Status

- **Entity onboarding** (the original scope of this repo): structure only. Fill in `docs/process/01-current-state.md` first — today's manual onboarding steps, as they actually happen, before automating anything.
- **Branch onboarding**: reference material is well developed (see `docs/reference/branch-config/`), but almost all of it is empirically grounded in Tier 1 (Madrid/London) — nothing yet in Tier 2 (US/Brazil/Mexico). Agent design is done — see `docs/reference/branch-config/agent-architecture.md` and the four agents under `agents/` (`branch-onboarding-orchestrator`, `box-datalake-expert`, `box-fe-expert`, `box-acc-expert`) — but none has a real eval fixture yet. The live case is `docs/examples/ny-sch-branch-onboarding.md`; everything is blocked on Tier 2 DB access.
