"""Wave 2 Phase B predictive + heatmap tests (stdlib only)."""

from __future__ import annotations

from pathlib import Path

from c2g.outcome_tracker import OutcomeTracker
from c2g.pitch_analyzer import PitchIntelligenceAnalyzer
from c2g.predictive import (
    PredictiveModel,
    blend_prior,
    outcomes_time_series,
    render_heatmap_markdown,
    risk_heatmap,
)
from c2g.predictive_report import build_report


def test_ema_linear_forecast_empty():
    r = PredictiveModel(horizon=2).fit_series([])
    assert r["n"] == 0
    assert r["trend"] == "flat"
    assert len(r["forecast"]) == 2
    assert r["deps"] == "stdlib-only"


def test_forecast_improving_trend():
    series = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    r = PredictiveModel(horizon=3, alpha=0.5).fit_series(series)
    assert r["n"] == 6
    assert r["trend"] == "improving"
    assert r["slope"] > 0
    assert all(0.0 <= f["predicted"] <= 1.0 for f in r["forecast"])
    for f in r["forecast"]:
        assert f["lower"] <= f["predicted"] <= f["upper"]


def test_forecast_declining_trend():
    series = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
    r = PredictiveModel().fit_series(series)
    assert r["trend"] == "declining"


def test_risk_heatmap_buckets(tmp_path: Path):
    t = OutcomeTracker(tmp_path)
    t.track_pitch_creation("p1", "/a")
    t.track_task_generation("p1", ["t1", "t2"])
    t.track_task_completion("p1", "t1", success=True)
    t.track_task_completion("p1", "t2", success=False)
    t.track_pitch_creation("p2", "/b")
    t._outcomes["p2"]["success_score"] = 0.9
    t._outcomes["p2"]["status"] = "completed"
    t._save_outcomes()

    heat = risk_heatmap(t._outcomes)
    assert heat["totals"]["pitches"] == 2
    assert sum(sum(row.values()) for row in heat["matrix"].values()) == 2
    md = render_heatmap_markdown(heat)
    assert "active" in md
    assert "low" in md or "mid" in md or "high" in md


def test_outcomes_time_series_order(tmp_path: Path):
    t = OutcomeTracker(tmp_path)
    t.track_pitch_creation("late", "/l")
    t.track_pitch_creation("early", "/e")
    t._outcomes["early"]["created_at"] = "2020-01-01T00:00:00Z"
    t._outcomes["early"]["success_score"] = 0.1
    t._outcomes["late"]["created_at"] = "2021-01-01T00:00:00Z"
    t._outcomes["late"]["success_score"] = 0.9
    series = outcomes_time_series(t._outcomes)
    assert series == [0.1, 0.9]


def test_blend_prior_more_history_pulls_toward_mean():
    # few samples → stay near heuristic
    a = blend_prior(0.9, 0.2, n=1, k=5)
    # many samples → closer to hist
    b = blend_prior(0.9, 0.2, n=50, k=5)
    assert a > b
    assert 0.2 < b < 0.9


def test_pitch_analyzer_blends_history(tmp_path: Path):
    t = OutcomeTracker(tmp_path)
    for i in range(10):
        pid = f"p{i}"
        t.track_pitch_creation(pid, f"/{i}")
        t._outcomes[pid]["success_score"] = 0.2
        t._outcomes[pid]["created_at"] = f"2024-01-{i + 1:02d}T00:00:00Z"
    t._save_outcomes()
    analyzer = PitchIntelligenceAnalyzer(t)
    good = "# X\nUpstream: done\nAppetite: 1d\nAcceptance: yes\nRisk: low\n"
    # pure heuristic would be ~0.85; history pulls down
    p = analyzer.predict_pitch_success_probability(good)
    assert p < 0.85
    assert p > 0.2


def test_tracker_predictive_report(tmp_path: Path):
    t = OutcomeTracker(tmp_path)
    t.track_pitch_creation("p1", "/a")
    t.track_task_generation("p1", ["t1"])
    t.track_task_completion("p1", "t1", success=True)
    r = t.predictive_report(horizon=2)
    assert r["phase"] == "wave2-b"
    assert "forecast" in r
    assert "heatmap" in r
    assert "heatmap_markdown" in r
    assert r["backtest"]["pitch_count"] == 1


def test_build_report_cli_payload(tmp_path: Path):
    t = OutcomeTracker(tmp_path)
    t.track_pitch_creation("p1", "/a")
    r = build_report(tmp_path, horizon=2)
    assert r["adr"] == "0185"
    assert r["forecast"]["n"] == 1
    assert "matrix" in r["heatmap"]
