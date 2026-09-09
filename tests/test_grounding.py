from replora.grounding import analyze_claims, analyze_grounding, split_claims


def test_claim_split():
    assert len(split_claims("Thanks. We can help. Please send your ID.")) == 3


def test_unsupported_commitment_is_flagged():
    checks = analyze_claims(
        "I have processed your refund. You will receive it within 5 business days.",
        "Can I get a refund?",
        [],
        ["refund already processed", "specific refund date"],
    )
    assert len([x for x in checks if x.status == "Unsupported"]) == 2
    assert all(x.risk == "HIGH" for x in checks)


def test_supported_claim_has_evidence():
    checks = analyze_claims("Please send your transaction ID.", "I was charged twice.", ["Please send the transaction ID so we can investigate."])
    assert checks[0].status == "Supported"
    assert checks[0].risk == "LOW"


def test_grounding_returns_claim_details():
    unsupported, covered, total, checks = analyze_grounding("Please send your transaction ID.", "I was charged twice.", ["Please send the transaction ID."])
    assert not unsupported
    assert covered == 1
    assert total == 1
    assert checks[0].status == "Supported"
