"""Deterministic validation layer for generated support replies.

The validator is intentionally independent of the LLM judge. It checks
claims, required information, forbidden actions, contradictions, security
issues, and basic response structure before a reply can be considered safe.
"""
from dataclasses import dataclass, field
import re

from .models import ClaimCheck

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "is",
    "are", "be", "it", "this", "that", "we", "you", "your", "i", "can",
    "will", "please", "with", "from", "our", "us", "so", "as", "do", "does",
}

OPERATIONAL_PATTERNS = [
    r"\bprocessed\b", r"\bcompleted\b", r"\bapproved\b", r"\brefunded\b",
    r"\bcredited\b", r"\bupgraded\b", r"\bcancelled\b", r"\bcanceled\b",
    r"\bactivated\b", r"\bfixed\b", r"\bresolved\b", r"\bsent\b",
    r"\bremoved\b", r"\badded\b", r"\bchanged\b", r"\brestored\b",
    r"\bwill receive\b", r"\bwill arrive\b", r"\barrive by\b",
    r"\bguarantee(?:d)?\b", r"\bdefinitely\b",
]

SECRET_PATTERNS = [
    r"\bpassword\b", r"\botp\b", r"\bone[- ]time password\b",
    r"\bauth(?:entication|enticator)? (?:code|secret|token)\b",
    r"\bapi key\b", r"\bapi secret\b", r"\bprivate key\b",
    r"\bcvv\b", r"\bsecurity code\b",
]

NEGATION_WORDS = {"not", "never", "no", "cannot", "can't", "isn't", "wasn't", "haven't", "hasn't", "didn't", "doesn't"}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS and len(w) > 2}


def similarity(a: str, b: str) -> float:
    aw, bw = _words(a), _words(b)
    if not aw or not bw:
        return 0.0
    return len(aw & bw) / max(1, len(aw))


def _sentences(text: str) -> list[str]:
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x.strip()]


def _is_operational(text: str) -> bool:
    return any(re.search(p, text.lower()) for p in OPERATIONAL_PATTERNS)


def _has_secret_request(text: str) -> bool:
    lower = text.lower()
    return any(re.search(p, lower) for p in SECRET_PATTERNS) and any(
        w in lower for w in ("send", "share", "provide", "tell", "give", "enter", "reply")
    )


def _contradiction(reply: str, source: str) -> list[str]:
    """Detect targeted contradictions for common support-state statements.

    This is deliberately conservative rather than pretending to be a general
    natural-language inference model.
    """
    pairs = [
        (r"\b(?:not|hasn't|haven't|didn't|doesn't|can't|cannot)\b[^.?!]{0,80}\b(received|arrived|processed|fixed|resolved|cancelled|activated)\b",
         r"\b(received|arrived|processed|fixed|resolved|cancelled|activated)\b"),
        (r"\b(?:not|hasn't|haven't|didn't|doesn't|can't|cannot)\b[^.?!]{0,80}\b(refund|cancellation|access)\b",
         r"\b(?:completed|processed|restored|cancelled|refunded)\b[^.?!]{0,80}\b(refund|cancellation|access)?\b"),
    ]
    issues = []
    src = source.lower()
    for negative, affirmative in pairs:
        if re.search(negative, src) and re.search(affirmative, reply.lower()):
            issues.append("Generated reply conflicts with a state explicitly stated by the customer.")
            break
    return issues


@dataclass
class RequiredPointCheck:
    point: str
    status: str
    matched_text: str = ""


@dataclass
class ValidationReport:
    claims: list[ClaimCheck] = field(default_factory=list)
    required_points: list[RequiredPointCheck] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    security_issues: list[str] = field(default_factory=list)
    structural_issues: list[str] = field(default_factory=list)
    validation_score: float = 100.0

    @property
    def unsupported_claims(self) -> list[str]:
        return [c.claim for c in self.claims if c.status in {"Unsupported", "Contradicted"}]

    @property
    def evidence_coverage(self) -> float:
        if not self.claims:
            return 1.0
        return sum(c.status == "Supported" for c in self.claims) / len(self.claims)

    @property
    def critical(self) -> bool:
        return bool(self.contradictions or self.security_issues or self.forbidden_claims)

    def to_dict(self):
        return {
            "claims": [c.to_dict() for c in self.claims],
            "required_points": [r.__dict__ for r in self.required_points],
            "forbidden_claims": self.forbidden_claims,
            "contradictions": self.contradictions,
            "security_issues": self.security_issues,
            "structural_issues": self.structural_issues,
            "validation_score": self.validation_score,
            "evidence_coverage": self.evidence_coverage,
        }


def validate_reply(
    reply: str,
    customer_email: str,
    evidence_texts: list[str],
    required_points: list[str] | None = None,
    forbidden_claims: list[str] | None = None,
) -> ValidationReport:
    required_points = required_points or []
    forbidden_claims = forbidden_claims or []
    sentences = _sentences(reply)
    sources = [customer_email, *evidence_texts]
    report = ValidationReport()

    if not reply.strip():
        report.structural_issues.append("Reply is empty.")
    if len(reply.split()) > 180:
        report.structural_issues.append("Reply is unusually long for a support suggestion.")
    if len(sentences) != len(set(s.lower() for s in sentences)):
        report.structural_issues.append("Reply contains a repeated sentence.")

    for sentence in sentences:
        best_score = max((similarity(sentence, source) for source in sources), default=0.0)
        forbidden_score = max((similarity(sentence, f) for f in forbidden_claims), default=0.0)
        operational = _is_operational(sentence)
        if forbidden_score >= 0.45:
            report.claims.append(ClaimCheck(sentence, "Unsupported", "Matches a forbidden-claim constraint.", "CRITICAL"))
            report.forbidden_claims.append(sentence)
        elif best_score >= 0.50:
            report.claims.append(ClaimCheck(sentence, "Supported", f"Evidence similarity {best_score:.2f}.", "LOW"))
        elif best_score >= 0.25:
            report.claims.append(ClaimCheck(sentence, "Partially supported", f"Partial evidence similarity {best_score:.2f}.", "MEDIUM" if operational else "LOW"))
        elif operational:
            report.claims.append(ClaimCheck(sentence, "Unsupported", "Operational commitment lacks sufficient evidence.", "HIGH"))
        else:
            report.claims.append(ClaimCheck(sentence, "Unverified", "No strong textual evidence; not classified as an operational commitment.", "LOW"))

        if _has_secret_request(sentence):
            report.security_issues.append(f"Potential credential/secret request: {sentence}")

    report.contradictions = _contradiction(reply, customer_email)

    for point in required_points:
        scores = [(similarity(point, sentence), sentence) for sentence in sentences]
        best, matched = max(scores, default=(0.0, ""))
        status = "PASS" if best >= 0.45 else "MISSING"
        report.required_points.append(RequiredPointCheck(point, status, matched if status == "PASS" else ""))

    penalty = 0.0
    penalty += 45 * len(report.forbidden_claims)
    penalty += 45 * len(report.contradictions)
    penalty += 45 * len(report.security_issues)
    penalty += 20 * sum(c.risk == "HIGH" for c in report.claims if c.claim not in report.forbidden_claims)
    penalty += 10 * sum(c.status == "Partially supported" for c in report.claims)
    penalty += 10 * sum(r.status == "MISSING" for r in report.required_points)
    penalty += 5 * len(report.structural_issues)
    report.validation_score = round(max(0.0, 100.0 - penalty), 2)
    return report
