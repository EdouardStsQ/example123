# Devin kickoff — NY_SCH branch onboarding

Paste this as the task prompt to Devin. Swap `NY_SCH` throughout for a future branch's code once this one is done — the workflow is designed to be reusable, but check the "Evidence boundary" and "Deliberately not built yet" sections of `agent-architecture.md` for what's still NY_SCH-specific before assuming it transfers as-is.

---

You are running as this repo's `branch-onboarding-orchestrator` (`agents/branch-onboarding-orchestrator/AGENT.md`, full design in `docs/reference/branch-config/agent-architecture.md`).

**Your goal: get branch NY_SCH onboarded into BOX.** NY_SCH is live in GBO Tier 2 and absent from BOX; your job is to reproduce in BOX what GBO already does for it, with GBO as the source of truth for values and SMEs as the authority that confirms them. Read the **Definition of done** in your `AGENT.md` before you start and treat it as the bar — in particular, note that passing the readiness chain is not sufficient on its own, and that its reconciliation criterion is still an unconfirmed proposal you should raise with an SME early rather than discover late.

Follow the Phase 0 → 4 workflow, and keep `docs/examples/ny-sch-branch-onboarding.md` current as the single record of where this stands — current phase, each expert's status, and every open question with who it's blocked on.

**Capture what you learn as you go.** Read the *Standing obligation* section of your `AGENT.md` and treat its triggers as live throughout, not as a write-up at the end. You are producing the first Tier 2 evidence this repo has ever contained — nearly every `[confirmed: DB]` claim in `docs/reference/branch-config/` is Tier 1 (Madrid/London) only. When a Tier 2 finding contradicts one of those, that is the most valuable thing you will produce all project: draft the correction against the specific doc and flag it prominently. Propose, never rewrite a confirmed claim on your own authority. This obligation never justifies deferring onboarding work, and onboarding pressure never justifies skipping it.

**Execution mode.** You are one Devin session, not four separate agents. Where the workflow calls for invoking `box-datalake-expert`, `box-fe-expert`, or `box-acc-expert`, that means: read that agent's `AGENT.md`, adopt its scope and escalation rules for that phase, and — since none of its skills are implemented yet — build whatever skill you need as you reach it, rather than assuming it already exists as a callable service. Keep each expert's boundaries intact even while you're the one executing all of them (don't let ACC-config reasoning leak into the FE-expert phase, don't let DataLake routing work wander into FE processing).

**Non-negotiable rules:**

- Phase 0 (Gate) first, always: confirm Tier 2 DB access, NY_SCH's branch-group resolution, product scope, and whether online/CROSS_REF is in scope for v1. Do not proceed to Phase 1 until these are answered. If Tier 2 DB access isn't available yet, stop here and report that as the blocker — don't simulate or infer what the data would show.
- Never invent a config value — no GL account, portfolio property, SIGOM tab value, or routing identifier. Every value is either mined from GBO Tier 2 or flagged as an open question for SME sign-off. This is the rule every source doc in this repo repeats; it's not optional.
- Phase 2 (Sign-off) is a hard stop: present proposals, wait for confirmation, apply nothing unconfirmed.
- If you hit the online (CROSS_REF) gap, or anything not covered by an existing doc, stop and report it rather than routing around it — that's a real evidence gap in this repo, not something to guess through.
- As you go, replace the pending eval-case stubs in `evals/cases/` (`box-datalake-expert-happy-path.md`, `box-fe-expert-happy-path.md`, `box-acc-expert-happy-path.md`, `branch-onboarding-orchestrator-happy-path.md`) with what actually happened, and update the open questions in `docs/examples/ny-sch-branch-onboarding.md` as they get answered.

Report back after each phase, not just at the end.
