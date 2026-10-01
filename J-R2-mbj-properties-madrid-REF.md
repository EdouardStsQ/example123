# J-R2 — MBJ job-level rows, Madrid (Tier 1) — reference evidence

- **Source:** operator screenshot of the SIGOM `BOX - Accounting > MBJ Config` screen query, Tier 1, 2026-10-01.
- **Filter:** `T2.PK = 22.21 AND T1.FK_PARENT IS NULL AND T1.FK_OWNER_OBJ = 35000182.65` → **50 rows** (same 50
  without `FK_PARENT IS NULL` — operator); first 8 visible, columns up to the label (the rest are off-screen).
- **Not copied:** the label descriptions (book names) — the label PK is enough. Branch shown as "MADRID REAL".
- Madrid is not the proposed reference branch (SLB, open item 3); these rows document the **shape** of a row.
  Re-run J-R2 for SLB and save its CSV here as `J-R2-mbj-properties-REF.csv`.

| # | MBJ PK | Branch | Instanze | Job | Instrument | Group | Group name | Label PK |
|---|---|---|---|---|---|---|---|---|
| 1 | 700.21 | 22.21 | AUKI | GMBX4ES55D07 | 20.4 Cross Currency Swap | 3275.65 | BOX CCS - Accounting General by Book | 1004.21 |
| 2 | 701.21 | 22.21 | AUKI | GMBX4ES55D09 | 20.4 Cross Currency Swap | 3375.65 | BOX CCS - Mark to Market CorteH (Reval) | 1004.21 |
| 3 | 702.21 | 22.21 | AUKI | GMBX6ES55D07 | 20314.4 Forward Rate Agreement | 3721.65 | BOX FRA - Accounting General by Book | 1004.21 |
| 4 | 703.21 | 22.21 | AUKI | GMBX6ES55D09 | 20314.4 Forward Rate Agreement | 3741.65 | BOX FRA - Accounting Mark to Market by Book | 1004.21 |
| 5 | 704.21 | 22.21 | AUKI | GMBX7ES55D07 | 20111.4 OTC Option | 3821.65 | BOX OTC Option - Accounting General by Book | 1004.21 |
| 6 | 705.21 | 22.21 | AUKI | GMBX7ES55D09 | 20111.4 OTC Option | 3801.65 | BOX OTC - Accounting Mark to Market by Book | 1004.21 |
| 7 | 706.21 | 22.21 | AUKI | GMBX4ES56D07 | 20.4 Cross Currency Swap | 3275.65 | BOX CCS - Accounting General by Book | 1005.21 |
| 8 | 707.21 | 22.21 | AUKI | GMBX4ES56D09 | 20.4 Cross Currency Swap | 3375.65 | BOX CCS - Mark to Market CorteH (Reval) | 1005.21 |

## Read from it

- `D07` = Accounting General by Book, `D09` = Mark to Market / Reval by Book — one pair per book × product.
- Job book number ↔ label: `ES55` → `1004.21`, `ES56` → `1005.21` (label codes presumably `XES55`, `XES56`
  `[inferred]` — J-R2's `label_code` column confirms).
- Same group for every book of a product (`3275.65` for CCS D07): a new book needs new MBJ rows and jobs,
  not new groups.
- MBJ and label PKs carry `.21` — created in Madrid's auth code. NY's rows would carry Tier 2's `.44`; NY's
  labels get the fixed PKs the BOX FE team gives (skill `set-up-book-labels`).
