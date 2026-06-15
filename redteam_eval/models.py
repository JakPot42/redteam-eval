from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Score(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class EvaluatorConfig:
    type: str
    required_keywords: list[str] = field(default_factory=list)
    forbidden_keywords: list[str] = field(default_factory=list)
    pattern: Optional[str] = None
    judge_criteria: Optional[str] = None
    judge_model: Optional[str] = None


@dataclass
class TestCase:
    id: str
    prompt: str
    evaluator: EvaluatorConfig
    description: str = ""
    category: str = "general"
    domain: str = ""
    system_prompt: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    stakes: str = "medium"


@dataclass
class TestSuite:
    name: str
    cases: list[TestCase]
    description: str = ""
    version: str = "1.0"
    model: str = "claude-haiku-4-5-20251001"
    system_prompt: Optional[str] = None


@dataclass
class CaseResult:
    test_id: str
    prompt: str
    response: str
    score: Score
    reason: str
    latency_ms: int
    tokens_used: int = 0
    error: Optional[str] = None


@dataclass
class RunResult:
    run_id: str
    suite_name: str
    model: str
    timestamp: str
    case_results: list[CaseResult]

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.case_results if r.score == Score.PASS)

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.case_results if r.score == Score.FAIL)

    @property
    def pass_rate(self) -> float:
        total = len(self.case_results)
        return self.pass_count / total if total > 0 else 0.0
