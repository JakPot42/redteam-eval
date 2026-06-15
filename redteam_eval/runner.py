from __future__ import annotations
import uuid
from datetime import datetime, timezone

from .evaluators import get_evaluator
from .models import CaseResult, RunResult, Score, TestSuite
from .providers.base import BaseProvider
from .providers.claude import ClaudeProvider


class SuiteRunner:
    def __init__(self, provider: BaseProvider | None = None) -> None:
        self._provider = provider

    def run(self, suite: TestSuite, verbose: bool = False) -> RunResult:
        provider = self._provider or ClaudeProvider(model=suite.model)

        # Give evaluators access to the Claude client for llm_judge type
        claude_client = getattr(provider, "client", None)

        case_results: list[CaseResult] = []
        for case in suite.cases:
            system_prompt = case.system_prompt or suite.system_prompt
            evaluator = get_evaluator(case.evaluator, claude_client)

            if verbose:
                label = case.description or case.prompt[:60]
                print(f"  [{case.id}] {label}...")

            try:
                resp = provider.complete(case.prompt, system_prompt)
                score, reason = evaluator.evaluate(case, resp.text)
                result = CaseResult(
                    test_id=case.id,
                    prompt=case.prompt,
                    response=resp.text,
                    score=score,
                    reason=reason,
                    latency_ms=resp.latency_ms,
                    tokens_used=resp.tokens_used,
                )
            except Exception as exc:
                result = CaseResult(
                    test_id=case.id,
                    prompt=case.prompt,
                    response="",
                    score=Score.ERROR,
                    reason=f"Provider error: {exc}",
                    latency_ms=0,
                    tokens_used=0,
                    error=str(exc),
                )

            case_results.append(result)

        return RunResult(
            run_id=str(uuid.uuid4()),
            suite_name=suite.name,
            model=provider.model_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            case_results=case_results,
        )
