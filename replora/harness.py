"""Assignment evaluation harness for a completed 150-250 example golden set."""
from __future__ import annotations

import json
from pathlib import Path
from .baselines import majority_intent, simple_retrieval_baseline
from .intents import intent_accuracy
from .models import EmailExample


def load_golden(path="data/golden_set.json"):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = payload.get("rows", payload) if isinstance(payload, (dict, list)) else []
    if not 150 <= len(rows) <= 250:
        raise ValueError(f"Golden set must contain 150-250 examples; found {len(rows)}")
    required = {"id", "customer_message", "intent", "reference_reply", "escalation_required", "human_reply_quality", "human_escalation_label"}
    for row in rows:
        missing = required - row.keys()
        if missing:
            raise ValueError(f"{row.get('id', '?')}: missing {sorted(missing)}")
        if not row["intent"] or row["human_escalation_label"] not in {"auto-handle", "escalate"}:
            raise ValueError(f"{row.get('id', '?')}: human labels are incomplete")
        if row["human_reply_quality"] not in {1, 2, 3, 4, 5}:
            raise ValueError(f"{row.get('id', '?')}: human_reply_quality must be 1-5")
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
