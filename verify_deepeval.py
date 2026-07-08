#!/usr/bin/env python3
"""verify_deepeval.py — semantic completeness gate (ADOPTED: DeepEval SummarizationMetric).

The prose/PDF lane of the verify gate. Uses DeepEval's SummarizationMetric = min(alignment, coverage)
with OUR OWN Claude as the local judge (no third-party cloud). The decisive part is that we SEED it
with our deterministic checklist (the assessment_questions produced by ingest_inventory.py) so the
coverage check is EXHAUSTIVE over every must-preserve accounting element — not DeepEval's default
sample of ~5 auto-generated questions. Each seeded question the SOURCE answers "yes" but the wiki
page answers "no" is an OMISSION, caught and named.

This catches what the deterministic floor (ingest_verify.py) cannot: elements COMPRESSED to prose
(token still present but no longer a faithful table). Pandera gates the structured/tabular lane.

Usage:
    ANTHROPIC_API_KEY=...  verify_deepeval.py <questions.json> <source_text> <wiki1.md> [wiki2.md ...]
Env: GATE_THRESHOLD (default 0.90), JUDGE_MODEL (default claude-sonnet-4-6), MAX_QUESTIONS (cap for a
     cheap demo run). Exit 1 if score < threshold.
"""
import json
import os
import sys

from deepeval.test_case import LLMTestCase  # no API needed to import/construct


def semantic_available(env=None):
    """G5: the DeepEval semantic layer can only run with an API key for the judge. Without it the
    layer is SKIPPED (LOUD degraded mode) and the deterministic floor + positional gate must carry
    the gate — a skip is never reported as a pass."""
    env = os.environ if env is None else env
    return bool(env.get("ANTHROPIC_API_KEY"))


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    qpath, srcpath, wikis = sys.argv[1], sys.argv[2], sys.argv[3:]
    questions = json.load(open(qpath, encoding="utf-8"))
    cap = int(os.environ.get("MAX_QUESTIONS", "0"))
    if cap:
        questions = questions[:cap]
    source = open(srcpath, encoding="utf-8").read()
    wiki = "\n\n".join(open(w, encoding="utf-8").read() for w in wikis)
    tc = LLMTestCase(input=source, actual_output=wiki)  # constructs the case (validates wiring)

    if not semantic_available():
        print("⚠️  MODO DEGRADADO — capa semántica DeepEval NO ejecutada (falta ANTHROPIC_API_KEY).")
        print("   La completitud semántica (elementos COMPRIMIDOS a prosa) NO queda verificada;")
        print("   el gate lo cubren SOLO el floor determinista + posicional + Pandera. NO es un PASS.")
        print(f"   (harness OK: {len(questions)} preguntas sembradas · fuente {len(source):,} · wiki {len(wiki):,} chars)")
        print("   Para verificar de verdad:  ANTHROPIC_API_KEY=…  python3 scripts/verify_deepeval.py "
              f"{qpath} {srcpath} {' '.join(wikis)}")
        return 0

    from deepeval.models import AnthropicModel
    from deepeval.metrics import SummarizationMetric
    judge = AnthropicModel(model=os.environ.get("JUDGE_MODEL", "claude-sonnet-4-6"), temperature=0)
    threshold = float(os.environ.get("GATE_THRESHOLD", "0.90"))
    metric = SummarizationMetric(
        threshold=threshold, model=judge,
        assessment_questions=questions, include_reason=True, verbose_mode=True,
    )
    metric.measure(tc)
    print(f"\nscore: {metric.score}  (umbral {threshold})")
    print(f"reason: {metric.reason}")
    passed = (metric.score or 0) >= threshold
    print("GATE:", "✓ PASA" if passed else "✗ BLOQUEA (omisiones detectadas — ver arriba)")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
