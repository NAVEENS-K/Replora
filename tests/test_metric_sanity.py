from replora.evaluator import evaluate

EMAIL = "I was charged twice. Can you help me get the duplicate charge refunded?"
REFERENCE = "Sorry about the duplicate charge. Please send the transaction ID so we can investigate it and help with the refund."
POINTS = ["acknowledge duplicate charge", "request transaction ID", "investigate duplicate payment"]
FORBIDDEN = ["refund already processed", "specific refund date", "refund guaranteed"]
EVIDENCE = [REFERENCE]


def score(reply):
    return evaluate(EMAIL, reply, REFERENCE, POINTS, EVIDENCE, FORBIDDEN)


def test_metric_prefers_good_response_to_hallucinated_response():
    good = score(REFERENCE)
    hallucinated = score("I've processed your refund and you will receive it tomorrow.")
    assert good.quality_score > hallucinated.quality_score
    assert good.risk_score < hallucinated.risk_score
    assert good.recommendation == "✓ SAFE TO SUGGEST"
    assert hallucinated.recommendation == "✕ DO NOT SUGGEST"


def test_metric_penalizes_missing_required_information():
    complete = score(REFERENCE)
    incomplete = score("Sorry about the duplicate charge. We can help with the refund.")
    assert complete.completeness > incomplete.completeness


def test_metric_is_not_exact_match_only():
    paraphrase = score("Sorry about the duplicate payment. Please provide the transaction ID so we can investigate and assist with the refund.")
    assert paraphrase.quality_score >= 70
    assert paraphrase.recommendation != "✕ DO NOT SUGGEST"
