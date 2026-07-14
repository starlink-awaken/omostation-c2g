"""Wave 2 Phase A backtest."""

from pathlib import Path

from c2g.outcome_tracker import OutcomeTracker


def test_backtest_empty(tmp_path: Path):
    t = OutcomeTracker(tmp_path)
    r = t.backtest_report()
    assert r["status"] == "empty"
    assert r["pitch_count"] == 0


def test_backtest_with_data(tmp_path: Path):
    t = OutcomeTracker(tmp_path)
    t.track_pitch_creation("p1", "pitches/p1.md")
    t.track_task_generation("p1", ["t1", "t2"])
    t.track_task_completion("p1", "t1", success=True)
    t.track_task_completion("p1", "t2", success=False)
    r = t.backtest_report()
    assert r["status"] == "ok"
    assert r["pitch_count"] == 1
    assert 0.0 <= r["mean_success_score"] <= 1.0
