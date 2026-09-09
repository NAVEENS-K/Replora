from replora.decision import decide


def test_safe_reply():
    assert decide(92, 4, []).label == "SAFE TO SUGGEST"


def test_review_reply():
    assert decide(82, 25, []).label == "NEEDS REVIEW"


def test_high_risk_reply():
    assert decide(80, 65, ["I processed your refund", "You will receive it tomorrow"]).label == "DO NOT SUGGEST"
