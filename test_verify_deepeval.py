"""G5 — the DeepEval semantic layer needs an API key for the judge. Without it the layer must be
SKIPPED in a LOUD, unambiguous degraded mode (not reported as a pass), so the deterministic floor is
known to be carrying the gate. This pins the availability decision.
"""
from verify_deepeval import semantic_available


def test_semantic_layer_requires_an_api_key():
    assert semantic_available({}) is False
    assert semantic_available({"ANTHROPIC_API_KEY": ""}) is False      # empty == not configured
    assert semantic_available({"ANTHROPIC_API_KEY": "sk-ant-xxx"}) is True
