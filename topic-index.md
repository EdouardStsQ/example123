# Topic Index — Branch Onboarding

A second index alongside `README.md` (which organizes by document *kind*): this one organizes by **which BOX subsystem a doc informs**, cutting across `reference/`, `reference/branch-config/`, `process/checklists/` and `reference/job-chains/`. Use it when the question is "which docs do I need to understand X," not "where does a new doc go."

This taxonomy is a first draft, not a governed standard — the categories are mine, proposed while reviewing the imported docs, and should be treated as provisional until an SME pushes back on them.

## The categories

| Code | Category | What it covers |
|---|---|---|
| Gate | Branch master & product scope | GBO branch identity, existing-vs-new branch group, explicit SME-owned product scope — the prerequisites nothing else can start without |
| Online | Online arrival (CROSS_REF) | Real-time API path: Murex → TIBCO EMS → Camunda → BOX_TRD, `T_BOX_CROSS_REF_S` value translation |
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
| `reference/repo-index.md` | *(cross-reference — no primary)* | FE, ACC, DataLake |
| `process/checklists/acc-add-product-checklist.md` | ACC *(product axis)* | Instr, FE |
| `reference/branch-config/branch-config-madrid-london-diff.md` | ACC | Gate |
| `process/checklists/branch-onboarding-checklist.md` | **All** — the master checklist | — |
| `reference/branch-config/accounting-resolution-chain.md` | Accept | ACC, Instr |
| `reference/job-chains/control-m-batch-layer.md` | DataLake | Gate |
| `reference/branch-config/branch-config-surface.md` | ACC | Gate |
| `reference/branch-config/branch-trading-readiness.md` | Accept | Gate, Online, FE, ACC, Instr |
| `reference/branch-config/fe-branch-configuration.md` | FE | Gate, DataLake |
| `reference/fe-raw-data-stage.md` | DataLake | FE |

## Known gap

**Online (CROSS_REF) has no document written for it** — only an architectural mention (`system-overview.md`) and a flagged evidence gap (`branch-trading-readiness.md` §2). Every other category has at least one doc that plays the "deep-dive" role `branch-config-surface.md` plays for ACC or `control-m-batch-layer.md` plays for DataLake; Online doesn't yet. If you're deciding what to research next, this is it. The role that would own it already has a name, though — `branch-trading-readiness.md` names `branch-trd-agent` alongside `branch-onboarding-orchestrator` — so use that name rather than coining a new one when this gap gets filled.

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
