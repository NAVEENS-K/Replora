# Evaluation Protocol

Replora must be evaluated on a held-out golden set of 150-250 examples from the selected brand in Customer Support on Twitter.

## Three required prediction tasks

1. Intent classification: exact accuracy and per-intent accuracy.
2. Reply quality: LLM-as-judge score using correctness, relevance, completeness, groundedness, and tone.
3. Escalation: precision, recall, F1, and confusion matrix for auto-handle vs escalate.

## Baselines

- Trivial intent baseline: always predict the majority intent from the training split.
- Simple baseline: nearest historical customer message using the same lightweight retrieval mechanism, with its historical reply returned as the response and a fixed escalation rule.

The full Replora system is compared against both baselines on the same held-out examples.

## Human agreement protocol

Randomly sample 50-75 generated replies from the golden set. Have a human rate each reply independently on a 1-5 quality scale and label auto-handle vs escalate. Freeze the human labels before comparing them with the LLM judge. Report Pearson/Spearman correlation for quality where appropriate and agreement/F1 for the binary escalation label. Include disagreement examples.

## Leakage controls

The target conversation must never appear in the retrieval pool for its own evaluation case. Sampling, labeling, and benchmark code must keep the golden set isolated from training/retrieval examples.

## Mandatory analysis

Report the top five failure modes with concrete examples and hypotheses. Add a section titled "What is misleading about my headline number?" explaining sampling bias, synthetic/hand-label effects, judge bias, confidence intervals where available, and why offline results are not production guarantees. Finish with a one-week improvement plan.
