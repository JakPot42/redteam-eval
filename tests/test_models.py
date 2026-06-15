import pytest
from redteam_eval.models import (
    CaseResult,
    EvaluatorConfig,
    RunResult,
    Score,
    TestCase,
    TestSuite,
)


def test_score_values():
    assert Score.PASS == "PASS"
    assert Score.FAIL == "FAIL"
    assert Score.WARN == "WARN"
    assert Score.ERROR == "ERROR"


def test_evaluator_config_defaults():
    cfg = EvaluatorConfig(type="keyword")
    assert cfg.required_keywords == []
    assert cfg.forbidden_keywords == []
    assert cfg.pattern is None
    assert cfg.judge_criteria is None


def test_test_case_defaults():
    tc = TestCase(
        id="x",
        prompt="hello",
        evaluator=EvaluatorConfig(type="keyword"),
    )
    assert tc.category == "general"
    assert tc.domain == ""
    assert tc.tags == []
    assert tc.stakes == "medium"
    assert tc.system_prompt is None


def test_run_result_pass_count():
    from tests.conftest import make_case_result, make_run_result

    results = [
        make_case_result("a", Score.PASS),
        make_case_result("b", Score.FAIL),
        make_case_result("c", Score.PASS),
        make_case_result("d", Score.ERROR),
    ]
    run = make_run_result(case_results=results)
    assert run.pass_count == 2


def test_run_result_fail_count():
    from tests.conftest import make_case_result, make_run_result

    results = [make_case_result("a", Score.FAIL), make_case_result("b", Score.FAIL)]
    run = make_run_result(case_results=results)
    assert run.fail_count == 2


def test_run_result_pass_rate():
    from tests.conftest import make_case_result, make_run_result

    results = [
        make_case_result("a", Score.PASS),
        make_case_result("b", Score.FAIL),
        make_case_result("c", Score.PASS),
        make_case_result("d", Score.PASS),
    ]
    run = make_run_result(case_results=results)
    assert run.pass_rate == pytest.approx(0.75)


def test_run_result_pass_rate_empty():
    from tests.conftest import make_run_result

    run = make_run_result(case_results=[])
    assert run.pass_rate == 0.0


def test_test_suite_defaults():
    suite = TestSuite(name="My Suite", cases=[])
    assert suite.model == "claude-haiku-4-5-20251001"
    assert suite.system_prompt is None
    assert suite.version == "1.0"
