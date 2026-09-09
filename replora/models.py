from dataclasses import dataclass, field
from typing import Any


@dataclass
class EmailExample:
    id: str
    category: str
    incoming_email: str
    reference_reply: str
    key_points: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)


@dataclass
class RetrievedExample:
    example: EmailExample
    score: float


@dataclass
class ClaimCheck:
    claim: str
    status: str
    evidence: str
    risk: str

    def to_dict(self) -> dict[str, str]:
        return self.__dict__.copy()


@dataclass
class EvaluationResult:
    relevance: float
    correctness: float
    completeness: float
    groundedness: float
    tone: float
    quality_score: float
    risk_score: float
    missing_points: list[str]
    unsupported_claims: list[str]
    strengths: list[str]
    reason: str
    recommendation: str
    evidence_coverage: int
    evidence_total: int
    claim_checks: list[ClaimCheck] = field(default_factory=list)
    validation_score: float = 100.0
    validation_report: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        data["claim_checks"] = [x.to_dict() for x in self.claim_checks]
        return data
