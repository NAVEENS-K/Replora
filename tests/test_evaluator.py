from replora.evaluator import evaluate


def test_good_reply_scores_well():
    email = "I was charged twice. Can you refund the duplicate?"
    reference = "Sorry about the duplicate charge. Please send the transaction ID so we can investigate and help with the refund."
    reply = reference
    result = evaluate(email, reply, reference, ["acknowledge duplicate charge", "request transaction ID", "investigate duplicate payment"], [reference])
    assert result.quality_score >= 70
    assert result.risk_score <= 20


def test_hallucinated_refund_increases_risk():
    result = evaluate(
        "I was charged twice. Can you refund the duplicate?",
        "I have processed your refund and you will receive it tomorrow.",
        "Sorry about the duplicate charge. Please send the transaction ID so we can investigate.",
        ["request transaction ID", "do not claim refund is already processed"],
        []
    )
    assert result.unsupported_claims
    assert result.risk_score > 0
