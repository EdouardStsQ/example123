# BOX_FE RAW Deal, Flow and Market Data Stage

## Snapshot `[confirmed: raw Tier 1 sample]`

All three supplied samples are `Mx3EU` rows with `PROCESSDATE=26-AUG-26`. They are operational RAW
payloads before product DATADEAL/FINANCST processing; the upstream Murex-to-RAW feeder and the exact
RAW-to-DATADEAL transformation remain separate evidence questions.

| RAW table | Sample rows | Columns | Observed grain/key evidence |
|---|---:|---:|---|
| `T_BOX_RAW_DEAL_DATA_S` | 3,500 | 66 | leg-oriented deal data; 904 distinct `FRONT_ID`/`CURRENT_CONTRACT` values |
| `T_BOX_RAW_FLOW_DATA_S` | 3,500 | 31 | cash-flow data; 3,500 distinct `FRONT_ID`/`CURRENT_CONTRACT` values in the capped sample |
| `T_BOX_RAW_MARKET_DATA_S` | 3,500 | 30 | market-value data; 1,448 distinct `FRONT_ID`/`CURRENT_CONTRACT` values |

## Configured feed lineage `[confirmed: repository configuration]`

The three repositories establish this configured path:

```text
Control-M Job: APILaunchProcessAirflow.sh
→ Airflow DAG: auki_bo_sql_generic
→ hybrid Lambda SQL entry: AUKI_DEAL_DATA / AUKI_FLOW_DATA / AUKI_MARKET_DATA
→ Lambda SQL JSON: scib_auki_{deal|flow|market}_data_all.json
→ Data Lake auki/{deal|flow|market}_data/data_date_part
→ Oracle sinks T_BOX_RAW_{DEAL|FLOW|MARKET}_DATA_S
```

The Madrid migration job configuration calls `auki_bo_sql_generic` with process, dataset/alias, parquet,
load-date and Mx3EU/Book/status arguments. Airflow maps AUKI_DEAL_DATA, AUKI_FLOW_DATA and
AUKI_MARKET_DATA to their corresponding Lambda SQL JSON files. The query repository provides the actual
SELECT transformations and Oracle sink targets.

| AUKI dataset | Primary Data Lake sources | AUKI bucket table | Oracle sink |
|---|---|---|---|
| Deal | `trade_details_current`, `murex_pnl_leg_current` (plus AUKI SQL auxiliary tables) | not read in the supplied Deal Lambda SQL; it sinks directly to Oracle | `T_BOX_RAW_DEAL_DATA_S` |
| Flow | `trade_details_current`, `murex_past_flows_current`, `future_flows_current` | `scib_bu_aukibo_s3.auki_flow_data` | `T_BOX_RAW_FLOW_DATA_S` |
| Market | `trade_details_current`, `position`, `murex_pnl_current` | `scib_bu_aukibo_s3.auki_market_data` | `T_BOX_RAW_MARKET_DATA_S` |

`[confirmed: code]` Deal direction maps Murex Pay/Receive leg values to Borrower/Loan. Flow direction
maps a flow `liability_flag`: Y → Loan; otherwise → Borrower. RAW Flow Book comes from the joined trade-
details Book context, separately from the trade-details portfolio used as the Deal/FOLDER context.
`[open-question]` The Murex/other operational feeder into the Data Lake input remains outside these
repositories; this evidence proves configured AUKI extraction and RAW sinking, not the upstream origin job.

## Deal payload

RAW Deal carries source, Front ID, trade status, folder, currency, counterparty, instrument type,
trade/value/maturity dates, principal, direction, rate/index, calendars, interest type, quote reference,
book, product label and execution metadata. The sample contains IRS (3,322 rows), Commodity Swap (168),
Currency Swap (8) and Loan/Deposit (2). A Front ID can have multiple leg-oriented RAW rows.

## Flow payload

RAW Flow carries source, Front ID, currency, cash-flow type, amount, dates, rate, notional, fixing dates,
settlement/subflow, direction, current contract, execution type and book. The capped BFEE sample must
not be treated as a complete cash-flow typology catalogue.

### Targeted typology samples `[confirmed: raw Tier 1 samples]`

Additional 26-AUG-26 Mx3EU samples establish the following RAW Flow populations:

| CASHFLOWTYPE | Rows | Distinct current contracts | Label / subflow | Direction mix |
|---|---:|---:|---|---|
| `NOM` | 2,000 | 1,723 | `CAP` / `C` | Loan 1,079; Borrower 921 |
| `XIT` | 50 | 25 | `CAP` / `C` | Loan 22; Borrower 28 |
| `STL` | 1,548 | 98 | `CAP` / `C` | Loan 767; Borrower 781 |
| `RPL` | 8 | 2 | `CAP` / `C` | Borrower 8 |
| `PERF` | 2,000 | 1,814 | `REV` / `R` | Loan 1,057; Borrower 943 |
| `CPN` | 2,000 | 1,393 | `REV` / `R` | Loan 1,105; Borrower 895 |
| `IPAY` | 2,000 | 1,987 | `CAP` / `C` / `P` | Loan 846; Borrower 1,154 |
| null | 2,000 | 1,518 | mostly null / `C` | Loan 1,188; Borrower 812 |

`[confirmed: Murex + RAW]` For the Mx3EU IPAY example, Murex `TRN_HDR_DBF.M_CONTRACT=68075204` equals
both `RAW_FLOW.FRONT_ID` and `RAW_FLOW.CURRENT_CONTRACT`. The same Murex trade has a specific buy
portfolio (name omitted per your no-portfolio-names rule), while RAW Flow has a specific `BOOK` value
(also omitted). This confirms RAW `BOOK` is a separate BOX/Data Lake processing Book dimension, not the
Murex buy/sell portfolio. The source origin of cash-flow labels and the Pay/Receive-to-Loan/Borrower
direction transformation remain open.

## Processed Flow stage `[confirmed: raw Tier 1 sample]`

`T_BOX_FLOW_DATA_S` is the processed Flow layer. Its 27-AUG-26 Mx3EU sample contains 3,500 Live rows
across 305 `FRONT_ID`/`CURRENT_CONTRACT` values. 3,459 rows have `BO_SOURCE=DATALAKE`, confirming a
Data Lake-origin marker in the processed population.

Compared with RAW Flow, processed Flow has generated PKs and adds normalized/derived fields including
`STATUS`, `INPUTDATE`, `REVDATE`, `LASTCHANGE`, `AMOUNTL`, `CALENDAR`, `BASIS`, `QUOTEREFINDEX`,
`ADDFACTOR`, `PROPAGATION`, `INSTRUMENT`, `DISCOUNT_NPV`, `ACCRUAL`, `FLOW_TYPOLOGY3`, `BO_SOURCE` and
`UNDERLYINGTYPE`. Observed classifications are Interest (2,504), Nominal (461), null (438), Others Deal
Flows (59) and Dummy (38); observed `FLOW_TYPOLOGY3` values include VAR, FIX, RTRN, INIT and MID.

`[confirmed: code + DB]` `PKG_FE_FLOW_CALCULATION.p_Import_Flow_Data` merges RAW Flow into
`T_BOX_FLOW_DATA_S` and enriches processed flow values/classification. A same-date 27-AUG-26 join returns
500 matched pairs and 500 distinct processed Flow PKs. `PROCESSDATE`, `FRONT_ID`, `CURRENT_CONTRACT`,
`DIRECTION`, `CURRENCY`, `AMOUNT` and `PAYMENTDATE` are preserved in every matched pair; all processed
rows have `BO_SOURCE=DATALAKE`.

The transformation is not a simple typology rename. In the witness, raw `CPN` becomes processed
`Interest` with `FLOW_TYPOLOGY3` FIX or VAR; raw `IPAY` becomes Others Deal Flows; and raw `NOM` has
multiple outcomes including Interest/RTRN, Nominal/INIT and blank. The selected join key has 498 distinct
raw attribute combinations for 500 rows, so it is a strong correlation witness but not a complete
physical-PK lineage proof.

## Processed Deal stage `[confirmed: raw Tier 1 sample]`

`T_BOX_DATADEAL_S` is a wide processed deal/accounting-enrichment surface. Its 27-AUG-26 sample has
3,000 active-status rows over 2,855 `DEAL_ID` values and 139 columns. It includes source/front/back IDs,
accounting reference, status, folder/currency/counterparty/strategy, trade/value/maturity dates,
direction/instrument, Portfolio Property, Accounting Document, financial cash/receivable fields,
current contract, product subtype, label, revaluation/discount/accrual values and option fields.

The sample includes IRS (2,096 rows) and CCS (904), with branches 20087.4 and 22.21. This confirms
DATADEAL is a shared cross-product processing surface. `[open-question]` no same-date RAW Deal →
DATADEAL row-level join has yet been supplied.

## Shared MTM stage `[confirmed: raw Tier 1 sample]`

`T_BOX_MTM_DATA_S` is a compact shared valuation surface. Its 27-AUG-26 sample has 3,000 rows over
1,336 `DEAL_ID` values and 21 columns. It holds `NPVMAN`, `NPVACC`, BPV/risk measures, source,
propagation, currency, margin, label, direction and instrument. It contains CCS (1,713 rows), IRS
(1,284) and MM (3), with multiple valuation rows per deal. `[open-question]` no same-date RAW Market →
MTM row-level join has yet been supplied.

## Days Matured lifecycle control `[confirmed: DB]`

`BOX_FE.T_BOX_ENGDAYS_MATURED_S` configures `NUM_DAYS` by instrument, with no branch column. The full
Tier 1 extract has a value of **30 days** for every observed configured instrument: MM, Commodity Swap,
IRS, CCS, CFM, FRA, OTC Option and Cap/Floor. This is the product-level threshold used between maturity
and matured/dead processing; exact downstream state-transition package/event semantics still require code
or runtime evidence.

## Market payload

RAW Market carries product family/group/type, folder, source, market value, currency, direction,
initiator side, trade number, Front ID, contract reference, net market value, book and instrument. The
sample contains Currency Swap (2,076 rows), IRS (1,422) and Loan/Deposit (2). Multiple market rows can
exist per Front ID, including currency/direction legs.

## Manual RAW feed as a test path `[stated: BOX Lead, 2026-09-10]`

For onboarding a branch that is **already live in GBO**, testing does not require anyone to book a trade
in Murex. That branch's trades are already in the Data Lake tables, so they can be taken from there and
fed into `T_BOX_RAW_{DEAL|FLOW|MARKET}_DATA_S` manually to run technical tests of the RAW → FE → ACC
path. For NY_SCH this removes what looked like a hard external dependency (FO booking capacity in a test
environment); see `../examples/ny-sch-branch-onboarding.md` §2.

Two conditions come with it, and neither is incidental:

**The trade status will not be `BOValidated`.** That is the AUKI status; a GBO-native branch's trades in
the Data Lake carry something else. The configured extraction path above filters on it — see
`job-chains/control-m-batch-layer.md` §2, where `status_vr`/`status_native_vr` = `BOValidated` is
recorded (and, until now, described as boilerplate). Running the standard job unchanged would therefore
select **none** of the trades this test path depends on. Whether the right answer is a parameter
override, a separate test job, or a direct INSERT into RAW is undecided. `[open-question]`

**The online entry must be simulated.** The online path is what validates the accounting attributes
(strategy, portfolio properties) that accounting generation later depends on — `system-overview.md`'s
*Two Arrival Paths* states this explicitly. Feeding RAW alone bypasses that validation, so a test run
needs something standing in for it. Whether that stand-in is a test harness or evidence that the online
path is genuinely in scope for this branch is an open decision with real consequences for project size
— see `../examples/ny-sch-branch-onboarding.md` §2. `[open-question]`

**What this path does and does not prove.** It exercises the plumbing, not a production-shaped flow.
Rows arriving by hand, with a non-AUKI status and a simulated online entry, are a weaker witness than a
normal business day's feed: a downstream break could be the configuration or could be the hand-feeding.
Useful for technical validation; not sufficient for a reconciliation against the source system.
`[inferred]`

## Agent implication

BOX_FE traceability must retain separate Deal, Flow and Market RAW payloads. A product requirement may
demand one or more of these feeds, but sample co-occurrence does not prove a common row key or RAW-to-
DATADEAL/FINANCST derivation. Those joins need a targeted same-date, same-product witness.
