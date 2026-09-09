# Replora

**Evidence-grounded AI suggested-response system for email.**

Replora takes an incoming customer email, retrieves similar historical email/reply pairs, uses an LLM to draft a suggested response, and independently evaluates how good and well-grounded that response is.

This repository targets the **AI email suggested-response challenge**. The core deliverable is not merely generation, but a credible way to measure response quality.

## Approach

```text
Incoming email
      ↓
Historical email/reply retrieval
      ↓
Relevant evidence
      ↓
LLM suggested reply
      ↓
Independent evaluator + deterministic validation
      ↓
Per-response quality + explanation
```

## 1. Dataset

The project owns its dataset interface and supports compact email/reply pairs. The included prototype data is synthetic and explicitly for development/demo use; it must not be described as real customer data.

The dataset format contains an incoming email, its historical reply, key points, and forbidden claims. See `data/README.md` and `data/dataset.json`.

For a final submission, the README should identify the exact dataset source, explain its provenance, and justify why the sample is representative of the intended support workload.

## 2. Generative response system

`replora/generator.py` uses an LLM to draft the suggested reply. It is grounded by historical examples returned by `replora/retrieval.py`.

The generator is instructed not to invent refunds, credits, account changes, delivery dates, policies, guarantees, or completed actions that are not established by the available evidence.

If an API key is unavailable, a deterministic demo path keeps the repository runnable end-to-end. API-backed runs use the configured LLM provider.

## 3. Measuring response quality

Evaluation is the primary focus. Exact-match accuracy is inappropriate because different replies can be equally good.

The hybrid evaluator scores:

| Dimension | Weight |
|---|---:|
| Correctness | 30% |
| Relevance | 25% |
| Completeness | 20% |
| Groundedness | 15% |
| Tone | 10% |

Correctness has the highest weight because a fluent but factually incorrect support reply is more harmful than an imperfectly worded correct response.

The LLM judge evaluates semantic response quality. Deterministic validation independently checks evidence support, missing required points, contradictions, unsupported operational claims, credential/secret requests, and structural problems. Critical deterministic findings cannot be overridden by an optimistic LLM score.

Every evaluated response exposes component scores, overall quality score, risk score, evidence coverage, missing points, unsupported claims, validation findings, and recommendation.

### Validating the evaluator

A quality metric is only useful if it reflects human judgement. `replora/human_agreement.py` provides agreement calculations for an independently human-rated calibration sample, including Spearman correlation, mean absolute error, exact agreement, Cohen's kappa, and label agreement.

Do not manufacture human ratings or agreement statistics. A final benchmark should freeze a calibration sample, have a human independently rate it, then report measured agreement and representative disagreements.

## Dataset/evaluation separation

Reference replies and gold metadata are evaluator inputs. They are not supplied to the generator as hidden truth. During leave-one-out evaluation, the target example is removed from the retrieval pool. This prevents direct target retrieval and target-label leakage.

Synthetic development data is not presented as human-labelled evidence.

## Running

Install dependencies:

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

Configure the LLM API key in `.env` using `.env.example` for an API-backed run.

Run the end-to-end demo:

```bash
python main.py --email "I was charged twice for my subscription. Can you help?"
```

Run automated tests:

```bash
pytest -q
```

Run the reusable benchmark harness with a completed email/reply evaluation set:

```bash
PYTHONPATH=. python scripts/run_hiver_benchmark.py --golden data/golden_set.json
```

The script name is retained for compatibility with the existing harness; the project no longer claims that Twitter or Hiver-specific data is required for this challenge.

## Final evaluation report

A final submission should include:

1. Dataset source and sampling rationale.
2. Overall mean quality score.
3. Per-dimension scores.
4. Per-response scores and explanations.
5. Strong and weak response examples.
6. Human-vs-judge calibration results.
7. Limitations and known failure cases.

The headline claim should be reproducible from a clean checkout using the documented commands.

## Trade-offs

A lightweight lexical retrieval implementation was chosen instead of a vector database to keep the system inspectable and easy to reproduce. Embedding retrieval can be substituted later without changing the generator/evaluator contract.

The system intentionally does not attempt autonomous email sending, CRM integration, fine-tuning, or production workflow automation. The scope is suggested-response generation and trustworthy measurement.

## AI tools

AI coding assistance was used during development. The author should review and be able to explain the implementation. Borrowed material and external datasets should be cited in the final submission.

## Project structure

```text
replora/
  retrieval.py       # historical email retrieval
  generator.py       # LLM suggested-response generation
  evaluator.py       # hybrid semantic evaluation
  grounding.py       # evidence/claim analysis
  validation.py      # deterministic safety and grounding checks
  models.py          # shared data models
  human_agreement.py # human-vs-judge calibration statistics

data/
  dataset.json       # compact synthetic development dataset

scripts/
  run_hiver_benchmark.py  # reusable benchmark harness

tests/               # automated tests
```

See `docs/EMAIL_CHALLENGE.md` for the problem framing and evaluation philosophy.
