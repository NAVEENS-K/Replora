# Decision Log

1. Choose one brand from Customer Support on Twitter rather than mixing brands, so intent and resolution behavior remain brand-specific.
2. Use a small intent taxonomy discovered from the selected brand's data instead of importing a generic taxonomy.
3. Separate customer facts from historical workflow evidence so retrieved replies are not treated as ground truth in interactive mode.
4. Use leave-one-out evaluation to prevent the target reply from being retrieved during benchmarking.
5. Keep retrieval lightweight and reproducible because the assignment expects a subsample and a runnable pipeline under 15 minutes.
6. Use retrieval + prompting instead of fine-tuning to reduce implementation and reproduction cost.
7. Score reply quality on correctness, relevance, completeness, groundedness, and tone rather than exact string match.
8. Keep deterministic validation independent from the LLM judge for safety-sensitive claims.
9. Treat contradiction, credential requests, and unsupported operational commitments as escalation-critical findings.
10. Add a bounded single repair pass instead of an uncontrolled generation loop.
11. Report both quality and risk so a high-quality-looking but unsafe response cannot automatically pass.
12. Validate metric behavior with adversarial and monotonicity tests rather than trusting a single headline number.
13. Compare against a trivial baseline and a simple retrieval baseline before claiming improvement.
14. Reserve a human-rated subset for validating LLM-as-judge agreement and document disagreements.
15. Explicitly document what is misleading about headline metrics because benchmark scores on a synthetic or sampled set can overstate production performance.
