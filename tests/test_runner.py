import pytest
from unittest.mock import MagicMock, patch
from redteam_eval.runner import SuiteRunner
from redteam_eval.models import Score, TestCase, TestSuite, EvaluatorConfig
from redteam_eval.providers.base import BaseProvider, ProviderResponse


def _make_provider(response_text: str = "CFIUS mandatory filing applies.", latency_ms: int = 100) -> BaseProvider:
    provider = MagicMock(spec=BaseProvider)
    provider.model_id = "mock-model"
    provider.complete.return_value = ProviderResponse(
        text=response_text,
        tokens_used=50,
        latency_ms=latency_ms,
    )
    return provider


def _make_suite(cases=None, system_prompt=None) -> TestSuite:
    default_cases = [
        TestCase(
            id="t-001",
            prompt="Does CFIUS mandatory apply?",
            evaluator=EvaluatorConfig(type="keyword", required_keywords=["mandatory"]),
        )
    ]
    return TestSuite(
        name="Mock Suite",
        cases=cases or default_cases,
        system_prompt=system_prompt,
    )


def test_runner_returns_run_result():
    provider = _make_provider()
    runner = SuiteRunner(provider=provider)
    result = runner.run(_make_suite())
    assert result.suite_name == "Mock Suite"
    assert result.model == "mock-model"


def test_runner_generates_unique_run_id():
    provider = _make_provider()
    runner = SuiteRunner(provider=provider)
    r1 = runner.run(_make_suite())
    r2 = runner.run(_make_suite())
    assert r1.run_id != r2.run_id


def test_runner_pass_when_keyword_present():
    provider = _make_provider("mandatory filing applies")
    runner = SuiteRunner(provider=provider)
    result = runner.run(_make_suite())
    assert result.case_results[0].score == Score.PASS


def test_runner_fail_when_keyword_missing():
    provider = _make_provider("No special review needed.")
    runner = SuiteRunner(provider=provider)
    result = runner.run(_make_suite())
    assert result.case_results[0].score == Score.FAIL


def test_runner_error_when_provider_raises():
    provider = MagicMock(spec=BaseProvider)
    provider.model_id = "mock-model"
    provider.complete.side_effect = RuntimeError("API timeout")
    runner = SuiteRunner(provider=provider)
    result = runner.run(_make_suite())
    assert result.case_results[0].score == Score.ERROR
    assert "API timeout" in result.case_results[0].error


def test_runner_case_count_matches_suite():
    cases = [
        TestCase(
            id=f"t-{i:03d}",
            prompt=f"Question {i}",
            evaluator=EvaluatorConfig(type="non_refusal"),
        )
        for i in range(5)
    ]
    provider = _make_provider("Here is the answer.")
    runner = SuiteRunner(provider=provider)
    result = runner.run(_make_suite(cases=cases))
    assert len(result.case_results) == 5


def test_runner_passes_suite_system_prompt():
    suite = _make_suite(system_prompt="You are an expert.")
    provider = _make_provider("mandatory filing required")
    runner = SuiteRunner(provider=provider)
    runner.run(suite)
    call_args = provider.complete.call_args
    assert call_args[0][1] == "You are an expert." or call_args[1].get("system_prompt") == "You are an expert."


def test_runner_case_system_prompt_overrides_suite():
    case_with_override = TestCase(
        id="t-001",
        prompt="Question?",
        evaluator=EvaluatorConfig(type="non_refusal"),
        system_prompt="Case-level override.",
    )
    suite = _make_suite(cases=[case_with_override], system_prompt="Suite-level prompt.")
    provider = _make_provider("Here is the answer.")
    runner = SuiteRunner(provider=provider)
    runner.run(suite)
    call_args = provider.complete.call_args
    passed_system = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("system_prompt")
    assert passed_system == "Case-level override."


def test_runner_timestamps_are_iso_format():
    provider = _make_provider()
    runner = SuiteRunner(provider=provider)
    result = runner.run(_make_suite())
    assert "T" in result.timestamp
    assert "+" in result.timestamp or "Z" in result.timestamp
