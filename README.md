# Replora

**Evidence-grounded AI support agent for the Hiver SDE Intern take-home assignment.**

Replora is designed around the assignment's central requirement: build a support agent from the **Customer Support on Twitter** dataset and prove that it works. The system is intended to operate on one selected brand and combines intent classification, historical-resolution retrieval, LLM reply generation, independent validation, and an auto-handle/escalate decision.

## Assignment alignment

| Requirement | Repository component |
|---|---|
| Public runnable repo | This repository |
| Customer Support on Twitter source | `data/prepare_twitter.py` + `replora/twitter_data.py` |
| Brand-specific subset | `data/raw_brand_subset.json` generated locally |
| Intent classification | `replora/intents.py` |
| Historical grounded reply | `replora/retrieval.py` + `replora/generator.py` |
| Auto-handle / escalation | `replora/decision.py` |
| 150-250 golden examples | `scripts/build_golden_candidates.py` + `scripts/label_golden.py` |
| Automated evaluation | `replora/evaluator.py` + `replora/validation.py` |
| LLM-as-judge | `replora/evaluator.py` |
| Human-vs-judge agreement | `replora/human_agreement.py` + `docs/EVALUATION_PROTOCOL.md` |
| Baselines | `replora/baselines.py` + `scripts/run_hiver_benchmark.py` |
| Failure analysis/report | `reports/FINAL_REPORT_TEMPLATE.md` |
| Decision log | `docs/DECISION_LOG.md` |

**Important:** the repository previously contained a small synthetic email benchmark used during prototyping. It is not presented as the Hiver golden set and must not be used as evidence of assignment performance. The assignment benchmark must be built from the real Twitter dataset.

## Data source and provenance

Primary source: **Customer Support on Twitter**, Kaggle dataset `thoughtvector/customer-support-on-twitter`.

The source contains tweet-level records with `tweet_id`, `author_id`, `inbound`, `created_at`, `text`, `response_tweet_id`, and `in_response_to_tweet_id`. The dataset is multi-turn and conversations can be reconstructed through the response-ID links. urlKaggle dataset pagehttps://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter

The full dataset is not committed to GitHub. Download it locally, inspect frequent outbound support-account authors, choose one brand, and generate a compact subset. The preparation command now reconstructs direct customer->brand response pairs rather than merely copying outbound brand tweets.

```bash
python data/prepare_twitter.py --input data/raw/twcs.csv --list-authors
python data/prepare_twitter.py --input data/raw/twcs.csv --brand-name <BRAND> --brand-author-id <AUTHOR_ID> --output data/raw_brand_subset.json --limit 2000
```

The final report must record the selected brand, author ID, sampling rule, exclusions, and labeling protocol.

## Intent classification

The selected brand's training data defines the intent taxonomy. Intents are not imported from Banking77 or invented independently of the selected brand.

`replora/intents.py` provides the lightweight classification path. The first implementation uses the same reproducible retrieval representation as the simple baseline. A stronger classifier can be substituted without changing the evaluation interface.

The golden set must contain a hand-labelled `intent` for every example.

## Response generation

The intended pipeline is:

```text
Customer Twitter message
        ↓
Intent classification
        ↓
Historical brand-specific retrieval
        ↓
Evidence bundle
        ↓
LLM response generation
        ↓
Independent validation
        ↓
Auto-handle / Escalate
```

`replora/generator.py` generates the suggested response. `replora/retrieval.py` retrieves historical examples. `replora/validation.py` checks claim support, required information, contradictions, unsupported operational commitments, forbidden claims, and credential requests.

## Evaluation: the main deliverable

The assignment explicitly values proof over the system. Replora therefore separates three evaluation questions:

1. **Did the agent understand the customer?** — intent accuracy and macro-F1.
2. **Did it draft a good, historically grounded reply?** — semantic reply-quality evaluation.
3. **Did it know when not to act automatically?** — escalation precision/recall/F1.

### Reply-quality rubric

The existing hybrid evaluator scores:

| Dimension | Weight |
|---|---:|
| Correctness | 30% |
| Relevance | 25% |
| Completeness | 20% |
| Groundedness | 15% |
| Tone | 10% |

Exact-match is deliberately avoided because valid support replies can use different wording. Correctness receives the largest weight because a fluent but factually incorrect support response is more harmful than an imperfectly worded correct response.

The LLM judge evaluates semantic quality, while deterministic validation independently checks explicit safety-sensitive behavior. A critical deterministic finding can override an optimistic LLM score.

### Golden evaluation set

The final assignment submission must contain **150-250 hand-labelled held-out examples** from the selected brand. The repo now provides an auditable workflow:

```bash
# 1. Build an unlabeled candidate queue from the held-out portion.
PYTHONPATH=. python scripts/build_golden_candidates.py --input data/raw/twcs.csv --brand-author-id <AUTHOR_ID> --brand-name <BRAND> --n 200

# 2. Human reviews and labels every candidate.
PYTHONPATH=. python scripts/label_golden.py --input data/golden_candidates.json --output data/golden_set.json

# 3. Only the completed human-reviewed file is accepted by the benchmark harness.
PYTHONPATH=. python scripts/run_hiver_benchmark.py --golden data/golden_set.json
```

The candidate builder is deliberately incapable of claiming that generated candidates are hand-labelled. The labeling tool records the intent taxonomy, escalation label, and 1-5 human quality rating. This separation is important for honest evaluation.

### Human agreement for the LLM judge

This is mandatory for the assignment. Follow `docs/EVALUATION_PROTOCOL.md`. Freeze approximately 50-75 generated replies, have a human rate them independently, then calculate quality-score agreement and escalation-label agreement with `replora/human_agreement.py`. Report the statistic, sample size, and representative disagreements. Never manufacture agreement numbers.

### Baselines

The final benchmark compares Replora against at least two baselines:

1. **Trivial baseline:** always predict the majority intent.
2. **Simple baseline:** nearest historical customer message and return its historical reply, with a fixed escalation policy.

`replora/baselines.py` contains the baseline implementations. `scripts/run_hiver_benchmark.py` evaluates intent accuracy, Replora macro-F1, escalation F1, and mean judged quality on the same held-out split. The target row is excluded from the retrieval pool for each Replora prediction.

### Leakage control

The target example is excluded from the retrieval pool when evaluating that example. Gold/reference fields are evaluator-only and are never passed to Replora's generator in the assignment benchmark. This prevents both direct target retrieval and hidden-label leakage.

Interactive retrieval examples are evidence/workflow examples, not hidden truth labels.

## Required report

`reports/FINAL_REPORT_TEMPLATE.md` is the report structure required by the assignment. It covers:

- problem framing and what was deliberately not built;
- results against two baselines;
- top five failure modes with real examples and hypotheses;
- **"What is misleading about my headline number?"**;
- what would be done with one more week.

`docs/DECISION_LOG.md` contains the 10-15 non-obvious engineering decisions and their rationale.

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

Configure the LLM API key using `.env` based on `.env.example`.

For the current prototype/demo path:

```bash
python main.py --email "I was charged twice for my subscription. Can you help?"
```

The legacy synthetic benchmark can still be used for unit-level development, but it is **not** the final Hiver evaluation.

For the assignment benchmark, complete the human golden set first and then run `scripts/run_hiver_benchmark.py`. The output is written to `results/hiver_benchmark.json`. The final report should quote only measured results from that artifact.

## Testing

```bash
pytest -q
```

GitHub Actions runs the automated tests on pushes and pull requests.

## What is not claimed

The repository does not claim that the current small synthetic prototype proves production quality. The Hiver submission score must come from the real selected-brand golden set, baseline comparison, and human-vs-LLM-judge validation described above.

The headline benchmark can still be misleading because a single brand, historical period, sampling strategy, and human-labeled set may not represent future traffic. LLM judges can also be biased. These limitations must be reported rather than hidden.

## AI tools and reproducibility

AI coding assistance was used during development. The implementation, evaluation design, dataset labeling decisions, and final claims must be reviewed by the author. No private customer data should be committed to this repository.
