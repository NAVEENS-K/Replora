from dataclasses import dataclass, field
from typing import Any


@dataclass
class EmailExample:
    id: str
    category: str
    incoming_email: str
    reference_reply: str
    key_points: list[str] = field(default_factory=list)


@dataclass
class RetrievedExample:
    example: EmailExample
    score: float


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

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()
