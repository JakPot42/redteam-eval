from __future__ import annotations
from pathlib import Path
from typing import Optional

from sqlalchemy import Column, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from .models import CaseResult, RunResult, Score

DEFAULT_DB_PATH = Path.home() / ".redteam_eval" / "results.db"


class _Base(DeclarativeBase):
    pass


class _RunRecord(_Base):
    __tablename__ = "runs"
    run_id = Column(String, primary_key=True)
    suite_name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    pass_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    pass_rate = Column(Float, default=0.0)


class _CaseRecord(_Base):
    __tablename__ = "case_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, nullable=False, index=True)
    test_id = Column(String, nullable=False)
    prompt = Column(Text)
    response = Column(Text)
    score = Column(String)
    reason = Column(Text)
    latency_ms = Column(Integer)
    tokens_used = Column(Integer)
    error = Column(Text, nullable=True)


class ResultTracker:
    def __init__(self, db_path: str | Path | None = None) -> None:
        path = Path(db_path) if db_path else DEFAULT_DB_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(f"sqlite:///{path}")
        _Base.metadata.create_all(self._engine)

    def save(self, result: RunResult) -> None:
        with Session(self._engine) as session:
            session.add(
                _RunRecord(
                    run_id=result.run_id,
                    suite_name=result.suite_name,
                    model=result.model,
                    timestamp=result.timestamp,
                    pass_count=result.pass_count,
                    fail_count=result.fail_count,
                    total_count=len(result.case_results),
                    pass_rate=result.pass_rate,
                )
            )
            for cr in result.case_results:
                session.add(
                    _CaseRecord(
                        run_id=result.run_id,
                        test_id=cr.test_id,
                        prompt=cr.prompt,
                        response=cr.response,
                        score=cr.score.value,
                        reason=cr.reason,
                        latency_ms=cr.latency_ms,
                        tokens_used=cr.tokens_used,
                        error=cr.error,
                    )
                )
            session.commit()

    def list_runs(self, limit: int = 20) -> list[dict]:
        with Session(self._engine) as session:
            rows = (
                session.query(_RunRecord)
                .order_by(_RunRecord.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "run_id": r.run_id[:8],
                    "full_run_id": r.run_id,
                    "suite_name": r.suite_name,
                    "model": r.model,
                    "timestamp": r.timestamp,
                    "pass_count": r.pass_count,
                    "fail_count": r.fail_count,
                    "total_count": r.total_count,
                    "pass_rate": r.pass_rate,
                }
                for r in rows
            ]

    def get_run(self, run_id_prefix: str) -> Optional[dict]:
        with Session(self._engine) as session:
            row = (
                session.query(_RunRecord)
                .filter(_RunRecord.run_id.startswith(run_id_prefix))
                .first()
            )
            if not row:
                return None
            cases = (
                session.query(_CaseRecord)
                .filter(_CaseRecord.run_id == row.run_id)
                .all()
            )
            return {
                "run_id": row.run_id,
                "suite_name": row.suite_name,
                "model": row.model,
                "timestamp": row.timestamp,
                "pass_rate": row.pass_rate,
                "cases": [
                    {
                        "test_id": c.test_id,
                        "score": c.score,
                        "reason": c.reason,
                        "latency_ms": c.latency_ms,
                        "tokens_used": c.tokens_used,
                        "prompt": c.prompt,
                        "response": c.response,
                        "error": c.error,
                    }
                    for c in cases
                ],
            }
