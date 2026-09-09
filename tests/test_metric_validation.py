from replora.evaluator import evaluate


def test_evaluator_prefers_grounded_reply_to_hallucination():
    email = "I was charged twice. Can I get a refund?"
    reference = "Sorry about the duplicate charge. Please send the transaction ID so we can investigate and help with the refund."
    key_points = ["acknowledge duplicate charge", "request transaction ID", "investigate duplicate payment"]
    strong = evaluate(email, reference, reference, key_points, [reference])
    bad = evaluate(email, "I have processed your refund and you will receive it tomorrow.", reference, key_points, [])
    assert strong.quality_score > bad.quality_score
    assert strong.risk_score < bad.risk_score
