# Source Repository Index

The BOX/GBO-adjacent repositories this project has actually looked at, and what each one is evidence for. Repo names are scattered across several docs already — this is the one place to check what a repo is *for* without hunting.

Scope: repos that produced evidence in this project (Devin's own code, or this repo's `agents/`/`skills/`, aren't listed — this is source-of-truth systems, not tooling), plus — as of the section below — infrastructure/deployment repos the team will actually operate as part of doing the onboarding. Different kind of repo, kept separate, not evidence for a BOX-config doc.

## Mined for real evidence

| Repo | Purpose | Tier | Evidence for | Status |
|---|---|---|---|---|
| `cib-boxacc-dbboxacc` | BOX_ACC module — committed PL/SQL + DDL | **Both** *(inferred — BOX_ACC is a core module, not branch-specific; `system-overview.md` states BOX itself is installed in both Tier 1 and Tier 2. Not independently confirmed at the repo level.)* | `branch-config-surface.md` (branch config surface, deterministically reverse-engineered), `system-overview.md`'s module table | `[confirmed: repo]` |
| `cib-boxfin-dbboxfe` | BOX_FE module — committed PL/SQL/DDL, GOM metadata, runtime code | **Both** *(same inference as above)* | `fe-branch-configuration.md`, `branch-config-surface.md`, `system-overview.md`'s module table | `[confirmed: repo]` |
| `cib-auki-aukictrlmcntrm` | Control-M orchestration ("control room") for AUKI BO — `diaria.json` job definitions per process/country | **Both — confirmed.** Observed `country_code_vr` values: `ES`, `LB` (Tier 1: Madrid, London) and `MX`, `BR` (Tier 2: Mexico, Brazil). **No `US` value has been observed yet** — see open question below. | `control-m-batch-layer.md` (reverse-engineered 2026-08-24) | `[confirmed: repo]` |

## Named, not yet imported into a doc

Five repos came up in a conversation with a BOX Developer (relayed by Edouard, corroborated by Devin's screenshot analysis) clarifying that BOX_FE/BOX_ACC batch jobs are Oracle DB jobs distinct from the Data-Lake bucket jobs `cib-auki-aukictrlmcntrm` covers above. The per-repo purposes below come from that conversation, not from a doc — tag them accordingly, and treat every line here as provisional until `box-fe-acc-batch-runtime.md` (pending, see `job-chains/README.md`) actually imports and supersedes it.

| Repo | Purpose (from BOX Developer conversation, `[stated: BOX Developer, not yet doc-evidenced]`) | Tier |
|---|---|---|
| `cib-boxfin-t1mdesfe` | Core FE job topology — the per-book D01–D06 pattern (create process queues by book → calculate raw-flow dates/import → update current values → load/process MTM → insert product-specific deal data → execute financial process) | Tier 1 (Madrid) *(inferred)* |
| `cib-boxfin-t1mdalmfields` | ALM update jobs — a separate post-processing layer after the D01–D06 topology above | Tier 1 (Madrid) *(inferred)* |
| `cib-boxfin-mdfinancialcheck` | FE completion/checkpoint barrier — `RunAsDummy`, waits on D06-OK events. Not a calculation itself; it's the signal that FE finished | Tier 1 (Madrid) *(inferred)* |
| `cib-boxacc-t1mdesac` | Main ACC job topology — initial accounting, portfolio-properties/reclass/reval init, product/book accounting, MTM, revaluation, MBJ ruler-group updates | Tier 1 (Madrid) *(inferred)* |
| `cib-boxacc-t1mdacccheck` | ACC completion/checkpoint layer, mirroring `cib-boxfin-mdfinancialcheck`'s role for FE | Tier 1 (Madrid) *(inferred)* |

Tier here is inferred, not confirmed: four of the five names contain `t1md` (read as "Tier 1 Madrid"); the fifth (`cib-boxfin-mdfinancialcheck`) carries `md` without the explicit `t1` but follows the same family. This lines up with the BOX Developer conversation itself being specifically about Madrid. Nobody has asked whether Tier 2 equivalents exist.

`cib-boxfin-mdfinancialcheck` and `cib-boxacc-t1mdacccheck` are very likely the two ends of the FE→ACC completion-event contract flagged as unbuilt in `branch-config/agent-architecture.md` — worth checking first once `box-fe-acc-batch-runtime.md` lands.

## Open question: do these FE/ACC batch repos have Tier 2 equivalents at all?

All five repos in the table above are Tier 1 (Madrid) by inference, and none has a confirmed Tier 2 counterpart. This is a different and more basic blocker than "Tier 2 DB access is pending" (the blocker tracked everywhere else in this repo): it's not yet established that a Tier 2 version of this FE/ACC batch-job layer has even been *identified*, let alone accessed. If it turns out Tier 2 runs the same repos under different environment config, that's one thing; if it turns out there's a wholly separate, not-yet-named repo family for Tier 2's FE/ACC batch topology, `branch-config-agent` has a repo-discovery step to do before its batch-topology work (as opposed to its config-mining work, which is a DB question) can even start. Not yet asked of the BOX Developer or anyone else — worth adding to `docs/examples/ny-sch-branch-onboarding.md`'s open questions.

## Infrastructure / deployment repos

Different kind of repo entirely — not mined for BOX facts, but a real tool the team will operate as part of doing the onboarding.

**⚠️ Terminology collision, read before anything else in this section:** this repo's environment folders — `certification/`, `preproduction/`, `production/` — are **deployment/SDLC stages**. They are not this project's Tier 1 (Madrid) / Tier 2 (US) data-center split, used everywhere else in this document. Don't conflate them: a change can need to move through all three deployment stages while being entirely about a Tier 2 branch, or vice versa.

| Repo | Purpose | Notes |
|---|---|---|
| *(name not yet recorded — the bank-provided Ansible inventory + Vault template for CIB Box environments; Edouard was given this repo to work in for NY_SCH onboarding)* | Ansible inventory template bundled with a Variable Substitution System (VSS): per-environment host inventory and non-sensitive `group_vars/all.yml`, with sensitive values (credentials, connection strings) encrypted into `vault/sensitive_data.yml` via Ansible Vault. A manually-dispatched GitHub Action (`encrypt-decrypt-workflow.yml`) does the encrypt/decrypt; `update-component-workflow.yml` is intentionally a no-op ("this component is not updatable"). All changes owned via CODEOWNERS (`@santander-group-scib-gln/gr_almnxtgn_cib_box_tl`); `production/` is meant to require reviewers. `encrypt` cannot run on `main`. | `[stated: Devin's repo summary, not independently verified]` |

**Most likely role in this project — a lead, not a confirmed fact:** this is plausibly the actual provisioning mechanism for **Tier 2 DB access**, the single most-cited blocker across this repo (`docs/examples/ny-sch-branch-onboarding.md` open question 1, and everywhere the "blocked on Tier 2 access" caveat appears). A Tier 2 connection credential is exactly the shape of thing that would live vault-encrypted here, per environment stage. Worth confirming directly rather than assumed.

**Open questions before this section can be written up with confidence:**

1. This repo's actual name/slug — not yet recorded.
2. Does `update-component-workflow.yml`'s "component" mean NY_SCH specifically, or is this a generic per-BOX-component template being reused for this onboarding? The structure shown (`group_vars/all.yml` holding only explanatory comments) reads as an empty template instantiation — confirm whether anything is already filled in for NY_SCH before assuming it's a blank slate.
3. Does this repo (or its generated `vault/sensitive_data.yml`) already reference Tier 2 connection details anywhere, or is Tier 2 DB access provisioned through a separate, unrelated process? This is the single highest-value question to answer here.
4. Confirm the working assumption that BOX's own business config (GL accounts, SIGOM tabs — what `branch-config-agent` proposes) never goes through this repo. Current read: no, this is infra/credentials only, BOX config stays inside BOX's own configuration surface — but that's inferred from a structural summary, not confirmed.

## Keeping this current

Same discipline as `../topic-index.md`: when a new repo is named anywhere in this project, add a row here (draft it, don't just leave it buried in a table cell of whatever doc happened to mention it first) — a person confirms the purpose line before it's treated as settled, same propose-and-flag rule as everything else.
