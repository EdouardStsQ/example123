#!/usr/bin/env python3
"""verify_positional.py — G1: positional (cell-tuple) verification for the ingest gate.

The deterministic floor (ingest_verify.py) catches a token that VANISHED, but is blind to a token
that is PRESENT BUT MISPLACED — e.g. a GL account rendered under the wrong axis cell, where the
value multiset is unchanged (proven in arch-val/exp1). This module compares positional
(key -> value) tuples so misplacement and silent leg-loss are caught.

See tests/test_verify_positional.py.

CLI:  python3 scripts/verify_positional.py <source.csv> <source.merges.json> <wiki-page.md>
Exit 1 if the wiki table does not reproduce the source's forward-filled rows.
"""
import collections
import csv
import json
import re
import sys

from openpyxl.utils import range_boundaries


def diff_positional(source, rendered):
    """Compare two positional maps ``{key_tuple: value}`` and return human-readable discrepancies.

    - MISPLACED: a key present in both but with a different value (the misplacement case).
    - MISSING:   a source key absent from rendered (silent leg / row loss).
    - EXTRA:     a rendered key absent from source.

    An empty list means the rendering faithfully preserves the source's positional tuples.
    """
    out = []
    for key, val in source.items():
        if key not in rendered:
            out.append(f"MISSING {key} -> expected {val!r}")
        elif rendered[key] != val:
            out.append(f"MISPLACED at {key}: expected {val!r}, found {rendered[key]!r}")
    for key, val in rendered.items():
        if key not in source:
            out.append(f"EXTRA {key} = {val!r}")
    return out


def fill_grid(grid, merged_ranges):
    """Apply Excel merged-range forward-fill (the deterministic ground truth from ingest_xlsx).

    Each merged range (e.g. "A1:A3") holds its value only in the anchor (top-left) cell in the CSV;
    the continuation cells are blank. This expands the anchor value across the whole range. Cells
    NOT inside any merged range are left exactly as-is (a blank stays blank — never invent data).
    """
    filled = [list(row) for row in grid]
    for rng in merged_ranges:
        min_c, min_r, max_c, max_r = range_boundaries(rng)
        anchor = filled[min_r - 1][min_c - 1]
        for r in range(min_r - 1, max_r):
            for c in range(min_c - 1, max_c):
                filled[r][c] = anchor
    return filled


def markdown_to_grid(md):
    """Parse a markdown table into a grid of row-cells, skipping the |---| separator row."""
    rows = []
    for line in md.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip().replace("\\|", "|") for c in line.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue  # separator row
        rows.append(cells)
    return rows


def diff_rows(source_rows, rendered_rows):
    """Compare two grids as MULTISETS of (forward-filled) rows — the unit is a leg/row.

    Robust to benign row reordering; a dropped leg -> MISSING; a misplaced or mis-filled cell
    changes its row -> that row MISSING + the corrupted row EXTRA. Empty list => faithful.
    """
    src = collections.Counter(tuple(r) for r in source_rows)
    rnd = collections.Counter(tuple(r) for r in rendered_rows)
    out = []
    for row, n in (src - rnd).items():
        out.append(f"MISSING row x{n}: {list(row)}")
    for row, n in (rnd - src).items():
        out.append(f"EXTRA row x{n}: {list(row)}")
    return out


def verify(source_csv_path, merges_path, wiki_md_path):
    """Gate: does the wiki markdown table reproduce the source's forward-filled rows?

    Returns a list of discrepancies (empty = faithful). The source CSV + merges.json come from
    ingest_xlsx (merged ranges = forward-fill ground truth); the wiki table is the rendered view.
    """
    with open(source_csv_path, encoding="utf-8") as fh:
        grid = list(csv.reader(fh))
    merged = json.load(open(merges_path, encoding="utf-8")).get("merged_ranges", [])
    source_rows = fill_grid(grid, merged)
    rendered_rows = markdown_to_grid(open(wiki_md_path, encoding="utf-8").read())
    return diff_rows(source_rows, rendered_rows)


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: verify_positional.py <source.csv> <source.merges.json> <wiki-page.md>")
    discrepancies = verify(sys.argv[1], sys.argv[2], sys.argv[3])
    if discrepancies:
        print(f"✗ GATE POSICIONAL FALLA — {len(discrepancies)} discrepancia(s) de fila:")
        for d in discrepancies:
            print("  " + d)
        sys.exit(1)
    print("✓ posicional OK — la tabla wiki reproduce las filas del source (tras forward-fill)")
    sys.exit(0)


if __name__ == "__main__":
    main()
