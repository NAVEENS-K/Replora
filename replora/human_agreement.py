"""Agreement calculations for the human-vs-LLM judge calibration sample."""
from __future__ import annotations

from .metrics import cohens_kappa, spearman


def compare_quality(human_scores: list[float], judge_scores: list[float]) -> dict:
    if len(human_scores) != len(judge_scores) or not human_scores:
        raise ValueError("Human and judge score lists must have equal non-zero length")
    return {
        "n": len(human_scores),
        "spearman_quality": spearman(human_scores, judge_scores),
        "mean_absolute_error": sum(abs(a - b) for a, b in zip(human_scores, judge_scores)) / len(human_scores),
        "exact_agreement_rate": sum(a == b for a, b in zip(human_scores, judge_scores)) / len(human_scores),
    }


def compare_escalation(human_labels: list[str], judge_labels: list[str]) -> dict:
    if len(human_labels) != len(judge_labels) or not human_labels:
        raise ValueError("Human and judge label lists must have equal non-zero length")
    return {
        "n": len(human_labels),
        "cohens_kappa": cohens_kappa(human_labels, judge_labels),
        "agreement_rate": sum(a == b for a, b in zip(human_labels, judge_labels)) / len(human_labels),
    }
