# Replora

**Evidence-grounded AI email suggestions with measurable quality and risk.**

Replora is an AI email copilot prototype for customer-support teams. It retrieves similar historical conversations, generates a suggested reply with an LLM, and then independently evaluates the reply for relevance, correctness, completeness, tone, and groundedness. Its differentiating feature is claim-level evidence checking: Replora identifies unsupported claims and converts them into an actionable risk signal before a human agent uses the suggestion.

## Product idea

Fluent text is not the same as a good support reply. A response can sound professional while inventing a refund, promising a delivery date, or claiming an account action happened. Replora separates **generation** from **verification**.

The product answers two questions:

1. **How good is this suggested reply?**
2. **Is there anything risky or unsupported that an agent should catch before sending it?**

## Architecture

```text
Incoming email
      |
      v
Historical retrieval
      |
      v
Relevant examples + email
      |
      v
LLM response generator
      |
      v
Suggested reply
      |
      +-------------------------+
      |                         |
      v                         v
Quality evaluator       Claim/evidence checker
      |                         |
      +------------+------------+
                   v
            Quality + Risk
                   |
                   v
             Sendability
       /          |           \
SAFE TO      NEEDS REVIEW   DO NOT SUGGEST
SUGGEST
```

## Evaluation model

Replora deliberately avoids exact-match accuracy. Two good support replies can use different wording while solving the same customer problem.

The Reply Quality Score is a weighted semantic evaluation:

| Dimension | Weight | Question |
|---|---:|---|
| Correctness | 30% | Does the response preserve the correct facts and intent? |
| Relevance | 25% | Does it address what the customer actually asked? |
| Completeness | 20% | Does it cover the important required points? |
| Groundedness | 15% | Are its claims supported by available evidence? |
| Tone | 10% | Is it appropriate for customer support? |

The weights prioritize correctness because a polished but incorrect support answer is worse than a less polished correct answer.

## Novelty: Claim & Evidence Verification

The key differentiator is that Replora does not stop at an LLM-generated quality score.

It breaks the generated response into claims and checks those claims against the customer email and retrieved historical evidence. Operational commitments receive special scrutiny.

Example:

```text
Customer:
"I was charged twice. Can I get a refund?"

Generated:
"I have processed your refund. You will receive it tomorrow."

Claim 1: refund request exists
✓ Supported

Claim 2: refund was processed
✗ Unsupported — HIGH RISK

Claim 3: refund arrives tomorrow
✗ Unsupported — HIGH RISK
```

This produces two distinct signals:

- **Quality Score:** how useful the response is.
- **Risk Score:** how much unsupported or overconfident content it contains.

## Sendability decision

Replora turns the scores into an actionable recommendation:

```text
Quality >= 80 and Risk <= 20
→ SAFE TO SUGGEST

Quality < 75 or Risk > 20
→ NEEDS REVIEW

Risk >= 50 or multiple unsupported commitments
→ DO NOT SUGGEST
```

These are challenge-time thresholds, not claims of production safety. A human agent remains responsible for the final response.

## Dataset

The included dataset is intentionally synthetic and hand-authored for this challenge. It covers common support intents including billing, refunds, cancellation, account access, technical issues, features, shipping, upgrades, invoices, and integrations.

Each example contains:

- incoming email
- reference reply
- category
- structured key points

The benchmark uses **leave-one-out evaluation**: for each target email, that exact example is removed from the retrieval pool before generating the response. Therefore the generator cannot retrieve its own reference reply.

This is not claimed to be representative of Hiver's production traffic. Synthetic data makes the benchmark reproducible and avoids exposing private customer information. A production system should validate the evaluator against a larger, human-labeled support dataset.

## Metric validation

The test suite includes intentionally strong and hallucinated responses and checks that the evaluator behaves in the expected direction:

```text
Strong / grounded reply
        >
Hallucinated / unsupported reply
```

The grounding tests separately verify that unsupported operational commitments are detected.

This is a **sanity check**, not proof that an automated evaluator perfectly matches human judgment. In production, we would calibrate the metric against human labels and monitor disagreement between human reviewers and the evaluator.

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
│   ├── decision.py
│   └── pipeline.py
├── tests/
│   ├── test_retrieval.py
│   ├── test_evaluator.py
│   ├── test_grounding.py
│   └── test_decision.py
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

Generate and evaluate a reply:

```bash
python main.py --email "I was charged twice for my subscription. Can you refund one of the charges?"
```

Run the benchmark:

```bash
python main.py --evaluate
```

Run tests:

```bash
pytest
```

Without an API key, Replora uses a deterministic local demo generator so retrieval, grounding, scoring, and sendability can still be demonstrated. Configure an LLM provider for the actual Gen-AI generation required by the challenge.

## Trade-offs

### Retrieval instead of fine-tuning

Retrieval plus few-shot prompting is faster to implement, easier to inspect, and lets new historical examples be added without retraining. Fine-tuning may improve consistency at scale but adds training and deployment complexity.

### Local retrieval instead of a vector database

The benchmark is small. Local retrieval keeps the challenge reproducible and avoids infrastructure that does not improve the core evaluation idea.

### Hybrid evaluation

Replora combines deterministic grounding/risk checks with semantic LLM evaluation. This avoids making the entire quality decision depend on one opaque number while retaining semantic judgment for dimensions such as relevance and tone.

## Limitations

- The dataset is synthetic and small.
- The lightweight retrieval method is not a production-scale search engine.
- LLM judges can have bias and variance.
- Claim grounding uses heuristic matching in the challenge implementation and should be replaced or calibrated with stronger evidence attribution in production.
- Risk detection is a safety signal, not a formal guarantee.

## AI tools used

AI coding assistance was used during development. The author reviewed the architecture, dataset design, evaluation criteria, implementation, and integration. No private customer data is used.

## Challenge alignment

Replora delivers:

1. A reproducible paired email/reply dataset.
2. LLM-based suggested-response generation grounded in historical examples.
3. Per-response quality signals with explanations.
4. Claim-level evidence and unsupported-claim detection.
5. Quality and risk scores plus an actionable sendability decision.
6. A leave-one-out benchmark and overall system score.
7. Tests validating retrieval, grounding, scoring, and decision behavior.
8. Documentation of approach, metric design, trade-offs, limitations, and AI-tool usage.
