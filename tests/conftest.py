import pytest
from redteam_eval.models import EvaluatorConfig, TestCase, Score, CaseResult, RunResult


def make_test_case(
    id="test-001",
    prompt="What is CFIUS?",
    eval_type="keyword",
    required_keywords=None,
    forbidden_keywords=None,
    pattern=None,
) -> TestCase:
    return TestCase(
        id=id,
        prompt=prompt,
        evaluator=EvaluatorConfig(
            type=eval_type,
            required_keywords=required_keywords or [],
            forbidden_keywords=forbidden_keywords or [],
            pattern=pattern,
        ),
    )


def make_case_result(test_id="test-001", score=Score.PASS, reason="ok") -> CaseResult:
    return CaseResult(
        test_id=test_id,
        prompt="test prompt",
        response="test response",
        score=score,
        reason=reason,
        latency_ms=100,
        tokens_used=50,
    )


def make_run_result(suite_name="Test Suite", case_results=None) -> RunResult:
    return RunResult(
        run_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        suite_name=suite_name,
        model="claude-haiku-4-5-20251001",
        timestamp="2026-06-14T12:00:00+00:00",
        case_results=case_results or [],
    )
