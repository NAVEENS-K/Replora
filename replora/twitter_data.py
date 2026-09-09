"""Utilities for turning the Customer Support on Twitter dataset into pairs.

The source is tweet-level.  This module reconstructs direct customer -> brand
reply pairs while retaining the conversation id and enough context for review.
It intentionally streams the CSV so the full multi-million-row dataset does
not need to be loaded into memory.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Tweet:
    tweet_id: str
    author_id: str
    inbound: bool
    created_at: str
    text: str
    response_tweet_id: str
    in_response_to_tweet_id: str


@dataclass(frozen=True)
class ConversationPair:
    customer_tweet: Tweet
    brand_reply: Tweet
    context: tuple[Tweet, ...] = ()


def _bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def iter_tweets(path: str | Path):
    with open(path, newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            text = (row.get("text") or "").strip()
            tweet_id = (row.get("tweet_id") or "").strip()
            if not tweet_id or not text:
                continue
            yield Tweet(
                tweet_id=tweet_id,
                author_id=(row.get("author_id") or "").strip(),
                inbound=_bool(row.get("inbound", "")),
                created_at=(row.get("created_at") or "").strip(),
                text=text,
                response_tweet_id=(row.get("response_tweet_id") or "").strip(),
                in_response_to_tweet_id=(row.get("in_response_to_tweet_id") or "").strip(),
            )


def frequent_brand_authors(path: str | Path, limit: int = 50) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for tweet in iter_tweets(path):
        if not tweet.inbound and tweet.author_id:
            counts[tweet.author_id] = counts.get(tweet.author_id, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]


def reconstruct_pairs(path: str | Path, brand_author_id: str, limit: int | None = None) -> list[ConversationPair]:
    """Return inbound customer tweets with a direct outbound brand response.

    A response is considered direct when the brand tweet's
    ``in_response_to_tweet_id`` points to the customer tweet. This avoids
    pretending that unrelated tweets from the same brand are resolutions.
    """
    tweets = list(iter_tweets(path))
    by_id = {tweet.tweet_id: tweet for tweet in tweets}
    replies_by_parent: dict[str, list[Tweet]] = {}
    for tweet in tweets:
        if tweet.author_id == brand_author_id and not tweet.inbound and tweet.in_response_to_tweet_id:
            replies_by_parent.setdefault(tweet.in_response_to_tweet_id, []).append(tweet)

    pairs: list[ConversationPair] = []
    for customer in tweets:
        if not customer.inbound:
            continue
        replies = sorted(replies_by_parent.get(customer.tweet_id, []), key=lambda x: x.created_at)
        if not replies:
            continue
        reply = replies[0]
        context_ids = [customer.in_response_to_tweet_id]
        context = tuple(by_id[cid] for cid in context_ids if cid in by_id)
        pairs.append(ConversationPair(customer, reply, context))
        if limit is not None and len(pairs) >= limit:
            break
    return pairs
