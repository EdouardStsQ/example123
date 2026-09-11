# Current State — Manual Onboarding (As-Is)

**Status: first draft, not yet SME-confirmed.** The steps below come from Edouard's own high-level description of how this is done today `[stated: Edouard, 2026-09-09]` — by his own caveat, possibly oversimplified or missing steps. Treat this as a starting draft to correct, not settled ground truth. If the BOX team or an SME corrects a step here, edit this file directly (don't just note the correction elsewhere) — same standing-obligation discipline the orchestrator applies everywhere else in this repo.

## Steps today

| # | Step | Owner/team | System | Notes / pain points |
|---|------|-----------|--------|----------------------|
| 1 | **Configs — look up existing config.** Manually check, in SIGOM, which branch × instrument configuration already exists in GBO for both the Financial Engine (FE) and Accounting Engine (ACC) — control settings, portfolio properties, accounts, etc. | `[open-question]` who does this today — BOX team, SME, or both | SIGOM (GBO side) | `[stated]` Done manually, screen by screen — no automated diff yet. The eight FE config tabs this maps onto are catalogued in `../reference/branch-config/fe-branch-configuration.md`; the ACC-side objects (portfolio properties, topic→GLTA maps, GL accounts) in `../reference/branch-config/branch-config-surface.md`. |
| 2 | **Configs — adapt to BOX schema.** Manually recreate the equivalent configuration in BOX's own SIGOM screens. E.g. `GBO > Financial Engine > Control > Configuration` becomes `BOX > Financial Engine > Control > Configuration`. | same | SIGOM (BOX side) | `[stated]` The one-for-one screen mapping is the working assumption, not yet proven for every tab/object — some BOX_ACC objects (GL accounts, topic→GLTA maps) are BOX-native and don't have a literal GBO screen equivalent (see the SIGOM/GBO open-question in `branch-config-surface.md` §4). |
| 3 | **Configs — deploy to PRE.** Deploy the configuration change into the pre-production environment to test. | `[open-question]` | `[open-question]` which pipeline | Whether "PRE" here is the same `preproduction/` deployment stage tracked by the bank-provided Ansible/VSS repo (see the Infrastructure section of `../reference/repo-index.md`) or a separate BOX-environment promotion step isn't confirmed yet — worth asking directly, since if it's the same pipeline, that repo's mechanics (CODEOWNERS review, the encrypt/decrypt Action) apply here too. |
| 4 | **Jobs — Control-M/Data-Lake analogue.** Review the Control-M / Data-Lake batch jobs an existing, already-live branch runs (Madrid/SLB today), identify which similar jobs the new branch needs — per book (e.g. `Mx3LT`, NY's books). | same | Control-M | `[confirmed: repo]` Already well-documented — see `../reference/job-chains/control-m-batch-layer.md` for the exact per-book 6-job template (Deal/Flow/Market Data) and naming convention. This step is the most template-able one in the whole process. |
| 5 | **Jobs — BOX_FE/BOX_ACC internal batch analogue.** Review the BOX_FE / BOX_ACC internal batch jobs (Control-M / MBJ), general and product-specific, an existing branch runs for a given product, and create the equivalent for the new branch — e.g. "if Madrid Deposits runs this job sequence, NY Deposits probably needs the same sequence." | same | Control-M / MBJ, BOX_FE/BOX_ACC internal batch | `[stated]` Corroborates the still-pending `box-fe-acc-batch-runtime.md` (see `job-chains/README.md`) — five repo names are known (`cib-boxfin-t1mdesfe` and others, all Tier 1/Madrid so far by naming inference — see `repo-index.md`), but the actual job topology hasn't been imported into a doc yet. This step stays a sketch until that import lands. |
| 6 | **Jobs — deploy to PRE.** Deploy the new/updated jobs into the pre-production environment to test. | same | `[open-question]`, same pipeline question as step 3 | |
| 7 | **Test.** Run an end-to-end test in PRE. | same | `[open-question]` what the test concretely checks | `[stated]` Not yet specified whether this means a single booked trade flowing through, a specific instrument, or a reconciliation against GBO. `../reference/branch-config/accounting-resolution-chain.md`'s trace (deal → instrument type → portfolio property → topic → GLTA → account key → posted movement) is the natural candidate for what this step *should* formally be — not yet confirmed that it's what's actually run today. |

## Inputs required to start

- An existing branch in GBO to onboard (NY_SCH today).
- Tier 2 DB access, to look up the branch's actual GBO config — blocked as of this writing (see `../examples/ny-sch-branch-onboarding.md`).
- An analogous, already-live branch to pattern steps 4–5 on. Madrid/SLB is the only proven analogue so far, and it's Tier 1 — whether it's structurally right for a Tier 2 branch like NY_SCH is itself an open question (`../examples/ny-sch-branch-onboarding.md`, open question 5).

## Manual checks / tribal knowledge

- **Picking the analogue branch** (steps 4–5) is currently a judgment call, not a documented rule. `branch-config-madrid-london-diff.md` proved concrete config values don't transfer even between two Tier-1 branches — worth surfacing to whoever does this today before copying values across branches by habit.
- **The GBO-screen-to-BOX-screen mapping** (step 2) is assumed one-for-one; where it isn't has never been written down (see `branch-config-surface.md` §4).
- **What the PRE test (step 7) actually checks** is currently tribal knowledge — not written down anywhere in this repo yet.

## Known failure modes today

Not yet documented — nobody has been asked "what goes wrong, and how often." Worth a direct question to whoever runs this process rather than assuming there are none.
