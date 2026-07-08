"""G1 — positional (cell-tuple) verification for the ingest gate.

The dominant ingest failure for accounting matrices is NOT a missing token but a token that is
PRESENT BUT MISPLACED (a GL account rendered under the wrong axis). Token-presence checks are blind
to it because the value MULTISET is unchanged (proven in arch-val/exp1). These tests pin the
behaviour that the gate compares positional (key -> value) tuples, not just value presence.
"""
import json

from verify_positional import diff_positional, fill_grid, markdown_to_grid, diff_rows, verify


def test_misplaced_value_detected_even_when_value_multiset_is_identical():
    # two concept x axis keys resolving to two different GL accounts
    source = {
        ("InterestExp", "Hedge", "Divisa/Euro"): "925238",
        ("InterestExp", "Hedge", "Divisa/Divisa"): "925241",
    }
    # the wiki rendering swapped the two accounts: BOTH still present, wrong positions
    rendered = {
        ("InterestExp", "Hedge", "Divisa/Euro"): "925241",
        ("InterestExp", "Hedge", "Divisa/Divisa"): "925238",
    }
    # a token/value-only check is provably blind here — the multisets are identical:
    assert sorted(source.values()) == sorted(rendered.values())

    discrepancies = diff_positional(source, rendered)

    assert discrepancies, "positional gate must flag the misplacement"
    assert any("925238" in d for d in discrepancies)
    assert any("925241" in d for d in discrepancies)


def test_vertical_merged_range_forward_fills_anchor_value():
    # merged-cell ranges (from ingest_xlsx merges.json) are the forward-fill ground truth:
    # the anchor (top-left) value fills the whole range; continuation cells are blank in the CSV.
    grid = [
        ["IRS", "Notional", "925238"],
        ["",    "Coupon",   "925241"],
        ["",    "Reset",    "925239"],
    ]
    filled = fill_grid(grid, ["A1:A3"])  # column A, rows 1-3, merged
    assert [row[0] for row in filled] == ["IRS", "IRS", "IRS"]
    assert [row[1] for row in filled] == ["Notional", "Coupon", "Reset"]  # other cols untouched


def test_blank_cell_outside_any_merge_is_not_filled():
    # over-filling would INVENT data; only merged ranges fill.
    grid = [["IRS", ""], ["", "X"]]
    filled = fill_grid(grid, ["A1:A2"])  # only column A is merged
    assert [row[0] for row in filled] == ["IRS", "IRS"]
    assert filled[0][1] == ""  # B1 is blank and not in any merge -> stays blank


def test_markdown_table_parses_to_grid_skipping_separator():
    md = (
        "| Subproduct | Concept | Account |\n"
        "|---|---|---|\n"
        "| IRS | Notional | 925238 |\n"
        "| IRS | Coupon | 925241 |\n"
    )
    assert markdown_to_grid(md) == [
        ["Subproduct", "Concept", "Account"],
        ["IRS", "Notional", "925238"],
        ["IRS", "Coupon", "925241"],
    ]


def test_diff_rows_flags_dropped_leg_as_missing_row():
    source = [["IRS", "Notional", "925238"], ["IRS", "Coupon", "925241"]]
    rendered = [["IRS", "Notional", "925238"]]  # the Coupon leg vanished
    assert any("925241" in x for x in diff_rows(source, rendered))


# --- the headline: end-to-end gate reproduces & blocks the three EXP-1 corruptions ---

_CSV = "Subproduct,Concept,Account\nIRS,Notional,925238\n,Coupon,925241\n,Reset,925239\n"
_MERGES = {"merged_ranges": ["A2:A4"]}  # Subproduct merged down its data rows = forward-fill truth


def _source(tmp_path):
    (tmp_path / "m.csv").write_text(_CSV, encoding="utf-8")
    (tmp_path / "m.merges.json").write_text(json.dumps(_MERGES), encoding="utf-8")
    return str(tmp_path / "m.csv"), str(tmp_path / "m.merges.json")


def _wiki(tmp_path, body):
    p = tmp_path / "page.md"
    p.write_text("| Subproduct | Concept | Account |\n|---|---|---|\n" + body, encoding="utf-8")
    return str(p)


def test_gate_passes_a_faithful_rendering(tmp_path):
    csvp, mp = _source(tmp_path)
    page = _wiki(tmp_path, "| IRS | Notional | 925238 |\n| IRS | Coupon | 925241 |\n| IRS | Reset | 925239 |\n")
    assert verify(csvp, mp, page) == []


def test_gate_blocks_dropped_leg(tmp_path):
    csvp, mp = _source(tmp_path)
    page = _wiki(tmp_path, "| IRS | Notional | 925238 |\n| IRS | Reset | 925239 |\n")  # Coupon leg dropped
    assert verify(csvp, mp, page)


def test_gate_blocks_misplaced_account_even_though_value_set_is_identical(tmp_path):
    csvp, mp = _source(tmp_path)
    # 925238 and 925241 swapped -> value multiset unchanged, only position differs
    page = _wiki(tmp_path, "| IRS | Notional | 925241 |\n| IRS | Coupon | 925238 |\n| IRS | Reset | 925239 |\n")
    assert verify(csvp, mp, page)


def test_gate_blocks_wrong_forward_fill(tmp_path):
    csvp, mp = _source(tmp_path)
    # the Reset leg re-pinned to the wrong subproduct (CMS instead of the merged IRS)
    page = _wiki(tmp_path, "| IRS | Notional | 925238 |\n| IRS | Coupon | 925241 |\n| CMS | Reset | 925239 |\n")
    assert verify(csvp, mp, page)
