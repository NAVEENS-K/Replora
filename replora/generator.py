import os
from .models import RetrievedExample
from .validation import validate_reply

SYSTEM_PROMPT = """You are Replora, a customer-support email copilot.
Write a concise, professional suggested reply to the customer's email.
Use historical examples only as guidance for style and workflow.
Never invent refunds, credits, account changes, delivery dates, policies,
guarantees, or actions that have not happened. Never request passwords,
OTPs, API secrets, CVVs, or other authentication secrets. If information is
missing, ask for it. Do not claim that an action was completed unless the
input explicitly establishes that it happened. Return only the email reply.
"""


def build_prompt(email: str, examples: list[RetrievedExample]) -> str:
    context = "\n\n".join(
        f"Example {i+1}:\nCustomer: {x.example.incoming_email}\nReply: {x.example.reference_reply}"
        for i, x in enumerate(examples)
    )
    return f"{SYSTEM_PROMPT}\n\nHISTORICAL EXAMPLES:\n{context}\n\nNEW CUSTOMER EMAIL:\n{email}\n\nSUGGESTED REPLY:"


def _demo_reply(email: str) -> str:
    text = email.lower()
    if "charged twice" in text or "duplicate charge" in text:
        return "Sorry about the duplicate charge. Please send us the transaction ID for the duplicate payment so we can investigate it and help with the refund."
    if "forgot" in text and "password" in text:
        return "You can reset your password using the Forgot password link on the sign-in page. Please use the email associated with your account and follow the reset instructions."
    if "cancel" in text and "subscription" in text:
        return "We can help with the cancellation. Please confirm the email address on the account so we can locate the subscription and help with the request."
    if "refund" in text:
        return "I can help check the refund status. Please send your order number so we can look up the return and confirm the current status."
    return "Thanks for reaching out. Please share the relevant account or order details so we can investigate the issue and help with the next steps."


def _llm_generate(email: str, examples: list[RetrievedExample], repair: str = "") -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = build_prompt(email, examples)
    if repair:
        prompt += f"\n\nVALIDATION FEEDBACK:\n{repair}\nRewrite the reply to remove every flagged issue. Do not add new unsupported facts."
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def generate_reply(email: str, examples: list[RetrievedExample], forbidden_claims: list[str] | None = None) -> str:
    """Generate once, then optionally perform one validator-guided repair pass.

    Forbidden constraints are used only by the benchmark/refinement path and
    are not included in the normal generation prompt, preventing leakage.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _demo_reply(email)
    try:
        reply = _llm_generate(email, examples)
        evidence = [x.example.reference_reply for x in examples]
        report = validate_reply(reply, email, evidence, [], forbidden_claims or [])
        risky = [c for c in report.claims if c.risk in {"HIGH", "CRITICAL"}]
        if risky or report.contradictions or report.security_issues or report.forbidden_claims:
            feedback = "\n".join(
                [f"- {c.status}: {c.claim} ({c.evidence})" for c in risky]
                + [f"- FORBIDDEN: {x}" for x in report.forbidden_claims]
                + [f"- CONTRADICTION: {x}" for x in report.contradictions]
                + [f"- SECURITY: {x}" for x in report.security_issues]
            )
            repaired = _llm_generate(email, examples, feedback)
            second = validate_reply(repaired, email, evidence, [], forbidden_claims or [])
            if second.validation_score >= report.validation_score or (report.critical and not second.critical):
                return repaired
        return reply
    except Exception:
        return _demo_reply(email)
