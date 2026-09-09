from dataclasses import dataclass


@dataclass
class Sendability:
    label: str
    reason: str


def decide(quality_score: float, risk_score: float, unsupported_claims: list[str], validation_report: dict | None = None) -> Sendability:
    report = validation_report or {}
    critical = bool(report.get("forbidden_claims") or report.get("contradictions") or report.get("security_issues"))
    if critical or risk_score >= 50 or len(unsupported_claims) >= 2:
        reasons = []
        if report.get("contradictions"):
            reasons.append("contradiction")
        if report.get("security_issues"):
            reasons.append("security issue")
        if report.get("forbidden_claims"):
            reasons.append("forbidden claim")
        reason = "Critical validation finding" + (": " + ", ".join(reasons) if reasons else "") + "; correction is required before an agent uses the suggestion."
        return Sendability("DO NOT SUGGEST", reason)
    if risk_score > 20 or quality_score < 75 or unsupported_claims:
        return Sendability("NEEDS REVIEW", "The reply has quality, evidence, or grounding concerns that should be checked by an agent.")
    return Sendability("SAFE TO SUGGEST", "The reply clears the quality and grounding thresholds; normal human review still applies.")
