# Worked trace — one BOX ACC job, from Control-M to posted entries (GMBX3ES02D07, Tier 1)

The reference answer for [`box-batch-jobs-agent`](../../agents/box-batch-jobs-agent/AGENT.md) EXPLAIN
mode, and the fixture of eval case
[`box-batch-jobs-agent-explain`](../../evals/cases/box-batch-jobs-agent-explain.md). Traced by hand
2026-09-29 (operator's Tier 1 and Tier 2 queries + Devin reading the repos). The mechanism it exercises
is [`box-batch-chain.md`](../reference/job-chains/box-batch-chain.md). The book is written
`<BOOK_CODE>` (label code only; its description is not reproduced).

**Question:** *what does job `GMBX3ES02D07` run?* · **Environment:** Tier 1 (Madrid).

## Answer in one paragraph

`GMBX3ES02D07` is **step 7 of the IRS/SWAP chain for one Madrid book** (`GMBX` BOX · `3` IRS ·
`ES02` book label 02 · `D07` step). When the common step `GMBX3ES00D02` and the previous step
`GMBX3ES02D06` are OK, Control-M runs it; its `db.conf` line runs group **2735.65 "BOX SWAP -
Accounting General by Book"** for Madrid, SWAP, that book and the process date. The group's 7 events
first create the accounting document, then post the swap **nominal adjustment**, the **anti-natura
interest adjustment**, **premium pay / receive**, and **premium cancellations and their
reclassification** — each as balanced debit/credit pairs written by `BOX_ACC.Pkg_AcctGeneral.p_Put_Mov`.
It then emits `GMBX3ES02D07-OK`.

## Level by level

| Level | Value | Key to the next level | Evidence | |
|---|---|---|---|---|
| L1 Schedule | `Job:Script`, `/appl/gm/scripts/GMBX3ES02D07`, arg `%%$ODATE`; waits `GMBX3ES00D02-OK` + `GMBX3ES02D06-OK`; emits `GMBX3ES02D07-OK` | job name | `cib-boxacc-t1mdesac.json:5674-5719` | CONFIRMED |
| L2 Step | `PGT_ES.Pkg_GMBatchprocess.f_ExecuteGroup(2735.65, CST_PK_BRANC_MAD, to_date('$ODATE','YYYYMMDD'), CST_PK_SWAP, CST_PK_DINAMIC, BOX_SYS.PKG_BOXUTILITY.f_getPKByLabel('<BOOK_CODE>'))` | 1st argument = group | `db.conf` (Tier 1), operator | CONFIRMED |
| | arguments decoded: branch `22.21` (Madrid), instrument `20092.4` (SWAP), book by label code | — | `PGT_ES.PKG_GMBATCHPROCESS` spec lines 11, 39, 1535-1542 | CONFIRMED |
| | mode `CST_PK_DINAMIC = 0` (`P_VSTATIC` 0 = dynamic; `CST_PK_STATIC = 1`) | — | Tier 1 value from Devin's spec extract; names from Tier 2 spec lines 74-75 | CONFIRMED (Tier 1 line not seen) |
| L3 Group | `2735.65` "BOX SWAP - Accounting General by Book", 7 events | `EVENTCODE` | J-C2, Tier 1 and Tier 2 (identical) | CONFIRMED |
| L4 Event query | e.g. 3608.65 reads `BOX_FE.T_BOX_IRDATADEAL_S` + `BOX_FE.T_BOX_IRFINANCST_S` (loan and borrow legs), `WHERE` branch = `#BRANCH#`, label = `#LABEL#`, date = `#EV_DATE#`, `FK_STATUS = 96.4`, `FK_ACCTDOC IS NOT NULL` | event PK | repo snapshot `001-data_eventsheader_360865.sql:288-345` (via Devin) — **not yet J-C4 live** | CONFIRMED (committed copy) |
| L5 Entries | calculation rows first, then posting pairs (below) | `TXFUNCNAME` | J-C3 Tier 1; order rule `pkg_batchprocess_mbj_body.sql:1037-1043` | CONFIRMED |
| L6 Code | `BOX_ACC.Pkg_AcctGeneral.p_Put_Mov`: `MC_DRCR` 1 → debit, 0 → credit, inserted into `T_BOX_ACCT_MOV_S` | — | `r0.0.38/…/000-pkg_acctgeneral_body.sql:284-290, 411-456` | CONFIRMED (committed copy) |

## The 7 events (J-C2 — identical in Tier 1 and Tier 2)

| Order | Event | Name (`T_PGT_EVE_S.NAME`) | Instrument | Update rows | Procedures (repo snapshot) |
|---|---|---|---|---|---|
| 0 | `4117.65` | BOX Generic Accounting document | — (generic) | 2 | `p_CreateDoc`, `p_ProcessOK` |
| 1 | `3608.65` | BOX SWAP Nominal Adjust | `20092.4` | 20 | `p_GetGroupNo`, `Pkg_IRSACCT.p_GetNominalSWAPAccount`, `p_GetSwapAdjustNominalNew`, `p_Put_Mov` |
| 2 | `3609.65` | BOX SWAP Interest Adjust Local Anti Natura (No Reval No BM) | `20092.4` | 119 | `p_Put_Nivelacion`, `p_Put_Mov` |
| 3 | `3614.65` | BOX Swap Premium - Pay Local (No Reval No BM) | `20092.4` | 38 | `p_Put_Mov`, `p_Put_Nivelacion`, `Pkg_AcctGenerAux.*` (not enumerated) |
| 4 | `3611.65` | BOX Swap Premium - Rec Local (No Reval No BM) | `20092.4` | 38 | as 3614.65 |
| 5 | `4280.65` | BOX SWAP Premium Cancelations Local NDC (No Reval No BM) | `20092.4` | 114 | `p_Put_Mov` |
| 6 | `4619.65` | BOX SWAP Premium Cancelations Reclasification - NDC | `20092.4` | 13 | `p_Put_Mov` |

`4117.65` running first fits 3608.65 requiring `FK_ACCTDOC IS NOT NULL` (the document it creates) —
`INFERRED`, not read from code.

## Event 3608.65 as entries (J-C3, Tier 1)

**Calculation rows** (run first): `p_GetGroupNo`, `p_GetNominalSWAPAccount`,
`p_GetSwapAdjustNominalNew` (twice) — they fill the accounts and the amount fields below.

**Postings** — currency `PKCurrency`, date `ProcessDate`, 16 rows = 8 balanced pairs:

| Orders | Amount field | Debit (`MC_DRCR` 1) | Credit (`MC_DRCR` 0) |
|---|---|---|---|
| 0 / 1 | `AsAdjNomDbLoc` | `CAsNomSwap` | `CAsCTRNomSwap` |
| 2 / 3 | `AsAdjNomCrLoc` | `CAsCTRNomSwap` | `CAsNomSwap` |
| 4 / 5 | `LiAdjNomDbLoc` | `CLiNomSwap` | `CLiCTRNomSwap` |
| 6 / 7 | `LiAdjNomCrLoc` | `CLiCTRNomSwap` | `CLiNomSwap` |
| 10 / 11 … 16 / 17 | the same four, `…FxLoc` | as above | as above |

In words: **asset-side and liability-side swap nominal adjustments, debit and credit, in local and FX
amounts, each against its counterpart account.**

## What differs in Tier 2 (why this trace cannot be copied)

| | Tier 1 | Tier 2 |
|---|---|---|
| Wrapper | `PGT_ES.PKG_GMBATCHPROCESS`, `f_executegroup` with `P_LABEL` / `P_SUBLABEL` | `PGT_NY.PKG_GMBATCHPROCESS`, **5 arguments, no label** |
| Group 2735.65 and its events | present | **present, identical** |
| A `db.conf` line and Control-M job for it | yes (Madrid) | none for NY (NY is not in BOX yet) |

## Open points in this trace

- L4 read from the repo snapshot; J-C4 in the live catalog not run yet.
- Procedures of 3614.65 / 3611.65 not fully enumerated (`Pkg_AcctGenerAux.*`).
- Whether the engine skips an event of another instrument (the wrapper body is not readable).
