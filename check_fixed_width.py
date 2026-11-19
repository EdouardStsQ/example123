#!/usr/bin/env python3
"""
check_fixed_width.py - is a fixed-width report file exactly what its layout says? (box-report-migration-agent, ADR 0028)

    python3 scripts/check_fixed_width.py <file> --layout runs/<BRANCH>/branch/reports/<report>/layout.csv
        [--out <report.md>] [--max-errors 20]

Every record must be exactly the layout's length (the newline excluded) and every field must hold an allowed value,
left-aligned, right-padded with spaces. A record a few characters short whose last field is complete once padded is
reported as `trimmed` - the usual cause is a spool with TRIMSPOOL ON, which removes the trailing spaces.

The report gives counts only: per field the distinct values and how often each occurs (a `sensitive` field - trade id,
GL account - only its number of distinct values), byte-identical duplicate records, line endings, and the first
errors (line number, field, why; a sensitive field's value never printed). It can go into a run folder; the file
itself never does (trade-level data stays local, ADR 0028). Standard library only.
Exit 0 OK · 1 FAIL (a record or field outside the layout) · 2 bad invocation / layout.
"""
from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixed_width as fw  # noqa: E402

TOP = 15


def check(path, fields, max_errors=20) -> tuple[bool, list[str]]:
    reclen = fw.record_length(fields)
    recs, facts = fw.read_records(path)
    errors, err_count = [], collections.Counter()
    dist = [collections.Counter() for _ in fields]
    lengths = collections.Counter()
    trimmed = 0
    dupes = collections.Counter(recs)

    def err(kind, msg):
        err_count[kind] += 1
        if len(errors) < max_errors:
            errors.append(msg)

    for i, rec in enumerate(recs, 1):
        lengths[len(rec)] += 1
        if len(rec) > reclen:
            err("long", f"line {i}: {len(rec)} characters, layout {reclen}")
            continue
        if len(rec) < reclen:
            padded = rec + " " * (reclen - len(rec))
            if fw.field_problem(fields[-1], fw.split(padded, fields)[-1]) is None and rec.rstrip(" ") == rec:
                trimmed += 1
                err("trimmed", f"line {i}: {len(rec)} characters - trailing spaces removed (spool TRIMSPOOL ON?)")
            else:
                err("short", f"line {i}: {len(rec)} characters, layout {reclen}")
            rec = padded
        for f, raw, d in zip(fields, fw.split(rec, fields), dist):
            v = fw.value(raw)
            d[v] += 1
            why = fw.field_problem(f, raw)
            if why:
                err(f"field {f.n}", f"line {i}: field {f.n} {f.name} = {fw.shown(f, v)}: {why}")

    ok = not err_count and facts["lines"] > 0
    out = [f"# Fixed-width check - `{Path(path).name}`", "",
           "| | |", "|---|---|",
           f"| Records | {facts['lines']} |",
           f"| Record length (layout) | {reclen} |",
           f"| Lengths found | {', '.join(f'{k}: {v}' for k, v in sorted(lengths.items()))} |",
           f"| CRLF line endings | {facts['crlf']} |",
           f"| Final newline | {'yes' if facts['final_newline'] else 'no'} |",
           f"| Byte-identical duplicates | {sum(c - 1 for c in dupes.values() if c > 1)} extra record(s) in "
           f"{sum(1 for c in dupes.values() if c > 1)} group(s) |",
           f"| Trimmed records (TRIMSPOOL) | {trimmed} |",
           f"| Errors | {sum(err_count.values())} ({', '.join(f'{k}: {v}' for k, v in sorted(err_count.items())) or 'none'}) |",
           ""]
    if errors:
        out += ["## First errors", ""] + [f"- {e}" for e in errors] + [""]
    out += ["## Values per field", "", "| # | Field | Distinct | Values (count) |", "|---|---|---|---|"]
    for f, d in zip(fields, dist):
        vals = "(sensitive - not listed)" if f.sensitive else ", ".join(
            f"{fw.shown(f, v)}: {c}" for v, c in d.most_common(TOP)) + (" …" if len(d) > TOP else "")
        out.append(f"| {f.n} | {f.name} | {len(d)} | {vals} |")
    out += ["", f"CHECK {'OK' if ok else 'FAIL'}|{facts['lines']} record(s)|{sum(err_count.values())} error(s)"]
    return ok, out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("file")
    ap.add_argument("--layout", required=True)
    ap.add_argument("--out", help="write the report here (markdown); default: print it")
    ap.add_argument("--max-errors", type=int, default=20)
    a = ap.parse_args(argv)
    try:
        fields = fw.load_layout(a.layout)
    except (fw.LayoutError, OSError) as exc:
        print(f"REFUSED layout: {exc}", file=sys.stderr)
        return 2
    if not Path(a.file).is_file():
        print(f"REFUSED file-missing: {a.file}", file=sys.stderr)
        return 2
    ok, out = check(a.file, fields, a.max_errors)
    text = "\n".join(out) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(out[-1])
    else:
        print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
