import json
import math
import re
from collections import Counter
from pathlib import Path
from .models import EmailExample, RetrievedExample


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


def load_dataset(path: str | Path = "data/dataset.json") -> list[EmailExample]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [EmailExample(**item) for item in raw]


def retrieve(query: str, examples: list[EmailExample], top_k: int = 3) -> list[RetrievedExample]:
    q = _vector(query)
    scored = [RetrievedExample(ex, _cosine(q, _vector(ex.incoming_email))) for ex in examples]
    return sorted(scored, key=lambda x: x.score, reverse=True)[:top_k]
