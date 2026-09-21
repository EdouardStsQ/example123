# Topic Index — Branch Onboarding

A second index alongside `README.md` (which organizes by document *kind*): this one organizes by **which BOX subsystem a doc informs**, cutting across `reference/`, `reference/branch-config/`, `process/checklists/` and `reference/job-chains/`. Use it when the question is "which docs do I need to understand X," not "where does a new doc go."

This taxonomy is a first draft, not a governed standard — the categories are mine, proposed while reviewing the imported docs, and should be treated as provisional until an SME pushes back on them.

## The categories

| Code | Category | What it covers |
|---|---|---|
| Gate | Branch master & product scope | GBO branch identity, existing-vs-new branch group, explicit SME-owned product scope — the prerequisites nothing else can start without |
| Online | Online arrival (CROSS_REF) | Real-time API path: Murex → TIBCO EMS → Camunda → BOX_TRD. ⚠️ **The `T_BOX_CROSS_REF_S` half of this category name is now questionable** — the team's own page documents that table as translating **Integrity Check** values into GBO Static-Data equivalents, which is a reconciliation concern, not obviously this path. See [`reference/tables/t-box-cross-ref-s.md`](reference/tables/t-box-cross-ref-s.md); the category is left as-is pending evidence of what actually reads the table |
| DataLake | Data Lake mapping | Overnight batch path: Control-M `diaria.json` → Airflow → Data Lake → BOX RAW tables |
| FE | BOX FE configs | GBO→BOX_FE bridge, the eight SIGOM config tabs, fixing curves/QR FX |
| ACC | BOX ACC configs | Portfolio properties, topic→GLTA mapping, GL accounts, net-contract/cross-account config |
| Instr | Instruments | Instrument-type resolution (configured vs. fallback), per-product instrument identity |
| Accept | Acceptance / validation | The full resolution trace used as the acceptance test once a branch is built |

## Doc → category map

| Document | Primary | Also touches |
|---|---|---|
| `reference/system-overview.md` | Online, DataLake | Gate, FE, ACC |
| `reference/box-data-model.md` | *(cross-reference — no primary)* | FE, ACC, Instr |
| `reference/sigom-metamodel.md` | *(cross-reference — no primary)* — **how to ask SIGOM what it declares** rather than inferring it: object↔table catalogue, the field type system, identity columns, pre-commit procedures. Applies to any SIGOM-managed schema, so it is not FE-specific | FE, ACC, Instr, Gate |
| `reference/confirmed-joins.md` | *(cross-reference — no primary)* — the confirmed relationships the metamodel does **not** declare: cross-environment rules, branch identity, PK allocation, known-broken | FE, ACC, Instr |
| `reference/repo-index.md` | *(cross-reference — no primary)* | FE, ACC, DataLake |
| `process/checklists/acc-add-product-checklist.md` | ACC *(product axis)* | Instr, FE |
| `reference/branch-config/branch-config-madrid-london-diff.md` | ACC | Gate |
| `process/checklists/branch-onboarding-checklist.md` | **All** — the master checklist | — |
| `reference/branch-config/accounting-resolution-chain.md` | Accept | ACC, Instr |
| `reference/job-chains/control-m-batch-layer.md` | DataLake | Gate |
| `process/04-add-book-procedure.md` | DataLake *(Part 1)*, FE + ACC *(Part 2)* — **the Book axis**, cutting across categories the way the master checklist does | Instr |
| `reference/tables/t-box-cross-ref-s.md` | Instr — IC↔GBO instrument, direction, flow-type and source translation | Online *(by association, now questioned — see the category note)*, Accept |
| `process/05-add-product-procedure.md` | Instr — **the Product axis**, end to end across BOX API, FE and ACC | FE, ACC, Gate *(instrument-type resolution)* |
| `reference/job-chains/box-fe-acc-batch-runtime.md` | FE + ACC — the **scheduler** layer: Control-M job families, the `T_BOX_MBJ_PROPERTIES_S` job→(branch, instrument, MBJ group) binding, and the FE→ACC handoff through Control-M events | DataLake *(picks up where the RAW load ends)*, Accept, Online *(one job carries `MIC_FLOW_MODE=On-Line` — an unexplained touchpoint)* |
| `reference/job-chains/fe-batch-event-groups.md` | FE — the **inside-Oracle** layer: nine event groups in order, with PKs and per-procedure execution order. Supplies the `group` values for the dispatcher signature recorded in the row above | DataLake, Accept |
| `reference/branch-config/branch-config-surface.md` | ACC | Gate |
| `reference/branch-config/branch-trading-readiness.md` | Accept | Gate, Online, FE, ACC, Instr |
| `reference/branch-config/fe-branch-configuration.md` | FE | Gate, DataLake |
| `reference/fe-raw-data-stage.md` | DataLake | FE |

## Known gap

**Online (CROSS_REF) still has no document for the *arrival path*** — only an architectural mention (`system-overview.md`) and a flagged evidence gap (`branch-trading-readiness.md` §2). Every other category has at least one doc that plays the "deep-dive" role `branch-config-surface.md` plays for ACC or `control-m-batch-layer.md` plays for DataLake; Online doesn't yet. If you're deciding what to research next, this is it. The role that would own it already has a name, though — `branch-trading-readiness.md` names `branch-trd-agent` alongside `branch-onboarding-orchestrator` — so use that name rather than coining a new one when this gap gets filled.

**Partial update, 2026-09-16:** [`reference/tables/t-box-cross-ref-s.md`](reference/tables/t-box-cross-ref-s.md) is now a full deep-dive of `T_BOX_CROSS_REF_S` — the table this category is half-named after. It does **not** close the gap above, and may in fact widen it: the table's documented purpose is Integrity-Check → GBO Static-Data translation, so the real-time Murex → TIBCO → Camunda → BOX_TRD path is *still* undocumented **and** its assumed link to this table is now itself unproven. Two questions to research, where the list previously implied one.

## Keeping this current

**Don't auto-classify silently.** When a new doc lands:

1. **Cheap first pass (mechanical, no judgment needed):** scan the doc for the markers below. They're strong signals, not proof — a doc can legitimately touch a category without containing its marker.

   | Category | Markers to grep for |
   |---|---|
   | Gate | `T_PGT_BRANCH_S`, `FK_LOCALGROUP`, "product scope", "SME" |
   | Online | `T_BOX_CROSS_REF_S`, "Kafka", "TIBCO", "online", "real-time" |
   | DataLake | `diaria.json`, "Control-M", "Airflow", `T_BOX_RAW_`, "Data Lake" |
   | FE | `T_BOX_ENGCONF_S`, `T_BOX_ENGCONF_X`, `T_BOX_CONF_BY_BOOK_S`, "SIGOM", "financial engine" |
   | ACC | `T_BOX_ACCT_`, `T_BOX_CROSS_ACCTCONF_S`, `T_BOX_NETCONTRACT_S`, "GLTA", "accounting" |
   | Instr | `T_BOX_CONF_INSTRUM_TYPE_S`, `T_PGT_INSTRUMENT_S`, "instrument type" |
   | Accept | "reconciliation", "acceptance", "FINANCST", "posted movement" |

2. **Draft a row** (primary/also-touches + one-line why) from that scan.
3. **A person confirms or corrects it** before it's added above — same propose-and-flag discipline as everything else in this repo. Never merge a draft row unreviewed.

Once this has been done by hand a few dozen times and the marker table has proven itself, it's a good candidate for an actual skill (`classify-doc-into-topic-index`) that does step 1 automatically and opens step 2 as a proposal. Not worth building before then.
