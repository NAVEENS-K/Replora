import json
import os
from .grounding import analyze_grounding
from .models import EvaluationResult

WEIGHTS = {"correctness": 0.30, "relevance": 0.25, "completeness": 0.20, "groundedness": 0.15, "tone": 0.10}


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _policy(quality: float, risk: float, unsupported_count: int) -> str:
    if unsupported_count > 0 or risk >= 50:
        return "✕ DO NOT SUGGEST"
    if quality >= 80 and risk <= 20:
        return "✓ SAFE TO SUGGEST"
    return "⚠ NEEDS REVIEW"


def _heuristic_eval(email, reply, reference, key_points, checks, coverage, total):
    email_words = set(email.lower().split())
    ref_words = set(reference.lower().split())
    reply_words = set(reply.lower().split())
    overlap_ref = len(reply_words & ref_words) / max(1, len(ref_words))
    overlap_email = len(reply_words & email_words) / max(1, min(12, len(email_words)))
    relevance = _clamp(0.55 + 0.45 * overlap_email)
    correctness = _clamp(0.55 + 0.45 * overlap_ref)
    low_words = {w for w in reply.lower().replace(".", " ").split() if len(w) > 3}
    point_hits = sum(1 for p in key_points if any(w in low_words for w in p.lower().split() if len(w) > 3))
    completeness = _clamp(point_hits / max(1, len(key_points)))
    groundedness = coverage / max(1, total)
    tone = 0.95 if any(x in reply.lower() for x in ["please", "thanks", "sorry", "happy to help", "can help"]) else 0.78
    quality = 100 * sum(WEIGHTS[k] * v for k, v in {"correctness": correctness, "relevance": relevance, "completeness": completeness, "groundedness": groundedness, "tone": tone}.items())
    high = sum(x.risk == "HIGH" for x in checks)
    medium = sum(x.risk == "MEDIUM" for x in checks)
    risk = min(100.0, high * 45 + medium * 12 + (1 - groundedness) * 35)
    missing = [p for p in key_points if not any(w in reply.lower() for w in p.lower().split() if len(w) > 3)]
    strengths = ["Addresses the customer's request" if relevance >= .8 else "Partially addresses the request", "Professional support tone" if tone >= .85 else "Tone could be improved"]
    recommendation = _policy(quality, risk, len([x for x in checks if x.status == "Unsupported"]))
    reason = "Quality combines semantic dimensions; deterministic claim verification independently penalizes unsupported operational commitments."
    return EvaluationResult(relevance, correctness, completeness, groundedness, tone, round(quality, 2), round(risk, 2), missing, [x.claim for x in checks if x.status == "Unsupported"], strengths, reason, recommendation, coverage, total, checks)


def _llm_eval(email, reply, reference, key_points, checks):
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = f"""Evaluate a customer-support email reply. Return JSON only.
Customer email: {email}
Reference reply (ground truth for benchmark): {reference}
Required key points: {json.dumps(key_points)}
Generated reply: {reply}
Deterministic claim checks: {json.dumps([x.to_dict() for x in checks])}
Score 0 to 1: relevance, correctness, completeness, groundedness, tone. Judge meaning, not wording similarity. Do not override an unsupported operational claim merely because the reply sounds plausible. Explain briefly with reason, missing_points, strengths."""
    r = client.chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0, response_format={"type": "json_object"}, messages=[{"role": "system", "content": "You are a strict, conservative customer-support quality judge."}, {"role": "user", "content": prompt}])
    return json.loads(r.choices[0].message.content)


def evaluate(email: str, reply: str, reference: str, key_points: list[str], evidence: list[str], forbidden_claims: list[str] | None = None) -> EvaluationResult:
    unsupported, coverage, total, checks = analyze_grounding(reply, email, evidence, forbidden_claims)
    high = sum(x.risk == "HIGH" for x in checks)
    medium = sum(x.risk == "MEDIUM" for x in checks)
    if os.getenv("OPENAI_API_KEY"):
        try:
            d = _llm_eval(email, reply, reference, key_points, checks)
            vals = {k: _clamp(d.get(k, 0.0)) for k in WEIGHTS}
            # Deterministic grounding is authoritative for safety-sensitive claims.
            vals["groundedness"] = min(vals["groundedness"], coverage / max(1, total))
            quality = 100 * sum(WEIGHTS[k] * vals[k] for k in WEIGHTS)
            risk = min(100.0, high * 45 + medium * 12 + (1 - vals["groundedness"]) * 35)
            missing = d.get("missing_points", [])
            strengths = d.get("strengths", [])
            recommendation = _policy(quality, risk, len(unsupported))
            return EvaluationResult(vals["relevance"], vals["correctness"], vals["completeness"], vals["groundedness"], vals["tone"], round(quality, 2), round(risk, 2), missing, unsupported, strengths, d.get("reason", ""), recommendation, coverage, total, checks)
        except Exception:
            pass
    return _heuristic_eval(email, reply, reference, key_points, checks, coverage, total)
