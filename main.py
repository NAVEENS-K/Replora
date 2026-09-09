import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
from replora.retrieval import load_dataset, retrieve
from replora.generator import generate_reply
from replora.evaluator import evaluate
from replora.decision import decide

load_dotenv()


def print_result(email, reply, result, retrieved):
    decision = decide(result.quality_score, result.risk_score, result.unsupported_claims)
    print("\n" + "=" * 68)
    print("REPLORA")
    print("=" * 68)
    print("\nCUSTOMER EMAIL\n" + email)
    print("\nSUGGESTED REPLY\n" + reply)
    print("\nREPLY QUALITY")
    for name in ["correctness", "relevance", "completeness", "groundedness", "tone"]:
        print(f"{name.title():16} {getattr(result, name) * 100:.0f}/100")
    print(f"\nQuality Score     {result.quality_score:.1f}/100")
    print(f"Risk Score        {result.risk_score:.1f}/100")
    print(f"Evidence Coverage {result.evidence_coverage}/{result.evidence_total}")
    if result.claim_checks:
        print("\nCLAIM VERIFICATION")
        for c in result.claim_checks:
            print(f"- [{c.status.upper()} | {c.risk}] {c.claim}")
            print(f"  {c.evidence}")
    if result.missing_points:
        print("\nMissing points:")
        for x in result.missing_points:
            print("- " + x)
    print("\nSENDABILITY: " + decision.label)
    print(decision.reason)
    print("\nRetrieved examples:")
    for x in retrieved:
        print(f"- {x.example.id} ({x.score:.3f}) [{x.example.category}]")


def benchmark(examples):
    results = []
    for i, target in enumerate(examples):
        pool = examples[:i] + examples[i + 1:]
        retrieved = retrieve(target.incoming_email, pool, top_k=3)
        reply = generate_reply(target.incoming_email, retrieved)
        evidence = [x.example.reference_reply for x in retrieved]
        result = evaluate(target.incoming_email, reply, target.reference_reply, target.key_points, evidence, target.forbidden_claims)
        decision = decide(result.quality_score, result.risk_score, result.unsupported_claims)
        results.append({"id": target.id, "category": target.category, "quality_score": result.quality_score, "risk_score": result.risk_score, "evidence_coverage": result.evidence_coverage, "evidence_total": result.evidence_total, "correctness": result.correctness, "relevance": result.relevance, "completeness": result.completeness, "groundedness": result.groundedness, "tone": result.tone, "unsupported_claims": result.unsupported_claims, "missing_points": result.missing_points, "recommendation": decision.label})
        print(f"{target.id:8} quality={result.quality_score:5.1f} risk={result.risk_score:5.1f} coverage={result.evidence_coverage}/{result.evidence_total} {decision.label}")
    if not results:
        return
    summary = {
        "test_cases": len(results),
        "average_quality_score": round(sum(x["quality_score"] for x in results) / len(results), 2),
        "average_risk_score": round(sum(x["risk_score"] for x in results) / len(results), 2),
        "average_evidence_coverage": round(sum(x["evidence_coverage"] / max(1, x["evidence_total"]) for x in results) / len(results) * 100, 2),
        "average_correctness": round(sum(x["correctness"] for x in results) / len(results) * 100, 2),
        "average_relevance": round(sum(x["relevance"] for x in results) / len(results) * 100, 2),
        "average_completeness": round(sum(x["completeness"] for x in results) / len(results) * 100, 2),
        "average_groundedness": round(sum(x["groundedness"] for x in results) / len(results) * 100, 2),
        "average_tone": round(sum(x["tone"] for x in results) / len(results) * 100, 2),
        "high_risk_responses": sum(x["risk_score"] >= 50 for x in results),
        "safe_to_suggest": sum(x["recommendation"] == "SAFE TO SUGGEST" for x in results),
        "needs_review": sum(x["recommendation"] == "NEEDS REVIEW" for x in results),
        "do_not_suggest": sum(x["recommendation"] == "DO NOT SUGGEST" for x in results),
        "responses": results,
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/evaluation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n" + "=" * 68)
    print("REPLORA BENCHMARK")
    print("=" * 68)
    for k, label in [("test_cases", "Test cases"), ("average_quality_score", "Quality Score"), ("average_risk_score", "Risk Score"), ("average_evidence_coverage", "Evidence Coverage"), ("average_correctness", "Correctness"), ("average_relevance", "Relevance"), ("average_completeness", "Completeness"), ("average_groundedness", "Groundedness"), ("average_tone", "Tone"), ("high_risk_responses", "High-risk replies"), ("safe_to_suggest", "Safe to suggest"), ("needs_review", "Needs review"), ("do_not_suggest", "Do not suggest")]:
        print(f"{label + ':':21} {summary[k]}")


def main():
    parser = argparse.ArgumentParser(description="Replora AI email copilot")
    parser.add_argument("--email", help="Generate and evaluate a reply for an email")
    parser.add_argument("--evaluate", action="store_true", help="Run the leave-one-out benchmark")
    args = parser.parse_args()
    examples = load_dataset()
    if args.evaluate:
        benchmark(examples)
    elif args.email:
        retrieved = retrieve(args.email, examples, top_k=3)
        reply = generate_reply(args.email, retrieved)
        ref = retrieved[0].example if retrieved else None
        result = evaluate(args.email, reply, ref.reference_reply if ref else "", ref.key_points if ref else [], [x.example.reference_reply for x in retrieved], ref.forbidden_claims if ref else [])
        print_result(args.email, reply, result, retrieved)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
