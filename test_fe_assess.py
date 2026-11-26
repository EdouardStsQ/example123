#!/usr/bin/env python3
"""Tests of scripts/fe_assess.py and scripts/xlsx_lite.py (the standard GBO vs BOX FE assessment, ADR 0030).
Synthetic deals reproduce each case met in the IRS parallel test of 25-Sep-2026. Standard library only."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OK = True


def report(ok, what, detail=""):
    global OK
    print(("✓ " if ok else "✗ ") + what)
    if not ok:
        OK = False
        print("    " + str(detail)[:2000])


def write(p: Path, header, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def main() -> int:
    sys.path.insert(0, str(ROOT / "scripts"))
    import xlsx_lite
    tmp = Path(tempfile.mkdtemp())

    # --- xlsx_lite ------------------------------------------------------------------------------------------------
    x = tmp / "t.xlsx"
    xlsx_lite.write(x, [("Summary", [["a", "b"], [1, 2.5], ["x<&>", None]]), ("Summary", [["c"], ["d"]])])
    with zipfile.ZipFile(x) as z:
        names = z.namelist()
        wb = z.read("xl/workbook.xml").decode()
        s1 = z.read("xl/worksheets/sheet1.xml").decode()
    report("xl/worksheets/sheet2.xml" in names and 'name="Summary"' in wb and 'name="Summary_2"' in wb
           and "<v>2.5</v>" in s1 and "x&lt;&amp;&gt;" in s1 and 'state="frozen"' in s1
           and xlsx_lite.as_number("1.234,5") == 1234.5 and xlsx_lite.as_number("14550803.44") == 14550803.44
           and xlsx_lite.as_number("abc") == "abc",
           "xlsx_lite: a valid workbook (sheets, unique names, numbers as numbers, text escaped, header frozen); "
           "Spanish-format numbers read", names)

    # --- a run: 8 deals, one per case -----------------------------------------------------------------------------
    run = tmp / "run"
    ev = run / "01-evidence/2026-09-25"
    (run / "parallel-test-inputs.json").parent.mkdir(parents=True, exist_ok=True)
    (run / "parallel-test-inputs.json").write_text(json.dumps({
        "branch": "NY_SCH", "products": ["irs"], "areas": ["financial", "deal"], "gbo_branch": "20007.4",
        "dates": ["2026-09-25"]}))
    fh = ["RECON_DATE", "GBO_DEAL_ID", "DEAL_ID", "FRONT_ID", "FK_DIRECTION", "FK_CURRENCY", "FK_INSTRUMENT",
          "NOTIONAL", "RATECUR", "INTERESTCUR", "INTERESTCASH", "INTERESTPLACC", "DEAD_DATE"]
          # GBO; BOX also has FK_INSTRUMTYPE
    g, b = [], []
    def leg(rows, box, deal, bid, dirn, ccy, inst, notl, rate, icur, icash, placc, dead):
        r = ["2026-09-25", deal, bid if box else deal, "999" if box else "111", dirn, ccy, "" if box else inst, notl,
             rate, icur, icash, placc, dead]
        rows.append(r + ([inst] if box else []))
    for dirn in ("183.4", "184.4"):
        # D1 100.35: identical
        leg(g, 0, "100.35", "", dirn, "159.4", "10146.4", "1000", "4", "10", "5", "", "06-JUN-66")
        leg(b, 1, "100.35", "1100.513", dirn, "159.4", "20092.4", "1000", "4", "10", "5", "", "")
        # D2 200.35: functional INTERESTCUR, gbo_zero RATECUR, sentinel vs maturity, by-design PLACC
        leg(g, 0, "200.35", "", dirn, "172.4", "10146.4", "1000", "0", "500", "", "1000", "06-JUN-66")
        leg(b, 1, "200.35", "1200.513", dirn, "172.4", "20092.4", "1000", "4.5", "0", "0", "", "2027-01-04")
        # D3 300.35: rebooked (capture date) - notional and cash
        leg(g, 0, "300.35", "", dirn, "159.4", "10146.4", "100", "4", "10", "0", "", "")
        leg(b, 1, "300.35", "1300.513", dirn, "159.4", "20092.4", "115.44", "4", "10", "50", "", "")
        # D5 500.35: GBO only
        leg(g, 0, "500.35", "", dirn, "159.4", "10146.4", "1", "1", "1", "1", "", "")
        # D6 600.35: no current interest flow in BOX
        leg(g, 0, "600.35", "", dirn, "159.4", "10146.4", "1", "1", "1", "1", "", "")
        leg(b, 1, "600.35", "1600.513", dirn, "159.4", "20092.4", "1", "1", "1", "1", "", "")
        # D7 700.35: an unexplained notional difference
        leg(g, 0, "700.35", "", dirn, "159.4", "10146.4", "1000", "4", "10", "5", "", "")
        leg(b, 1, "700.35", "1700.513", dirn, "159.4", "20092.4", "1250", "4", "10", "5", "", "")
        # D8 800.35: no BOX deal-data row
        leg(g, 0, "800.35", "", dirn, "159.4", "10146.4", "1", "1", "1", "1", "", "")
        leg(b, 1, "800.35", "1800.513", dirn, "159.4", "20092.4", "1", "1", "1", "1", "", "")
    # D2: BOX's all-zero USD settlement row; D4 400.35: BOX holds one direction only
    leg(b, 1, "200.35", "1200.513", "183.4", "159.4", "20092.4", "0", "0", "0", "0", "", "")
    leg(g, 0, "400.35", "", "183.4", "159.4", "10146.4", "1", "1", "1", "1", "", "")
    leg(g, 0, "400.35", "", "184.4", "159.4", "10146.4", "1", "1", "1", "1", "", "")
    leg(b, 1, "400.35", "1400.513", "183.4", "159.4", "20092.4", "1", "1", "1", "1", "", "")
    write(ev / "gbo-irs-financial.csv", fh, g)
    write(ev / "box-irs-financial.csv", fh + ["FK_INSTRUMTYPE"], b)
    dh = ["RECON_DATE", "GBO_DEAL_ID", "DEAL_ID", "FK_DIRECTION", "FK_CURRENCY", "MATURITYDATE", "CAPTUREDATE", "FK_STATUS"]
    gd, bd = [], []
    for deal, bid, gmat, bmat, gcap, bcap in (
            ("100.35", "1100.513", "2027-01-04", "2027-01-04", "2024-01-01", "2024-01-01"),
            ("200.35", "1200.513", "2027-01-04", "2027-01-06", "2024-01-01", "2024-01-01"),
            ("300.35", "1300.513", "2027-01-04", "2027-01-04", "2025-07-02", "2025-05-22"),
            ("600.35", "1600.513", "2027-01-04", "2027-01-04", "2024-01-01", "2024-01-01"),
            ("700.35", "1700.513", "2027-01-04", "2027-01-04", "2024-01-01", "2024-01-01"),
            ("800.35", "1800.513", "2027-01-04", "2027-01-04", "2024-01-01", "2024-01-01")):
        ccy = "172.4" if deal == "200.35" else "159.4"
        for dirn in ("183.4", "184.4"):
            gd.append(["2026-09-25", deal, deal, dirn, ccy, gmat, gcap, "220.4"])
            if deal != "800.35":
                bd.append(["2026-09-25", deal, bid, dirn, ccy, bmat, bcap, "96.4"])
    write(ev / "gbo-irs-deal.csv", dh, gd)
    write(ev / "box-irs-deal.csv", dh, bd)
    write(ev / "box-irs-flows.csv", ["RECON_DATE", "GBO_DEAL_ID", "N_DIRECTIONS", "N_DIR_CURRENT_INTEREST", "N_DIR_DATED"],
          [["2026-09-25", d_, "2", "1" if d_ == "600.35" else "2", "2"]
           for d_ in ("100.35", "200.35", "300.35", "600.35", "700.35", "800.35")])

    r = subprocess.run([sys.executable, str(ROOT / "scripts/fe_assess.py"), str(run)], capture_output=True, text=True)
    md = (run / "03-assessment.md").read_text() if (run / "03-assessment.md").exists() else ""
    det = (run / "local/2026-09-25-irs-details.csv").read_text() if (run / "local/2026-09-25-irs-details.csv").exists() else ""
    xl = run / "local/2026-09-25-irs-assessment.xlsx"
    report(r.returncode == 0 and "| a. same legs on both sides | 6 |" in md and "| b. every leg in both deal extracts | 5 |" in md
           and "| c. BOX current interest flow on every direction | 4 |" in md and "| CLEAN - compared | 4 |" in md
           and "| GBO only (not in BOX) | 1 |" in md and "a. legs differ - BOX lacks" in md
           and "b. deal data row missing in BOX | 1 |" in md and "c. BOX lacks the current interest flow on a direction | 1 |" in md,
           "fe_assess: the clean-set funnel - legs (BOX's all-zero row dropped first), deal data, current interest flow; "
           "every left-out deal counted per reason", r.stdout + r.stderr + md)
    report("| full match (no mismatch class) | 1 |" in md and "| rebooked deals (flagged) | 1 |" in md
           and "| full match leaving aside the functional differences | 2 |" in md
           and "300.35,1300.513,financial,183.4|159.4,NOTIONAL,100,115.44" in det and "rebooked deal" in det
           and "functional - GBO projects" in det and "explained - GBO leaves 0" in det
           and "explained - convention" in det and "explained - not calculated in BOX (by design)" in det
           and "explained - payment date vs accrual end" in det
           and "700.35,1700.513,financial,183.4|159.4,NOTIONAL,1000,1250,250,DIFF - unexplained" in det
           and "FK_INSTRUMENT" not in det and "FK_STATUS" not in det and "100.35," not in det,
           "fe_assess: rules - rename + decode (instrument), decode (status), blank = 0, the dead-date sentinel, by design, "
           "rebooked deal (capture date), GBO-zero / BOX-zero, payment lag; the rest DIFF - unexplained; full match counts",
           det)
    rows_md = [ln for ln in md.splitlines() if ln.startswith("| 1 | ")]
    sheets = zipfile.ZipFile(xl).read("xl/workbook.xml").decode() if xl.exists() else ""
    report(xl.exists() and all(f'name="{s}"' in sheets for s in ("Summary", "Issues", "Deals", "Details", "Excluded", "Rules"))
           and "700.35" not in md and "1300.513" not in md and "NOTIONAL differs - no rule explains it" in md
           and rows_md and "rebooked deal" in rows_md[0],
           "fe_assess: 03-assessment.md counts only (no deal id), rebooked first; the xlsx in local/ (Summary, Issues with "
           "examples, Deals, Details, Excluded, Rules)", md)
    (run / ".frozen").write_text("x")
    r2 = subprocess.run([sys.executable, str(ROOT / "scripts/fe_assess.py"), str(run)], capture_output=True, text=True)
    report(r2.returncode == 1 and "run-frozen" in r2.stderr, "fe_assess: a frozen run is refused", r2.stderr)

    print("\nall passed" if OK else "\nFAILURES")
    return 0 if OK else 1


if __name__ == "__main__":
    sys.exit(main())
