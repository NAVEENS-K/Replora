import json
import os
from .grounding import analyze_grounding
from .models import EvaluationResult
from .validation import validate_reply

WEIGHTS = {"correctness": 0.30, "relevance": 0.25, "completeness": 0.20, "groundedness": 0.15, "tone": 0.10}


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _policy(quality: float, risk: float, unsupported_count: int, validation) -> str:
    if validation.critical or risk >= 50 or unsupported_count >= 2:
        return "✕ DO NOT SUGGEST"
    if quality >= 80 and risk <= 20 and unsupported_count == 0 and validation.validation_score >= 80:
        return "✓ SAFE TO SUGGEST"
    return "⚠ NEEDS REVIEW"


def _missing_points(validation, llm_missing):
    deterministic = [x.point for x in validation.required_points if x.status == "MISSING"]
    return list(dict.fromkeys(deterministic + (llm_missing or [])))


def _score_result(email, reply, reference, key_points, validation, llm_values=None, reason=""):
    checks = validation.claims
    coverage = sum(c.status == "Supported" for c in checks)
    total = len(checks)
    values = llm_values or {}
    email_words = set(email.lower().split())
    ref_words = set(reference.lower().split())
    reply_words = set(reply.lower().split())
    overlap_ref = len(reply_words & ref_words) / max(1, len(ref_words))
    overlap_email = len(reply_words & email_words) / max(1, min(12, len(email_words)))
    relevance = _clamp(0.55 + 0.45 * overlap_email)
    correctness = _clamp(0.55 + 0.45 * overlap_ref)
    point_hits = sum(x.status == "PASS" for x in validation.required_points)
    completeness = point_hits / max(1, len(validation.required_points)) if validation.required_points else _clamp(values.get("completeness", 0.8))
    groundedness = validation.evidence_coverage
    tone = 0.95 if any(x in reply.lower() for x in ["please", "thanks", "sorry", "happy to help", "can help"]) else 0.78

    if values:
        relevance = _clamp(values.get("relevance", relevance))
        correctness = _clamp(values.get("correctness", correctness))
        completeness = min(_clamp(values.get("completeness", completeness)), completeness) if validation.required_points else _clamp(values.get("completeness", completeness))
        tone = _clamp(values.get("tone", tone))
        groundedness = min(_clamp(values.get("groundedness", groundedness)), groundedness)

    quality = 100 * sum(WEIGHTS[k] * v for k, v in {"correctness": correctness, "relevance": relevance, "completeness": completeness, "groundedness": groundedness, "tone": tone}.items())
    high = sum(c.risk in {"HIGH", "CRITICAL"} for c in checks)
    medium = sum(c.risk == "MEDIUM" for c in checks)
    risk = min(100.0, high * 40 + medium * 12 + (1 - groundedness) * 35 + (100 - validation.validation_score) * 0.6)
    unsupported = validation.unsupported_claims
    missing = _missing_points(validation, values.get("missing_points", []))
    strengths = values.get("strengths", []) or [
        "Addresses the customer's request" if relevance >= .8 else "Partially addresses the request",
        "Professional support tone" if tone >= .85 else "Tone could be improved",
    ]
    recommendation = _policy(quality, risk, len(unsupported), validation)
    reason = reason or "Quality combines semantic evaluation with an independent deterministic validation layer; safety-sensitive claims cannot be cleared by the LLM judge alone."
    return EvaluationResult(
        relevance, correctness, completeness, groundedness, tone,
        round(quality, 2), round(risk, 2), missing, unsupported, strengths,
        reason, recommendation, coverage, total, checks,
        validation.validation_score, validation.to_dict(),
    )


def _llm_eval(email, reply, reference, key_points, checks):
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = f"""Evaluate a customer-support email reply. Return JSON only.
Customer email: {email}
Reference reply (benchmark only): {reference}
Required key points: {json.dumps(key_points)}
Generated reply: {reply}
Deterministic validation: {json.dumps([x.to_dict() for x in checks])}
Score 0 to 1: relevance, correctness, completeness, groundedness, tone. Judge meaning, not wording similarity. Never override a deterministic contradiction, security violation, forbidden claim, or unsupported operational claim. Explain briefly with reason, missing_points, strengths."""
    r = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a strict, conservative customer-support quality judge."},
            {"role": "user", "content": prompt},
        ],
    )
    return json.loads(r.choices[0].message.content)


def evaluate(email: str, reply: str, reference: str, key_points: list[str], evidence: list[str], forbidden_claims: list[str] | None = None) -> EvaluationResult:
    validation = validate_reply(reply, email, evidence, key_points, forbidden_claims)
    # Keep the existing grounding API for compatibility/tests; the new validator
    # is authoritative for the final decision and risk-sensitive grounding.
    _, _, _, checks = analyze_grounding(reply, email, evidence, forbidden_claims)
    validation.claims = validation.claims or checks

    if os.getenv("OPENAI_API_KEY"):
        try:
            d = _llm_eval(email, reply, reference, key_points, validation.claims)
            return _score_result(email, reply, reference, key_points, validation, d, d.get("reason", ""))
        except Exception:
            pass
    return _score_result(email, reply, reference, key_points, validation)
