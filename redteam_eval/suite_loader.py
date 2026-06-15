from __future__ import annotations
from pathlib import Path

import yaml

from .models import EvaluatorConfig, TestCase, TestSuite


def load_suite(path: str | Path) -> TestSuite:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    suite_system_prompt: str | None = data.get("system_prompt")
    suite_model: str = data.get("model", "claude-haiku-4-5-20251001")

    cases: list[TestCase] = []
    for c in data.get("cases", []):
        eval_cfg_raw = c.get("evaluator", {})
        evaluator = EvaluatorConfig(
            type=eval_cfg_raw.get("type", "keyword"),
            required_keywords=eval_cfg_raw.get("required_keywords", []),
            forbidden_keywords=eval_cfg_raw.get("forbidden_keywords", []),
            pattern=eval_cfg_raw.get("pattern"),
            judge_criteria=eval_cfg_raw.get("judge_criteria"),
            judge_model=eval_cfg_raw.get("judge_model"),
        )
        cases.append(
            TestCase(
                id=c["id"],
                prompt=c["prompt"],
                evaluator=evaluator,
                description=c.get("description", ""),
                category=c.get("category", "general"),
                domain=c.get("domain", ""),
                system_prompt=c.get("system_prompt"),
                tags=c.get("tags", []),
                stakes=c.get("stakes", "medium"),
            )
        )

    return TestSuite(
        name=data["name"],
        cases=cases,
        description=data.get("description", ""),
        version=str(data.get("version", "1.0")),
        model=suite_model,
        system_prompt=suite_system_prompt,
    )
