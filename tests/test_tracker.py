import pytest
from pathlib import Path
from redteam_eval.tracker import ResultTracker
from redteam_eval.models import Score
from tests.conftest import make_case_result, make_run_result


@pytest.fixture
def tracker(tmp_path: Path) -> ResultTracker:
    return ResultTracker(db_path=tmp_path / "test_results.db")


def test_save_and_list_run(tracker):
    run = make_run_result()
    tracker.save(run)
    runs = tracker.list_runs()
    assert len(runs) == 1
    assert runs[0]["suite_name"] == "Test Suite"


def test_list_returns_run_id_prefix(tracker):
    run = make_run_result()
    tracker.save(run)
    runs = tracker.list_runs()
    assert runs[0]["run_id"] == run.run_id[:8]


def test_get_run_by_prefix(tracker):
    run = make_run_result()
    tracker.save(run)
    data = tracker.get_run(run.run_id[:8])
    assert data is not None
    assert data["suite_name"] == "Test Suite"


def test_get_run_not_found(tracker):
    result = tracker.get_run("nonexistent")
    assert result is None


def test_save_stores_case_results(tracker):
    cases = [
        make_case_result("c-001", Score.PASS, "keyword match"),
        make_case_result("c-002", Score.FAIL, "keyword missing"),
    ]
    run = make_run_result(case_results=cases)
    tracker.save(run)
    data = tracker.get_run(run.run_id[:8])
    assert len(data["cases"]) == 2
    test_ids = [c["test_id"] for c in data["cases"]]
    assert "c-001" in test_ids
    assert "c-002" in test_ids


def test_pass_rate_stored_correctly(tracker):
    cases = [
        make_case_result("a", Score.PASS),
        make_case_result("b", Score.PASS),
        make_case_result("c", Score.FAIL),
    ]
    run = make_run_result(case_results=cases)
    tracker.save(run)
    runs = tracker.list_runs()
    assert runs[0]["pass_rate"] == pytest.approx(2 / 3)


def test_multiple_runs_ordered_newest_first(tracker):
    run1 = make_run_result(suite_name="Suite Alpha")
    run1_id = run1.run_id
    # Force a later timestamp on run2
    import dataclasses
    run2 = dataclasses.replace(
        make_run_result(suite_name="Suite Beta"),
        run_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        timestamp="2026-06-14T13:00:00+00:00",
    )
    tracker.save(run1)
    tracker.save(run2)
    runs = tracker.list_runs()
    assert runs[0]["suite_name"] == "Suite Beta"  # newer first
    assert runs[1]["suite_name"] == "Suite Alpha"


def test_case_score_stored_as_string(tracker):
    cases = [make_case_result("t-001", Score.PASS)]
    run = make_run_result(case_results=cases)
    tracker.save(run)
    data = tracker.get_run(run.run_id[:8])
    assert data["cases"][0]["score"] == "PASS"
