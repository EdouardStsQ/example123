# Source Repository Index

The BOX/GBO-adjacent repositories this project has actually looked at, and what each one is evidence for. Repo names are scattered across several docs already — this is the one place to check what a repo is *for* without hunting.

Scope: repos that produced evidence in this project (Devin's own code, or this repo's `agents/`/`skills/`, aren't listed — this is source-of-truth systems, not tooling), plus — as of the section below — infrastructure/deployment repos the team will actually operate as part of doing the onboarding. Different kind of repo, kept separate, not evidence for a BOX-config doc.

## Mined for real evidence

| Repo | Purpose | Tier | Evidence for | Status |
|---|---|---|---|---|
| `cib-boxacc-dbboxacc` | BOX_ACC module — committed PL/SQL + DDL | **Both** *(inferred — BOX_ACC is a core module, not branch-specific; `system-overview.md` states BOX itself is installed in both Tier 1 and Tier 2. Not independently confirmed at the repo level.)* | `branch-config-surface.md` (branch config surface, deterministically reverse-engineered), `system-overview.md`'s module table | `[confirmed: repo]` |
| `cib-boxfin-dbboxfe` | BOX_FE module — committed PL/SQL/DDL, GOM metadata, runtime code | **Both** *(same inference as above)* | `fe-branch-configuration.md`, `branch-config-surface.md`, `system-overview.md`'s module table | `[confirmed: repo]` |
| `cib-auki-aukictrlmcntrm` | Control-M orchestration ("control room") for AUKI BO — `diaria.json` job definitions per process/country | **Both — confirmed.** Observed `country_code_vr` values: `ES`, `LB` (Tier 1: Madrid, London) and `MX`, `BR` (Tier 2: Mexico, Brazil). **No `US` value has been observed yet** — see open question below. | `control-m-batch-layer.md` (reverse-engineered 2026-08-24) | `[confirmed: repo]` |

## The FE/ACC batch repos — now doc-evidenced `[upgraded 2026-09-16]`

Five repos came up in a conversation with a BOX Developer (relayed by Edouard, corroborated by Devin's screenshot analysis) clarifying that BOX_FE/BOX_ACC batch jobs are Oracle DB jobs distinct from the Data-Lake bucket jobs `cib-auki-aukictrlmcntrm` covers above.

**These are no longer provisional.** `job-chains/box-fe-acc-batch-runtime.md` has landed and reads all five directly, tagged `[confirmed: repository configuration]`. The purposes below were written from the BOX Developer conversation and **survive contact with the repository evidence** — nothing in that doc contradicts them, and it adds structure the conversation didn't carry:

- Jobs are declared as `Job:Script`, under subapplication **`FINANCIAL_ENGINE`** (the three `boxfin` repos) or **`ACCOUNTING`** (the two `boxacc` repos).
- Their configuration names a script under **`/appl/gm/scripts`** with `%%$ODATE` as the process-date argument. **None of the five repos contains that path** — the wrapper implementation itself lives somewhere not yet identified. That is now the single most useful open question about this repo family.
- The live FE database changelog reaches release line **`r0.0.46`**.

| Repo | Purpose `[confirmed: repository configuration via box-fe-acc-batch-runtime.md]` | Tier |
|---|---|---|
| `cib-boxfin-t1mdesfe` | Core FE job topology — the per-book D01–D06 pattern (create process queues by book → calculate raw-flow dates/import → update current values → load/process MTM → insert product-specific deal data → execute financial process) | Tier 1 (Madrid) *(inferred)* |
| `cib-boxfin-t1mdalmfields` | ALM update jobs — a separate post-processing layer after the D01–D06 topology above | Tier 1 (Madrid) *(inferred)* |
| `cib-boxfin-mdfinancialcheck` | FE completion/checkpoint barrier — `RunAsDummy`, waits on D06-OK events. Not a calculation itself; it's the signal that FE finished | Tier 1 (Madrid) *(inferred)* |
| `cib-boxacc-t1mdesac` | Main ACC job topology — initial accounting, portfolio-properties/reclass/reval init, product/book accounting, MTM, revaluation, MBJ ruler-group updates | Tier 1 (Madrid) *(inferred)* |
| `cib-boxacc-t1mdacccheck` | ACC completion/checkpoint layer, mirroring `cib-boxfin-mdfinancialcheck`'s role for FE | Tier 1 (Madrid) *(inferred)* |

Tier here is inferred, not confirmed: four of the five names contain `t1md` (read as "Tier 1 Madrid"); the fifth (`cib-boxfin-mdfinancialcheck`) carries `md` without the explicit `t1` but follows the same family. This lines up with the BOX Developer conversation itself being specifically about Madrid. Nobody has asked whether Tier 2 equivalents exist.

`cib-boxfin-mdfinancialcheck` and `cib-boxacc-t1mdacccheck` were flagged here as "very likely the two ends of the FE→ACC completion-event contract." **Confirmed.** `job-chains/box-fe-acc-batch-runtime.md` §4 records that FE completion events are declared dependencies of the accounting jobs, making FE and ACC **separate Oracle batch layers joined through Control-M events** rather than one continuous chain. Both check repos use `RunAsDummy`-style jobs purely as aggregate barriers — they are dependency/control points, not calculations.

## Open question: do these FE/ACC batch repos have Tier 2 equivalents at all?

All five repos in the table above are Tier 1 (Madrid) by inference, and none has a confirmed Tier 2 counterpart. This is a different and more basic blocker than "Tier 2 DB access is pending" (the blocker tracked everywhere else in this repo): it's not yet established that a Tier 2 version of this FE/ACC batch-job layer has even been *identified*, let alone accessed. If it turns out Tier 2 runs the same repos under different environment config, that's one thing; if it turns out there's a wholly separate, not-yet-named repo family for Tier 2's FE/ACC batch topology, `branch-config-agent` has a repo-discovery step to do before its batch-topology work (as opposed to its config-mining work, which is a DB question) can even start. Not yet asked of the BOX Developer or anyone else — worth adding to `docs/examples/ny-sch-branch-onboarding.md`'s open questions.

## Configuration-as-code repos

Repos holding **BOX configuration** as versioned SQL, rather than application code. Different from the
infrastructure repos below (which hold environment/credential config) and from the source repos above
(which were mined as evidence) — these are repos the team *writes to* as part of doing configuration
work.

| Repo | Purpose | Notes |
|---|---|---|
| `cib-box-cntdblite` | Every cross-reference mapping created or modified in SIGOM **must also be committed here** as a SQL script, under `src/main/resources/dml/01-BOX_SYS/r<version>/05_Static-Data/`, named `NNN_data_lite_t_box_cross_ref_s.sql`. The `r<version>` folders match the `r0.0.x` release references already cited throughout [acc-add-product-checklist](../process/checklists/acc-add-product-checklist.md) §4 | `[stated: team page, 2026-09-16]` — not yet opened or read by this project. See [tables/t-box-cross-ref-s.md](tables/t-box-cross-ref-s.md) |

**Worth reading before the FE run.** This repo is the closest thing found so far to a worked example of
*how BOX configuration is actually written, versioned and promoted* — the exact question
`sigom-box-fe-configs-agent` has to answer before it can emit anything runnable. Its DML conventions
(hand-assigned PKs, idempotent delete-then-insert, release-numbered folders) are a template the agent's
output could plausibly have to match. `[open-question]` — whether `BOX_FE` config follows the same
convention in the same or a sibling repo is unknown, and is a better first question than it looks.

## Infrastructure / deployment repos

Different kind of repo entirely — not mined for BOX facts, but a real tool the team will operate as part of doing the onboarding.

**⚠️ Terminology collision, read before anything else in this section:** this repo's environment folders — `certification/`, `preproduction/`, `production/` — are **deployment/SDLC stages**. They are not this project's Tier 1 (Madrid) / Tier 2 (US) data-center split, used everywhere else in this document. Don't conflate them: a change can need to move through all three deployment stages while being entirely about a Tier 2 branch, or vice versa.

| Repo | Purpose | Notes |
|---|---|---|
| **`cib-box-aukinbranch`** `[confirmed: repo, 2026-09-14]` (name previously unrecorded) — the bank-provided Ansible inventory + Vault template for CIB Box environments; Edouard was given this repo to work in for NY_SCH onboarding | Created from GitHub's "Empty Ansible Inventory" template. Ansible inventory bundled with a Variable Substitution System (VSS): per-environment host inventory and non-sensitive `group_vars/all.yml`, with sensitive values (credentials, connection strings) encrypted into `vault/sensitive_data.yml` via Ansible Vault. A manually-dispatched GitHub Action (`encrypt-decrypt-workflow.yml`) does the encrypt/decrypt; `update-component-workflow.yml` is intentionally a no-op ("this component is not updatable"). All changes owned via CODEOWNERS (`@santander-group-scib-gln/gr_almnxtgn_cib_box_tl`); `production/` is meant to require reviewers. `encrypt` cannot run on `main`. Top level currently holds `.github/`, `certification/`, `preproduction/`, `production/`, `README.md` — a clean template instantiation, nothing branch-specific added yet. | `[stated: Devin's repo summary]` for the internals; repo name and top-level structure `[confirmed: repo, 2026-09-14]` |

**Explicit boundary — this is not where the automation/docs repo goes.** Someone asked why `cib-box-aukinbranch` was created from this template and whether it's right for "what we will build" — the answer is that this repo and the docs/agents/skills/runs automation scaffold are two structurally unrelated things, and neither belongs inside the other. An Ansible Inventory template holds infrastructure hosts, groups and (vault-encrypted) variables per deployment stage; it has no place for a `docs/reference/` wiki, `AGENT.md` charters, or `runs/` evidence folders, and pasting them in would not fit the template's structure at all. If `cib-box-aukinbranch` does turn out to be the Tier 2 credential provisioning mechanism (see below), its role in this project is as an **infrastructure dependency the orchestrator's Phase 0 gate waits on** — not as a home for anything this repo produces.

**Most likely role in this project — a lead, still not a confirmed fact:** this is plausibly the actual provisioning mechanism for **Tier 2 DB access**, the single most-cited blocker across this repo (`docs/examples/ny-sch-branch-onboarding.md` open question 1, and everywhere the "blocked on Tier 2 access" caveat appears). A Tier 2 connection credential is exactly the shape of thing that would live vault-encrypted here, per environment stage. Worth confirming directly rather than assumed — now that the repo is identified and accessible, this is answerable directly rather than inferred.

**Open questions, now that the repo is identified:**

1. ~~This repo's actual name/slug — not yet recorded.~~ **Resolved:** `cib-box-aukinbranch`.
2. Does `update-component-workflow.yml`'s "component" mean NY_SCH specifically, or is this a generic per-BOX-component template being reused for this onboarding? The structure shown (`group_vars/all.yml` holding only explanatory comments) reads as an empty template instantiation — confirm whether anything is already filled in for NY_SCH before assuming it's a blank slate.
3. Does this repo (or its generated `vault/sensitive_data.yml`) already reference Tier 2 connection details anywhere, or is Tier 2 DB access provisioned through a separate, unrelated process? This is the single highest-value question to answer here, and the repo is now open and accessible to answer it directly — check inside `certification/`, `preproduction/` and `production/` for host inventory and `group_vars/all.yml` content before assuming Tier 2 detail is present or absent.
4. Confirm the working assumption that BOX's own business config (GL accounts, SIGOM tabs — what `branch-config-agent` proposes) never goes through this repo. Current read: no, this is infra/credentials only, BOX config stays inside BOX's own configuration surface — but that's inferred from a structural summary, not confirmed.

## Keeping this current

Same discipline as `../topic-index.md`: when a new repo is named anywhere in this project, add a row here (draft it, don't just leave it buried in a table cell of whatever doc happened to mention it first) — a person confirms the purpose line before it's treated as settled, same propose-and-flag rule as everything else.
