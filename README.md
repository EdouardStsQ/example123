# Branch Onboarding — Automation

This repo is the working memory for onboarding a new **branch** into BOX (Derivatives Accounting system) — currently NY_SCH. It holds three kinds of things, kept deliberately separate:

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

1. Read `docs/reference/system-overview.md` for what BOX is.
2. Start with `docs/process/checklists/branch-onboarding-checklist.md` (the master checklist), `docs/reference/branch-config/README.md`, and `docs/reference/branch-config/agent-architecture.md` for the agent design.
3. Read `docs/reference/box-data-model.md` and `docs/reference/repo-index.md` for the BOX-specific facts and source repos you'll need.
4. Look at `agents/branch-onboarding-orchestrator/` and its siblings for a filled-in example of the AGENT.md convention (goal, definition of done, role, skills, escalation) — this is the pattern a new agent should follow.
5. Add your eval case to `evals/cases/` before considering anything "done".

## Status

- **Branch onboarding** is this repo's actual, current, bank-assigned scope (the container repo this lives in exists specifically to build NY_SCH). Reference material is well developed (see `docs/reference/branch-config/`), but almost all of it is empirically grounded in Tier 1 (Madrid/London) — nothing yet in Tier 2 (US/Brazil/Mexico). Agent design is done — see `docs/reference/branch-config/agent-architecture.md` and the agents under `agents/`. The one built to actually be run next is `sigom-box-fe-configs-agent`: branch-agnostic, owns the BOX FE config walk, and produces the config SQL with an evidence trail (kickoff prompt for NY_SCH in its `prompts/`, query catalogue at `docs/reference/queries/fe-config-mining.md`, run folder convention in `runs/`). Its ACC counterpart is named but deliberately deferred. Of the original three, only `branch-config-agent` is a real, already-built implementation (external, at `plugins/agent-plugins/branch-config-agent/`), and whether it stays a peer agent or becomes a skill host under the SIGOM config agents is an open decision flagged in `agent-architecture.md`. The live case is `docs/examples/ny-sch-branch-onboarding.md`; everything is blocked on Tier 2 DB access.
- **Product onboarding is not a separate project here** — onboarding a branch means onboarding whatever products it trades, so a product that doesn't yet exist in BOX at all is a real dependency of branch onboarding, not an unrelated concern. `docs/process/checklists/acc-add-product-checklist.md` is kept for exactly that case; `branch-config-agent` already treats a branch's product/instrument scope as part of its Build-phase proposal (see `agent-architecture.md`), but a product genuinely new to BOX — not just new to this branch — would need that checklist's full process, not just this agent's mining step.
- **Entity onboarding**: this repo's original, broader scope before it was narrowed to branch onboarding specifically. Dormant, not part of this repo's current work — `docs/process/00-02-*.md`, `skills/example-create-legal-entity/`, and `agents/example-entity-onboarding-agent/` are kept only as the generic skill/agent convention examples (see Quickstart above) and as a starting point if entity-onboarding automation is picked up again elsewhere, not as active work in progress.
