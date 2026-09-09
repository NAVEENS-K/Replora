import re


def split_claims(reply: str) -> list[str]:
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", reply.strip()) if x.strip()]


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def analyze_grounding(reply: str, source_text: str, evidence_texts: list[str]) -> tuple[list[str], int, int]:
    sources = [source_text, *evidence_texts]
    source_words = [_words(x) for x in sources]
    unsupported: list[str] = []
    claims = split_claims(reply)
    for claim in claims:
        words = _words(claim)
        if not words:
            continue
        supported = False
        for sw in source_words:
            overlap = len(words & sw) / max(1, len(words))
            if overlap >= 0.35:
                supported = True
                break
        if not supported:
            # Common operational commitments are high-risk when not explicitly grounded.
            risky = any(p in claim.lower() for p in [
                "processed", "completed", "will receive", "guarantee", "approved",
                "refunded", "credited", "upgraded", "cancelled", "cancelled already"
            ])
            if risky:
                unsupported.append(claim)
    total = len(claims)
    supported_count = max(0, total - len(unsupported))
    return unsupported, supported_count, total
