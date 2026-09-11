# BOX Accounting Resolution Chain — Instrument Type to Posted Movement

## 1. Effective instrument type `[confirmed: code + DB]`

`BOX_TRD.PKG_BOX_DEAL_LITE_DATA_API.f_CalculateInstrumentType(P_BOCode)` reads the target deal,
leg and contract context by BO code. Its product-specific logic can call
`BOX_ACC.PKG_BOX_VALIDACIONES.f_calculateinstype`; it is not a universal unconditional table lookup.

`PKG_BOX_VALIDACIONES.f_calculateinstype` reads `BOX_ACC.T_BOX_CONF_INSTRUM_TYPE_S` for matching
`FK_BRANCH`, `FK_INSTRUMENT`, `CODE`, `TYPE`, owner and root configuration rows. It selects the
highest-priority match: exact value + exact counterparty (3), exact value + all counterparties (2),
or `#ALL` value + exact counterparty (1). A `PortfolioCode=#ALL` rule with no counterparty is
explicitly skipped. If no match exists, it returns null to the BOX_TRD product logic, which applies
its calculated fallback.

`[confirmed: DB]` The configuration population contains real branch/instrument/folder-or-additional-
info/counterparty rules and an instrument-type result. It must not be treated as a global static
product classification.

## 2. Portfolio Property selection `[confirmed: DB; evaluator semantics open]`

`T_BOX_ACCT_PORT_PROP_S` is the portfolio-property header, scoped by branch/group and instrument.
`T_BOX_ACCT_LIST_COND_S.FK_PARENT → T_BOX_ACCT_PORT_PROP_S.PK` attaches condition rows. Condition
columns include instrument type, portfolio, deal treatment, counterparty, collateral indicator,
strategy, structure and trade subtype.

A property can have multiple condition rows. The Tier 1 profile shows many valid Portfolio Properties
with five condition rows and five distinct condition types, including instrument-type and strategy
conditions. Therefore "one valid condition" must mean one effective portfolio-property rule set, not
one condition row.

`[confirmed: DB]` `T_BOX_ACCT_LIST_COND_S.FK_CONDITION` identifies a condition definition in
`T_BOX_CONDPAR_PROP_S`. `TYPE_COND=1` definitions are direct parameter conditions, including
Instrument Type, Portfolio, Strategy, Collateral Indicator, Entity, Deal Treatment and Structure
Indicator. `TYPE_COND=0` definitions carry a configured function name, including residency, option
class/underlying, delivery/cash, commodity, local economic sector and loan/borrower currency tests.

`[confirmed: DB]` `T_BOX_CONF_LO_PROP_S` is a branch/group × instrument local-property configuration
header. It includes distinct FRA "Conditions Portfolio Properties" entries for Spain and London, so
condition configuration is product/branch-context-specific. `[confirmed: DB]` it does not directly
parent `T_BOX_ACCT_PORT_PROP_S`: every supplied `CONF_LO_PROP → PORT_PROP.FK_PARENT` aggregate is zero.

`[confirmed: code + DB]` Relevant Condition Portfolio link rows provide the indirect condition-definition
bridge: `T_BOX_CONF_LO_PROP_S.PK → T_BOX_LINK_ARRAY_X.FK_PARENT`, then
`T_BOX_LINK_ARRAY_X.FK_BS → T_BOX_CONDPAR_PROP_S.PK`. The Tier 1 extract confirms direct parameter
links such as Strategy and function links such as local economic sector, buy/sell, OTC option class,
delivery/cash, loan/borrower currency, quote-currency and residency. Local Properties therefore select
available condition definitions for a branch/instrument context; they are not the Portfolio Property
header. Not every Link Array row is a condition-definition row: other extensions return no Condition
Portfolio definition and must not be interpreted as one.

`[proposed: BOX developer explanation]` Portfolio Properties operate as competing condition rule sets
and the runtime applies exactly one best match. `[open-question]` The runtime evaluator still needs
code or runtime evidence for AND/OR semantics within a rule set, best-match priority/scoring,
zero-match handling and fallback.

## 3. Topic-to-account configuration `[confirmed: code + DB]`

`T_BOX_ACCT_TOPICS_S` defines accounting-topic identities. The actual configuration mapping is:

```text
Portfolio Property PK
→ T_BOX_ACCT_LIST_TOPIC_S.FK_PARENT
→ FK_TOPIC → T_BOX_ACCT_TOPICS_S
→ FK_GLTA → T_BOX_ACCT_GLTA_S
```

A topic is the reusable accounting concept; its GLTA account is selected by the effective
Portfolio Property configuration. Portfolio-property selection and GLTA values are accounting-user/
SIGOM-owned configuration, not universal-library facts.

## 4. Internal GLTA account `[confirmed: DB; reporting semantics open]`

`T_BOX_ACCT_GLTA_S` contains a real account with `CODE=INTERNAL`, `SHORTNAME=Internal` and
`DESCRIPTION=Internal Account`. Its `HOSTINTERFIND` value is 0 and it has no parent account, branch
group or FX-adjustment relation in the supplied row. This confirms INTERNAL is a genuine GLTA account
identity used for internal accounting treatment. `[open-question]` The code/UI semantics of
`HOSTINTERFIND`, `FK_GLTATYPE`, `FK_DIRECTION` and `BYKEY` are still required before claiming precisely
how INTERNAL is excluded from external reporting or affects account-key creation.

## 5. Runtime account key `[confirmed: DB]`

`T_BOX_ACCT_KEY_S` holds the effective runtime accounting identity. It includes branch, currency,
instrument, folder, entity, registry, properties, topic, account strategy, source currency and the
resolved GL account. It is the bridge between configured topic/account treatment and
balances/movements.

## 6. Accounting Document `[confirmed: DB]`

`T_BOX_ACCT_DOC_S` is the active trade-level accounting container. The 27-AUG-26 IRS sample proves
`T_BOX_ACCT_MOV_S.FK_PARENT → T_BOX_ACCT_DOC_S.PK`: all 500 movement rows join a document, all 500
have `MC_CANCEL=0`, and every document `FK_TRADEEVENT` equals the movement `FK_REGISTRY`. The sample
has 99 documents for 500 movements. Document codes/descriptions identify the trade accounting container
(e.g. `IRBOX...`, "Swap BOX"); documents were created before the observed posting date, so this evidence
supports reusable trade-level documents that accumulate/refer to later movements rather than a new
per-day document assumption.

## 7. Posted movement and Historic Standard `[confirmed: DB]`

`T_BOX_ACCT_MOV_S` records debit/credit local and currency amounts plus `FK_PARENT` (Accounting
Document), `FK_PROPERTIES`, `FK_TOPIC`, `FK_GLTA`, `FK_ACCT_KEY` and `FK_HISTSTDACCT`.

The 27-AUG-26 IRS sample confirms movement values match the joined key dimensions and GL account.
`FK_HISTSTDACCT → T_BOX_ACCT_HISTSTD` resolves to historic codes/descriptions including `SWMVMTM`
("Swaps - Market value deals MTM") and `SWAPCLOMTM` ("SWAP - Close Market value deals MTM").

`[confirmed: DB]` Historic Standard allocation is configured by
`T_BOX_ACCT_BY_STD_HIST_S.FK_PARENT → PGT_PRC.T_PGT_EVE_S.PK` and
`FK_HISTSTDACCT → T_BOX_ACCT_HISTSTD.PK`. The 36-row Tier 1 mapping proves one accounting event can
have multiple Historic Standards: event `1.21` has `MMMVMTM` and `MMREVMTM` mappings. Most sampled
rows map an event to `MMMVMTM`. `[confirmed: DB]` `MMMVMTM` also occurs in real posted Money Market
movement rows with account keys, Portfolio Property `5.21`, topics and GLTA accounts. Consequently,
`DO_ACCOUNTING=0` in the supplied mapping rows must not be interpreted as "inactive" without its code
semantics; `FK_DIRECTION`/`DO_ACCOUNTING` runtime selection semantics remain open. `MMREVMTM` was not
observed in the first 500 configured-Historic movement rows. `T_BOX_ST_HIST_GROUP_S` exists but is not
the parent of these mapping rows through `T_BOX_ACCT_BY_STD_HIST_S.FK_PARENT`.

Historic Standard is a user-configured event allocation/provenance classification; it must not be
assumed to be the functional E-code or event name without a further source-event/stage join.

## 8. Ordered batch event execution `[confirmed: DB]`

An accounting batch grouping is a header in `PGT_PRC.T_PGT_BR_EVE_S`. Its event membership is stored
in `T_PGT_BR_EVE_EXT_S`: `FK_PARENT → grouping PK`, `EVENTCODE → T_PGT_EVE_S.PK` and
`ORDERTOEXECUTE` defines the required execution order. A grouping therefore contains one or more
configured accounting events; it is not a single event or a universal E-code.

The Tier 1 OTC example grouping `3821.65` ("BOX OTC Option - Accounting General by Book") contains
eight distinct events in orders 0-7, beginning with nominal Sell and Buy adjustments and continuing
with exercise, premium and cash treatment events. The observed group proves that the engine supports
ordered multi-event execution; a product commonly having generic and MtM groups must not be modelled
as an exactly-two-groups rule.

Each member event is defined in `T_PGT_EVE_S` and composes the Tables (`T_PGT_TABLE_S`), Fields
(`T_PGT_COLS_S`), Conditions (`T_PGT_COND_S`) and Update/Calculate (`T_PGT_UPDATE_S`) configuration
surfaces. The resulting event order is an operational dependency and must be retained in any
universalisation or post-build trace.

## 9. Runtime Event Log `[confirmed: DB schema; population pending]`

`T_PGT_EVLOG_GROUP_S` records a group execution, including group, status, start/end time, final event,
execution mode, last instruction/error and movement execution flag. The 25-27 AUG 2026 Tier 1 extract
contains real executions, including FRA attribute generation group `3617.65` and ACC initial-accounting
group `2409.65`, both executed by `GM` in Dynamic mode.

`T_PGT_EVLOG_HEADER_S` records an event execution, status, instruction, affected rows and error. The
27-AUG-26 extract includes executed MM events and their generated SELECT/instruction text. This confirms
that runtime logs expose the exact input aliases, fixed Historic/HistoricAux values, process date and
source query used by an event. It also demonstrates multiple Historic slots in one event instruction.

`[confirmed: DB]` The compact 27-AUG-26 lineage extract proves
`T_PGT_EVLOG_DETAIL_S.FK_PARENT → T_PGT_EVLOG_HEADER_S.PK`. Detail rows therefore attach to one
executed accounting-event header. They record actual procedure calls and input/output slots, not only
diagnostic text: the sample includes group-number allocation, accounting-topic resolution, local-currency
loading, twelve `PGT_PRG.Pkg_AcctGeneral.p_Put_Mov` calls and two `p_Put_Nivelacion` calls. Small
examples cover a one-row Net Cash Flows event, seven-row MM premium-cancellation reclassification events
and an eight-row revaluation event.

`[open-question]` In the supplied header rows, `FK_GROUP` is null and `HEADER.FK_PARENT` is not found
as a same-window `T_PGT_EVLOG_GROUP_S.PK`; do not assert the Group Log → Header parent join. The
Detail → Header link is proved, but runtime correlation from a header to dispatcher/group execution and
posted movements remains open.

## 10. Agent and acceptance implication

The required post-build trace is:

```text
deal context → effective instrument type → effective Portfolio Property
→ topic → GLTA → account key → Historic Standard → posted movement
```

The Matrix Agent proposes universal events/topics only. Accounting users approve Portfolio Property
and topic-to-GLTA configuration. The Reconciliation & Acceptance Agent validates the full effective
path against target-product runtime evidence.
