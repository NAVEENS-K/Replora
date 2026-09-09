"""Prepare a compact brand-specific subset from Customer Support on Twitter.

The source is tweet-level, so this command now exports direct customer -> brand
reply pairs rather than an outbound-only slice. The raw dataset is never committed.
"""
import argparse
import json
from pathlib import Path

from replora.twitter_data import frequent_brand_authors, reconstruct_pairs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--brand-name")
    p.add_argument("--brand-author-id")
    p.add_argument("--output", default="data/raw_brand_subset.json")
    p.add_argument("--limit", type=int, default=2000)
    p.add_argument("--list-authors", action="store_true")
    args = p.parse_args()

    if args.list_authors:
        for author, count in frequent_brand_authors(args.input, 50):
            print(f"{author}\t{count}")
        return

    if not args.brand_author_id or not args.brand_name:
        raise SystemExit("Provide both --brand-name and --brand-author-id; use --list-authors first.")

    pairs = reconstruct_pairs(args.input, args.brand_author_id, args.limit)
    rows = []
    for pair in pairs:
        rows.append({
            "tweet_id": pair.customer_tweet.tweet_id,
            "brand_reply_tweet_id": pair.brand_reply.tweet_id,
            "customer_author_id": pair.customer_tweet.author_id,
            "brand_author_id": pair.brand_reply.author_id,
            "created_at": pair.customer_tweet.created_at,
            "customer_message": pair.customer_tweet.text,
            "historical_brand_reply": pair.brand_reply.text,
            "conversation_context": [t.text for t in pair.context],
        })

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "brand": args.brand_name,
        "brand_author_id": args.brand_author_id,
        "pair_count": len(rows),
        "rows": rows,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Reconstructed {len(rows)} customer->brand pairs for {args.brand_name}; wrote {output}")


if __name__ == "__main__":
    main()
