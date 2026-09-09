# Dataset workflow

The assignment's primary source is Kaggle's **Customer Support on Twitter** dataset (`thoughtvector/customer-support-on-twitter`). Do not commit the full multi-million-row source dataset to this repository.

## Download

Download the Kaggle dataset into `data/raw/` using Kaggle's normal download mechanism. If the dataset requires authentication, configure Kaggle credentials locally; never commit credentials.

## Build a brand subset

Use `data/prepare_twitter.py` to inspect the source CSV, select one brand, reconstruct customer/support turns where possible, and write a compact JSONL/JSON subset for the benchmark.

## Golden set

The final submission should contain 150-250 hand-labelled held-out examples for the selected brand. Use `golden_set_template.json` as the schema if building the set manually.

## Provenance

The source is real customer-support Twitter data released for research. The project should state the selected brand, sampling rule, date/row filters, exclusions, and labeling protocol in the final report. Never claim that the golden set is representative of all Hiver traffic.
