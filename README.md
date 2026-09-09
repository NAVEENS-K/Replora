# Replora

**Evidence-grounded AI email suggestions with measurable quality, trust, and risk.**

Replora is an AI email copilot prototype for customer-support teams. It retrieves similar historical conversations, generates a suggested reply with an LLM, independently validates the reply, evaluates semantic quality, and converts the findings into a risk-aware sendability decision.

The central design principle is simple: **an LLM may generate a reply and help judge semantic quality, but it does not have final authority over safety-sensitive claims.**

## Why Replora

A fluent support reply can still be dangerous. It may invent a refund, promise a delivery date, claim an account action happened, contradict the customer's state, or request a secret. Replora separates generation from verification.

It answers two questions:

1. **How good is this suggested reply?**
2. **Is there evidence that the reply is safe enough for an agent to use?**

## Architecture

```text
Customer email
      |
      v
Intent-aware retrieval
      |
      v
Evidence bundle
      |
      v
LLM generator
      |
      v
Generated reply
      |
      +-----------------------------+
      |                             |
      v                             v
Independent validation         LLM evaluator
      |                             |
  +---+---+---+---+---+       Semantic quality
  |   |   |   |   |             judgment
Claims Required Forbidden Contradiction Security
  |   |   |   |   |
  +---+---+---+---+
          |
          v
    Validation report
          |
          +----------------+
          |                |
          v                v
      Quality           Risk engine
          |                |
          +-------+--------+
                  v
            Sendability
       /         |          \
SAFE TO     NEEDS REVIEW   DO NOT SUGGEST
SUGGEST
```

If the first LLM reply contains a high-risk issue, Replora can perform one validator-guided refinement pass and validate the revised response again. This is deliberately bounded to avoid an uncontrolled agent loop.

## Evaluation model

Replora deliberately avoids exact-match accuracy. Two good support replies can use different wording while solving the same customer problem.

The Reply Quality Score is weighted as follows:

| Dimension | Weight | Question |
|---|---:|---|
| Correctness | 30% | Does the response preserve the correct facts and intent? |
| Relevance | 25% | Does it address what the customer actually asked? |
| Completeness | 20% | Does it cover important required points? |
| Groundedness | 15% | Are claims supported by available evidence? |
| Tone | 10% | Is it appropriate for customer support? |

Correctness has the largest weight because a polished but incorrect support answer is worse than a less polished correct answer.

Replora uses a **hybrid evaluator**. The LLM judges semantic dimensions such as correctness, relevance, completeness and tone. The deterministic validation layer independently checks safety-sensitive claims. Deterministic findings can lower groundedness and risk can override a favorable LLM judgment.

## Independent validation layer

`replora/validation.py` is a separate safety-oriented layer. It checks:

- claim-level evidence support;
- required-point coverage;
- forbidden-claim violations;
- contradictions with explicit customer state;
- credential and secret requests;
- unsupported operational commitments;
- basic structural problems.

Claims receive statuses such as **Supported**, **Partially supported**, **Unsupported**, and **Unverified**. Critical findings include contradictions, forbidden claims and security issues.

Example:

```text
Customer:
"I was charged twice. Can I get a refund?"

Generated:
"I have processed your refund. You will receive it tomorrow."

Claim 1: refund was processed
✗ Unsupported — HIGH/CRITICAL RISK

Claim 2: refund arrives tomorrow
✗ Unsupported — HIGH/CRITICAL RISK

Decision: DO NOT SUGGEST
```

A contradiction is treated separately from ordinary lack of evidence. For example, a customer saying an order has not arrived and a generated reply saying it has arrived is a critical validation finding.

## Sendability

```text
Critical validation finding
OR risk >= 50
OR multiple unsupported claims
→ DO NOT SUGGEST

Quality >= 80
AND risk <= 20
AND no unsupported claims
AND validation >= 80
→ SAFE TO SUGGEST

Otherwise
→ NEEDS REVIEW
```

These are challenge-time thresholds, not claims of production safety. A human agent remains responsible for the final response.

## Dataset

The checked-in dataset is synthetic and hand-authored for this challenge. It covers billing, refunds, cancellation, account access, 2FA, technical issues, features, shipping, upgrades, invoices, and integrations.

Each example contains:

- incoming email;
- reference reply;
- category;
- required key points;
- forbidden claims.

Forbidden claims are evaluation constraints and are not supplied to the generator, preventing direct leakage of the expected failure cases.

The benchmark uses **leave-one-out evaluation**. For every target, the exact target example is removed from the retrieval pool before generation, so the generator cannot retrieve its own reference answer.

The dataset is intentionally not presented as representative of Hiver production traffic. Synthetic data makes the benchmark reproducible and avoids private customer data. A production system should calibrate the evaluator on a substantially larger human-labeled support dataset.

## Metric validation

Replora does not assume that a metric is trustworthy merely because it produces a plausible number. `tests/test_metric_sanity.py` checks directional properties of the evaluator.

The suite tests that:

- a grounded response scores better and has lower risk than a hallucinated response;
- missing required information reduces completeness;
- paraphrases are not rejected just because wording differs;
- unsupported operational claims trigger conservative decisions;
- validation detects security-sensitive requests and contradictions.

The intended ranking is:

```text
Strong + grounded
      >
Correct but incomplete
      >
Vague / weakly supported
      >
Unsupported / hallucinated
      >
Contradictory / unsafe
```

This is **metric sanity validation**, not proof of human correlation. The next production validation step would be a human-labeled dataset: compare human quality/safety ratings with Replora scores, inspect disagreements, measure agreement, and calibrate thresholds.

## Benchmark outputs

`python main.py --evaluate` reports:

- average quality score;
- average risk score;
- average validation score;
- evidence coverage;
- correctness, relevance, completeness, groundedness and tone;
- high-risk replies;
- contradictions and security issues;
- SAFE / REVIEW / DO NOT SUGGEST counts.

The detailed per-case report is written to `results/evaluation.json`.

## Project structure

```text
Replora/
├── data/
│   ├── dataset.json
│   └── generate_dataset.py
├── replora/
│   ├── __init__.py
│   ├── models.py
│   ├── retrieval.py
│   ├── generator.py
│   ├── evaluator.py
│   ├── grounding.py
│   ├── validation.py
│   ├── decision.py
│   └── pipeline.py
├── tests/
│   ├── test_retrieval.py
│   ├── test_evaluator.py
│   ├── test_grounding.py
│   ├── test_validation.py
│   ├── test_decision.py
│   └── test_metric_sanity.py
├── results/
│   └── evaluation.json
├── main.py
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your LLM API key.

## Usage

Generate and validate a reply:

```bash
python main.py --email "I was charged twice for my subscription. Can you refund one of the charges?"
```

Run the leave-one-out benchmark:

```bash
python main.py --evaluate
```

Run tests:

```bash
pytest
```

Without an API key, Replora uses a deterministic local demo generator so retrieval, validation, grounding, scoring and sendability can still be demonstrated. Configure an LLM provider for the actual LLM generation required by the challenge.

## Trade-offs

### Retrieval instead of fine-tuning

Retrieval plus few-shot prompting is faster to implement, easier to inspect, and lets new examples be added without retraining. Fine-tuning may improve consistency at scale but adds training and deployment complexity.

### Lightweight retrieval instead of a vector database

The benchmark is small. Local weighted lexical retrieval keeps the challenge reproducible and avoids infrastructure that does not directly improve the evaluation idea.

### Deterministic validation plus LLM evaluation

Rules are strong for explicit safety constraints and operational claims but weak at nuanced semantics. The LLM is stronger at semantic judgment but can be biased or overconfident. Replora therefore uses each where it is strongest and lets deterministic critical findings override optimistic semantic scoring.

### One bounded refinement pass

A validator-guided second generation can repair an unsafe suggestion. The loop is intentionally limited to one retry so the system remains predictable, inexpensive and easy to audit.

## Limitations

- The dataset is synthetic and currently small.
- Lightweight retrieval is not a production-scale search engine.
- The validation layer uses conservative heuristics rather than a full natural-language inference model.
- LLM judges can have bias and variance.
- Risk detection is a conservative safety signal, not a formal guarantee.
- Human correlation has not yet been measured on production support data.

## AI tools used

AI coding assistance was used during development. The author reviewed the architecture, dataset design, evaluation criteria, implementation, and integration. No private customer data is used.

## Challenge alignment

Replora delivers:

1. A reproducible paired email/reply dataset.
2. LLM-based suggested-response generation grounded in historical examples.
3. Independent claim/evidence validation.
4. Required-point and forbidden-claim checking.
5. Contradiction and security-risk detection.
6. Semantic quality evaluation with explicit weighted metrics.
7. Quality and risk scores plus actionable sendability.
8. Validator-guided bounded refinement.
9. Leave-one-out benchmark evaluation without target leakage.
10. Adversarial metric sanity tests.
11. Automated tests and GitHub Actions.
12. Documentation of approach, trade-offs, limitations and AI-tool usage.
