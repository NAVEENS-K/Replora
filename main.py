import argparse
import json
from pathlib import Path
from replora.retrieval import load_dataset, retrieve
from replora.generator import generate_reply
from replora.evaluator import evaluate


def print_result(email, reply, result, retrieved):
    print("\n" + "=" * 64)
    print("REPLORA")
    print("=" * 64)
    print("\nCUSTOMER EMAIL\n" + email)
    print("\nSUGGESTED REPLY\n" + reply)
    print("\nREPLY QUALITY")
    for name in ["correctness", "relevance", "completeness", "groundedness", "tone"]:
        print(f"{name.title():16} {getattr(result, name) * 100:.0f}/100")
    print(f"\nQuality Score     {result.quality_score:.1f}/100")
    print(f"Risk Score        {result.risk_score:.1f}/100")
    print(f"Evidence Coverage {result.evidence_coverage}/{result.evidence_total}")
    if result.unsupported_claims:
        print("\nUnsupported claims:")
        for x in result.unsupported_claims: print("- " + x)
    if result.missing_points:
        print("\nMissing points:")
        for x in result.missing_points: print("- " + x)
    print("\nRecommendation: " + result.recommendation)
    print("\nRetrieved examples:")
    for x in retrieved: print(f"- {x.example.id} ({x.score:.3f}) [{x.example.category}]")


def benchmark(examples):
    # Leave-one-out evaluation prevents the test email itself from being retrieved.
    results = []
    for i, target in enumerate(examples):
        pool = examples[:i] + examples[i+1:]
        retrieved = retrieve(target.incoming_email, pool, top_k=3)
        reply = generate_reply(target.incoming_email, retrieved)
        evidence = [x.example.reference_reply for x in retrieved]
        result = evaluate(target.incoming_email, reply, target.reference_reply, target.key_points, evidence)
        results.append({"id": target.id, "category": target.category, "quality_score": result.quality_score, "risk_score": result.risk_score, "correctness": result.correctness, "relevance": result.relevance, "completeness": result.completeness, "groundedness": result.groundedness, "tone": result.tone, "unsupported_claims": result.unsupported_claims, "missing_points": result.missing_points, "recommendation": result.recommendation})
        print(f"{target.id:8} quality={result.quality_score:5.1f} risk={result.risk_score:5.1f}")
    avg = lambda key: round(sum(x[key] for x in results) / len(results) * (100 if key != "quality_score" and key != "risk_score" else 1), 2)
    summary = {
        "test_cases": len(results),
        "average_quality_score": round(sum(x["quality_score"] for x in results) / len(results), 2),
        "average_risk_score": round(sum(x["risk_score"] for x in results) / len(results), 2),
        "average_correctness": avg("correctness"),
        "average_relevance": avg("relevance"),
        "average_completeness": avg("completeness"),
        "average_groundedness": avg("groundedness"),
        "average_tone": avg("tone"),
        "high_risk_responses": sum(x["risk_score"] > 20 for x in results),
        "responses": results,
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/evaluation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n" + "=" * 64)
    print("REPLORA BENCHMARK")
    print("=" * 64)
    print(f"Test cases:        {summary['test_cases']}")
    print(f"Quality Score:     {summary['average_quality_score']}")
    print(f"Correctness:       {summary['average_correctness']}")
    print(f"Relevance:         {summary['average_relevance']}")
    print(f"Completeness:      {summary['average_completeness']}")
    print(f"Groundedness:      {summary['average_groundedness']}")
    print(f"Tone:              {summary['average_tone']}")
    print(f"High-risk replies: {summary['high_risk_responses']}")


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
        # Interactive evaluation uses retrieved examples as evidence and labels the closest historical reply as a reference proxy.
        # Benchmark mode uses a true held-out reference.
        ref = retrieved[0].example if retrieved else None
        result = evaluate(args.email, reply, ref.reference_reply if ref else "", ref.key_points if ref else [], [x.example.reference_reply for x in retrieved])
        print_result(args.email, reply, result, retrieved)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
