"""Create a blank 150-250-example labeling file from held-out Twitter pairs.

This script deliberately does NOT label the examples. The resulting file is a
human-labeling work queue, not evaluation evidence, until a person reviews and
fills the labels.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from replora.twitter_data import reconstruct_pairs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--brand-author-id", required=True)
    parser.add_argument("--brand-name", required=True)
    parser.add_argument("--output", default="data/golden_candidates.json")
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--holdout-fraction", type=float, default=0.25)
    args = parser.parse_args()
    if not 150 <= args.n <= 250:
        raise SystemExit("--n must be between 150 and 250")

    pairs = reconstruct_pairs(args.input, args.brand_author_id)
    if len(pairs) < args.n:
        raise SystemExit(f"Only {len(pairs)} usable direct pairs found; need {args.n}.")
    rng = random.Random(args.seed)
    rng.shuffle(pairs)
    start = int(len(pairs) * (1 - args.holdout_fraction))
    candidates = pairs[start:]
    if len(candidates) < args.n:
        raise SystemExit("Holdout is smaller than requested candidate count; reduce --holdout-fraction.")
    candidates = candidates[:args.n]

    rows = []
    for i, pair in enumerate(candidates, 1):
        rows.append({
            "id": f"golden-{i:03d}",
            "brand": args.brand_name,
            "customer_message": pair.customer_tweet.text,
            "historical_brand_reply": pair.brand_reply.text,
            "conversation_context": [t.text for t in pair.context],
            "intent": "",
            "reference_resolution": "",
            "reference_reply": pair.brand_reply.text,
            "escalation_required": None,
            "human_reply_quality": None,
            "human_escalation_label": "",
        })

    payload = {
        "status": "HUMAN_LABELING_REQUIRED",
        "sampling": {"seed": args.seed, "holdout_fraction": args.holdout_fraction, "selection": "random sample from held-out direct customer->brand pairs"},
        "instructions": "A human must review every row, define the brand-specific intent taxonomy, label intent/escalation/quality, and verify the historical reply as the reference. Do not report this file as a golden evaluation set until completed.",
        "rows": rows,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(rows)} human-labeling candidates to {out}")


if __name__ == "__main__":
    main()
