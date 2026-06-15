"""
Motivating demo: red-team all 9 portfolio compliance projects with one command.

Usage:
    python run_demo.py
    python run_demo.py --suite suites/cfius_consistency.yaml
    python run_demo.py --all
    python run_demo.py --no-save
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

from redteam_eval.suite_loader import load_suite
from redteam_eval.runner import SuiteRunner
from redteam_eval.tracker import ResultTracker
from redteam_eval.dashboard import generate_dashboard
from redteam_eval.providers.claude import ClaudeProvider

SUITES_DIR = Path(__file__).parent / "suites"

DEMO_SUITES = [
    SUITES_DIR / "portfolio_overview.yaml",
]

ALL_SUITES = [
    SUITES_DIR / "portfolio_overview.yaml",
    SUITES_DIR / "cfius_consistency.yaml",
    SUITES_DIR / "rai_accuracy.yaml",
    SUITES_DIR / "ncf_refusal.yaml",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="redteam-eval motivating demo")
    parser.add_argument("--suite", help="Path to a specific suite YAML to run")
    parser.add_argument("--all", action="store_true", help="Run all four built-in suites")
    parser.add_argument("--model", default=None, help="Override model for all suites")
    parser.add_argument("--no-save", action="store_true", help="Skip saving results")
    parser.add_argument("--dashboard", action="store_true", help="Generate dashboard PNGs")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set. Export it and retry.")
        sys.exit(1)

    if args.suite:
        suite_paths = [Path(args.suite)]
    elif args.all:
        suite_paths = ALL_SUITES
    else:
        suite_paths = DEMO_SUITES

    tracker = ResultTracker() if not args.no_save else None
    total_pass = total_fail = total_cases = 0

    print(f"\n{'='*60}")
    print("  redteam-eval — Portfolio Red-Team Demo")
    print(f"{'='*60}\n")

    for suite_path in suite_paths:
        suite = load_suite(suite_path)
        if args.model:
            suite.model = args.model

        provider = ClaudeProvider(model=suite.model, api_key=api_key)
        runner = SuiteRunner(provider=provider)

        print(f"Running: {suite.name}")
        print(f"  Model : {suite.model}")
        print(f"  Cases : {len(suite.cases)}")

        result = runner.run(suite, verbose=True)

        total_pass += result.pass_count
        total_fail += result.fail_count
        total_cases += len(result.case_results)

        print(f"  Result: {result.pass_count}/{len(result.case_results)} PASS ({result.pass_rate:.0%})")

        if tracker:
            tracker.save(result)
            print(f"  Saved : run {result.run_id[:8]}")

        if args.dashboard:
            out = Path(f"dashboard_{result.run_id[:8]}.png")
            generate_dashboard(tracker.get_run(result.run_id[:8]) if tracker else _result_to_dict(result), out)
            print(f"  Chart : {out}")

        print()

    print(f"{'='*60}")
    print(f"  TOTAL: {total_pass}/{total_cases} PASS  ({total_pass/total_cases:.0%})")
    print(f"{'='*60}\n")

    if not args.no_save:
        print("Run  redteam list  to see all saved results.")
        print("Run  redteam dashboard <run-id>  to generate a chart.")


def _result_to_dict(result) -> dict:
    """Minimal dict for dashboard generation without a saved tracker."""
    return {
        "run_id": result.run_id,
        "suite_name": result.suite_name,
        "model": result.model,
        "timestamp": result.timestamp,
        "pass_rate": result.pass_rate,
        "cases": [
            {
                "test_id": c.test_id,
                "score": c.score.value,
                "reason": c.reason,
                "latency_ms": c.latency_ms,
                "tokens_used": c.tokens_used,
                "prompt": c.prompt,
                "response": c.response,
                "error": c.error,
            }
            for c in result.case_results
        ],
    }


if __name__ == "__main__":
    main()
