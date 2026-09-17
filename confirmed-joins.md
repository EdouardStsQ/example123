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
| `PGT_MRK` | Market data — quote reference, quote source | Shared **between BOX and GBO within an environment**; across environments `[open-question]` |
| `DEVENG` | GBO Financial Engine — the mining **source** | ❌ Environment-specific |
| `BOX_FE` | BOX Financial Engine — the **target** | ❌ Environment-specific |

**Consequences.** A reference FK resolving into `PGT_STC` or `PGT_SYS` — calendar, currency, branch,
Sub-Product instrument, any domain value — needs **no cross-environment verification**; it is the same
row everywhere by design. Do not ask a human to run those comparisons. This also explains the `.4` PK
suffix on that data: it is allocated in the global reference environment, which is what "shared" means
in practice.

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
| `PGT_MRK` replicated **across tiers**? | `[open-question]` — known shared between BOX and GBO *within* a tier; cross-tier unrecorded. Matters for step 4 under gate 0f |
| `T_BOX_ERRORS_FE_S` BOX-side column names | Unconfirmed — run Q-13(a) |
