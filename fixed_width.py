#!/usr/bin/env python3
"""
fixed_width.py - module (no CLI): a fixed-width report's layout and its records, shared by check_fixed_width.py and
compare_fixed_width.py (box-report-migration-agent, ADR 0028). Standard library only.

A layout is a CSV with one row per field: n, name, start, end, width (1-based, inclusive positions), kind (text |
date_yymmdd), allowed (a regular expression the right-trimmed value must match in full; empty = always blank),
sensitive (yes: the value is never printed - a hash or a count only), source (where the definition comes from).
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Field:
    n: int
    name: str
    start: int
    end: int
    width: int
    kind: str
    allowed: re.Pattern
    sensitive: bool
    source: str


class LayoutError(ValueError):
    pass


def load_layout(path) -> list[Field]:
    """Read and check a layout: numbered 1..N, contiguous from position 1, width = end - start + 1."""
    rows = list(csv.DictReader(Path(path).open(encoding="utf-8")))
    if not rows:
        raise LayoutError(f"{path}: no field")
    need = {"n", "name", "start", "end", "width", "kind", "allowed", "sensitive", "source"}
    if not need <= set(rows[0]):
        raise LayoutError(f"{path}: columns {sorted(need - set(rows[0]))} missing")
    fields, pos = [], 1
    for i, r in enumerate(rows, 1):
        if None in r or any(v is None for v in r.values()):
            raise LayoutError(f"{path}: row {i}: wrong number of columns (a comma in a value? quote it)")
        try:
            n, s, e, w = int(r["n"]), int(r["start"]), int(r["end"]), int(r["width"])
        except ValueError as exc:
            raise LayoutError(f"{path}: row {i}: {exc}") from exc
        if n != i:
            raise LayoutError(f"{path}: row {i} numbered {n}")
        if s != pos or e - s + 1 != w or w < 1:
            raise LayoutError(f"{path}: field {n} {r['name']}: start {s} end {e} width {w} - expected start {pos}, "
                              "end = start + width - 1")
        if r["kind"] not in ("text", "date_yymmdd"):
            raise LayoutError(f"{path}: field {n}: kind {r['kind']!r} (text | date_yymmdd)")
        try:
            pat = re.compile(r["allowed"] or "")
        except re.error as exc:
            raise LayoutError(f"{path}: field {n}: allowed {r['allowed']!r}: {exc}") from exc
        fields.append(Field(n, r["name"], s, e, w, r["kind"], pat, r["sensitive"].strip().lower() == "yes",
                            r["source"]))
        pos = e + 1
    return fields


def record_length(fields: list[Field]) -> int:
    return fields[-1].end


def split(line: str, fields: list[Field]) -> list[str]:
    """The raw (untrimmed) slices of one record, field by field."""
    return [line[f.start - 1:f.end] for f in fields]


def value(raw: str) -> str:
    """A field's value: right-padded with spaces (RPAD), so the right spaces are padding."""
    return raw.rstrip(" ")


def field_problem(f: Field, raw: str) -> str | None:
    """Why this raw slice is not a valid value of field f, or None."""
    v = value(raw)
    if len(raw) != f.width:
        return f"width {len(raw)}, expected {f.width}"
    if v and v[0] == " ":
        return "value not left-aligned (RPAD pads on the right)"
    if not f.allowed.fullmatch(v):
        return "value outside the allowed set" if f.allowed.pattern else "value where the field is always blank"
    if f.kind == "date_yymmdd" and v:
        try:
            datetime.datetime.strptime(v, "%y%m%d")
        except ValueError:
            return "not a YYMMDD date"
    return None


def shown(f: Field, v: str) -> str:
    """A value as a report may show it: a sensitive field's value is replaced by a short hash."""
    if not f.sensitive:
        return repr(v)
    return "#" + hashlib.sha1(v.encode("utf-8")).hexdigest()[:8] if v else "''"


def read_records(path) -> tuple[list[str], dict]:
    """The records of a file (newline and a carriage return removed) and facts about its line endings."""
    data = Path(path).read_bytes()
    text = data.decode("latin-1")  # byte-for-byte: a fixed-width file is single-byte
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    crlf = sum(1 for ln in lines if ln.endswith("\r"))
    recs = [ln[:-1] if ln.endswith("\r") else ln for ln in lines]
    return recs, {"lines": len(recs), "crlf": crlf, "final_newline": text.endswith("\n")}
