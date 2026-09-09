from collections import Counter
from .intents import classify_intent
from .retrieval import retrieve


def majority_intent(train_rows: list[dict]) -> str:
    counts = Counter(r["gold_intent"] for r in train_rows)
    return counts.most_common(1)[0][0] if counts else "unknown"


def trivial_baseline(train_rows: list[dict], test_rows: list[dict]) -> list[dict]:
    label = majority_intent(train_rows)
    return [{**r, "predicted_intent": label, "baseline": "majority"} for r in test_rows]


def simple_retrieval_baseline(train_examples, test_rows: list[dict]) -> list[dict]:
    out = []
    for row in test_rows:
        hits = retrieve(row["customer_message"], train_examples, top_k=1)
        prediction = hits[0].example.category if hits else "unknown"
        reply = hits[0].example.reference_reply if hits else ""
        out.append({**row, "predicted_intent": prediction, "reply": reply, "baseline": "nearest-neighbor"})
    return out
