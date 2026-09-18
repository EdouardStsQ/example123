# Confirmed joins and identifiers — check here before asserting one

**One page, one job:** every FK relationship and identifier this repo has *confirmed*, in one place, so
a query author does not have to know which of thirty documents holds the answer.

## Why this exists

Four query defects in three days, and **three of them asserted a relationship this repo had already
confirmed elsewhere**:

| Date | Defect | Where the answer already was |
|---|---|---|
| 2026-09-18 | Q-05c joined `FK_INSTRUMENT` to Processed Instruments | `box-data-model.md` — confirmed 2026-09-11 |
| 2026-09-18 | Q-04 filtered an `_X` bridge on `FK_BS` instead of `FK_PARENT` | The `_X` pattern, evidenced on two other tables |
| 2026-09-18 | A branch lookup searched `CODE IN ('SLB','ESP')` | `fe-branch-configuration.md` §1 — the baseline table pairs those descriptions with `MADRID` / `LND BRANCH` |

The information was never missing. It was **scattered**, so "check before you assume" cost more than
guessing. This page makes checking cheap. **Adding a confirmed relationship here is part of confirming
it** — a fact recorded only in the document where it was discovered will be missed again.

Nothing here is new evidence; every row cites where it was established.

---

## Which schemas are shared across environments

`[stated: Edouard, 2026-09-18]` **This is the fact that decides whether a value needs a
cross-environment check at all.** It was knowable and unwritten, and cost a round of pointless queries.

| Schema | Holds | Same rows in every environment? |
|---|---|---|
| `PGT_STC` | Static config — branch master, currency, calendar, entity | ✅ **Yes** |
| `PGT_SYS` | System config — Family/Product/Sub-Product, `PGT_DOMAINS` | ✅ **Yes** |
| `PGT_MRK` | Market data — quote reference, quote source | Shared **between BOX and GBO within an environment** ✅. **NOT replicated across environments** `[confirmed: DB, 2026-09-18]` — see below |
| `DEVENG` | GBO Financial Engine — the mining **source** | ❌ Environment-specific |
| `BOX_FE` | BOX Financial Engine — the **target** | ❌ Environment-specific |

**Consequences.** A reference FK resolving into `PGT_STC` or `PGT_SYS` — calendar, currency, branch,
Sub-Product instrument, any domain value — needs **no cross-environment verification**; it is the same
row everywhere by design. Do not ask a human to run those comparisons. This also explains the `.4` PK
suffix on that data: it is allocated in the global reference environment, which is what "shared" means
in practice.

### `PGT_MRK` is the exception — environment-specific market data

`[confirmed: DB via Edouard, 2026-09-18]` NY_SCH's fixing curve references **38 quote references**; only
**2** exist in another environment. **35 of the 38 carry the `.35` suffix** — allocated locally in NY's
own environment. Quote references are largely *local* market-data objects, not shared reference data.

And `.4` does **not** guarantee identity here the way it does in `PGT_STC`/`PGT_SYS`: `6401.4` resolves
to **SANTANDER NY SPOT CLOSING PRICES** in one environment and **EUROPEAN CENTRAL BANK FIXING** in
another. Same PK, different object.

**Consequence:** a quote reference mined in one environment cannot be assumed valid in another. Within
one environment BOX and GBO share it, so a same-environment run is unaffected — which is why walk step 4
resolves natively in a real run and is **not rehearsable** in a split-environment one.

**If a `PGT_STC` or `PGT_SYS` value ever appears to differ between environments, that is a platform
escalation** — a shared schema out of sync is much bigger than one branch onboarding — not a finding
about the walk, and not a reason to block a run.

## Instrument FKs — not one table

`FK_INSTRUMENT` does **not** point at the same table everywhere. Check before every use.

| Table | `FK_INSTRUMENT` → | Confirmed |
|---|---|---|
| `T_BOX_ENGACCRCONF_S` (Accrual) | `PGT_SYS.T_PGT_SUB_PRODUCT_S.PK` | DB, 2026-09-18 |
| `T_BOX_CONF_BY_BOOK_S` (Book) | `PGT_SYS.T_PGT_SUB_PRODUCT_S.PK` | DB, 2026-09-11 |
| `T_BOX_MBJ_PROPERTIES_S` (MBJ) | instrument PKs in the `.4` space (e.g. CCS `20.4`, OTC `20111.4`) | DB extract, 2026-09-16 |

**`BOX_FE.T_BOX_ENGINSTRUMENTS_S` (Processed Instruments) is a different key space** — PKs `1.65`,
`2.65`, `3.65` — and is *not* the lookup for the Accrual or Book tables. It is BOX's own 18-row
catalogue of what BOX processes.

## Quote-reference anatomy `[confirmed: DB, 2026-09-18]`

`PGT_MRK.T_PGT_QUOTE_REFERENCE_S` is what a fixing curve's array points at. A quote reference is a
**tuple**, not an opaque id:

| Column | → | Schema | Shared across environments? |
|---|---|---|---|
| `FK_QUOTEINSTRUMENT` | `PGT_STC.T_PGT_CURR_PAIR_S.PK` — currency pair (`SHORTNAME`) | `PGT_STC` | ✅ Yes |
| `FK_QUOTETYPE` | `PGT_SYS.PGT_DOMAINS.PK` — quote type | `PGT_SYS` | ✅ Yes |
| `FK_QUOTESOURCE` | `PGT_MRK.T_PGT_QUOTE_SOURCE_S.PK` — the market-data feed | `PGT_MRK` | ❌ **No** |
| `FK_QUOTEDIRECTION` | **unconfirmed** `[open-question]` — `PGT_DOMAINS` is the obvious candidate | — | — |
| `FK_MATURITY` | **unconfirmed** `[open-question]` | — | — |
| `FK_PARENT` | **unconfirmed** `[open-question]` — the owning object, whatever that is here | — | — |

The listed columns are a useful subset; the table's full shape is unconfirmed.

**Why this matters beyond decoding.** Two of the three identity components are shared and one is not —
which is exactly why `6401.4` names a different feed in two environments. It also makes step 4's findings
reviewable: an SME can sign off *"Santander NY spot closing prices, EUR/USD"* and cannot sign off
`6401.4`. Use **Q-04b**.

**`T_PGT_CURR_PAIR_S` is new to this repo as of 2026-09-18** — a currency-pair master in `PGT_STC`, so
shared and identical everywhere.

## `FK_PARENT` means "owner" beyond bridge tables

The `_X` convention below is the sharpest case, but the pattern is broader: on `_S` tables too,
`FK_PARENT` points at the **owning object** — `T_*_ENGACCRCONF_S.FK_PARENT` → the configuration header,
`T_*_ENGLKFC_X.FK_PARENT` → the fixing curve. So when an unfamiliar `FK_PARENT` appears (as on
`T_PGT_QUOTE_REFERENCE_S`), *"what owns this row?"* is the right question to ask of it.

`[inferred]` — a pattern, not a developer-stated rule, and one `FK_PARENT` in this corpus is **proven
wrong** (see the known-broken table at the end). Treat it as a hypothesis to check.

## `_X` bridge tables — `FK_PARENT` up, `FK_BS` across

**Filter on `FK_PARENT`, join on `FK_BS`.** Never the reverse.

| Bridge | `FK_PARENT` → (the owner) | `FK_BS` → (the link) |
|---|---|---|
| `T_BOX_ENGCONF_X` | FE configuration header `T_BOX_ENGCONF_S` | GBO branch `PGT_STC.T_PGT_BRANCH_S` |
| `T_BOX_LINK_ARRAY_X` | `T_BOX_CONF_LO_PROP_S` | `T_BOX_CONDPAR_PROP_S` |
| `T_BOX_ENGLKFC_X` / `T_PGT_ENGLKFC_X` | fixing curve `T_*_ENGFCURVE_S` | quote reference `PGT_MRK.T_PGT_QUOTE_REFERENCE_S` |

`[inferred]` The pattern is strongly evidenced, not developer-stated. Treat a fourth `_X` table as
fitting it **until checked**.

## Branch identity

| Fact | Value |
|---|---|
| Branch master | `PGT_STC.T_PGT_BRANCH_S`, ~137 rows, overloaded (entities, SPVs, counterparties, test records — not 137 booking branches) |
| Code column | **`CODE`**, with `DESCRIPTION` alongside `[confirmed: DB, 2026-09-18]` |
| Madrid | `PK 22.21`, `CODE = MADRID` — appears in config descriptions as **(ESP)** |
| London / SLB | `PK 20087.4`, `CODE = LND BRANCH` — appears in config descriptions as **(SLB)** |
| NY_SCH | `PK 20007.4`, `FK_ENTITY 31398.4`, `FK_CURRENCY 159.4`, `FK_CALENDAR 83.4`, `FK_LOCALGROUP 21447.4` |

⚠️ **`ESP` and `SLB` are description abbreviations, not branch codes.** Resolve a branch by PK from
Q-G1, or by `CODE` — never by the parenthetical in a configuration's description.

## GBO ↔ BOX table twins

The per-tab mapping lives in [`branch-config/fe-branch-configuration.md`](branch-config/fe-branch-configuration.md) §2.
Two worth repeating because they are exceptions:

| BOX FE table | GBO twin |
|---|---|
| `T_BOX_CONF_BY_BOOK_S` (Book) | **none** — BOX-only functionality `[stated: BOX FE Developer, 2026-09-11]` |
| `T_BOX_ERRORS_FE_S` (Allowed Errors) | `DEVENG.T_PGT_ERRORS_FE_S`, keyed by **`FK_BRANCH`** `[confirmed: DB, 2026-09-18]` |

## Primary keys

`F___SEQUENCE(TABLE_NAME, seq_range)` allocates every BOX FE PK: `NEXTVAL` from **`SQ_BOX_FINANENG1`**
(all walk tables) plus, with `seq_range = 'X'`, the environment's auth code as a fraction —
`auth_code / 10^length(auth_code)`, read from `gom_glb_sys.t__CORE_INFO_S`.
`[confirmed: source via BOX FE Developer, 2026-09-17]`

So a PK's suffix records **which environment allocated the row**, not who owns it: `.4` global
reference, `.21` Tier 1, `.65` BOX-DEV, `.35` NY's Tier 2. One row can legitimately carry three
different suffixes across its columns.

## Known-broken and known-unconfirmed

Recorded so nobody re-derives them.

| Relationship | Status |
|---|---|
| `T_PGT_BRANCH_INST_S.FK_PARENT = T_PGT_BRANCH_CONFIG_S.PK` | ⛔ **Proven wrong** — fails for Madrid too. What `FK_PARENT` references is open |
| `T_BOX_ENGZCCONF_S.FK_PARENT` (Yield Curve) | Assumed, unvalidated — table empty in Tier 1 PRE |
| `T_BOX_ENGCURRENCYBASIS_S.FK_PARENT` (Currency Basis) | Assumed, unvalidated — table empty in Tier 1 PRE |
| `T_BOX_FIXING_BY_INSTR_S` → `V_BOX_PROC_INSTR_S` vs. `T_BOX_ENGINSTRUMENTS_S` | Same population? `[open-question]` |
| `PGT_MRK` replicated **across environments**? | ✅ **Answered 2026-09-18: no.** 35 of NY's 38 quote references are `.35` — locally allocated. One `.4` PK (`6401.4`) even resolves to a different object in each. Shared BOX↔GBO within an environment only |
| `.44` suffix — which environment? | `[open-question]` — second sighting (`12231.44` in NY's quote array; earlier in `T_PGT_BRANCH_INST_S.FK_PARENT`). An unidentified environment |
| `T_BOX_ERRORS_FE_S` BOX-side column names | Unconfirmed — run Q-13(a) |
