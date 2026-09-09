# Replora — Email Suggested-Response Challenge

Replora is an evidence-grounded AI email suggested-response system.

## Goal

Given a new incoming email, Replora retrieves similar historical email/reply pairs, asks an LLM to draft a suggested response using that evidence, and independently evaluates the generated response.

```text
Incoming email
     ↓
Historical retrieval
     ↓
Evidence bundle
     ↓
LLM suggested reply
     ↓
Independent evaluation
     ↓
Quality score + reasons
```

## What "good" means

A good suggested reply should address the customer's request, be factually consistent with the available historical evidence, cover important points, avoid unsupported commitments, and use a professional tone. Exact string matching is intentionally not used because multiple phrasings can be equally valid.

## Dataset

The repository may use a compact synthetic email/reply dataset for reproducible development and demonstration. Synthetic data is explicitly labelled as such. A public or hand-authored email/reply corpus can be substituted without changing the evaluation interface. The README must state the provenance of whichever dataset is used for a final submission and why its issue distribution is representative.

## Generation

The generator is an LLM-based component, not a classical classifier. Retrieval provides brand/domain-specific historical examples as grounding context. The prompt instructs the model to use the evidence as guidance and not invent actions, policies, refunds, dates, or other operational facts.

## Evaluation

The evaluator uses a weighted semantic rubric:

- Correctness — 30%
- Relevance — 25%
- Completeness — 20%
- Groundedness — 15%
- Tone — 10%

Deterministic validation is applied independently for safety-sensitive behavior and unsupported operational claims. This makes the evaluation more robust than relying on an LLM judge alone.

For each response the system reports the component scores, overall quality score, risk score, evidence coverage, missing points, unsupported claims, validation findings, and recommendation.

## Why these metrics

Correctness is weighted most heavily because a fluent but factually wrong support reply is worse than an imperfectly worded correct one. Relevance measures whether the response addresses the actual email. Completeness checks important requested points. Groundedness measures support from retrieved historical evidence. Tone measures whether the response is appropriate for customer support.

The metric should be validated against human ratings on a held-out calibration sample before claiming that it represents real-world quality. Agreement statistics should be reported rather than assumed.

## Trade-offs

The implementation favors a lightweight lexical retrieval layer over a vector database so that the project remains easy to run, inspect, and reproduce. The retrieval layer can later be replaced with embeddings without changing the generation/evaluation interfaces.

The system deliberately does not attempt autonomous email sending, production CRM integration, fine-tuning, or broad workflow automation. The task is suggested-response generation and measurement.

## AI tools

AI coding assistance was used during development. Generated code was reviewed and modified as part of the implementation. Final dataset provenance, evaluation claims, and benchmark numbers must be verified by the project author.
