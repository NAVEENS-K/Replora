import json
import math
import re
from collections import Counter
from pathlib import Path
from .models import EmailExample, RetrievedExample

GENERIC = {"help", "please", "issue", "problem", "account", "customer", "service", "can", "could", "want", "need"}
IMPORTANT = {"refund", "charge", "charged", "duplicate", "password", "2fa", "authentication", "shipping", "invoice", "webhook", "upgrade", "cancel", "cancellation", "csv", "dashboard", "delivery", "subscription", "payment", "order"}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _vector(text: str) -> Counter:
    return Counter(_tokens(text))


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[k] * b[k] for k in a.keys() & b.keys())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def _important_overlap(query: str, candidate: str) -> float:
    q = set(_tokens(query)) & IMPORTANT
    c = set(_tokens(candidate)) & IMPORTANT
    return len(q & c) / max(1, len(q))


def _specific_overlap(query: str, candidate: str) -> float:
    q = set(_tokens(query)) - GENERIC
    c = set(_tokens(candidate)) - GENERIC
    return len(q & c) / max(1, len(q))


def load_dataset(path: str | Path = "data/dataset.json") -> list[EmailExample]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [EmailExample(**item) for item in raw]


def retrieve(query: str, examples: list[EmailExample], top_k: int = 3) -> list[RetrievedExample]:
    q = _vector(query)
    scored = []
    for ex in examples:
        lexical = _cosine(q, _vector(ex.incoming_email))
        intent = _important_overlap(query, ex.incoming_email)
        specific = _specific_overlap(query, ex.incoming_email)
        score = 0.55 * lexical + 0.25 * intent + 0.20 * specific
        scored.append(RetrievedExample(ex, score))
    return sorted(scored, key=lambda x: x.score, reverse=True)[:top_k]
