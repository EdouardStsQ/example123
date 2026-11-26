#!/usr/bin/env python3
"""
xlsx_lite.py - module (no CLI): write a simple .xlsx workbook with the standard library only (zipfile + XML).

    import xlsx_lite
    xlsx_lite.write("out.xlsx", [("Summary", [["a", "b"], [1, 2.5]]), ("Details", rows)])

One sheet per (name, rows); the first row of each sheet is the header (bold, frozen, filtered). Numbers stay numbers,
everything else is written as text (inline strings - no shared-strings table). Column widths from the content (capped).
Enough for the reports the agents produce; not a general spreadsheet library. The bank PC allows no package install.
"""
from __future__ import annotations

import re
import zipfile
from xml.sax.saxutils import escape

_BAD = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_NUM = re.compile(r"-?\d+(\.\d+)?([eE][-+]?\d+)?")


def _col(i: int) -> str:
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def _cell(ref: str, v, style: int) -> str:
    st = f' s="{style}"' if style else ""
    if isinstance(v, bool) or v is None:
        v = "" if v is None else str(v)
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return f'<c r="{ref}"{st}><v>{v}</v></c>'
    t = _BAD.sub("", str(v))
    return f'<c r="{ref}" t="inlineStr"{st}><is><t xml:space="preserve">{escape(t)}</t></is></c>'


def _sheet(rows) -> str:
    rows = [list(r) for r in rows]
    ncol = max((len(r) for r in rows), default=1)
    widths = [min(60, max([len(str(r[c])) if c < len(r) and r[c] is not None else 0 for r in rows] + [6]) + 2)
              for c in range(ncol)]
    cols = "".join(f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths))
    body = []
    for ri, r in enumerate(rows, 1):
        cells = "".join(_cell(f"{_col(ci)}{ri}", v, 1 if ri == 1 else 0) for ci, v in enumerate(r))
        body.append(f'<row r="{ri}">{cells}</row>')
    last = f"{_col(ncol - 1)}{max(1, len(rows))}"
    pane = ('<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" '
            'state="frozen"/></sheetView></sheetViews>')
    flt = f'<autoFilter ref="A1:{last}"/>' if len(rows) > 1 else ""
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'{pane}<cols>{cols}</cols><sheetData>{"".join(body)}</sheetData>{flt}</worksheet>')


def write(path, sheets) -> None:
    """sheets: [(name, rows)]; names are cut to 31 characters and made unique."""
    names, seen = [], set()
    for n, _ in sheets:
        n = re.sub(r"[\[\]:*?/\\]", "_", str(n))[:31] or "Sheet"
        base, k = n, 2
        while n in seen:
            n = f"{base[:28]}_{k}"
            k += 1
        seen.add(n)
        names.append(n)
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" '
          'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
          '<Override PartName="/xl/styles.xml" '
          'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
          + "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
                    'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                    for i in range(1, len(sheets) + 1)) + '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
            'officeDocument" Target="xl/workbook.xml"/></Relationships>')
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
          + "".join(f'<sheet name="{escape(n)}" sheetId="{i}" r:id="rId{i}"/>' for i, n in enumerate(names, 1))
          + '</sheets></workbook>')
    wbrels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
              + "".join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                        f'relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
                        for i in range(1, len(sheets) + 1))
              + f'<Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/'
                '2006/relationships/styles" Target="styles.xml"/></Relationships>')
    styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              '<fonts count="2"><font><sz val="10"/><name val="Arial"/></font>'
              '<font><b/><sz val="10"/><name val="Arial"/></font></fonts>'
              '<fills count="2"><fill><patternFill patternType="none"/></fill>'
              '<fill><patternFill patternType="gray125"/></fill></fills>'
              '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
              '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
              '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
              '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>'
              '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", wbrels)
        z.writestr("xl/styles.xml", styles)
        for i, (_, rows) in enumerate(sheets, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", _sheet(rows))


def as_number(v):
    """A CSV value as a number when it is one (Spanish or plain format), else the text."""
    s = str(v if v is not None else "").strip()
    t = s.replace(" ", "")
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})*,\d+", t) or re.fullmatch(r"-?\d+,\d+", t):
        t = t.replace(".", "").replace(",", ".")
    if _NUM.fullmatch(t) and len(t.lstrip("-").split(".")[0]) <= 15:
        try:
            f = float(t)
            return int(f) if re.fullmatch(r"-?\d+", t) else f
        except ValueError:
            return s
    return s
