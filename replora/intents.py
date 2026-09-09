from collections import Counter
from .models import EmailExample


def infer_intents(examples: list[EmailExample]) -> list[str]:
    return sorted({ex.category for ex in examples})


def classify_intent(text: str, examples: list[EmailExample]) -> tuple[str, float]:
    """Lightweight, reproducible intent classifier used as the baseline/model path."""
    from .retrieval import retrieve
    hits = retrieve(text, examples, top_k=1)
    if not hits:
        return "unknown", 0.0
    return hits[0].example.category, hits[0].score


def intent_accuracy(rows: list[dict]) -> float:
    if not rows:
        return 0.0
    return sum(r["predicted_intent"] == r["gold_intent"] for r in rows) / len(rows)
