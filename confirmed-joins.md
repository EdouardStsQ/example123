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
| 2026-09-18 | The draft SQL carried GBO's `FK_OWNER_OBJ` into a `BOX_FE` INSERT | Q-05c's own result note — "`FK_OWNER_OBJ`/`FK_EXTENSION` are `35000126.65`/`35001114.65` (BOX-DEV)", written to corroborate the auth-code finding and never read as a rule |
| 2026-09-18 | Q-07 mined fixing exceptions with no `FK_PARENT` filter | The Q-04 correction three days earlier — *same defect, same shape, different table* |

The information was never missing. It was **scattered**, so "check before you assume" cost more than
guessing. This page makes checking cheap. **Adding a confirmed relationship here is part of confirming
it** — a fact recorded only in the document where it was discovered will be missed again.

Nothing here is new evidence; every row cites where it was established.

> ## ⛔ Why this page cannot be replaced by the database
>
> `[confirmed: DDL via Devin, 2026-09-21]` **There is not one `FOREIGN KEY` constraint in any BOX FE or
> BOX ACC configuration table.** Every `FK_*` column is a plain `NUMBER`; referential integrity is
> entirely application-layer.
>
> So there is no `ALL_CONSTRAINTS` fallback, no dictionary copy of the join graph, and **no constraint
> that will reject a wrong FK** — it inserts cleanly and fails silently later, in a batch, far from the
> cause. The declared relationships in [`sigom-metamodel.md`](sigom-metamodel.md) plus this page are the
> whole of what stands between a mined value and a wrong number in the books.

> ## 📉 This page got smaller on 2026-09-18, and that is the point
>
> **SIGOM declares its own relationships.** `GOM_GLB_SYS.T__EXT_DEF_S` names, for every field of every
> object, what it points at — so the instrument map, the `_X` convention and the identity columns are no
> longer patterns this repo maintains by hand. They are **lookups**, and they live in
> [`sigom-metamodel.md`](sigom-metamodel.md).
>
> Every defect in the table above was a relationship the database states outright. This page keeps what
> the metamodel does *not* cover — the cross-environment rules, branch identity, PK allocation, and the
> known-broken list — and points at the metamodel for the rest. **If a join is declared, don't copy it
> here; cite it.** Two copies of a fact is how the fact drifts.

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

## SIGOM identity columns — `FK_OWNER_OBJ` and `FK_EXTENSION` belong to the *destination*

**Never mined from GBO.** `FK_OWNER_OBJ` is the **screen the row is edited through** and `FK_EXTENSION`
is **which tab within it** — properties of the destination object, not values a GBO row can supply.
Charter hard rule 9.

> **Corrected 2026-09-18, after the object catalogue was found.** This page first recorded
> `FK_OWNER_OBJ` as "the owning SIGOM module" and constant across BOX FE. Both wrong. `35000126.65` is
> the *Config screen*; the module is `35000005.65`. And the Fixing Curve tables carry `35000123.65`, so
> a single constant across the walk produces wrong rows for steps 3 and 4. The original reading was
> built from two tables that happened to share a screen.

**The full rule, the derivation and its four-for-four validation are in
[`sigom-metamodel.md`](sigom-metamodel.md) §3.** In short: base table → the object's PK with a NULL
extension; extension table → the extension's `FK_PARENT` with the extension's own PK. Derivable from
`GOM_GLB_SYS` with no `BOX_FE` read, which is why **Q-G6 is no longer in the deferred set**.

For contrast, the GBO side: `DEVENG.T_PGT_ENGCONF_S` carries `FK_OWNER_OBJ = 12198.4` on every row —
the GBO Financial Engine's own object. Copying it into a BOX row is the 2026-09-18 draft defect.

## Environment suffixes are queryable — `PGT_SYS.T_PGT_SOURCE_S.SIGOMID`

`[stated: Edouard, 2026-09-18]` The auth-code suffix on any PK can be resolved to a named environment
through the **`SIGOMID`** column of `PGT_SYS.T_PGT_SOURCE_S`. Examples given: `.4` = global (visible in
every environment), `.21` = Tier 1 Madrid.

This turns the suffix model from **inference into lookup**. Until now the repo read suffixes by
pattern-matching against known facts (`.35` appears on NY objects, therefore `.35` is NY's Tier 2). Now
there is a registry, and it sits in `PGT_SYS` — a **shared schema**, so one query in any environment
returns the full list. See **Q-G5**.

Two things this should settle on first use: the identity of **`.44`**, sighted twice and never
explained; and confirmation that **`.65` is BOX-DEV**, which the repo has been asserting on
circumstantial evidence.

## Instrument FKs — not one table

`FK_INSTRUMENT` does **not** point at the same table everywhere. **The complete declared map is in
[`sigom-metamodel.md`](sigom-metamodel.md) §6** — six objects resolve to
`PGT_SYS.T_PGT_SUB_PRODUCT_S`, and the two **fixing** objects (walk steps 8 and 13) resolve to
`V_BOX_PROC_INSTR_S`. That is the whole rule; it is declared, not inferred, and it is why Q-05c was
wrong and Q-07 legitimately differs from its neighbours.

Outside the FE walk and so not in that map:

| Table | `FK_INSTRUMENT` → | Confirmed |
|---|---|---|
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

✅ **Promoted from `[inferred]` to `[confirmed: DB, 2026-09-18]`.** This is not a pattern — it is the
declared behaviour of a **`FK_KIND = 4.1` link array**, and the `_X` table is that field's
`EXT_STORAGE`. A `4.1` field gets a bridge because its target exists independently; a `3.1` *owned
collection* gets no bridge because its rows belong to the parent. Both are filtered by `FK_PARENT`; only
`4.1` has an `FK_BS`. See [`sigom-metamodel.md`](sigom-metamodel.md) §4.

| Bridge | Declared as | `FK_PARENT` → (the owner) | `FK_BS` → (the link) |
|---|---|---|---|
| `T_BOX_ENGCONF_X` | `BOX_ENG_Config.apBranch` | `T_BOX_ENGCONF_S` | `PGT_STC.T_PGT_BRANCH_S` |
| `T_BOX_ENGLKFC_X` / `T_PGT_ENGLKFC_X` | `BOX_ENG_FixingCurve.apQuoteReference` | `T_*_ENGFCURVE_S` | `PGT_MRK.T_PGT_QUOTE_REFERENCE_S` |
| `T_PGT_LINK_ARRAY_X` | `EXT_STORAGE` of `PGT - Branch` | — | — `[open-question]`, not yet used |

> ### ⛔ `T_BOX_LINK_ARRAY_X` — this entry was replaced, 2026-09-21
>
> This page used to record it as a single relationship: *"`FK_PARENT` → `T_BOX_CONF_LO_PROP_S`,
> `FK_BS` → `T_BOX_CONDPAR_PROP_S`."* That is **1 of 17**. `[confirmed: DB, 2026-09-21]`
>
> Unlike FE, where each object gets its own bridge, **ACC puts nine objects and seventeen relationships
> into this one table**, and `FK_BS` points at **nine different target tables** depending on
> `(FK_OWNER_OBJ, FK_EXTENSION)`. `BOX - Config LOC Property` alone puts four arrays in it, three of
> them targeting the same table — so even owner *and* target don't disambiguate; only `FK_EXTENSION`
> does.
>
> **Never filter a shared bridge on `FK_PARENT` alone.** The filter is
> `(FK_OWNER_OBJ, FK_EXTENSION, FK_PARENT)`. Anything less returns rows from unrelated arrays that look
> entirely reasonable — the most dangerous shape of wrong in this corpus, and the old entry here was an
> authoritative-looking instance of it.
>
> Full table in [`sigom-metamodel.md`](sigom-metamodel.md) §4. `T_BOX_MOV_LINK_ARRAY_X` is a second
> generic bridge; assume it behaves the same way until checked.
>
> **It is `BOX_ACC.T_BOX_LINK_ARRAY_X`, not `BOX_FE`** `[confirmed: DDL, 2026-09-21]` — this page had it
> unqualified. And its DDL confirms the model while offering no protection: `FK_OWNER_OBJ` and
> `FK_EXTENSION` are `NOT NULL` but appear only in a **non-unique** header index; the PK constraint is on
> `PK` alone. **Nothing at the database level stops a cross-array query returning nonsense.**

**To check a new `_X` table, don't pattern-match — look it up.** Q-G7 against its owning object names
the field and its kind.

## `PGT_DOMAINS` — one table, many enumerations

`[confirmed: DB, 2026-09-21]` `PGT_SYS.PGT_DOMAINS` is the storage of dozens of unrelated
enumerations — Label Config (`17910.4`), SubLabel Config, Strategy, Trade Direction, Reference Type,
Criteria Treatment, Cash Flow Status, quote type, and three **BOX ACC** ones (Acct Indicator, GLTA
Type, Param Fixed). `FK_OWNER_OBJ` is what separates them.

**Joining by PK is safe. Enumerating without `FK_OWNER_OBJ` is not.** Every catalogue query that
*lists* domain values needs the discriminator; every query that *resolves* a known PK does not.

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
| `T_BOX_ENGZCCONF_S.FK_PARENT` (Yield Curve) | ✅ **Resolved 2026-09-18** — declared as `BOX_ENG_Config.amZeroCoupon`, a `3.1` owned collection, so the parent *is* the configuration header. An empty table can't validate a join; a declaration doesn't need to |
| `T_BOX_ENGCURRENCYBASIS_S.FK_PARENT` (Currency Basis) | ✅ **Resolved 2026-09-18** — declared as `BOX_ENG_Config.amCurrencyBasis`. Same reasoning |
| `T_BOX_FIXING_BY_INSTR_S` → `V_BOX_PROC_INSTR_S` vs. `T_BOX_ENGINSTRUMENTS_S` | ✅ **Resolved 2026-09-18** — declared: `BOX_ENG_Fixing_By_Instrum.pInstrument → V_BOX_PROC_INSTR_S`. The view, not the catalogue |
| Accrual Exceptions / Allowed Errors `FK_BRANCH` — geographic or product-shaped? | ✅ **Resolved 2026-09-18** — both declare `pBranch → PGT_STC.T_PGT_BRANCH_S`. The `BOX CCS` / `BOX FX` values are rows *inside* that overloaded master. See [`sigom-metamodel.md`](sigom-metamodel.md) §6 |
| `T__OBJ_DEF_S.FK_PARENT` and `.FK_CONNECTION` targets | `[open-question]` — **not** `T__OBJ_DEF_S`. Reading them as such resolves `35000007.65` to "BOX - Colour Config", a PK collision across tables |
| `T_BOX_BRPROCCAL_S.FK_BRANCH` | The object declares no branch field, yet Q-11 filters on one. Most likely runtime columns SIGOM doesn't surface `[open-question]` |
| **`pBranch` on ACC objects** | ⚠️ **Not always the branch.** `BOX - Acct Port Property` and `BOX - Config LOC Property` declare `pBranch → T_PGT_BRANCH_GROUP_S`; twelve other ACC objects declare `pBranch → T_PGT_BRANCH_S`. Same field name, different target. Resolve per object from Q-G7 `[confirmed: DB, 2026-09-21]` |
| `BOX_ACC.T_BOX_NETCONTRACT_S.FK_FOLDER` → a BOX twin or `PGT_STC.T_PGT_FOLDER_S`? | ✅ **Resolved 2026-09-21** — declared as `BOX - Net Contract.pFolder → PGT - Folders → PGT_STC.T_PGT_FOLDER_S`. **No BOX folder twin exists.** Same for Acct Movements, Acct Key, Grouped Movements |
| BOOK ↔ FOLDER mapping in BOX | ✅ **Answered 2026-09-21: none exists**, evidenced three ways over the metamodel. But it is **derivable** from deal-level tables — see [`book-and-folder.md`](book-and-folder.md) |
| `BOX - Conf Instru Type` declares `T_BOX_LINK_ARRAY_X` as `EXT_STORAGE` but no `4.1` field | `[open-question]` — unused extension slot, or something the catalogue doesn't show |
| `PGT_MRK` replicated **across environments**? | ✅ **Answered 2026-09-18: no.** 35 of NY's 38 quote references are `.35` — locally allocated. One `.4` PK (`6401.4`) even resolves to a different object in each. Shared BOX↔GBO within an environment only |
| `.44` suffix — which environment? | `[open-question]` — second sighting (`12231.44` in NY's quote array; earlier in `T_PGT_BRANCH_INST_S.FK_PARENT`). **Now cheap to answer: Q-G5 against `PGT_SYS.T_PGT_SOURCE_S.SIGOMID`** |
| `FK_OWNER_OBJ = 35000126.65` — same value in Tier 2? | `[open-question]` — a `.65` metadata PK, presumably promoted, unconfirmed. Q-G6, deferred with the rest of the `BOX_FE` reads |
| What object `35000126.65` *is* | `[open-question]` — never looked up. Not needed for the walk |
| `T_BOX_ERRORS_FE_S` BOX-side column names | Unconfirmed — run Q-13(a) |
