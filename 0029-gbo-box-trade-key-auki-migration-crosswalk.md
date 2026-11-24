# 0029. The GBO ↔ BOX trade key is the AUKI migration crosswalk, not FRONT_ID

Date: 2026-11-24
Status: accepted — supersedes the "common key = `FRONT_ID`" of `box-fe-test-lookups.md` §4 and ADR 0028 point 7

## Context

`[operator, 2026-11-24]` The IRS parallel test of 25-Sep-2026 (PRE-PARALELO) could not pair GBO trades with BOX trades.
The FE reconciliation (`fe_reconcile.py`, the field map) and the report agent (ADR 0028) both keyed trades on
`FRONT_ID`, assumed to be the id GBO and BOX share. It is not: for one IRS deal

| | GBO (`DEVENG.T_PGT_IRDATAMIS_S`) | BOX (`BOX_FE.T_BOX_DATADEAL_S`) |
|---|---|---|
| `DEAL_ID` | `40603.35` | `1680634.513` |
| `FRONT_ID` | `26420182` | `1680634` |

The link is the AUKI migration table **`BOX_MIG.T_BOX_AUKI_MIG_DEALS_S`**: `REGISTRY` = the GBO `DEAL_ID`
(`40603.35`), `FK_AUKI_ID` = the BOX `DEAL_ID` (`1680634.513`), with `PROCESS_DATE`, `FK_BRANCH_ORIGIN` (the GBO
branch, `20007.4`), `FK_BRANCH_DESTINATION`, `FK_INSTRUMENT` (the GBO instrument, `20092.4`). BOX's deal data also
carries the GBO id as text, `REFERENCE_ACCOUNTING = '40603,35'` (comma decimal) — a cross-check, not the key.

## Decision

1. **Trades are paired on the GBO `DEAL_ID`** (`GBO_DEAL_ID`): GBO's own `DEAL_ID`; BOX's `DEAL_ID` translated through
   the crosswalk (`FK_AUKI_ID` → `REGISTRY`), restricted to the branch (`FK_BRANCH_ORIGIN`) and, per BOX deal, the
   latest row up to the last date compared.
2. **Both sides write the key as text with a `.` decimal** (`TO_CHAR(x, 'TM9', 'NLS_NUMERIC_CHARACTERS=''.,''')`),
   so a Spanish-locale session or CSV export cannot break the match; the comparer also reads `40603,35` as
   `40603.35`.
3. **GBO's rows are the branch's** through its deal table (`FK_BRANCH`, `DDATE`), not a FRONT_ID join.
4. **`FRONT_ID`, `BACK_ID`, `REFERENCE_ACCOUNTING`, `FK_BRANCH` are never compared** — they differ by design.
5. **Before reading any ONLY_GBO / ONLY_BOX**, the crosswalk is checked (`sql/05-crosswalk-checks.sql`): one GBO id
   per BOX deal and back; per product and date, the BOX deals mapped to the branch and the GBO deals with a crosswalk
   row — a GBO deal with no row can only be ONLY_GBO.
6. **Field map**: role `xwalk` per product and area (deal, financial); keys `GBO_DEAL_ID` (IRS financial:
   `GBO_DEAL_ID,FK_DIRECTION,FK_CURRENCY`); BOX's shared deal table filtered by the crosswalk's GBO instrument.
7. **Report migration (ADR 0028)**: BOX can print GBO's own trade id in a report — `REGISTRY` (× 100 for GBUX field 1)
   — so the GBO and BOX files carry the same id and no id file is needed; decision D1's default changes accordingly.

## Alternatives considered

- **`REFERENCE_ACCOUNTING`** (BOX deal data, the GBO id as text): rejected as the key — a formatted string
  (`'40603,35'`), on one BOX table only; kept as a cross-check.
- **Keep `FRONT_ID`**: rejected — it identifies different things on each side.

## Consequences

- `scripts/fe_reconcile.py` (crosswalk SQL, key normalisation, duplicate keys counted, `05-crosswalk-checks.sql`,
  input `gbo_branch`, Y-test trades = GBO `DEAL_ID`s with `box_front_ids` for the trace), the field map, the lookups
  doc, the Y / parallel test skills and templates.
- **Every GBO vs BOX result paired on `FRONT_ID` is to be redone** — the 25-Sep-2026 IRS parallel test's shared /
  GBO-only / BOX-only counts and the official comparison file included.
- Open: whether the crosswalk holds every product (it carries `FK_INSTRUMENT`; confirmed for IRS), and the row grain
  of each product's deal table (IRS: two rows per deal on each side — the leg column to confirm).
