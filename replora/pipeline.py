from .evaluator import evaluate
from .generator import generate_reply
from .retrieval import retrieve


def run(email: str, examples, top_k: int = 3):
    """Run the interactive pipeline without treating retrieved references as truth labels."""
    retrieved = retrieve(email, examples, top_k=top_k)
    reply = generate_reply(email, retrieved)
    evidence = [x.example.reference_reply for x in retrieved]
    result = evaluate(email, reply, "", [], evidence, [])
    return reply, retrieved, result
