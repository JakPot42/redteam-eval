import textwrap
import pytest
from pathlib import Path
from redteam_eval.suite_loader import load_suite
from redteam_eval.models import TestSuite, TestCase


@pytest.fixture
def suite_yaml(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        name: Test Suite
        description: A test suite for unit testing
        version: "1.0"
        model: claude-haiku-4-5-20251001
        system_prompt: You are a helpful assistant.

        cases:
          - id: case-001
            description: Basic keyword test
            category: accuracy
            domain: cfius
            stakes: high
            prompt: What is CFIUS?
            evaluator:
              type: keyword
              required_keywords: [CFIUS, mandatory]
              forbidden_keywords: [I cannot]

          - id: case-002
            description: Regex test
            category: consistency
            domain: rai
            prompt: How many RAI principles are there?
            evaluator:
              type: regex
              pattern: "\\\\b(5|five)\\\\b"
    """)
    p = tmp_path / "suite.yaml"
    p.write_text(content, encoding="utf-8")
    return p


def test_load_suite_returns_test_suite(suite_yaml):
    suite = load_suite(suite_yaml)
    assert isinstance(suite, TestSuite)


def test_load_suite_name(suite_yaml):
    suite = load_suite(suite_yaml)
    assert suite.name == "Test Suite"


def test_load_suite_model(suite_yaml):
    suite = load_suite(suite_yaml)
    assert suite.model == "claude-haiku-4-5-20251001"


def test_load_suite_system_prompt(suite_yaml):
    suite = load_suite(suite_yaml)
    assert suite.system_prompt == "You are a helpful assistant."


def test_load_suite_case_count(suite_yaml):
    suite = load_suite(suite_yaml)
    assert len(suite.cases) == 2


def test_load_suite_first_case_id(suite_yaml):
    suite = load_suite(suite_yaml)
    assert suite.cases[0].id == "case-001"


def test_load_suite_evaluator_type(suite_yaml):
    suite = load_suite(suite_yaml)
    assert suite.cases[0].evaluator.type == "keyword"


def test_load_suite_required_keywords(suite_yaml):
    suite = load_suite(suite_yaml)
    assert "CFIUS" in suite.cases[0].evaluator.required_keywords
    assert "mandatory" in suite.cases[0].evaluator.required_keywords


def test_load_suite_forbidden_keywords(suite_yaml):
    suite = load_suite(suite_yaml)
    assert "I cannot" in suite.cases[0].evaluator.forbidden_keywords


def test_load_suite_second_case_regex(suite_yaml):
    suite = load_suite(suite_yaml)
    assert suite.cases[1].evaluator.type == "regex"
    assert suite.cases[1].evaluator.pattern is not None


def test_load_suite_case_metadata(suite_yaml):
    suite = load_suite(suite_yaml)
    case = suite.cases[0]
    assert case.category == "accuracy"
    assert case.domain == "cfius"
    assert case.stakes == "high"


def test_load_suite_missing_optional_fields(tmp_path):
    content = textwrap.dedent("""\
        name: Minimal Suite
        cases:
          - id: min-001
            prompt: Hello?
            evaluator:
              type: non_refusal
    """)
    p = tmp_path / "minimal.yaml"
    p.write_text(content, encoding="utf-8")
    suite = load_suite(p)
    assert suite.model == "claude-haiku-4-5-20251001"
    assert suite.system_prompt is None
    assert suite.cases[0].category == "general"
    assert suite.cases[0].stakes == "medium"
