# BOX_ACC — Branch-Configuration Surface

What must be **configured per branch/entity** to onboard it into BOX_ACC, reverse-engineered
deterministically from committed PL/SQL + DDL in `cib-boxacc-dbboxacc`. This is the evidence base for
the **branch-config onboarding agent** (`plugins/agent-plugins/branch-config-agent/`). It answers:
*when a new branch is added, which config objects/values must exist, which are manual vs
runtime-derived, and where the GL-account values actually come from.*

> **Scope note.** This page is the **BOX_ACC account-resolution** slice. The full new-branch surface
> (Infrastructure/static-data, BOX_ACC, BOX_FE, batch) is governed by [box-branch-onboarding-checklist](../../process/checklists/branch-onboarding-checklist.md)
> (the agent backbone); the batch/Data-Lake layer is in [box-branch-batch-controlm](../job-chains/control-m-batch-layer.md).

> **Golden rule (unchanged):** the agent **proposes + flags**; a named SME signs off; nothing is
> invented. GL-account values live in the system-of-record config (GBO/SIGOM), **not** the repo — so
> concrete account numbers are always `open-question` until sourced from that system or an SME.

---

## 1. Account resolution is two-tier

BOX_ACC turns an accounting **topic** (e.g. `ASSETNOTIONAL`) into a posted GL movement in two
deterministic steps. The **branch delta** lives in tier 1.

### Tier 1 — Topic → GL account (GLTA): the real per-branch manual config `[confirmed: code]`

`Pkg_AcctGeneral.f_getacctno(num_branch, num_properties, num_topic)` resolves a topic to a GL
account (GLTA) by reading **`T_BOX_ACCT_LIST_TOPIC_S`**:

```sql
SELECT t1.fk_glta INTO num_glta
FROM     "BOX_ACC".T_BOX_ACCT_LIST_TOPIC_S t1
WHERE   t1.fk_parent      = num_properties
   AND  t1.fk_owner_obj   = 35000170.65        -- SIGOM owner group for the topic-list object
   AND  t1.fk_topic       = num_topic;
```

Source: `code/08-BOX_ACC/r0.0.9/20_Packages/010-pkg_acctgeneral_body.sql` (`f_getacctno`, ~L522–649).

**Key finding:** the historical **branch-group** lookup (`T_PGT_BRANCH_S.FK_LOCALGROUP`) is
**commented out** — resolution is effectively keyed by **portfolio-properties + topic**, and the
portfolio-properties record is what carries the branch/entity/instrument dimension. So *"same topic,
different GL account per branch"* is realised **through the portfolio-properties record**, not through
a branch column on the mapping table.

> **⚠ DUAL KEYING — config by branch GROUP, runtime keys by branch PK** `[confirmed: DB proof 2026-08-24]`.
> The column literally named `FK_BRANCH` in `T_BOX_ACCT_PORT_PROP_S` (and its child topic maps) holds
> the branch **group** — `T_PGT_BRANCH_S.FK_LOCALGROUP` — **not** the branch PK. Proven on the DB:
>
> | Branch | PK | localgroup | properties by PK | properties by localgroup | acct-keys by PK | by localgroup |
> |---|---|---|---|---|---|---|
> | `MADRID` | `22.21` | `269.4` | 0 | **80** | **6,646,498** | 0 |
> | `LND BRANCH` | `20087.4` | `21462.4` | 0 | **101** | **2,157,013** | 0 |
>
> - **Manual config** (`T_BOX_ACCT_PORT_PROP_S` + topic→GL maps) is **keyed by branch group** → defined
>   once per group and **shared by every branch in it**. Filtering by branch PK returns nothing; filter
>   by localgroup.
> - **Runtime keys** (`T_BOX_ACCT_KEY_S`) are **keyed by the branch PK** (millions of rows; 0 by group),
>   like movements/BOX_FE.

> **Implication for onboarding:** a new branch **in an existing group inherits** the group's config
> (may need *no* new portfolio properties); a new branch that forms a **new group** needs a fresh config
> set. This reconciles the commented-out group lookup in §1 (the property set already encodes the group).

### Tier 2 — Account key: runtime-derived, NOT onboarding input `[confirmed: code]`

`Pkg_Acct_Trg.f_getacctkey(glno, branch, ccy, instrument, costcenter, security, entity, folder,
settacct, registry, properties, topic, acct_strategy, source_ccy)` looks up **`T_BOX_ACCT_KEY_S`** via
cursor `Cur_Acct_Key` on the full dimension tuple; `f_createacctkey` **auto-inserts** the key row (+ a
`T_BOX_ACCT_KEY_GROUP_S` row) when it does not yet exist.
Source: `code/08-BOX_ACC/r0.0.9/20_Packages/007-pkg_acct_trg_body.sql` (`F_GetAcctKey` ~L787,
`F_CreateAcctKey` ~L659, `Cur_Acct_Key` ~L41).

**Implication:** `T_BOX_ACCT_KEY_S` / `_GROUP_S` are a **derived cache** of dimension tuples the engine
has seen — **not** a human-onboarded object. They are, however, the best place to **mine an existing
branch's *effective* config** (every `(branch, ccy, instrument, entity, folder, properties, topic,
GLNO)` combination that branch has actually used).

---

## 2. The config objects (exact DDL columns) `[confirmed: DDL]`

DDL in `ddl/01-BOX_ACC/r0.0.1/05_Tables/` (dynamic `EXECUTE IMMEDIATE 'CREATE TABLE …'`).

### `T_BOX_ACCT_PORT_PROP_S` — Portfolio-property header (the per-branch object) — `003-...sql`

| Column | Notes |
|---|---|
| `PK` | SIGOM primary key — this is the `properties` identity used downstream |
| `FK_OWNER_OBJ` NOT NULL | SIGOM owner group |
| `FK_PARENT` | SIGOM parent object |
| `FK_EXTENSION` | SIGOM extension type |
| `FK_INSTRUMENT` NOT NULL | product/instrument the property set applies to |
| **`FK_BRANCH` NOT NULL** | **the branch dimension** — one (or more) property header(s) per branch × instrument |
| `INIVALPCDATE` NOT NULL | initial validity date |
| `DESCRIPTION`, `STATUS`, `MESSAGE` | free text / lifecycle |
| `LSTMNTDATE`, `LSTMNTUSER` | audit — stamped by trigger `G_T_BOX_ACCT_PORT_PROP_S_BIU` (audit-only) |

### `T_BOX_ACCT_LIST_TOPIC_S` — Topic → GL-account map (children of a property) — `006-...sql`

| Column | Notes |
|---|---|
| `PK`, `FK_OWNER_OBJ` NOT NULL, `FK_EXTENSION` | SIGOM identity |
| `FK_PARENT` | → the portfolio-property (the `num_properties` argument in `f_getacctno`) |
| **`FK_TOPIC`** NOT NULL | the accounting topic |
| **`FK_GLTA`** | the resolved GL account (→ `T_BOX_ACCT_GLTA_S`) |

Index `I_BOX_ACCT_LIST_TOPIC_S_PARENT_TOPIC` on `(FK_PARENT, FK_TOPIC)` = the resolution key. This is
the table that encodes *"for this branch's property set, topic X posts to GL account Y."*

### `T_BOX_ACCT_KEY_S` — derived account key (mining source, not input) — `005-...sql`

Full dimension tuple: `PK`, `FK_PARENT` (= GLNO / GL account), `FK_BRANCH`, `FK_CURRENCY`,
`FK_INSTRUMENT`, `FK_SECURITY`, `FK_ENTITY`, `FK_FOLDER`, `FK_SETTLEACCOUNT`, `FK_REGISTRY`,
`FK_PROPERTIES`, `FK_TOPIC`, `FK_ACCT_KEY_GROUP`, `FK_ACCT_STRATEGY`, `FK_SOURCECURRENCY`, `MAXDATE`,
`FK_STATUS`, `AMOUNT_CCY`, `AMOUNT_LOC`.

### Related (from `box-database-reference`)
- `T_BOX_ACCT_GLTA_S` — GL-account (GLTA) definitions (`GLTA_CODE`, `FK_GLTATYPE`).
- `T_PGT_BRANCH_S` — branch master (`FK_CALENDAR`, local currency) — the branch being onboarded.
- `T_BOX_ACCT_MOV_S` — posted movements; carries `fk_branch, fk_properties, fk_topic, fk_glta,
  fk_acct_key` (the other rich mining source — see `box-movement-reconciliation`).

---

## 3. What must be configured for a NEW branch `[inferred: structural]`

Derived from §1–§2; confirm framing with the BOX team / accounting SME.

1. **Branch master** (`T_PGT_BRANCH_S`) — the branch exists with its calendar + local currency.
2. **Portfolio-property header(s)** (`T_BOX_ACCT_PORT_PROP_S`) — one per (branch, instrument) the
   branch books, with its SIGOM `FK_OWNER_OBJ/FK_PARENT/FK_EXTENSION` identity + `INIVALPCDATE`.
3. **Topic → GL-account mappings** (`T_BOX_ACCT_LIST_TOPIC_S`) — for **every accounting topic** the
   product(s) on that branch use, a `(FK_PARENT=property, FK_TOPIC, FK_GLTA)` row.
4. **GL accounts** (`T_BOX_ACCT_GLTA_S`) — each `FK_GLTA` referenced above must exist.
5. Cross/revaluation-account + net-contract + local-property config (`T_BOX_CROSS_ACCTCONF_S`,
   `T_BOX_NETCONTRACT_S`, `T_BOX_CONF_LO_PROP_S`) — see [box-acc-add-product-checklist](../../process/checklists/acc-add-product-checklist.md) §3; these
   also carry `FK_BRANCH` and are branch-configured.

`T_BOX_ACCT_KEY_S` / `_GROUP_S` are **not** onboarded — the engine auto-creates them on first use.

---

## 4. The SIGOM / GBO open-question (scope boundary) `[open-question]`

The **GL-account values themselves** (what `GLTA_CODE` a topic maps to for a given branch) are entered
by users / migrated from the source-of-record config (GBO screens under `Portfolio Properties`), and
are surfaced in BOX only as SIGOM screen/metadata objects (`FK_OWNER_OBJ = 35000170.65`, etc.). They
are **not committed as repo data**. Therefore:

- The agent can read the **structure** and, from the DB, the **effective per-branch config actually in
  use** (portfolio properties, topic→GLTA rows, and the derived key store) — all `confirmed` from the
  system of record.
- The agent must treat any **not-yet-existing** GL-account value for a new branch as `open-question`
  / SME-sourced — never invented, never copied blindly.

---

## 5. How the agent mines an existing branch (deterministic) `[confirmed: schema]`

Read-only DB extracts a human with DB access runs (results are client-confidential → `.scratch/`):

Note the keying caveat above: `FK_BRANCH` in these tables = the branch **group** (`FK_LOCALGROUP`).
The agent's `extract_branch_config.py` therefore matches `FK_BRANCH IN (<branch PK>, <its localgroup>)`
and returns `FK_BRANCH` so the data reveals which key each table uses.

- **Property headers:** `T_BOX_ACCT_PORT_PROP_S WHERE FK_BRANCH IN (:pk, :localgroup)` → the property
  set (PKs) per instrument.
- **Topic→GL map:** `T_BOX_ACCT_LIST_TOPIC_S` joined to those properties → `T_BOX_ACCT_GLTA_S` for the
  `GLTA_CODE` → the group's topic→account mappings.
- **Effective usage (cross-check):** `T_BOX_ACCT_KEY_S WHERE FK_BRANCH IN (:pk, :localgroup)` → every
  `(currency, instrument, entity, folder, properties, topic, GLNO)` tuple actually in use.
- **Proof query** (`emit-diagnostic <pk>`): `pp_by_pk` vs `pp_by_localgroup` per branch — the decisive
  test of the branch-group keying before it is promoted to `confirmed`.

> **Matching key is deliberately not fixed yet.** Per the onboarding decision, we mine 1–2 real
> branches first and let the data reveal the right *analogous-branch* matching dimension (portfolio
> properties + topic→GLTA vs branch-master attributes). See the generic method
> `branch-config-onboarding`.

---

## 6. Confirmed branch identities (`T_PGT_BRANCH_S`) `[confirmed: system-of-record]`

Enumerated from a read-only `SELECT * FROM PGT_STC.T_PGT_BRANCH_S` (2026-08-24). The **two operational
accounting branches** are:

| Branch | PK (`FK_BRANCH`) | `CODE` | `DESCRIPTION` | `FK_ENTITY` | `FK_CURRENCY` | `FK_CALENDAR` | `FK_LOCALGROUP` |
|---|---|---|---|---|---|---|---|
| Spain (Madrid) | `22.21` | `MADRID` | `MADRID REAL` | `31434.4` | `160.4` | `84.4` | `269.4` |
| London (SLB) | `20087.4` | `LND BRANCH` | `LONDON BRANCH` | `31077.4` | `160.4` | `84.4` | `21462.4` |

Corroborated by the BOX_FE views, which special-case exactly `DECODE(DEAL.FK_BRANCH, 20087.4, '2286' --
London Branch …)` (`cib-boxfin-dbboxfe/.../10_Views/002-v_box_trade_details_swap_s.sql`), and by the
migration file's SLB/London entity `31077.4` (`AUKI_MIGRACION_SLB`).

**Nuances that matter for the automation:**
- **`T_PGT_BRANCH_S` is an overloaded registry (~137 rows)** — legal entities, SPVs/funds,
  counterparties, test/parallel/SWIFT/placeholder (`PH`) records — **not** 137 booking branches. The
  automation must **filter to real booking branches** (those with live BOX_ACC config / present in
  movements), not treat every row as a branch to configure.
- **Differentiator = `FK_ENTITY` + `FK_LOCALGROUP`, not currency/calendar** — both branches share
  `FK_CURRENCY=160.4` and `FK_CALENDAR=84.4`. Notably **`FK_LOCALGROUP`** (Madrid `269.4` vs London
  `21462.4`) is the very "branch-group" column that is *commented out* in `f_getacctno` (§1) — a strong
  candidate for the analogous-branch matching dimension.
- **Variants to disambiguate when mining:** an older `LONDON`/`LONDON REAL` (`42.21`), the AUKI-migration
  branches `AUKI_MIGMD` (`156.21`) / `AUKI_MIGLB` (`157.21`), and parallel/SWIFT branches
  (`PARALL_SLB` `20089.4`, `LONDON SW2` `20097.4`, `MADRID SW` `20098.4`). **Open-question:** which PK
  the live BOX_ACC config keys to (operational `22.21`/`20087.4` vs the `AUKI_MIG*` pair) — resolved by
  running the §5 `q1/q2/q3` extracts.

**Sources:** committed PL/SQL/DDL in `cib-boxacc-dbboxacc` + `cib-boxfin-dbboxfe` (cited inline);
read-only `T_PGT_BRANCH_S` extract (2026-08-24, system-of-record); `box-database-reference`,
[box-acc-add-product-checklist](../../process/checklists/acc-add-product-checklist.md), `box-movement-reconciliation`.
