"""Generate the challenge dataset deterministically.

The checked-in dataset is hand-authored to keep the benchmark transparent.
This script documents the schema and can create a fresh synthetic extension
without relying on private or scraped customer data.
"""
import json
from pathlib import Path

EXTRA = [
    {
        "id": "synthetic_01",
        "category": "feature",
        "incoming_email": "Does your team inbox support assigning a conversation to another teammate?",
        "reference_reply": "Yes, I can help confirm the assignment options for your account. Please share which plan you are using so we can provide the relevant details.",
        "key_points": ["address assignment question", "request plan", "do not invent plan-specific behavior"]
    },
    {
        "id": "synthetic_02",
        "category": "technical",
        "incoming_email": "Our integration returns a 401 error when connecting. What should we check?",
        "reference_reply": "A 401 usually means the credentials are not being accepted. Please confirm the configured credentials and share a recent request ID or timestamp so we can investigate further.",
        "key_points": ["address authentication error", "suggest checking credentials", "request request ID or timestamp"]
    }
]


def main():
    path = Path(__file__).with_name("generated_dataset.json")
    path.write_text(json.dumps(EXTRA, indent=2), encoding="utf-8")
    print(f"Wrote {len(EXTRA)} synthetic examples to {path}")


if __name__ == "__main__":
    main()
