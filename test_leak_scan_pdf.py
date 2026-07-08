"""G6 — the leak-scan must also see INSIDE PDFs (and flag other binaries).

The bash leak-scan greps text files only (`grep -I` skips binaries; `--include` lists md/txt/...).
So a PDF in the IP zone is invisible to it. G6 adds PDF-text scanning; the load-bearing part is the
token matcher (a false negative = a leak), so it is pinned here. Word-bounded + case-insensitive.
"""
from leak_scan_pdf import tokens_pattern, hits_in_text


def test_denylist_token_caught_word_bounded_and_case_insensitive():
    pat = tokens_pattern(["SECRETBANK"])
    assert hits_in_text("the SECRETBANK ledger", pat) == ["SECRETBANK"]
    assert hits_in_text("lowercase secretbank too", pat) == ["secretbank"]      # case-insensitive
    assert hits_in_text("secretbankers is a different word", pat) == []         # word-bounded
    assert hits_in_text("a generic sentence about swaps", pat) == []


def test_comments_and_blanks_in_denylist_are_ignored():
    pat = tokens_pattern(["# a comment", "", "ACME"])
    assert hits_in_text("ACME books here", pat) == ["ACME"]
    assert hits_in_text("nothing about a comment", pat) == []
