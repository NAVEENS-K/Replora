from replora.decision import decide


def test_safe_reply():
    assert decide(92, 4, []).label == "SAFE TO SUGGEST"


def test_review_reply():
    assert decide(82, 25, []).label == "NEEDS REVIEW"


def test_high_risk_reply():
    assert decide(80, 65, ["I processed your refund", "You will receive it tomorrow"]).label == "DO NOT SUGGEST"


def test_critical_validation_overrides_high_quality():
    report = {"contradictions": ["Generated state conflicts with customer state."], "forbidden_claims": [], "security_issues": []}
    assert decide(95, 15, ["Your order has arrived."], report).label == "DO NOT SUGGEST"


def test_security_issue_blocks_suggestion():
    report = {"contradictions": [], "forbidden_claims": [], "security_issues": ["Potential password request"]}
    assert decide(98, 5, [], report).label == "DO NOT SUGGEST"
