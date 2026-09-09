# Target State — Automated Onboarding (To-Be)

Maps `01-current-state.md`'s seven steps onto the agent architecture already designed in `../reference/branch-config/agent-architecture.md`. This file only reduces steps described there — it doesn't invent a new phase scheme; see that doc's Phase 0–4.

## Automated flow

| Current-state step | Becomes | Notes |
|---|---|---|
| 1. Configs — look up GBO's FE+ACC config | `box-fe-expert` + `box-acc-expert`, Phase 1 (mine) | Once Tier 2 DB access exists, this becomes a deterministic query (`branch-config-surface.md` §5's mining method) instead of manual SIGOM screen reading. |
| 2. Configs — adapt to BOX schema | `box-fe-expert` + `box-acc-expert`, Phase 1 (propose) / Phase 3 (apply) | Proposal is agent-driven for structure; GL account values and portfolio-property breakdowns stay SME-owned per the golden rule — never invented. See the "never writes GBO" guardrail in `agents/box-fe-expert/AGENT.md` and `agents/box-acc-expert/AGENT.md`. |
| 3. Configs — deploy to PRE | Phase 3 — Apply | **Stays manual for now.** The deployment mechanics (is this the Ansible/VSS repo's `preproduction/` stage, or a separate BOX promotion path?) aren't automated or even fully described yet — see the open note in `01-current-state.md` step 3. Resolve that question before scoping any automation here. |
| 4. Jobs — Control-M/Data-Lake analogue expansion | `box-datalake-expert`, Phase 1 | Already the most template-able part of the process — `control-m-batch-layer.md` §4 gives a deterministic expansion method (identify country/source_system → enumerate books → generate the 6-job-per-book template → wire `eventsToWaitFor`), rated 🟢 high automation potential in that doc already. |
| 5. Jobs — BOX_FE/BOX_ACC internal batch analogue | `box-fe-expert` / `box-acc-expert`, Phase 1 | Blocked on `box-fe-acc-batch-runtime.md` landing (see `job-chains/README.md`) — can't be scoped more precisely than "propose from analogue" until then. |
| 6. Jobs — deploy to PRE | Phase 3 — Apply | Same open deployment-mechanics question as step 3. |
| 7. Test | Phase 4 — Validate | Formalized as the `accounting-resolution-chain.md` trace, plus reconciliation against GBO — see the orchestrator's Definition of done in `agents/branch-onboarding-orchestrator/AGENT.md`. Whichever informal "run a test" check happens today should be reconciled with this trace once someone confirms what it currently covers. |

None of the seven steps has a standalone **skill** yet — today they're expressed as agent-owned mining/proposal steps inside the three experts, not broken out under `skills/`. Candidates worth extracting once the agents have actually run once for real: `mine-gbo-branch-config`, `expand-controlm-batch-template`.

Every step above becomes either an **agent** (`box-datalake-expert`, `box-fe-expert`, `box-acc-expert`, orchestrating via `branch-onboarding-orchestrator`) or **stays manual, with a reason**: deployment-to-PRE (mechanics not yet understood) and Phase 2 sign-off (manual by design, not a gap to close).

## Human checkpoints

- **Phase 0 — Gate.** Tier 2 DB access and product scope must be confirmed before anything downstream starts.
- **Phase 2 — Sign-off.** Every SME-owned value (GL accounts, portfolio properties, job event wiring for any feed not seen on the analogue branch) — this is a regulatory/financial-correctness checkpoint, not a review nicety.
- **Phase 4 — Validate.** A reconciliation break against GBO is a human escalation, not an auto-retry — see the Phase 4 note in `agent-architecture.md`.

## Rollback / error handling

Not yet defined — carried over unfilled from the original template, and genuinely open. Worth specifying before Phase 3 (Apply) is ever run for real:

- What happens if a deployed config turns out wrong in PRE — is the SIGOM change rolled back, or forward-fixed?
- Does a partially-run Control-M/Data-Lake job expansion need cleanup if a book turns out to be mis-scoped mid-onboarding?

Flag these to the orchestrator's Standing Obligation (`agents/branch-onboarding-orchestrator/AGENT.md`) once they stop being template gaps and become real questions someone needs answered.
