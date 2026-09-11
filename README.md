# Docs — Index & Filing Rules

`docs/` splits by **what kind of document it is**, not by topic. Topics are unbounded (you'll always find a new one); document kinds are not — there are only a handful of them, and you can name them all today.

Looking for "which doc explains BOX FE / BOX ACC / instrument resolution / etc." rather than "what kind of document is this"? See `topic-index.md` — a second, cross-cutting index by BOX subsystem.

## The four kinds

| Folder | What goes here | Style |
|---|---|---|
| `process/` | What onboarding *should* do, in general — the current and target flows | Narrative, prescriptive |
| `reference/` | Facts you look something up in — DB tables, queries, API specs, field glossaries, system orientation | Kept literally correct; register varies — most of it is dense and evidence-tagged (`[confirmed: DB]` etc.), but an orientation doc like `system-overview.md` is narrative on purpose, because its job is a good first read, not a lookup. Don't strip narrative out of a doc just because it lives here. |
| `examples/` | A specific, real job sequence, worked end to end — "here's what actually happened for one run" | Concrete, illustrative, not prescriptive |
| `decisions/` | Why we chose X over Y | Short ADRs |

If a new document doesn't obviously fit one of the four, put it in `reference/` and add a line to **Needs reclassification** below. Don't block on getting the taxonomy perfect before filing something.

## Growing a folder

Keep files flat inside each folder until one flavor of document has piled up. Once `reference/` (or any folder) has 3+ files that are clearly the same sub-type — e.g. several DB-table write-ups, several reusable queries — give that sub-type its own subfolder. So far: `reference/queries/` (SQL + sample-results.csv pairs), `reference/tables/` (per-table deep-dives), `reference/job-chains/` (chain description + .xlsx pairs), `process/checklists/` (sign-off checklists). Note none of these needed a new top-level kind — they all fit inside the existing four, just as subfolders.

## Index

Keep this list current — with many docs, a flat table of contents beats a clever tree.

| Doc | Folder | One-liner |
|---|---|---|
| 00-overview.md | process | End-to-end onboarding flow, map of stages |
| 01-current-state.md | process | Manual onboarding as it happens today |
| 02-target-state.md | process | Automated flow, mapped to skills/agents |
| 03-fe-sigom-config-procedure.md | process | Step-by-step procedure `sigom-box-fe-configs-agent` follows to produce BOX FE config SQL (gates → provisioning → mining → review → SQL → apply). The agent's *rules* live in its AGENT.md; this is the *sequence* |
| checklists/branch-onboarding-checklist.md | process | **Master checklist** — what must exist/be checked to onboard a new branch (Infra → BOX_TRD → BOX_ACC → BOX_FE), tagged confirmed/inferred/open-question + automation class |
| checklists/acc-add-product-checklist.md | process | The product-axis equivalent (onboarding a new *product* like BRS, not a new branch) |
| system-overview.md | reference | What BOX is, its 5 stages, Tier 1 (Madrid/London) vs Tier 2 (US/Brazil/Mexico) |
| box-data-model.md | reference | Full BOX schema reference — modules, table prefixes, FK glossary |
| repo-index.md | reference | Which source repos we've actually looked at, and what each is evidence for |
| box-apis.md | reference | BOX/Camunda integration points (skeleton — not yet filled in) |
| fe-raw-data-stage.md | reference | Data-Lake → BOX RAW tables → FE processing (Deal/Flow/Market payloads) |
| tables/*.md | reference | Per-table deep-dives (columns, relationships, gotchas) — none written yet; candidates live inline in `branch-config/branch-config-surface.md` §2 |
| branch-config/*.md | reference | How a branch's config resolves across BOX_TRD/FE/ACC — see `branch-config/README.md` |
| branch-config/agent-architecture.md | reference | The onboarding workflow (Build vs. Validate) and the agents that run it — see `agents/`. Carries corrections: the agent roster has changed twice, and one overlap decision is still open |
| queries/list-entity-static-data.sql (+ .sample-results.csv) | reference | Check whether BOX already has a record for entity_id |
| queries/check-chart-of-accounts-mapping.sql (+ .sample-results.csv) | reference | List CoA mappings configured for an entity |
| queries/fe-config-mining.md | reference | **Query catalogue** — the exact parameterised queries `sigom-box-fe-configs-agent` runs, by ID, with target database, expected results and output CSV filenames |
| job-chains/control-m-batch-layer.md | reference | How the Control-M/Data-Lake batch layer works, and how to expand it for a new branch |
| job-chains/box-fe-acc-batch-runtime.md | reference | *(pending — not yet imported)* BOX_FE/BOX_ACC internal Oracle DB batch job topology — see `job-chains/README.md` |
| ny-sch-branch-onboarding.md | examples | Live case: onboarding NY_SCH (Tier 2) — status, open questions, phased plan |
| 0000-template.md | decisions | ADR template |
| topic-index.md | *(cross-cutting, not one kind)* | Docs indexed by BOX subsystem (Gate/Online/DataLake/FE/ACC/Instr/Accept), not by kind — see the file itself |

## Needs reclassification

Docs filed in `reference/` by default that haven't been sorted into a proper kind yet:

- (none yet)

## Cross-references from the imported BOX docs

The documents imported from Devin's wiki cite each other by name using `[[wikilink]]` syntax. Where a cited name matches a doc we actually imported into this repo, it's now a real relative markdown link. Where it doesn't (it names a doc that lives only in the other wiki — e.g. `` `box-database-reference` ``, `` `box-acc-universal-engine` ``), it's left as plain backticked text rather than a clickable link: it's still useful as a citation of where a finding came from, but there's nothing to click through to here. Don't recreate these as empty placeholder files — if one of them becomes genuinely needed, import the real doc from the source wiki rather than stubbing it out.
