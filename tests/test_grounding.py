from replora.grounding import analyze_grounding, split_claims


def test_claim_split():
    assert len(split_claims("Thanks. We can help. Please send your ID.")) == 3


def test_unsupported_commitment_is_flagged():
    reply = "I have processed your refund. You will receive it within 5 business days."
    unsupported, covered, total = analyze_grounding(reply, "Can I get a refund?", [])
    assert len(unsupported) == 2
    assert covered < total
