"""Compare independently entered human ratings with stored judge ratings.

Input format is intentionally simple so the human calibration can be audited:
[{"id":"golden-001","human_quality":4,"judge_quality":0.82,
  "human_escalation":"auto-handle","judge_escalation":"SAFE TO SUGGEST"}]
Quality judge scores are normalized to the 1-5 scale before comparison.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from replora.human_agreement import compare_quality, compare_escalation


def normalize_judge_label(value: str) -> str:
    return "escalate" if value in {"⚠ NEEDS REVIEW", "✕ DO NOT SUGGEST", "escalate"} else "auto-handle"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="results/judge_agreement.json")
    args = parser.parse_args()
    rows = json.loads(Path(args.input).read_text(encoding="utf-8"))
    human_quality = [float(r["human_quality"]) for r in rows]
    judge_quality = [float(r["judge_quality"]) * 4 + 1 if float(r["judge_quality"]) <= 1 else float(r["judge_quality"]) for r in rows]
    human_escalation = [r["human_escalation"] for r in rows]
    judge_escalation = [normalize_judge_label(r["judge_escalation"]) for r in rows]
    result = {
        "quality": compare_quality(human_quality, judge_quality),
        "escalation": compare_escalation(human_escalation, judge_escalation),
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
