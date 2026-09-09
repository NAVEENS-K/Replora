from replora.validation import validate_reply


def test_supported_reply_passes_validation():
    report = validate_reply(
        "Sorry about the duplicate charge. Please send your transaction ID so we can investigate.",
        "I was charged twice for my subscription.",
        ["Please send the transaction ID for the duplicate payment so we can investigate."],
        ["acknowledge duplicate charge", "request transaction ID", "investigate duplicate payment"],
        ["refund already processed", "refund guaranteed"],
    )
    assert not report.critical
    assert report.validation_score >= 80


def test_forbidden_operational_claim_is_critical():
    report = validate_reply(
        "I have processed your refund. You will receive it tomorrow.",
        "Can I get a refund?",
        [],
        [],
        ["refund already processed", "specific refund date"],
    )
    assert report.forbidden_claims
    assert report.validation_score < 50
    assert report.critical


def test_security_secret_request_is_critical():
    report = validate_reply(
        "Please send your password so I can restore access.",
        "I forgot my password.",
        [],
    )
    assert report.security_issues
    assert report.critical


def test_missing_required_point_is_reported():
    report = validate_reply(
        "Sorry about the duplicate charge. We can help with the refund.",
        "I was charged twice.",
        ["We can investigate the duplicate payment."],
        ["acknowledge duplicate charge", "request transaction ID"],
    )
    assert any(x.status == "MISSING" for x in report.required_points)


def test_contradiction_is_detected():
    report = validate_reply(
        "Your order has arrived and was delivered.",
        "My order hasn't arrived yet. The tracking page still says it is in transit.",
        [],
    )
    assert report.contradictions
    assert report.critical


def test_paraphrase_is_not_rejected():
    report = validate_reply(
        "Please provide the transaction ID so we can investigate the duplicate payment.",
        "I was charged twice.",
        ["Please send the transaction ID for the duplicate payment so we can investigate."],
        ["request transaction ID", "investigate duplicate payment"],
    )
    assert not report.critical
