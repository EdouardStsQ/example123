"""G2 — the deterministic token floor must cover the PROSE / MARKDOWN lane, not only tables.

ingest_verify originally scanned PDF *tables* and CSVs. Docling-normalized output (Word/PPT/PDF
prose) and raw .md sources had NO deterministic floor — they leaned only on DeepEval. G2 adds a
text lane so every format has a deterministic denominator.
"""
from ingest_verify import source_tokens_text, code_tokens


def test_text_lane_extracts_code_tokens_from_prose(tmp_path):
    p = tmp_path / "doc.md"
    p.write_text(
        "The MTM_FULL event and ACCRUAL_PAYLEG follow IAS39. Ordinary prose words are ignored.",
        encoding="utf-8",
    )
    toks = source_tokens_text(str(p))
    assert {"MTM_FULL", "ACCRUAL_PAYLEG", "IAS39"} <= toks
    assert "Ordinary" not in toks and "event" not in toks


def test_run_on_pseudo_tokens_from_bad_pdf_extraction_are_rejected():
    # pdfplumber on a poor text layer glues words with no spaces; the giant string is an extraction
    # ARTIFACT, not a real code-token, and must not pollute the floor's denominator (caused a bogus
    # 46% on Accounting_Posting.pdf). Real codes are short.
    runon = "AReversalPostingiscreatedbycloningthePostingtobereversed"  # 56-char artifact
    assert runon not in code_tokens(runon)
    assert "ACCRUAL_REAL_MTM_CLOSING" in code_tokens("posts ACCRUAL_REAL_MTM_CLOSING daily")
