# Table: `BOX_SYS.T_BOX_CROSS_REF_S`

**SIGOM screen:** `BOX \ Config \ Cross Reference`

The first real per-table deep-dive in this folder — see [`README.md`](README.md) for the convention.

**Evidence:** an internal Confluence page describing the screen, its five mapping types, worked
examples from existing configurations, and the script convention `[stated: team page, imported
2026-09-16]`, plus the column list, which is `[confirmed: DML]` because the page includes a real
script. Where this contradicts or reframes something already in the repo, that is called out rather
than silently merged — see *What this changes* at the end.

## Purpose

A generic **value-translation table**: it pre-configures mappings between systems, translating codes
from one system's vocabulary into another's. The documented use is translating values from the
**Integrity Check (IC)** domain into their **GBO Static-Data** equivalents. Hence "Cross Reference" —
it cross-references codes from one system to another.

It is a *dictionary*, not branch or deal data. There is no `FK_BRANCH` column
(`[confirmed: Tier 1 schema]`, recorded in
[branch-trading-readiness](../branch-config/branch-trading-readiness.md) §1), so a mapping applies
system-wide, optionally narrowed by instrument.

## Columns `[confirmed: DML]`

Read directly off a real insert script, so these are actual column names, not inferred:

| Column | Screen field | Meaning |
|---|---|---|
| `PK` | — | Primary key. Hand-assigned in the script — see *Gotchas* |
| `FK_OWNER_OBJ` | — | Owner object. Constant `35000187.65` across every row in the observed script |
| `DESCRIPTION` | Description | Short summary of the mapping's purpose |
| `MAP_TYPE` | Type | Functional type of the mapping — one of five values, below |
| `MAP_FROM` | Mapping → From | **Input** value: the original, e.g. an IC domain value |
| `MAP_TO` | Mapping → To | **Output** value: the target, e.g. a GBO Static-Data domain value |
| `MAP_TO_TYPE` | Mapping → Type | Type of the target value. Typically `Code` |
| `FK_INSTRUMENT_FILTER` | Filters → Instrument | Narrows the mapping to one instrument. Mandatory for two map types, null for the other three |

## The five mapping types

`MAP_TYPE` drives everything: which catalogue `MAP_FROM` is drawn from, which SIGOM node supplies
`MAP_TO`, and whether the instrument filter applies.

| `MAP_TYPE` | `MAP_FROM` source | `MAP_TO` source (SIGOM node) | `MAP_TO_TYPE` | Instrument filter |
|---|---|---|---|---|
| `Instrument` | IC Instrument codes, *Integrity Check - Financial Instruments* catalogue | `GBO \ Documentation \ Reports \ Instrument Viewer` | `Code` | **Not applicable** (null) |
| `Direction` | IC *Flow Mappings*, field `direction` | `GBO \ SYS \ Selectors \ Trading \ General \ Direction` | `Code` | **Mandatory** |
| `Direction - Leg` | IC *Leg Mappings*, field `direction` | `GBO \ SYS \ Selectors \ Trading \ General \ Direction` | `Code` | **Mandatory** |
| `Flow Type` | IC *Flow Mappings*, field `type` | `GBO \ SYS \ Selectors \ Trading \ Cash` | `Code` | Not applicable |
| `Source` | IC *Source Systems*, field `IC Source System Name` | `GBO \ SYS \ Source Systems \ Sources` | `Code` | Not applicable |

`Direction` and `Direction - Leg` target the **same** GBO node but draw from **different** IC
catalogues (Flow Mappings vs Leg Mappings) with different source vocabularies — see below. Don't
collapse them.

### `Instrument` — IC code → GBO instrument code

| Description | From (IC) | To (GBO) |
|---|---|---|
| Deposit | `DEPOSIT` | `DEPOSIT` |
| Interest Rate Swap | `IRS` | `SWAP` |
| Cross Currency Swap | `CCS` | `CCS` |
| OTC Option | `FXOPT` | `OTC OPTION` |
| Swaption | `SWAPTION` | `OTC OPTION` |
| Cap/Floor | `CAPFLOOR` | `Cap/Floor` |
| Credit Derivatives | `CDS` | `Credit` |
| Forward Rate Agreement | `FRA` | `FRA` |
| Commodity | `COMMODITY` | `COMM_SWAP` |

**The mapping is not one-to-one.** `FXOPT` and `SWAPTION` both map to `OTC OPTION` — two IC
instruments collapsing into one GBO instrument. Any logic that assumes a reversible instrument
mapping is wrong in at least this case.

**`IRS → SWAP` corroborates an existing record.**
[acc-add-product-checklist](../../process/checklists/acc-add-product-checklist.md) already lists the
"Sigom instrument label" for IRS as `SWAP`, from a different source. Two independent records agreeing.

This is also a **third naming layer** on top of the two already documented. GBO's Financial Status
codes the same product `IR` and BOX FE codes it `IR`
([box-data-model](../box-data-model.md#financial-status-surfaces-gbo-vs-box-fe)), while IC calls it
`IRS` and the GBO instrument label is `SWAP`. Four vocabularies for one product; translate
deliberately rather than pattern-matching.

### `Direction` — cashflow direction

One pattern, stated to be **used by all instruments**:

| From (IC) | To (GBO) | Meaning |
|---|---|---|
| `RECEIVE` | `BOR` | Receive maps to Borrower |
| `PAY` | `LOA` | Pay maps to Loan |

Worked example given for instrument **OTC Option (`20111.4`)**.

### `Direction - Leg` — leg direction

Same GBO targets, different source vocabulary:

| From (IC) | To (GBO) |
|---|---|
| `SELL` | `BOR` |
| `BUY` | `LOA` |

Worked example also for OTC Option (`20111.4`). So a single instrument carries **both** a
`RECEIVE`/`PAY` pair and a `SELL`/`BUY` pair, both resolving into the same two GBO codes.

### `Flow Type` and `Source`

| `MAP_TYPE` | From (IC) | To (GBO) |
|---|---|---|
| `Flow Type` | `FEE` | `STA` |
| `Source` | `MUREX3-EUROPA` | `MUREX FXFI` |

The `Source` example is worth noting: `MUREX3-EUROPA` is the IC name for what the Control-M/Data-Lake
layer calls `Mx3EU` ([control-m-batch-layer](../job-chains/control-m-batch-layer.md) §2) and what GBO
calls `MUREX FXFI`. Three names for one source system, in three layers. `[inferred]` — the
correspondence is by meaning, not confirmed by a joint query.

## Relationships

- `FK_INSTRUMENT_FILTER` → a GBO instrument PK. Observed values: `20213.4` (CAPFLOOR), `20111.4` (OTC
  Option). These carry the `.4` suffix that instrument PKs elsewhere in the corpus also use
  (`20092.4` for IRS, per acc-add-product-checklist).
- `FK_OWNER_OBJ` → `35000187.65`, constant in the observed script. What object it points at is not
  stated. `[open-question]`
- No branch, entity or portfolio column. Mappings are global, optionally instrument-scoped.

## Creating rows

### Checklist for a new instrument

| `MAP_TYPE` | Instrument filter | Required? |
|---|---|---|
| `Instrument` | null | **Always** — 1 row |
| `Direction` | Mandatory | **Always** — 2 rows (`RECEIVE`, `PAY`) |
| `Direction - Leg` | Mandatory | **Always** — 2 rows (`SELL`, `BUY`) |
| `Flow Type` | null | No — only if a **new flow type** is introduced |
| `Source` | null | No — only if a **new source system** is introduced |

So **five rows minimum** per new instrument, and the two conditional types are about the
*vocabulary*, not the instrument: adding an instrument that uses only existing flow types and an
existing source system needs neither.

### Where they are created

Cross-reference mappings for **BOX-LITE** are created in the **BOX - DEV** SIGOM connection, database
`DGBOBOX`. Reaching that connection requires adding a `<add name="BOX_DEV" host="…">` entry to the
local `Sigom.config`. *(The hostname is deliberately not reproduced here — it is an environment
connection detail with no documentary value for this repo. It is on the source page.)*

`BOX-LITE` is a new term in this corpus. `PKG_BOX_DEAL_LITE_DATA_API` already appears in
[branch-onboarding-checklist](../../process/checklists/branch-onboarding-checklist.md) item 2.2, so
"LITE" is an established variant of something — but what BOX-LITE *is*, and whether these mappings
apply outside it, is not stated. `[open-question]`

### Persisting to the repository

Anything created or modified in SIGOM **must also be committed** as a SQL script to the repo
`cib-box-cntdblite`, under:

```text
src/main/resources/dml/01-BOX_SYS/r<version>/05_Static-Data/
```

with the filename convention `NNN_data_lite_t_box_cross_ref_s.sql`.

### Script pattern `[confirmed: DML]`

Abbreviated from the real example (adding `CAPFLOOR` mappings, release `r0.0.18`):

```sql
begin
    -- Instrument
    delete from BOX_SYS.T_BOX_CROSS_REF_S where PK in(113.65) and trunc(PK)=sign(PK)*(abs(PK)-.65);
    insert into BOX_SYS.T_BOX_CROSS_REF_S (PK,FK_OWNER_OBJ,DESCRIPTION,MAP_FROM,MAP_TO,MAP_TO_TYPE,MAP_TYPE)
    values (113.65,35000187.65,'CAPFLOOR','CAPFLOOR','Cap/Floor','Code','Instrument');

    -- Direction
    delete from BOX_SYS.T_BOX_CROSS_REF_S where PK in(114.65) and trunc(PK)=sign(PK)*(abs(PK)-.65);
    insert into BOX_SYS.T_BOX_CROSS_REF_S (PK,FK_OWNER_OBJ,DESCRIPTION,FK_INSTRUMENT_FILTER,MAP_FROM,MAP_TO,MAP_TO_TYPE,MAP_TYPE)
    values (114.65,35000187.65,'CAPFLOOR - Receive',20213.4,'RECEIVE','BOR','Code','Direction');

    -- Direction - Leg
    delete from BOX_SYS.T_BOX_CROSS_REF_S where PK in(117.65) and trunc(PK)=sign(PK)*(abs(PK)-.65);
    insert into BOX_SYS.T_BOX_CROSS_REF_S (PK,FK_OWNER_OBJ,DESCRIPTION,FK_INSTRUMENT_FILTER,MAP_FROM,MAP_TO,MAP_TO_TYPE,MAP_TYPE)
    values (117.65,35000187.65,'CAPFLOOR - Buy',20213.4,'BUY','LOA','Code','Direction - Leg');
end;
/
```

Note the `Instrument` insert omits `FK_INSTRUMENT_FILTER` from its column list entirely rather than
passing null — consistent with "not applicable" for that type.

## Gotchas

**PKs are hand-assigned literals.** `113.65`, `114.65`, `117.65` are written by whoever authors the
script — no sequence, no trigger, no default. This is a *different* mechanism from the one the
add-a-book runbook describes for MIS Book config ("export the book configuration file with dynamic
pk"), which means **BOX config does not have one uniform PK strategy**. Relevant to the FE walk's
gate 0d — see [fe-config-mining](../queries/fe-config-mining.md) Q-G3.

**The delete guard asserts the PK's fractional suffix.** Every statement is preceded by:

```sql
delete from … where PK in(<pk>) and trunc(PK)=sign(PK)*(abs(PK)-.65);
```

That predicate is only true when the fractional part of `PK` is exactly `.65` — for `113.65`,
`trunc` gives `113` and `1 * (113.65 - 0.65)` also gives `113`. It is a **defensive assertion that the
row being deleted belongs to the `.65` partition**, making the script idempotent (re-runnable) without
risking a row outside that partition.

This is the corpus's first concrete evidence that the unexplained `<integer>.<integer>` PK format is
**semantically meaningful and relied upon by code**, not cosmetic. Observed suffixes across the
corpus: `.4` (instruments, branches — `20092.4`, `20087.4`, `20007.4`), `.21` (Madrid-side config —
`22.21`, `132.21`), `.65` (BOX_SYS cross-ref rows, accounting events, batch event groups).

**Named, 2026-09-16: the suffix is an "authcode".** The team's add-a-product runbook
([`../../process/05-add-product-procedure.md`](../../process/05-add-product-procedure.md)) instructs
every SIGOM step to be performed *"on BOX-DEV environment (`.65` authcode)"*, and separately that
topics and conditions *"must be created in BOX as `.65`"*. So `.65` identifies **BOX-DEV**, and the
fractional part of a PK is an **authcode / environment-or-installation discriminator**, not an
arbitrary numeric convention. That is why the delete guard above can safely assert it: every row the
script owns lives in the same authcode space.

Two things this still does **not** settle, so don't over-read it. It doesn't follow that every `.65`
row is BOX-DEV-only — `.65` PKs appear in production-copy extracts elsewhere in this corpus (batch
event groups, accounting events), so the code more plausibly identifies an *installation or owning
system* that BOX-DEV happens to write into, than a throwaway dev marker. And it doesn't explain the
`.4`/`.21` split, where branches carry **both** (`22.21` Madrid, `20087.4` London) — if the suffix were
purely environmental those two would match. `[open-question]` — what `.4`, `.21` and `.65` each
designate, and whether a PK can be migrated across them.

**`Direction` and `Direction - Leg` are separate types with separate vocabularies.** `RECEIVE`/`PAY`
against `SELL`/`BUY`, both landing on `BOR`/`LOA`. Reading a `BOR` value back does not tell you which
type produced it.

**The instrument mapping is many-to-one** (`FXOPT`, `SWAPTION` → `OTC OPTION`). Not invertible.

## Used by

No query in [`../queries/`](../queries/) touches this table yet, and no skill exists for it. The FE
config walk (`sigom-box-fe-configs-agent`) does **not** cover it — this is `BOX_SYS`, outside that
agent's `BOX_FE` scope.

## What this changes elsewhere

**It reframes what CROSS_REF is for.** [topic-index](../../topic-index.md) names a whole category
"Online arrival (CROSS_REF)" and describes it as the real-time API path with "`T_BOX_CROSS_REF_S`
value translation". This page describes the table's documented purpose as translating **Integrity
Check** values into GBO Static-Data equivalents — a reconciliation/validation concern, not obviously
the real-time trade-arrival path. The two are not necessarily incompatible (one dictionary can serve
several consumers), but the repo's framing is at least incomplete. Qualified in `topic-index.md` and
[branch-trading-readiness](../branch-config/branch-trading-readiness.md) rather than rewritten, since
nothing here disproves an online consumer either. `[open-question]`

**It resolves the Pay/Receive → Loan/Borrower question.**
[fe-raw-data-stage](../fe-raw-data-stage.md) recorded that transformation as observed but unexplained
("the Pay/Receive-to-Loan/Borrower direction transformation remain[s] open"). It is **configured
here**, as `Direction` mappings, not hardcoded.

## Sources

Internal Confluence page on Cross Reference / instrument mapping configuration, imported 2026-09-16
`[stated: team page]`; column names and the script pattern `[confirmed: DML]` from the example script
it contains. Cross-referenced against
[branch-trading-readiness](../branch-config/branch-trading-readiness.md),
[fe-raw-data-stage](../fe-raw-data-stage.md),
[acc-add-product-checklist](../../process/checklists/acc-add-product-checklist.md),
[box-data-model](../box-data-model.md).
