---
name: entity-onboarding-agent
description: Orchestrates end-to-end onboarding of a new entity in BOX, from validated static data through go-live checks.
---

# Entity Onboarding Agent

## Goal

One or two sentences: the outcome this agent is accountable for, stated as an outcome — not "orchestrates X, Y, Z" (that's mechanism; it belongs in Role/Sequence below). If getting there requires a standing obligation beyond the immediate job (e.g. capturing what's learned along the way), say so here and keep it explicitly subordinate to the main goal — never a second goal it can trade off against.

## Definition of done

The concrete, checkable conditions under which this agent's job is actually finished — not "the sequence ran," but the real-world outcome that sequence exists to produce. Number them. Mark any criterion that's a proposal rather than something already agreed (see `branch-onboarding-orchestrator/AGENT.md` for a worked example, including how it handles an unconfirmed criterion honestly instead of asserting it).

## Role

One paragraph: what this agent is responsible for, and — just as important — what it is *not* responsible for (link to `docs/process/02-target-state.md`).

## Skills it may call

| Skill | Purpose |
|---|---|
| create-legal-entity | see `skills/example-create-legal-entity/SKILL.md` |
| ... | ... |

## Sequence

1. ...
2. ...

## Human checkpoints

Where this agent must stop and wait for sign-off, and from whom.

## Escalation rules

What it does when a skill fails, when required input is missing, or when it hits a case not covered by its sequence. Default should always be "stop and surface", never "guess and continue".

## Eval case

See `evals/cases/entity-onboarding-agent-happy-path.md`.
