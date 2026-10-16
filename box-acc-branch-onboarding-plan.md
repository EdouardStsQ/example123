# BOX ACC — onboarding a new branch: what to build from BOX, what from GBO

**For review by the BOX ACC expert.** Draft of 2026-10-16. First branch: **NY SCH** (`20007.4`, branch group
`21447.4` UNITED STATES). Reference branch already in BOX: **SLB** (`20087.4`, Tier 1). The plan is meant for any branch;
NY figures are examples.

**Goal.** The `sigom-box-acc-configs-agent` writes the SQL that configures, in SIGOM BOX ACC, **only what depends on
the branch**. It never runs anything: the BOX team reviews and runs the SQL.

**Guidance already received (BOX ACC expert)**, applied below:

1. Only update the configuration that depends on the branch.
2. Condition Port Properties do not depend on the branch: assume they stay the same (a new condition may be
   requested).
3. Config. Local Properties depend on the branch.
4. Accounting Topics and Event Grouping / Event Config are global (the same topics and events for a product in every
   branch). Ask whether to keep the global Event Grouping or create a branch copy (same configuration, the branch's PK).
5. Cross Account Config can be taken from GBO.
6. Portfolio Properties must **not** be taken directly from GBO, because that would bring GBO topics.
7. Global Accounts can be taken from GBO (the accounts are the same).

---

## 1. What each part does and what it depends on

| Part (BOX table) | Purpose | Keyed on | Depends on | Used by |
|---|---|---|---|---|
| **Condition Port Properties** (`T_BOX_CONDPAR_PROP_S`) | Catalogue of the criteria that select a portfolio property: a function (`NOM_FUNC`) or a domain (strategy, instrument type…) | global | — | local-property condition array; portfolio-property condition lists |
| **Accounting Topics** (`T_BOX_ACCT_TOPICS_S`) | Catalogue of accounting concepts that events produce and accounts receive | global | — | local-property arrays, portfolio-property lists, Cross Account Config, movements |
| **Standard Historic** (`T_BOX_ACCT_HISTSTD`) | Movement text templates | global | — | movements |
| **Event Grouping / Event Config** (shared `PGT_PRC`) | Which accounting events exist, how they are grouped, which group a job runs (e.g. Initial Accounting `2409.65`) | global, or a branch copy with its own PK | topics | ACC jobs (`db.conf` group PK), MBJ properties |
| **Global Accounts** (`T_BOX_ACCT_GLTA_S`, optional date rules) | Chart of accounts: code, type, `FK_BRANCHGROUP`, by-key | branch group | — | portfolio-property lists, Cross Account Config, movements |
| **Config. Local Properties** (`T_BOX_CONF_LO_PROP_S` + 4 arrays: local / global / internal topics, conditions) | Per **group × instrument × start date**: which topics apply and which conditions may be used. The template from which `PKG_ACCTPROP.f_GenTopicCond` generates the portfolio-property lists | branch group | topics, conditions | portfolio properties (the latest local property whose start date ≤ the portfolio property's) |
| **Portfolio Properties** (+ topic → account lists, condition lists) | Per **group × instrument × start date × condition values**: the account each topic posts to, for one slice of trades | branch group | local property, topics, accounts, conditions and their values | movements (`FK_PROPERTIES`). On save: a global or local topic without an account → InValid; an identical twin → InValid |
| **Cross Account Config** (`T_BOX_CROSS_ACCTCONF_S`) | Account by branch × currency (× entity / instrument / topic), with `ACC_TYPE` (0 matured / 1 live / 2 live balance) | **branch** | topics, accounts | the engine when the account does not come from the lists; revaluation (`ACC_TYPE`) |
| MBJ Properties | Job parameters per event group | — | event groups | ACC jobs — out of this agent (`box-acc-jobs-agent`) |
| Net Contract | Madrid only | — | — | N/A for NY |
| Conf Instru Type, Net CCS PlanBS, GLTA Local Dep | Branch- / group-keyed extras outside the checklist | branch / group | accounts, instruments | proposed only if the BOX team says the branch needs them |

**How a movement is posted (as we understand it):** an event (Event Config) produces a **topic** → the trade's
instrument and **condition values** select a **portfolio property** → its list gives the topic's **account**; if
not there, **Cross Account Config** gives it.

---

## 2. The plan, part by part

| Part | Branch-dependent? | Source | How | Asked / open |
|---|---|---|---|---|
| Condition Port Properties | no | **BOX, as is** | Check that every condition the reference's properties use exists; no row created | a new condition only if requested |
| Accounting Topics | no | **BOX, as is** | Check that every topic of the reference's local properties exists; never created | — |
| Standard Historic | no | **BOX, as is** | Check only | — |
| Event Grouping / Event Config | no (choice) | **BOX, the reference** | Per reference ACC group: keep the **global** group, or create a **branch copy** (same configuration, the branch's PK) | **asked per group**; a copy changes the group PK the branch's ACC jobs and its Initial Accounting `db.conf` line run |
| Global Accounts | yes (group) | **GBO, the target** | Every account the target's portfolio properties and Cross Account Config will use, missing in BOX → the GBO row copied (same code) | a code longer than BOX's column → finding; date rules only where GBO has one |
| Config. Local Properties | yes (group) | **BOX, the reference** | The reference's local property per instrument with its 4 arrays (BOX topics and conditions), re-keyed to the target's group; GBO only confirms the target's instruments | the start date (`INIVALPCDATE`) |
| Portfolio Properties | yes (group) | **Shape from BOX (reference), accounts from GBO (target)** | §3 | every account not found, every ambiguity |
| Cross Account Config | yes (branch) | **GBO, the target** | The target's GBO rows: branch → the target branch; currency / entity unchanged; topic → its BOX topic; account by code | `ACC_TYPE` per row (the reference's pattern or the BOX team) |
| Extras (Conf Instru Type, Net CCS PlanBS, GLTA Local Dep) | yes | BOX team | Proposed only on the BOX team's request | per branch |

**Order of creation:** accounts → local properties → portfolio properties → Cross Account Config (event groups, if
copied, before the ACC jobs).

---

## 3. Portfolio Properties — the method

1. **Template = the reference's BOX portfolio properties for the instrument** — BOX's consolidated set (BOX holds far
   fewer properties than GBO), their conditions and their BOX topics. The lists come from the target's new local
   property, so the topics are BOX topics by construction.
2. **Condition values:** shared domain values (strategy, instrument type) are kept; reference-specific values (e.g.
   a folder) are replaced by the target's or asked.
3. **Account per (property, BOX topic)** — from the target's **GBO** portfolio properties of the same instrument:
   - BOX topic → its GBO topic (the topic mapping; a plain code match if BOX's topic codes are GBO's);
   - one account across the target's GBO properties → that account;
   - several → the GBO property whose conditions match the BOX property's; otherwise asked;
   - none → **OPEN** (the property would be InValid);
   - internal-list topics: the reference's technical account, or left empty (not checked on save) — asked once.
4. **Group key:** portfolio and local properties are keyed on the branch **group**. When the target is the first branch
   of its group in BOX, they are created for the group (NY SCH: no BOX ACC row for group `21447.4` yet).

**Which GBO properties belong to the target branch** (a group can hold several branches): GBO NY separates them by a
**branch condition** (`PGT_NY.PKG_NY_ACCOUNTING_CONDITIONS.f_TradeBranch…`, value `NY_SCH`, `NY_IBF`, `INTERNAL`).
Only the properties valued `NY_SCH` are read for NY SCH's accounts (58 of 71 for NY's six instruments in PRE PARALELO).

---

## 4. What is read from GBO — and what is not

| Read from GBO (the target) | Not read from GBO |
|---|---|
| the target branch's portfolio properties → **accounts per topic** | Condition Port Properties |
| the target's **Cross Account Config** | Accounting Topics, Standard Historic |
| the **Global Accounts** rows of those accounts | Event Grouping / Event Config |
| usage (movements) — only to confirm and to find accounts outside the lists | GBO local properties (one topic array, GBO topics) |

GBO source when production is not accessible: **PRE PARALELO** (a recent copy of production).

---

## 5. Questions for the BOX expert

Please answer by number.

1. **The plan in §2** — is the source of each part right?
2. **Portfolio properties (§3)** — is "the reference's BOX properties as template, accounts from the target's GBO
   properties by topic" the right approach? If a BOX property has no clear GBO equivalent, what should the agent do?
3. **Topics** — are BOX topic codes the same as GBO topic codes (so the GBO → BOX topic mapping is a code match)? If
   not, where is the mapping kept?
4. **Branch condition** — while the target is the only branch of its group in BOX, do the BOX portfolio properties
   need a condition separating the group's branches? When a second branch of the same group comes to BOX, how should
   the properties be split?
5. **Internal-list topics** — account or none in BOX?
6. **Event groups** — keep global by default, or a branch copy by default? Does a branch copy change anything besides
   the group PK the ACC jobs run?
7. **Cross Account Config `ACC_TYPE`** — how to set it for rows coming from GBO (GBO has no such column)?
8. **Global Accounts** — copy every account the target's portfolio properties use, or only those used in production?
   Date rules (`T_BOX_ACCT_PARENT_DATE_S`): copy from GBO when they exist?
9. **Start date (`INIVALPCDATE`)** for the new local and portfolio properties — a fixed rule (e.g. the go-live date)?
10. **Extras** — does a branch need Conf Instru Type, Net CCS PlanBS (NY has CCS) or GLTA Local Dep rows?
11. **Delivery** — PL/SQL calling SIGOM's routines (`P_SETHEADER` / `F_GetPK`), or a Liquibase changeset with fixed
    PKs?
12. **NY specifics seen in GBO** — how does BOX produce: (a) postings with **no topic** (`FK_TOPIC = 0`, accounts
    `09xxxx.xxx`, e.g. `097487.001`); (b) real accounts posted with no portfolio property and no Cross Account Config
    (`GENTRANSITCASH` → `916103-299919`, `FXNETLOSS` → `9970241-939607`)?
