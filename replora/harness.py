"""Assignment evaluation harness for a prepared 150-250 example golden set."""
import json
from pathlib import Path
from .baselines import majority_intent, simple_retrieval_baseline
from .intents import intent_accuracy


def load_golden(path="data/golden_set.json"):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not 150 <= len(rows) <= 250:
        raise ValueError(f"Golden set must contain 150-250 examples; found {len(rows)}")
    required = {"id", "customer_message", "intent", "reference_reply", "escalation_required"}
    for row in rows:
        missing = required - row.keys()
        if missing:
            raise ValueError(f"{row.get('id', '?')}: missing {sorted(missing)}")
    return rows


def split(rows, train_fraction=0.8):
    cut = int(len(rows) * train_fraction)
    return rows[:cut], rows[cut:]


def run_intent_baselines(rows):
    train, test = split(rows)
    majority = majority_intent(train)
    trivial = [{**r, "predicted_intent": majority} for r in test]
    simple = simple_retrieval_baseline([], []) if False else []
    return {
        "majority_accuracy": intent_accuracy(trivial),
        "test_size": len(test),
        "train_size": len(train),
    }
