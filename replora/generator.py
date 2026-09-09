import os
from .models import RetrievedExample

SYSTEM_PROMPT = """You are Replora, a customer-support email copilot.
Write a concise, professional suggested reply to the customer's email.
Use the historical examples only as guidance for style and workflow.
Never invent refunds, credits, account changes, delivery dates, policies,
guarantees, or actions that have not happened. If information is missing,
ask for it. Do not claim that an action was completed unless the input
explicitly establishes that it happened. Return only the email reply.
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


def generate_reply(email: str, examples: list[RetrievedExample]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _demo_reply(email)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(email, examples)},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _demo_reply(email)
