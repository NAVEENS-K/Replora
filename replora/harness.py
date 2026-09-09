"""Assignment evaluation harness for a prepared 150-250 example golden set."""
import json
from pathlib import Path
from .baselines import majority_intent, simple_retrieval_baseline
from .intents import intent_accuracy
from .models import EmailExample


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


def as_examples(rows):
    return [EmailExample(
        id=r["id"], category=r["intent"], incoming_email=r["customer_message"],
        reference_reply=r["reference_reply"], key_points=[], forbidden_claims=[]
    ) for r in rows]


def run_baselines(rows):
    train, test = split(rows)
    majority = majority_intent(train)
    trivial = [{**r, "predicted_intent": majority} for r in test]
    retrieval = simple_retrieval_baseline(as_examples(train), test)
    return {
        "majority_accuracy": intent_accuracy(trivial),
        "nearest_neighbor_accuracy": intent_accuracy(retrieval),
        "train_size": len(train),
        "test_size": len(test),
    }
