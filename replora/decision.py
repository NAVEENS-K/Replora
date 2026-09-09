from dataclasses import dataclass


@dataclass
class Sendability:
    label: str
    reason: str


def decide(quality_score: float, risk_score: float, unsupported_claims: list[str]) -> Sendability:
    if risk_score >= 50 or len(unsupported_claims) >= 2:
        return Sendability("DO NOT SUGGEST", "High unsupported-claim risk requires correction before an agent sees the suggestion.")
    if risk_score > 20 or quality_score < 75 or unsupported_claims:
        return Sendability("NEEDS REVIEW", "The reply has quality or grounding concerns that should be checked by an agent.")
    return Sendability("SAFE TO SUGGEST", "The reply clears the quality and grounding thresholds; normal human review still applies.")
