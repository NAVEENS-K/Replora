# Replora — Hiver SDE Intern Take-Home Report

> Fill the bracketed fields only after running the real-brand benchmark. Do not invent results.

## 1. Problem framing

**Selected brand:** [BRAND]

Good means: correctly identify the customer's intent, draft a reply consistent with how this brand historically resolves that intent, and escalate cases where automation is unsafe or uncertain.

Not built: [list deliberate exclusions such as full production deployment, autonomous account actions, private-message tooling].

## 2. Data and golden set

Source: Customer Support on Twitter (`thoughtvector/customer-support-on-twitter`).

Sampling: [brand selection + sampling rule].

Golden set: [150-250] hand-labelled held-out examples.

Labels: intent, expected resolution/reference reply, escalation requirement, human reply-quality rating for the judge-agreement subset.

## 3. Results

| Task | Trivial baseline | Simple baseline | Replora |
|---|---:|---:|---:|
| Intent accuracy | [ ] | [ ] | [ ] |
| Reply quality | [ ] | [ ] | [ ] |
| Escalation F1 | [ ] | [ ] | [ ] |

LLM-as-judge quality: [mean / confidence interval if calculated].

Human-vs-judge agreement: [metric and value].

## 4. Why these metrics

Intent accuracy measures whether the agent understood the customer's problem. Reply quality uses correctness, relevance, completeness, groundedness, and tone because exact text match would unfairly penalize valid paraphrases. Escalation F1 captures the cost of both unsafe auto-handling and excessive escalation.

The LLM judge is independently checked against human ratings on a frozen subset. Deterministic validation remains authoritative for explicit safety-sensitive claims.

## 5. Top five failure modes

1. [Failure mode + real example + hypothesis]
2. [Failure mode + real example + hypothesis]
3. [Failure mode + real example + hypothesis]
4. [Failure mode + real example + hypothesis]
5. [Failure mode + real example + hypothesis]

## 6. What is misleading about my headline number?

The headline result is an offline score on a sampled, hand-labelled set from one brand and one historical period. It does not prove production performance. Sampling choices, label ambiguity, retrieval overlap, LLM-judge bias, and distribution shift can all inflate or reduce the number. Human agreement and failure examples are therefore reported alongside the headline score.

## 7. One more week

- [ ] Expand and rebalance the golden set.
- [ ] Calibrate escalation thresholds by intent.
- [ ] Improve conversation reconstruction and retrieval.
- [ ] Increase human-rated judge calibration.
- [ ] Evaluate robustness on newer/out-of-distribution messages.
