"""Prepare a compact brand-specific subset from Customer Support on Twitter.

The source CSV is tweet-level and does not reliably expose a human-readable brand
column. Select a support-account author_id after inspecting frequent outbound authors.

Examples:
    python data/prepare_twitter.py --input data/raw/twcs.csv --list-authors
    python data/prepare_twitter.py --input data/raw/twcs.csv --brand-name AppleSupport --brand-author-id <ID>
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def rows(path):
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        yield from csv.DictReader(f)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--brand-name")
    p.add_argument("--brand-author-id")
    p.add_argument("--output", default="data/raw_brand_subset.json")
    p.add_argument("--limit", type=int, default=2000)
    p.add_argument("--list-authors", action="store_true")
    args = p.parse_args()

    iterator = rows(args.input)
    first = next(iterator, None)
    if first is None:
        raise SystemExit("Input dataset is empty")

    if args.list_authors:
        counts = Counter()
        for row in iterator:
            if str(row.get("inbound", "")).lower() in {"false", "0", "no"}:
                author = row.get("author_id", "").strip()
                if author:
                    counts[author] += 1
        for author, count in counts.most_common(50):
            print(f"{author}\t{count}")
        return

    if not args.brand_author_id or not args.brand_name:
        raise SystemExit("Provide both --brand-name and --brand-author-id; use --list-authors first.")

    selected = []
    for row in [first, *iterator]:
        if len(selected) >= args.limit:
            break
        if row.get("author_id", "").strip() != args.brand_author_id:
            continue
        text = row.get("text", "").strip()
        if not text:
            continue
        selected.append({
            "tweet_id": row.get("tweet_id", ""),
            "author_id": row.get("author_id", ""),
            "inbound": row.get("inbound", ""),
            "created_at": row.get("created_at", ""),
            "text": text,
            "response_tweet_id": row.get("response_tweet_id", ""),
            "in_response_to_tweet_id": row.get("in_response_to_tweet_id", ""),
        })

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"brand": args.brand_name, "author_id": args.brand_author_id, "rows": selected}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Selected {len(selected)} rows for {args.brand_name}; wrote {output}")


if __name__ == "__main__":
    main()
