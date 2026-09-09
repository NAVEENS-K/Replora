from replora.metrics import accuracy, macro_f1, binary_f1, cohens_kappa, spearman


def test_classification_metrics():
    gold = ["a", "a", "b", "b"]
    pred = ["a", "b", "b", "b"]
    assert accuracy(gold, pred) == 0.75
    assert 0 < macro_f1(gold, pred) < 1


def test_escalation_metrics():
    gold = [True, False, True, False]
    pred = [True, False, False, False]
    assert binary_f1(gold, pred) > 0
    assert cohens_kappa(["x", "y"], ["x", "y"]) == 1.0


def test_spearman_perfect():
    assert spearman([1, 2, 3], [10, 20, 30]) == 1.0
