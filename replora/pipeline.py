from .evaluator import evaluate
from .generator import generate_reply
from .retrieval import retrieve


def run(email: str, examples, top_k: int = 3):
    retrieved = retrieve(email, examples, top_k=top_k)
    reply = generate_reply(email, retrieved)
    evidence = [x.example.reference_reply for x in retrieved]
    best = retrieved[0].example if retrieved else None
    result = evaluate(
        email,
        reply,
        best.reference_reply if best else "",
        best.key_points if best else [],
        evidence,
        best.forbidden_claims if best else [],
    )
    return reply, retrieved, result
