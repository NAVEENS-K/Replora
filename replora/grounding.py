import re
from .models import ClaimCheck

STOPWORDS = {"the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "is", "are", "be", "it", "this", "that", "we", "you", "your", "i", "can", "will", "please", "with", "from", "our"}
RISK_PATTERNS = [
    "processed", "already processed", "completed", "approved", "refunded", "credited",
    "upgraded", "cancelled", "canceled", "will receive", "arrive by", "guarantee",
    "guaranteed", "we have changed", "we changed", "we removed", "we added", "fixed",
]


def split_claims(reply: str) -> list[str]:
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", reply.strip()) if x.strip()]


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS and len(w) > 2}


def _similarity(a: str, b: str) -> float:
    aw, bw = _words(a), _words(b)
    if not aw or not bw:
        return 0.0
    return len(aw & bw) / max(1, len(aw))


def _is_risky(claim: str) -> bool:
    text = claim.lower()
    return any(pattern in text for pattern in RISK_PATTERNS)


def analyze_claims(reply: str, source_text: str, evidence_texts: list[str], forbidden_claims: list[str] | None = None) -> list[ClaimCheck]:
    sources = [source_text, *evidence_texts]
    forbidden_claims = forbidden_claims or []
    checks: list[ClaimCheck] = []
    for claim in split_claims(reply):
        scores = sorted((_similarity(claim, source) for source in sources), reverse=True)
        best = scores[0] if scores else 0.0
        forbidden_match = max((_similarity(claim, item) for item in forbidden_claims), default=0.0)
        risky = _is_risky(claim)
        if forbidden_match >= 0.45:
            status, risk, evidence = "Unsupported", "HIGH", "Matches a forbidden-claim pattern."
        elif best >= 0.50:
            status, risk, evidence = "Supported", "LOW", f"Evidence similarity {best:.2f}."
        elif best >= 0.25:
            status, risk, evidence = "Partially supported", "MEDIUM" if risky else "LOW", f"Partial evidence similarity {best:.2f}."
        elif risky:
            status, risk, evidence = "Unsupported", "HIGH", "No sufficient evidence for an operational commitment."
        else:
            status, risk, evidence = "Unverified", "LOW", "No strong textual evidence; claim is not an operational commitment."
        checks.append(ClaimCheck(claim, status, evidence, risk))
    return checks


def analyze_grounding(reply: str, source_text: str, evidence_texts: list[str], forbidden_claims: list[str] | None = None) -> tuple[list[str], int, int, list[ClaimCheck]]:
    checks = analyze_claims(reply, source_text, evidence_texts, forbidden_claims)
    unsupported = [x.claim for x in checks if x.status == "Unsupported"]
    covered = sum(x.status == "Supported" for x in checks)
    return unsupported, covered, len(checks), checks
