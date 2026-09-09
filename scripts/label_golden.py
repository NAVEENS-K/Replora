"""Interactive human labeling tool for the Hiver golden set."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def ask(prompt: str, default: str = "") -> str:
    value = input(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
    return value or default


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/golden_candidates.json")
    parser.add_argument("--output", default="data/golden_set.json")
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    rows = payload["rows"]
    intents = []
    print("Label each example. Define a compact taxonomy from the brand data; reuse an existing intent when appropriate.")
    print("For escalation use auto-handle or escalate. Quality is 1-5 for the historical reply as a support response.")
    for row in rows:
        print("\n" + "=" * 80)
        print(row["id"])
        print("CUSTOMER:", row["customer_message"])
        print("HISTORICAL REPLY:", row["historical_brand_reply"])
        print("CONTEXT:", " | ".join(row.get("conversation_context", [])))
        if intents:
            print("Existing intents:", ", ".join(intents))
        intent = ask("Intent")
        if intent and intent not in intents:
            intents.append(intent)
        resolution = ask("Reference resolution", row.get("reference_resolution", ""))
        escalation = ask("Escalation (auto-handle/escalate)", row.get("human_escalation_label", ""))
        quality = ask("Human reply quality (1-5)", "")
        if escalation not in {"auto-handle", "escalate"}:
            raise SystemExit("Escalation must be auto-handle or escalate")
        try:
            quality_int = int(quality)
            if quality_int not in range(1, 6):
                raise ValueError
        except ValueError:
            raise SystemExit("Quality must be an integer from 1 to 5")
        row.update({
            "intent": intent,
            "reference_resolution": resolution,
            "escalation_required": escalation == "escalate",
            "human_reply_quality": quality_int,
            "human_escalation_label": escalation,
        })

    out = Path(args.output)
    out.write_text(json.dumps({**payload, "status": "HUMAN_LABELLED", "intent_taxonomy": sorted(intents), "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(rows)} labeled examples to {out}")


if __name__ == "__main__":
    main()
