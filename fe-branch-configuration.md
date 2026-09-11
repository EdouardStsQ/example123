# BOX_FE — GBO branch to Financial-Engine configuration surface

The primary downstream configuration surface once a branch is available in **GBO** (`PGT_STC`). The
`branch-config-agent` supports two modes: it can prepare a **new-branch GBO creation handoff**, wait for
that GBO-created record as a gate, then assess this surface; or it can start here for an **existing GBO
branch**. GBO owns the implementation of branch creation; the agent proposes/packages but never writes
it. BOX_FE must determine whether the GBO branch can reuse an existing Financial-Engine configuration,
or needs a new configuration aggregate and its per-book/per-instrument adaptations. BOX_ACC group-config
is a downstream module.

## Evidence boundary `[confirmed]`

- **Production-copy DB extracts** are the source of truth for the production baseline values and
  relationships below (`GBO_BRANCHES.csv`, `BOXFE_Q1.csv`, `BOX_FE_X_Q.csv`,
  `BOXFE_ACCEX_Q2.csv`, `BOXFE_BOOK_Q3.csv`, `BOXFE_ACCR_Q4.csv`, `BOXFE_FXCR_Q5.csv`, read
  2026-08-27).
- **Test SIGOM screenshots** are evidence of the UI workflow and its eight tabs only. Their displayed
  records/PKs must **not** be compared or copied into production-copy config.
- **The GBO ↔ BOX FE table mapping** in §2 was supplied directly by the BOX Lead (2026-09-10) and is
  treated as confirmed for **table identity** — which GBO table corresponds to which BOX FE table.
  It is not evidence about row contents, and equivalence of name is not equivalence of value: a
  GBO row still has to be read before its BOX FE counterpart can be proposed.
- **Functional explanations from a named BOX FE Developer** (2026-09-11 onward) are treated as
  confirmed for **what an object is for**, distinct from the DB-level mapping above (what an object
  *is called*). Neither substitutes for the other: naming evidence says a GBO row exists to read;
  functional evidence says what a BOX row's presence or absence actually *does* at runtime.

## 1. The GBO → BOX_FE relationship `[confirmed: DB + committed DDL/code]`

```text
PGT_STC.T_PGT_BRANCH_S                    GBO branch master (GBO-owned)
        PK
        |
        | T_BOX_ENGCONF_X.FK_BS
        ▼

BOX_FE.T_BOX_ENGCONF_X                    branch-to-FE-configuration bridge
        FK_PARENT
        |
        ▼

BOX_FE.T_BOX_ENGCONF_S                    FE configuration header
```

`T_BOX_ENGCONF_S` is the SIGOM **BOX FE Configuration** aggregate. Its Generic header stores
`DESCRIPTION`, `FK_CALENDAR`, `FK_CURRENCY`, `FK_CURVEMAN`, `FK_CURVEACC`, `FK_SOURCE_FRONT`, and
`FK_SOURCE_BACK`. The bridge is unique per `(FK_PARENT, FK_OWNER_OBJ, FK_EXTENSION, FK_BS)`.

Tier 1 Madrid/SLB baseline (reference structure, not Tier 2 NY target state):

| FE config PK | Configuration | Linked GBO branch PK | Branch |
|---:|---|---:|---|
| `132.21` | `Configuracion -SCH (ESP)` | `22.21` | `MADRID` |
| `333105.21` | `Configuracion -SCH (SLB)` | `20087.4` | `LND BRANCH` |

`NY_SCH` (`20007.4`, USD / New York calendar / United States group) is present as static GBO data in
Tier 1, but absent from the Tier 1 two-row `T_BOX_ENGCONF_X` extract. This proves only that it has no
Tier 1 BOX_FE link; the BOX Lead confirms NY live GBO configuration/trading is Tier 2-owned and must be
assessed there before a target readiness conclusion is made.

## 2. SIGOM configuration aggregate — eight tabs

Every tab's BOX FE table now has a named GBO counterpart in the `DEVENG` schema
`[confirmed: DB via BOX Lead, 2026-09-10]`. This matters for NY_SCH specifically: the mining source
is **GBO Tier 2**, so for each tab the agent reads the `DEVENG.T_PGT_*` table and proposes rows for
the `BOX_FE.T_BOX_*` twin.

| Tab | BOX FE surface | GBO equivalent (`DEVENG`) | Role | Status |
|---|---|---|---|---|
| Generic | `T_BOX_ENGCONF_S` | `T_PGT_ENGCONF_S` | configuration defaults: local currency, calendar, manual/accounting fixing curve, source front/back | `confirmed` |
| Yield Curve | `T_BOX_ENGZCCONF_S` | `T_PGT_ENGZCCONF_S` | yield curve by currency/instrument | `confirmed` |
| Accrual | `T_BOX_ENGACCRCONF_S` | `T_PGT_ENGACCRCONF_S` | configuration × instrument: fee/interest first-day selectors, common basis, trigger/residual, interval, basis | `confirmed` |
| Fixing Exceptions | `T_BOX_FIXING_BY_INSTR_S`, joined to `V_BOX_PROC_INSTR_S` | `T_PGT_FIXING_BY_INSTR_S`, joined to `V_PGT_PROC_INSTR_S` | processed-instrument → manual/accounting fixing curve override | `confirmed` |
| Accrual Exceptions | `T_BOX_CONFIG_ACCRUAL_S` | `T_PGT_CONFIG_ACCRUAL_S` | configuration × instrument × strategy × instrument-type × **branch** → criterial | `confirmed` |
| Currency Basis | `T_BOX_ENGCURRENCYBASIS_S` | `T_PGT_ENGCURRENCYBASIS_S` | configuration × currency × maturity type → basis | `confirmed` |
| Branch | `T_BOX_ENGCONF_X` | none expected — see note | configuration → GBO branch association (`FK_BS`) | `confirmed` (BOX side) |
| Book | `T_BOX_CONF_BY_BOOK_S` | **none — confirmed no GBO analogue** | branch × instrument → FE batch execution registration (see note below; "label/book routing" undersold what this table does) | `confirmed` |

Two rows above deliberately do **not** name a GBO table, for two different reasons. `T_BOX_ENGCONF_X`
is the BOX-to-GBO bridge itself — its GBO side is `PGT_STC.T_PGT_BRANCH_S` (§1), not a `DEVENG` twin —
so no equivalent is expected. `T_BOX_CONF_BY_BOOK_S` is different: it was an open question until a
BOX FE Developer confirmed directly that **this is new BOX functionality with no GBO precedent at
all** — not a naming gap, an actual absence. See the dedicated note below; this is the first
confirmed non-analogue object in the whole walk, and it changes how that step must be evidenced.

### Fixing Exceptions — the processed-instrument join `[confirmed: DB via BOX Lead, 2026-09-10]`

The Fixing Exceptions tab is two objects, not one, on both sides:

```text
BOX FE:  BOX_FE.T_BOX_FIXING_BY_INSTR_S.FK_INSTRUMENT → BOX_FE.V_BOX_PROC_INSTR_S.PK
GBO:     DEVENG.T_PGT_FIXING_BY_INSTR_S.FK_INSTRUMENT → DEVENG.V_PGT_PROC_INSTR_S.PK
```

`V_BOX_PROC_INSTR_S` / `V_PGT_PROC_INSTR_S` are **views** (the `V_` prefix), supplying the processed
instrument the exception applies to. So the tab's grain is *processed instrument → curve override*,
and the view is what makes the exception readable — an exception row on its own carries only an
`FK_INSTRUMENT`. The `Processed Instruments` leaf under `BOX - Financial Engine > Static IT Data`
in `../sigom-reference.md` is the likely UI face of the same population. `[inferred]`

**Do not confuse this with `T_BOX_FIXING_ASSIGNMENT_S`** (§4, "Fixing configuration is
curve-driven"). `../box-data-model.md` lists the two as separate tables — "Fixing by instrument"
and "Fixing assignment" — and they play different roles here: `T_BOX_FIXING_BY_INSTR_S` is the
configurable Fixing Exceptions tab, in scope for branch onboarding; `T_BOX_FIXING_ASSIGNMENT_S` is
curve-driven derived data that follows from the header's curve selection and must never be written
during onboarding.

### GBO ↔ BOX FE naming rule `[confirmed: DB via BOX Lead, 2026-09-10]`

Across every mapping supplied, the GBO twin of a BOX FE configuration table is the same table name
with `T_BOX_` replaced by `T_PGT_`, in schema `DEVENG` instead of `BOX_FE` (and `V_BOX_` → `V_PGT_`
for views). The rule holds even where the BOX FE name breaks its own local convention — the `ENG`
infix is absent from `T_BOX_CONFIG_ACCRUAL_S` and `T_BOX_FIXING_BY_INSTR_S`, and absent from their
GBO twins in exactly the same way.

The mapping also covers the FE configuration tables that sit **outside** the eight-tab aggregate —
the three sibling screens under `Control > Configuration` plus the curve/quote linkage table:

| BOX FE table | GBO equivalent (`DEVENG`) | What it is |
|---|---|---|
| `T_BOX_ENGDAYS_MATURED_S` | `T_PGT_ENGDAYS_MATURED_S` | Days Matured configuration — product-level, **no branch column** |
| `T_BOX_ENGSETUP_S` | `T_PGT_ENGSETUP_S` | FE Parameters configuration — generic/EAV parameter store |
| `T_BOX_ENGFCURVE_S` | `T_PGT_ENGFCURVE_S` | Fixing Curve configuration (curve header) |
| `T_BOX_ENGLKFC_X` | `T_PGT_ENGLKFC_X` | Fixing curve → quote reference linkage (full join in the next section) |

Because the rule is uniform, a GBO-side table name can be *predicted* from a BOX FE one — but a
predicted name is `[inferred]` until read. Predicting a name is not evidence that the table exists
or that its rows mean the same thing on both sides. **The rule has one confirmed exception:**
`T_BOX_CONF_BY_BOOK_S` (Book, §2) has no GBO twin at all — it's new BOX-only functionality, not a
table this naming rule would ever find. Don't apply the substitution to it.

### Quote-reference array — the full join `[confirmed: DB via BOX Lead, 2026-09-10]`

The array of quote references behind a fixing curve (§4/§5, "the fixing curve is a configured array
of quote references") resolves through this chain, confirmed at the SQL level:

```sql
SELECT *
FROM   BOX_FE.T_BOX_ENGLKFC_X       T1,
       PGT_MRK.T_PGT_QUOTE_REFERENCE_S T3,
       PGT_MRK.T_PGT_QUOTE_SOURCE_S    T4,
       PGT_SYS.PGT_DOMAINS             T5
WHERE  T1.FK_BS          = T3.PK
AND    T3.FK_QUOTESOURCE = T4.PK
AND    T3.FK_QUOTETYPE   = T5.PK
```

So each `T_BOX_ENGLKFC_X` linkage row's `FK_BS` — not a generic `FK_PARENT` — is the join key into
`T_PGT_QUOTE_REFERENCE_S`, which is where the array actually lives: one reference row per
quote-source/quote-type/currency-pair/maturity combination the curve carries. From there:
`FK_QUOTESOURCE` resolves the market-data feed via a dedicated master table
(`T_PGT_QUOTE_SOURCE_S`), while `FK_QUOTETYPE` resolves via `PGT_SYS.PGT_DOMAINS` — a generic
domain/enumeration table, not a quote-specific one. That asymmetry is worth keeping straight: quote
*source* has its own reference table; quote *type* is one value drawn from a shared, general-purpose
domain list that presumably serves many unrelated fields too.

**GBO-side query, and why only one table changes.** The BOX Lead states `PGT_MRK` tables are market
data shared by both BOX and GBO — not tier- or module-specific — so the identical query against GBO
needs exactly one substitution:

```sql
SELECT *
FROM   DEVENG.T_PGT_ENGLKFC_X       T1,   -- was BOX_FE.T_BOX_ENGLKFC_X
       PGT_MRK.T_PGT_QUOTE_REFERENCE_S T3,
       PGT_MRK.T_PGT_QUOTE_SOURCE_S    T4,
       PGT_SYS.PGT_DOMAINS             T5
WHERE  T1.FK_BS          = T3.PK
AND    T3.FK_QUOTESOURCE = T4.PK
AND    T3.FK_QUOTETYPE   = T5.PK
```

This is a sharper version of the GBO ↔ BOX FE naming rule above, not an exception to it: the
`T_BOX_*` → `T_PGT_*` / `BOX_FE` → `DEVENG` substitution still applies to the one BOX-specific
table in the query (`T_BOX_ENGLKFC_X`), while `PGT_MRK` and (per this query) `PGT_SYS.PGT_DOMAINS`
aren't module-owned at all — there is one copy, read the same way regardless of which side (BOX or
GBO) is asking. Practically: mining a branch's quote-reference data from GBO Tier 2 does not
require a second, GBO-flavoured read of `T_PGT_QUOTE_REFERENCE_S`/`T_PGT_QUOTE_SOURCE_S`/
`PGT_DOMAINS` — there is only one, and it's whatever the BOX FE side would read too.

`[open-question]` Whether `PGT_SYS` is shared **as a whole** (like `PGT_MRK`) or only
`PGT_DOMAINS` happens to be a generic table used the same way everywhere is not established by this
query alone — don't generalise past what's shown here without checking another `PGT_SYS` table.

### Book — batch execution registration, not just routing `[stated: BOX FE Developer, 2026-09-11]`

Asked directly what `T_BOX_CONF_BY_BOOK_S` is *for*, a BOX FE Developer explained:

> This is a new functionality of BOX, that was not present in GBO, so there is no equivalent in GBO.
> Basically, this is where we create the registers in monitor to execute the FE batch. The books
> which are created there for X branch and X instrument are the ones that are executed.

Two things this confirms, and one thing it changes:

**Confirms:** `T_BOX_CONF_BY_BOOK_S` has no GBO twin, definitively — not merely absent from the
supplied mapping (§2's earlier, weaker phrasing). It also confirms and puts plain business language
on §5's "Runtime consequence" finding, which already described the mechanism at the code level: "the
queue maker resolves `T_BOX_CONF_BY_BOOK_S` by `(FK_BRANCH, FK_INSTRUMENT)`... creates
branch/instrument process-queue rows." The developer's answer is what that mechanism *is*: a
**"monitor" execution register**. A row here for `(branch, instrument)` is what makes the FE batch
actually process that combination. The two `Process Queues` / `Monitor` leaves under
`BOX - Financial Engine > Process Management` in `../sigom-reference.md` are the plausible UI face of
this same runtime population. `[inferred]`

**Changes:** this table's role is operationally load-bearing, not merely descriptive. A missing Book
row for `(branch, instrument)` doesn't mean "configuration incomplete, values default" — per this
description it means that combination is **never batch-processed at all**, silently. That makes Book
the one FE object in the whole walk where an omission is not just a data gap but a functional no-op,
and it should be validated accordingly at Phase 4 (readiness chain), not only at config sign-off.

### The confirmed join `[confirmed: DB via BOX FE Developer, 2026-09-11]`

```sql
SELECT T1.PK,
       BR.PK,   BR.DESCRIPTION,                    -- branch
       T3.PK,   T3.DESCRIPTION,                    -- instrument
       T4.PK,   T4.CODE || ' - ' || T4.DESCRIPTION  -- book label
FROM   BOX_FE.T_BOX_CONF_BY_BOOK_S    T1,
       PGT_STC.T_PGT_BRANCH_S         BR,
       PGT_SYS.T_PGT_SUB_PRODUCT_S    T3,
       PGT_SYS.PGT_DOMAINS            T4
WHERE  T1.FK_BRANCH     = BR.PK
AND    T1.FK_INSTRUMENT = T3.PK
AND    T1.FK_LABEL      = T4.PK
```

This is what the Book tab of the BOX FE MIS config actually shows, per the developer who supplied it
— save it as the canonical query for this object (also in the
[query catalogue](../queries/fe-config-mining.md)'s Q-10). Three things it establishes:

`FK_INSTRUMENT` resolves to `PGT_SYS.T_PGT_SUB_PRODUCT_S.PK` — the **Sub-Product** level of
`../box-data-model.md`'s Product classification hierarchy, not a separate BOX_FE-specific instrument
table. So "instrument" on the Book tab means the same three-level Family→Product→Sub-Product
classification documented there, and Book config is keyed at its most granular level.

`FK_LABEL` resolves to `PGT_SYS.PGT_DOMAINS.PK` — the **second** confirmed use of `PGT_DOMAINS` as a
generic, reused enumeration table (the first was quote type, in the fixing-curve join above). Two
independent fields now resolving through the same generic table is a stronger hint that `PGT_DOMAINS`
really is a shared, cross-purpose lookup rather than something specific to either use — still not
proof it spans the whole `PGT_SYS` schema, but stronger than the single earlier instance.

**Book, confirmed identical to the Data-Lake Book dimension.** Asked what these books actually are,
the same developer added: *"The books are the books that we have in the Data Lake (Lago)."* That
directly ties this table to a concept the repo already had independent evidence for:
`../fe-raw-data-stage.md` confirms "RAW `BOOK` is a separate BOX/Data Lake processing Book dimension,
not the Murex buy/sell portfolio" — same dimension, established from a completely different angle
(a Murex-to-RAW row trace, not a SIGOM config screen). Two independent confirmations of one concept.

**A promising but unverified match with Control-M's book abbreviations.**
`../job-chains/control-m-batch-layer.md` §3 lists `<BOOK-ABBREV>` job-naming examples including
`FIXINSLB` = "HPE FIXED INCOME SLB" — and this query's sample rows include a `PGT_DOMAINS` entry
`XLB01 - HPE FIXED INCOME SLB`, an exact description match. That document separately flags its
`<BOOK-ABBREV>` scheme as an unresolved open question ("no lookup table found → derive from the
analogue and flag"). `PGT_SYS.PGT_DOMAINS`, reached via this join, is a real candidate for exactly
that missing lookup table. `[open-question]` — one matching description is suggestive, not a
confirmed identity; the two systems' book lists should be cross-checked directly (same PK space? same
count?) before treating this as settled.

**Consequence for how this step is evidenced.** Every other object in this document has a GBO
counterpart to read (§2's table). Book has none — but it is not evidence-free the way the earlier
version of this note implied. Three sources now apply, none of them GBO: the **Data Lake / Murex book
enumeration** for this branch (the same enumeration `control-m-batch-layer.md` §4 step 2 already
requires for the batch-layer build — one piece of evidence-gathering work, not two), a **named SME
decision** on which of those books need FE batch registration specifically (not every Data-Lake book
necessarily needs one — that scoping judgment is still SME-owned), and **structural reference** to
existing BOX branches' Book rows (Madrid/London; see §3's row counts) for what a well-formed entry
looks like, never as a value to copy (hard rule 6 in full: 373 Madrid rows and 112 London rows are not
a template for NY's count). `EVIDENCE_REQUIRED`/`SME_DECISION_REQUIRED` is the default starting status
for every Book row on a new branch until the Data-Lake enumeration and SME scoping are both in hand.

## 3. Tier 1 baseline composition `[confirmed: DB]`

| Child surface | ESP config `132.21` | SLB config `333105.21` | Configuration grain |
|---|---:|---:|---|
| Generic header | 1 | 1 | FE configuration |
| Accrual (`T_BOX_ENGACCRCONF_S`) | 8 rows | 7 rows | configuration × instrument |
| Accrual Exceptions (`T_BOX_CONFIG_ACCRUAL_S`) | 6 rows | 5 rows | configuration × instrument × strategy × type × branch |
| Book (`T_BOX_CONF_BY_BOOK_S`) | 373 rows | 112 rows | configuration × branch × instrument × label/book |
| Fixing curve header (`T_BOX_ENGFCURVE_S`) | `64.21` | `333046.21` | curve × local currency |

Both current configurations share calendar `84.4`, currency `160.4`, source-front `413.4`, and
source-back `586.4`, but use distinct manual/accounting fixing-curve records. Do not infer that a
new USD/New-York branch can reuse either configuration solely from those common values.

## 4. GBO and runtime dependency findings `[confirmed: DB]`

### GBO prerequisite tree

The GBO configuration hierarchy is confirmed as:

```text
T_PGT_BRANCH_S.PK
  → T_PGT_BRANCH_CONFIG_S.FK_BRANCH
    → T_PGT_BRANCH_INST_S.FK_PARENT
      → T_PGT_BRANCH_INS_CONFIG_S.FK_PARENT
```

`T_PGT_BRANCH_CONFIG_S` adds MIS / back-office configuration plus settlement and fixing controls.
`FK_MISCONFIG` resolves to the distinct GBO Financial Engine store `DEVENG.T_PGT_ENGCONF_S`; BOX FE
uses its own `BOX_FE.T_BOX_ENGCONF_S` store. The BOX Lead confirms `T_BOX_MX_CONFIG_S` is not an
onboarding requirement, so its Tier 1 rows are legacy observations only. NY's Tier 1 branch-config row
(`9.21`, `FK_MISCONFIG=2.22`) and missing child rows cannot establish Tier 2 NY readiness.

### Fixing configuration is curve-driven

This section is about `T_BOX_FIXING_ASSIGNMENT_S` — **not** the Fixing Exceptions tab's
`T_BOX_FIXING_BY_INSTR_S` (§2). Separate tables, separate roles: the tab is configured during
onboarding, this one is derived and must not be written.

`T_BOX_FIXING_ASSIGNMENT_S` is **not** a child of the two `T_BOX_ENGCONF_S` headers: neither header
PK occurs in its 790 distinct `FK_PARENT` values. But the configuration's curve selection does drive
it: each of the two configured manual/accounting curves has **4,254 matching assignment rows**, covers
all **12** processed instruments, and spans **395** assignment-parent values. The agent follows
`ENGCONF.{FK_CURVEACC|FK_CURVEMAN} → FIXING_ASSIGNMENT.{FK_FIXINGCURVE_ACC|FK_FIXINGCURVE_MAN}`;
its own `FK_PARENT` remains a separate relationship and must not be invented.

### Runtime queues prove activity, not selected configuration

`T_BOX_BRPROCCAL_S` and `T_BOX_BRPROCCAL_QUEUE_S_OPTZ` contain Madrid (8 instruments) and London
(7 instruments) activity, but **zero** rows have `FK_CONFIG` or `FK_FIXCURVE` populated in the
Tier 1 extracts. `NY_SCH` has no Tier 1 rows in either table. Therefore these tables establish
branch/instrument **runtime presence** only in the queried tier, not which FE configuration/curve was
selected; configuration selection remains proven by the Branch/Book tables and code.

## 5. Runtime consequence `[confirmed: code]`

At runtime, BOX_FE resolves branch-specific fixing behavior through the bridge:
`branch PK → T_BOX_ENGCONF_X.FK_PARENT → T_BOX_ENGCONF_S.FK_CURVEACC`. The queue maker then resolves
`T_BOX_CONF_BY_BOOK_S` by `(FK_BRANCH, FK_INSTRUMENT)`, joins it to the configuration bridge, and
creates branch/instrument process-queue rows carrying `FK_CONFIG` + `FK_FIXCURVE`.

**In plain terms** (§2, "Book — batch execution registration"): this is the mechanism a BOX FE
Developer describes as creating "registers in monitor to execute the FE batch." A `(branch,
instrument)` combination with no Book row is not queued at all — the code-level finding above and the
developer's functional description are the same fact, confirmed from two independent angles.

## 5. Agent decision rule

For each branch onboarding request, select one entry mode:

1. **New branch:** check GBO for an existing matching branch. If absent, prepare a proposed GBO
   branch/branch-group/master-data handoff and wait for the resulting GBO record — `GBO-created` is a
   blocking evidence gate. The agent never writes GBO.
2. **Existing GBO branch:** read its GBO profile (PK, entity, local currency, calendar, group/country).
3. Look up `T_BOX_ENGCONF_X.FK_BS = branch PK`.
4. If present, read its complete eight-tab aggregate + Book rows and check completeness.
5. If absent (e.g. `NY_SCH`), rank existing FE configurations by evidence-backed compatibility:
   currency, calendar, source systems, fixing curves, entity/group/country, expected instruments and
   books. The agent **proposes** the smallest adaptation; it does not assign a configuration, a curve,
   or a book mapping without SME confirmation.
6. Produce a typed **branch-onboarding decision matrix** (Markdown + JSON): one row per GBO, BOX_FE,
   runtime and BOX_ACC dependency, each status-tagged as `CONFIRMED_PRESENT`, `CONFIRMED_ABSENT`,
   `PROPOSED`, `SME_DECISION_REQUIRED`, `EXTERNAL_CHECK_REQUIRED` or `EVIDENCE_REQUIRED`.
   The matrix never infers the target branch name, instruments, Books, curves or GL accounts from an
   analogue; those remain explicit SME-owned inputs. It emits inherited elements, proposed FE
   configuration/Branch/Book/accrual rows and external prerequisites (Data Lake, QR FX, Control-M).

**Sources:** committed `cib-boxfin-dbboxfe` DDL/GOM metadata/runtime code; read-only production-copy DB
extracts listed above; test SIGOM screenshots (UI shape only); [box-branch-onboarding-checklist](../../process/checklists/branch-onboarding-checklist.md).
