# Replora

**Evidence-grounded AI email suggestions with measurable quality and risk.**

Replora is an AI email copilot prototype for customer-support teams. It retrieves similar historical conversations, generates a suggested reply with an LLM, and then independently evaluates the reply for relevance, correctness, completeness, tone, and groundedness. Its differentiating feature is claim-level evidence checking: Replora identifies unsupported claims and converts them into an actionable risk signal before a human agent uses the suggestion.

## Why Replora?

Fluent text is not the same as a good support reply. A response can sound professional while inventing a refund, promising a delivery date, or claiming an account action happened. Replora separates **generation** from **verification**.

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
      +----------------------+
      |                      |
      v                      v
Quality evaluator       Claim/evidence checker
      |                      |
      +----------+-----------+
                 v
       Quality + Risk report
                 |
                 v
       Agent recommendation
```

## Evaluation model

Replora deliberately avoids exact-match accuracy. Two good support replies can use different wording while solving the same customer problem.

The Reply Quality Score is a weighted semantic evaluation:

- Correctness: 30%
- Relevance: 25%
- Completeness: 20%
- Groundedness: 15%
- Tone: 10%

The evaluator also reports missing key points, unsupported claims, and a recommendation. The weights prioritize factual correctness because a polished but incorrect support answer is worse than a less polished correct answer.

### Groundedness and risk

The novel layer checks important claims in the generated response against the customer email, retrieved historical evidence, and explicit facts available to the system. For example, if the model says `I have processed your refund` when the input only asks whether a refund is possible, Replora flags the statement as unsupported.

This produces two complementary signals:

- **Quality Score:** how useful and accurate the reply is.
- **Risk Score:** how much unsupported or overconfident content the reply contains.

A high-quality reply with a low risk score can be recommended for agent review. A reply containing unsupported commitments is flagged for revision.

## Dataset

The included dataset is intentionally synthetic and hand-authored for this challenge. It represents common customer-support intents including billing, refunds, cancellation, account access, technical issues, features, shipping, upgrades, invoices, and integrations.

Each example contains an incoming email, a reference reply, and structured key points. A held-out subset is used for evaluation rather than providing the reference response directly to the generator.

This is not claimed to be representative of Hiver's production traffic. Synthetic data makes the benchmark reproducible and avoids exposing private customer information. A production system should validate the evaluator against a larger, human-labeled support dataset.

## Metric validation

The evaluation metric is sanity-checked using intentionally strong, incomplete, irrelevant, and hallucinated responses. The expected behavior is that strong responses score above incomplete responses, while unsupported claims reduce groundedness and increase risk.

This validates metric behavior; it does **not** prove that an LLM-based evaluator perfectly matches human judgment. Human review remains the appropriate final validation method for production deployment.

## Project structure

```text
Replora/
├── data/
│   └── dataset.json
├── replora/
│   ├── __init__.py
│   ├── models.py
│   ├── retrieval.py
│   ├── generator.py
│   ├── evaluator.py
│   ├── grounding.py
│   └── pipeline.py
├── tests/
│   ├── test_retrieval.py
│   ├── test_evaluator.py
│   └── test_grounding.py
├── results/
│   └── .gitkeep
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
.venv\Scripts\activate
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

Run the held-out benchmark:

```bash
python main.py --evaluate
```

Run tests:

```bash
pytest
```

The project is designed to degrade gracefully when no API key is available: the local deterministic demo generator can be used to exercise retrieval and evaluation mechanics. For the challenge submission, configure an LLM provider to demonstrate true generative AI output.

## Trade-offs

### Why retrieval instead of fine-tuning?

The challenge has a strict time budget. Retrieval plus few-shot prompting is faster to implement, easier to inspect, and lets new historical examples be added without retraining a model. Fine-tuning may improve consistency at scale but adds data, training, evaluation, and deployment complexity.

### Why no vector database?

The benchmark is small. A local retrieval implementation keeps the project reproducible and avoids infrastructure that does not improve the core evaluation idea.

### Why an LLM-assisted evaluator?

Email quality is semantic and cannot be captured well by string overlap alone. The evaluator can reason about whether a response addresses the request and preserves important facts. The system still exposes structured criteria and deterministic aggregation so the final score is inspectable.

## AI tools used

AI coding assistance may be used during development. The repository's implementation, architecture decisions, dataset design, evaluation criteria, and final integration should be reviewed by the author. No private customer data is used.

## Limitations

- The dataset is synthetic and small.
- LLM evaluation can have judge bias and should be calibrated against human labels.
- Local retrieval is appropriate for the challenge benchmark but is not a production-scale search system.
- Risk detection is a safety signal, not a formal guarantee.
- A production deployment should add privacy controls, observability, prompt/version tracking, human feedback, and a larger evaluation set.

## Challenge alignment

Replora delivers all requested components:

1. A reproducible paired email/reply dataset.
2. LLM-based suggested-response generation grounded in historical examples.
3. Per-response quality and accuracy signals with explanations.
4. An overall benchmark score.
5. A documented metric and validation strategy.
6. A runnable end-to-end workflow.
