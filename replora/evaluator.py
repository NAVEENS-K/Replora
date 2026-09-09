import json
import os
from .grounding import analyze_grounding
from .models import EvaluationResult

WEIGHTS = {"correctness": 0.30, "relevance": 0.25, "completeness": 0.20, "groundedness": 0.15, "tone": 0.10}


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _heuristic_eval(email: str, reply: str, reference: str, key_points: list[str], unsupported: list[str], coverage: int, total: int) -> EvaluationResult:
    combined = (reply + " " + reference).lower()
    email_words = set(email.lower().split())
    ref_words = set(reference.lower().split())
    reply_words = set(reply.lower().split())
    overlap_ref = len(reply_words & ref_words) / max(1, len(ref_words))
    relevance = _clamp(0.65 + 0.35 * min(1, len(reply_words & email_words) / max(1, min(12, len(email_words)))))
    correctness = _clamp(0.55 + 0.45 * overlap_ref)
    point_hits = sum(1 for p in key_points if any(w in combined for w in p.lower().split() if len(w) > 3))
    completeness = _clamp(point_hits / max(1, len(key_points)))
    groundedness = 1.0 if not unsupported else _clamp(1.0 - 0.25 * len(unsupported))
    tone = 0.95 if any(x in reply.lower() for x in ["please", "thanks", "sorry", "happy to help", "can help"]) else 0.75
    quality = 100 * sum(WEIGHTS[k] * v for k, v in {"correctness": correctness, "relevance": relevance, "completeness": completeness, "groundedness": groundedness, "tone": tone}.items())
    risk = _clamp((1 - groundedness) * 100)
    missing = [p for p in key_points if not any(w in reply.lower() for w in p.lower().split() if len(w) > 3)]
    strengths = ["Addresses the customer's request" if relevance >= .8 else "Partially addresses the request", "Professional support tone" if tone >= .85 else "Tone could be improved"]
    recommendation = "✓ READY FOR AGENT REVIEW" if quality >= 80 and risk <= 20 else "⚠ REVIEW BEFORE SENDING"
    reason = "The reply is evaluated against the reference intent and required key points; unsupported operational claims increase risk."
    return EvaluationResult(relevance, correctness, completeness, groundedness, tone, round(quality, 2), round(risk, 2), missing, unsupported, strengths, reason, recommendation, coverage, total)


def _llm_eval(email: str, reply: str, reference: str, key_points: list[str], unsupported: list[str], coverage: int, total: int):
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = f"""Evaluate a customer-support email reply. Return JSON only.
Customer email: {email}
Reference reply: {reference}
Required key points: {json.dumps(key_points)}
Generated reply: {reply}
Unsupported claims already detected: {json.dumps(unsupported)}
Score each from 0 to 1: relevance, correctness, completeness, groundedness, tone. Explain briefly with reason, missing_points, strengths. Do not reward wording similarity; judge meaning and support."""
    r = client.chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0, response_format={"type":"json_object"}, messages=[{"role":"system","content":"You are a strict email-quality evaluator."},{"role":"user","content":prompt}])
    return json.loads(r.choices[0].message.content)


def evaluate(email: str, reply: str, reference: str, key_points: list[str], evidence: list[str]) -> EvaluationResult:
    unsupported, coverage, total = analyze_grounding(reply, email, evidence)
    if os.getenv("OPENAI_API_KEY"):
        try:
            d = _llm_eval(email, reply, reference, key_points, unsupported, coverage, total)
            vals = {k: _clamp(d.get(k, 0.0)) for k in WEIGHTS}
            quality = 100 * sum(WEIGHTS[k] * vals[k] for k in WEIGHTS)
            risk = _clamp((1 - vals["groundedness"]) * 100 + min(50, 15 * len(unsupported)))
            missing = d.get("missing_points", [])
            strengths = d.get("strengths", [])
            recommendation = "✓ READY FOR AGENT REVIEW" if quality >= 80 and risk <= 20 else "⚠ REVIEW BEFORE SENDING"
            return EvaluationResult(vals["relevance"], vals["correctness"], vals["completeness"], vals["groundedness"], vals["tone"], round(quality,2), round(risk,2), missing, unsupported, strengths, d.get("reason", ""), recommendation, coverage, total)
        except Exception:
            pass
    return _heuristic_eval(email, reply, reference, key_points, unsupported, coverage, total)
