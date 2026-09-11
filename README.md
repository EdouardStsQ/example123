# Branch Config

How a branch's configuration resolves across BOX_TRD / BOX_FE / BOX_ACC — the reference material behind branch onboarding specifically. A branch's product scope is part of this work, not separate from it (see the root README's Status section) — `../../process/checklists/acc-add-product-checklist.md` is the process to fall back on if a branch needs a product genuinely new to BOX, not just new to that branch. Carved out of `reference/` once it had this many closely-related files.

| Doc | Covers |
|---|---|
| `branch-config-surface.md` | BOX_ACC account resolution: the branch-group vs branch-PK dual-keying gotcha, what must be configured for a new branch, how to mine an existing branch's effective config |
| `fe-branch-configuration.md` | GBO → BOX_FE configuration bridge, the eight SIGOM config tabs, how to assess reuse-vs-new-config for a branch |
| `branch-trading-readiness.md` | The full readiness chain (source arrival → instrument type → FE status → ACC movement) and the required branch-onboarding workflow order |
| `branch-config-madrid-london-diff.md` | Empirical proof, from the two live Tier 1 branches, that GL accounts/properties do **not** transfer between branches — only topic vocabulary and instrument-topic scope do |
| `accounting-resolution-chain.md` | The runtime trace from deal → instrument type → portfolio property → topic → GLTA → account key → Historic Standard → posted movement — the acceptance-test path for any new branch |
| `agent-architecture.md` | The workflow and agent design for actually doing an onboarding — Build (mine GBO → propose → sign-off → apply) vs. Validate (this folder's readiness chain), and the three agents (`branch-onboarding-orchestrator`, `box-datalake-expert`, `branch-config-agent`) that carry it out |

## The one thing to hold onto across all five

**Scope is templatable from an analogous branch; values are not.** Every doc here converges on this. A new branch's *(instrument, topic)* coverage can be proposed from an existing branch's config; the actual GL account numbers and property breakdowns cannot — they are always SME/GBO-sourced, never invented or copied. See the golden rule stated in `../../process/checklists/branch-onboarding-checklist.md`.

## Cross-cutting index

For "which doc do I need to understand subsystem X" (BOX FE vs. BOX ACC vs. instrument resolution, etc.) rather than "what's in this folder," see `../../topic-index.md` — it indexes these five docs alongside the checklist, the Control-M doc and the system overview by BOX subsystem.

## Evidence boundary — read before trusting any "confirmed" tag here

Every empirical number in these five docs (the Madrid/London diff, the Tier 1 branch/property/topic counts) comes from **Tier 1** (the Madrid data center, hosting Madrid + SLB/London). Nothing here has been validated against **Tier 2** (the US data center, hosting US/NY, Brazil, Mexico). A `[confirmed: DB]` tag in these docs means confirmed *in Tier 1* — it does not mean confirmed for a Tier 2 branch. Treat any Tier 2 branch's config surface as unverified until it's actually queried there.
