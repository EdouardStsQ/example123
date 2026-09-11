# Agents

An agent owns an end-to-end job — e.g. "onboard a new entity" — by sequencing skills, handling their failures, and knowing when to stop and ask a human. Agents are what Devin (or another runtime) actually executes; skills are the tools they call.

## Convention

```
agents/<agent-name>/
  AGENT.md        # goal, definition of done, role, the skills it uses, guardrails, escalation rules
  prompts/         # system prompt / instructions, if the runtime needs them separate from AGENT.md
```

## Rules

- **An `AGENT.md` opens with a goal, not a mechanism.** State the outcome the agent is accountable for before describing what it sequences or calls — "Role"/"Skills it may call" describe *how*; they don't substitute for saying *what for*. An agent whose first line describes its call graph will optimize for running its steps, not for the outcome.
- **Every `AGENT.md` has a Definition of done** — the concrete, checkable conditions under which the job is actually finished. If "the workflow completed" and "the definition of done is met" can come apart (a phase resolves cleanly but the real-world outcome still isn't there), the definition of done is what's true; the workflow completing without it is a bug in the agent, not a success. Say so explicitly if any criterion is a proposal rather than an agreed one.
- An agent's `AGENT.md` must list every skill it's allowed to call — no implicit tool access.
- Define escalation explicitly: what the agent does when a skill fails, when it's unsure, and when a human sign-off is required (see `docs/process/02-target-state.md` for the checkpoints that must stay manual).
- No real entity/counterparty/portfolio names in prompts or examples.
- Every agent needs at least one eval case covering a full run, not just its individual skills.

See `example-entity-onboarding-agent/` for the section layout, and `branch-onboarding-orchestrator/AGENT.md` for a filled-in example of Goal + Definition of done done right — it's the worked example these two rules were written from, after an earlier draft of it shipped without either and had to be corrected.
