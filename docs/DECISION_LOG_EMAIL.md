# Decision Log — Email Suggested-Response Challenge

1. Use retrieval over historical email/reply pairs instead of fine-tuning. This keeps evidence inspectable and makes updates cheap.
2. Use a generative LLM for drafting because the task requires natural suggested replies.
3. Use lightweight lexical retrieval for the first implementation so the system stays easy to run and inspect.
4. Keep evaluation independent from generation so the generator does not grade itself.
5. Use a weighted semantic rubric instead of exact-match accuracy because multiple phrasings can be equally valid.
6. Weight correctness above tone because a fluent but false support reply is more harmful than awkward wording.
7. Score groundedness separately because a relevant reply can still be unsupported by historical evidence.
8. Add deterministic validation alongside the LLM judge for contradictions, unsupported operational commitments, and credential requests.
9. Keep reference replies outside the generation prompt during evaluation to prevent target leakage.
10. Report per-response scores as well as aggregate results so failures remain inspectable.
11. Treat synthetic data as development/demo data only and label it explicitly rather than presenting it as real customer evidence.
12. Validate the evaluator against independent human ratings before making strong claims about what the score represents.
13. Avoid autonomous email sending because the task is suggested-response generation and measurement, not production execution.
14. Keep retrieval and evaluation interfaces modular so embeddings or another LLM can be substituted later.
15. Document AI coding assistance and require author review so the implementation remains explainable.
