# Case: EXPLAIN reproduces the trace of one BOX ACC job, with the right debit/credit sides

Covers: box-batch-jobs-agent (EXPLAIN)
Type: happy path

Fixture: [`docs/examples/gmbx3es02d07-trace.md`](../../docs/examples/gmbx3es02d07-trace.md) — the
expected answer. The CSVs it rests on are the operator's 2026-09-29 Tier 1 / Tier 2 results.

## Given (input state)

`QUESTION = GMBX3ES02D07`, `ENV = Tier 1`. The agent has the chain doc, the query catalogue, read-only
access to `cib-boxacc-dbboxacc` and `cib-boxacc-t1mdesac`, and an operator who runs J-queries and returns
CSVs. It is **not** given the worked example.

## When (action)

The agent answers the question in EXPLAIN mode.

## Then (expected outcome)

- It asks for J-E1 / J-E2 (or cites them) before naming any owner, and names **`PGT_ES`** as the Tier 1
  wrapper — not by assumption.
- L1: waits for `GMBX3ES00D02-OK` and `GMBX3ES02D06-OK`, emits `GMBX3ES02D07-OK`, with the JSON file:line.
- L2: decodes the 6 arguments — group `2735.65`, Madrid `22.21`, SWAP `20092.4`, dynamic mode, the
  book by label code — naming the spec as the source of each constant.
- L3: the 7 events **in `ORDERTOEXECUTE` order** (4117 → 3608 → 3609 → 3614 → 3611 → 4280 → 4619), with
  **names from `T_PGT_EVE_S`** — 3609.65 is "Interest Adjust Local Anti Natura", **not** "revaluation".
- L5 for 3608.65: calculation rows run **before** postings; `CAsNomSwap` is **debited** with
  `AsAdjNomDbLoc` (`MC_DRCR = 1`) and `CAsCTRNomSwap` credited. Swapping debit and credit fails the case.
- Code citations say **committed copy** (highest `r` folder) unless J-X1 was run.
- Every row is tagged CONFIRMED or INFERRED; "4117.65 creates the document 3608.65 needs" is INFERRED.
- No book description, portfolio name or developer ID appears in the answer.
