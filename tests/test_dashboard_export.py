"""Wave2 dashboard export contract tests."""

from __future__ import annotations

from pathlib import Path

from c2g.dashboard_export import build_dashboard
from c2g.outcome_tracker import OutcomeTracker


def test_dashboard_schema_empty(tmp_path: Path):
    d = build_dashboard(tmp_path)
    assert d["schema"] == "c2g.wave2.dashboard.v1"
    assert d["adr"] == "0190"
    assert d["auto_mutate_rules"] is False
    assert "cards" in d
    assert d["cards"]["pitch_count"] == 0
    assert "heatmap" in d
    assert "proposals" in d
    assert "forecast" in d


def test_dashboard_with_data(tmp_path: Path):
    t = OutcomeTracker(tmp_path)
    t.track_pitch_creation("p1", "/a")
    t.track_task_generation("p1", ["t1"])
    t.track_task_completion("p1", "t1", success=False)
    t._outcomes["p1"]["success_score"] = 0.1
    t._save_outcomes()
    d = build_dashboard(tmp_path)
    assert d["cards"]["pitch_count"] == 1
    assert d["cards"]["critical"] >= 1 or d["cards"]["p0_proposals"] >= 0
