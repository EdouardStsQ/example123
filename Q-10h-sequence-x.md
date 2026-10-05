# Q-10h — `PGT_SYS.F___SEQUENCE` (Tier 2 PRE)

- **Source:** operator, 2026-10-05 — `ALL_SOURCE` of `PGT_SYS.F___SEQUENCE` in **Tier 2** (54 lines) and **Tier 1** (53 lines,
  same code — Tier 2 has one trailing blank line), screenshots; one call in Tier 2.

| What | Read |
|---|---|
| Signature | `F___SEQUENCE(Table_Name VARCHAR2, Seq_Range VARCHAR2, SigomSeq NUMBER DEFAULT 0) RETURN NUMBER` |
| Body | `SigomSeq = 0` → `SELECT SPK_<TABLE>.NextVal FROM DUAL`, else `SELECT <TABLE>$S.NextVal FROM DUAL` (dynamic SQL); returns it; `-20001` if NULL or on any error |
| `Seq_Range` | **not used** (nor the declared `dAuthCode`) — no auth-code fraction is ever added |
| Call | `F___SEQUENCE('PGT_DOMAINS','X')` → **24042** (integer) |

**Not the same function as `BOX_FE.F___SEQUENCE`** (Q-G3), which adds the fraction for `'X'`. The Label Config screen's
`NNNNN.44` PKs (Q-10g) therefore get their fraction after this call `[inferred]` — **and so do Tier 1's**: the same
function there returns integers too, yet Tier 1 labels carry `.21` (e.g. `1004.21`, MBJ evidence). The skill adds it the way
`BOX_FE.F___SEQUENCE` does — `AUTH_CODE` from `GOM_GLB_SYS.T__CORE_INFO_S`, `/ 10^length` — and checks it is the run's
auth code (44). Sequence values are not ordered (24044 on 10-02, then 24038, 24039, 24042): gaps and order don't matter;
the proposal checks each PK is unused.
