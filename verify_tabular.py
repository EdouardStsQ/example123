#!/usr/bin/env python3
"""verify_tabular.py — Pandera plausibility lint for the structured (matrix) lane.

ADOPTED tool (Pandera, MIT, 100% local) for the tabular lane of the verify gate. It does NOT replace
the lossless XLSX extraction (that already guarantees no cell is dropped); it adds a DETERMINISTIC
PLAUSIBILITY check on the extracted cells — e.g. the debit/credit movement alphabet must be {D, H}.

Per the strategy doc, a plausibility violation (such as the source's stray "C" where "H" was meant)
is NON-BLOCKING: it is raised as an open-question for the named accounting user, never auto-corrected.

Demo: scan a CSV for single-letter movement cells and assert they are in {D, H}; report any others.

Usage: verify_tabular.py <sheet.csv> [more.csv ...]
"""
import csv
import sys

import pandas as pd
try:
    import pandera.pandas as pa
except Exception:
    import pandera as pa
from pandera.errors import SchemaErrors


def movement_cells(path):
    """Collect single-letter movement values (D/H/C/...) with their location."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for r, row in enumerate(csv.reader(fh), 1):
            for c, cell in enumerate(row, 1):
                v = (cell or "").strip()
                if len(v) == 1 and v.isalpha():
                    rows.append({"value": v, "where": f"{path.split('/')[-1]}:{r}:{c}"})
    return pd.DataFrame(rows)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    df = pd.concat([movement_cells(p) for p in sys.argv[1:]], ignore_index=True)
    if df.empty:
        print("(no se hallaron celdas de movimiento de una letra)")
        return

    schema = pa.DataFrameSchema({
        "value": pa.Column(str, pa.Check.isin(["D", "H"]), nullable=False),
        "where": pa.Column(str),
    })
    print(f"Pandera · alfabeto de movimientos esperado = {{D, H}}  ({len(df)} celdas de 1 letra)")
    try:
        schema.validate(df, lazy=True)
        print("✓ todas las celdas de movimiento son D/H (sin anomalías de plausibilidad)")
    except SchemaErrors as err:
        bad = err.failure_cases[err.failure_cases["check"].str.contains("isin")]
        print(f"⚠️  {len(bad)} celda(s) fuera de {{D,H}} → OPEN-QUESTION (no se auto-corrige):")
        # map failing row indices back to their source location
        for _, fc in bad.iterrows():
            idx = fc.get("index")
            loc = df.iloc[idx]["where"] if idx is not None and idx < len(df) else "?"
            print(f"     valor «{fc['failure_case']}» en {loc}  → ¿debería ser 'H'? (decide contabilidad)")


if __name__ == "__main__":
    main()
