"""Prepare a small, reproducible brand-specific subset from Customer Support on Twitter.

Usage examples:
    python data/prepare_twitter.py --input data/raw/twcs.csv --brand amazon
    python data/prepare_twitter.py --input data/raw/twcs.csv --list-brands

The script intentionally does not require pandas so the benchmark stays lightweight.
It accepts the common TWCS CSV columns: tweet_id, author_id, inbound, created_at,
text, response_tweet_id, and in_response_to_tweet_id. Brand selection is based on
an explicit brand-name column when present, otherwise the script reports available
columns and asks the user to adapt the brand extraction rule.
"""
import argparse
import csv
import json
from pathlib import Path


def read_rows(path: str):
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        yield from csv.DictReader(f)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--brand")
    p.add_argument("--output", default="data/twitter_brand_subset.json")
    p.add_argument("--limit", type=int, default=1000)
    p.add_argument("--list-brands", action="store_true")
    args = p.parse_args()

    rows = read_rows(args.input)
    first = next(rows, None)
    if first is None:
        raise SystemExit("Input dataset is empty")

    fields = list(first)
    brand_field = next((x for x in fields if x.lower() in {"brand", "company", "brand_name"}), None)
    if args.list_brands:
        if not brand_field:
            print("No explicit brand column found. Columns:", ", ".join(fields))
            return
        counts = {}
        for row in rows:
            value = row.get(brand_field, "").strip()
            if value:
                counts[value] = counts.get(value, 0) + 1
        for name, count in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"{name}\t{count}")
        return

    if not args.brand:
        raise SystemExit("Provide --brand or use --list-brands")
    if not brand_field:
        raise SystemExit(
            "The standard TWCS export may not have a brand column. Select a brand using "
            "the account/author mapping supplied with your downloaded release, then adapt "
            "brand_field in this script rather than guessing."
        )

    selected = []
    def consider(row):
        if row.get(brand_field, "").strip().lower() != args.brand.lower():
            return
        text = row.get("text", "").strip()
        if not text:
            return
        selected.append({
            "tweet_id": row.get("tweet_id", ""),
            "author_id": row.get("author_id", ""),
            "inbound": row.get("inbound", ""),
            "created_at": row.get("created_at", ""),
            "text": text,
            "response_tweet_id": row.get("response_tweet_id", ""),
            "in_response_to_tweet_id": row.get("in_response_to_tweet_id", ""),
        })

    consider(first)
    for row in rows:
        if len(selected) >= args.limit:
            break
        consider(row)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(selected)} rows to {args.output}")


if __name__ == "__main__":
    main()
