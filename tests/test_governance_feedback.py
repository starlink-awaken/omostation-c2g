"""Wave 2 Phase C governance feedback tests."""

from __future__ import annotations

from pathlib import Path

from c2g.governance_feedback import apply_proposals_as_tasks, build_proposals
from c2g.outcome_tracker import OutcomeTracker


def test_empty_outcomes_bootstrap_proposal():
    r = build_proposals({})
    assert r["adr"] == "0188"
    assert r["auto_mutate_rules"] is False
    ids = {p["id"] for p in r["proposals"]}
    assert "prop-empty-baseline" in ids


def test_critical_generates_p0(tmp_path: Path):
    t = OutcomeTracker(tmp_path)
    t.track_pitch_creation("p1", "/a")
    t.track_task_generation("p1", ["t1", "t2"])
    t.track_task_completion("p1", "t1", success=False)
    t.track_task_completion("p1", "t2", success=False)
    # force low score
    t._outcomes["p1"]["success_score"] = 0.1
    t._save_outcomes()
    r = build_proposals(t._outcomes)
    ids = {p["id"] for p in r["proposals"]}
    assert "prop-critical-pitches" in ids
    p0 = next(p for p in r["proposals"] if p["id"] == "prop-critical-pitches")
    assert p0["priority"] == "P0"
    assert p0["suggested_omo_action"] == "create_planned_task"


def test_declining_trend_proposal(tmp_path: Path):
    t = OutcomeTracker(tmp_path)
    for i, score in enumerate([0.9, 0.7, 0.5, 0.3]):
        pid = f"p{i}"
        t.track_pitch_creation(pid, f"/{i}")
        t._outcomes[pid]["success_score"] = score
        t._outcomes[pid]["created_at"] = f"2024-0{i + 1}-01T00:00:00Z"
    t._save_outcomes()
    r = build_proposals(t._outcomes)
    assert r["forecast_summary"]["trend"] == "declining"
    ids = {p["id"] for p in r["proposals"]}
    assert "prop-declining-trend" in ids


def test_apply_dry_run_plan(tmp_path: Path):
    proposals = {
        "proposals": [
            {
                "id": "prop-critical-pitches",
                "suggested_omo_action": "create_planned_task",
                "suggested_task": {"title": "Review X", "priority": "P0"},
            },
            {
                "id": "prop-note",
                "suggested_omo_action": "note_only",
                "suggested_task": None,
            },
        ]
    }
    actions = apply_proposals_as_tasks(proposals, tmp_path / ".omo", dry_run=True)
    assert len(actions) == 1
    assert actions[0]["would_create"] is True
    assert actions[0]["dry_run"] is True
