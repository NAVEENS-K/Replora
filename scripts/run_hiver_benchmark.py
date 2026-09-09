"""Run Replora and two baselines on a completed golden set.

The target row is removed from the retrieval pool for every Replora prediction.
Gold/reference fields are supplied only to evaluation, never to generation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from replora.baselines import majority_intent, simple_retrieval_baseline
from replora.evaluator import evaluate
from replora.harness import load_golden, split, as_examples
from replora.intents import classify_intent
from replora.metrics import accuracy, macro_f1, binary_f1
from replora.retrieval import retrieve
from replora.generator import generate_reply
from replora.decision import decide


def run(rows):
    train, test = split(rows)
    train_examples = as_examples(train)
    majority = majority_intent(train)
    trivial_preds = [majority for _ in test]
    retrieval = simple_retrieval_baseline(train_examples, test)

    replora_intents, replora_escalations, replora_quality = [], [], []
    details = []
    for target in test:
        pool = [r for r in rows if r["id"] != target["id"]]
        examples = as_examples(pool)
        intent, intent_score = classify_intent(target["customer_message"], examples)
        hits = retrieve(target["customer_message"], examples, top_k=3)
        reply = generate_reply(target["customer_message"], hits)  # no target gold constraints
        evidence = [h.example.reference_reply for h in hits]
        result = evaluate(target["customer_message"], reply, target["reference_reply"], [], evidence, [])
        predicted_escalate = result.recommendation != "✓ SAFE TO SUGGEST"
        replora_intents.append(intent)
        replora_escalations.append(predicted_escalate)
        replora_quality.append(result.quality_score)
        details.append({
            "id": target["id"],
            "gold_intent": target["intent"],
            "predicted_intent": intent,
            "intent_score": round(intent_score, 4),
            "gold_escalate": bool(target["escalation_required"]),
            "predicted_escalate": predicted_escalate,
            "reply": reply,
            "quality_score": result.quality_score,
            "risk_score": result.risk_score,
            "validation_score": result.validation_score,
            "recommendation": result.recommendation,
            "unsupported_claims": result.unsupported_claims,
            "missing_points": result.missing_points,
        })

    gold_intents = [r["intent"] for r in test]
    gold_escalations = [bool(r["escalation_required"]) for r in test]
    return {
        "n": len(test),
        "baselines": {
            "majority": {"intent_accuracy": accuracy(gold_intents, trivial_preds)},
            "nearest_neighbor": {"intent_accuracy": accuracy(gold_intents, [r["predicted_intent"] for r in retrieval])},
        },
        "replora": {
            "intent_accuracy": accuracy(gold_intents, replora_intents),
            "intent_macro_f1": macro_f1(gold_intents, replora_intents),
            "escalation_f1": binary_f1(gold_escalations, replora_escalations),
            "mean_judge_quality": sum(replora_quality) / len(replora_quality) if replora_quality else 0.0,
        },
        "details": details,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", default="data/golden_set.json")
    parser.add_argument("--output", default="results/hiver_benchmark.json")
    args = parser.parse_args()
    rows = load_golden(args.golden)
    result = run(rows)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "details"}, indent=2))


if __name__ == "__main__":
    main()
