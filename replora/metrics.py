"""Small dependency-free metrics used by the Hiver evaluation harness."""
from __future__ import annotations

import math
from collections import Counter


def accuracy(gold: list[str], predicted: list[str]) -> float:
    if not gold or len(gold) != len(predicted):
        return 0.0
    return sum(a == b for a, b in zip(gold, predicted)) / len(gold)


def macro_f1(gold: list[str], predicted: list[str]) -> float:
    labels = sorted(set(gold) | set(predicted))
    if not labels:
        return 0.0
    scores = []
    for label in labels:
        tp = sum(g == label and p == label for g, p in zip(gold, predicted))
        fp = sum(g != label and p == label for g, p in zip(gold, predicted))
        fn = sum(g == label and p != label for g, p in zip(gold, predicted))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(scores) / len(scores)


def binary_f1(gold: list[bool], predicted: list[bool]) -> float:
    tp = sum(g and p for g, p in zip(gold, predicted))
    fp = sum((not g) and p for g, p in zip(gold, predicted))
    fn = sum(g and (not p) for g, p in zip(gold, predicted))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def spearman(x: list[float], y: list[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    def ranks(values):
        ordered = sorted(enumerate(values), key=lambda item: item[1])
        out = [0.0] * len(values)
        i = 0
        while i < len(ordered):
            j = i
            while j + 1 < len(ordered) and ordered[j + 1][1] == ordered[i][1]:
                j += 1
            rank = (i + j + 2) / 2
            for k in range(i, j + 1):
                out[ordered[k][0]] = rank
            i = j + 1
        return out
    return _pearson(ranks(x), ranks(y))


def _pearson(x, y) -> float:
    mx, my = sum(x) / len(x), sum(y) / len(y)
    dx = [v - mx for v in x]
    dy = [v - my for v in y]
    denom = math.sqrt(sum(v * v for v in dx) * sum(v * v for v in dy))
    return sum(a * b for a, b in zip(dx, dy)) / denom if denom else 0.0


def cohens_kappa(gold: list[str], predicted: list[str]) -> float:
    if len(gold) != len(predicted) or not gold:
        return 0.0
    n = len(gold)
    observed = sum(a == b for a, b in zip(gold, predicted)) / n
    labels = set(gold) | set(predicted)
    expected = sum(
        (gold.count(label) / n) * (predicted.count(label) / n)
        for label in labels
    )
    return (observed - expected) / (1 - expected) if expected < 1 else 1.0


def distribution(labels: list[str]) -> dict[str, int]:
    return dict(Counter(labels))
