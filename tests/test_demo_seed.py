"""Tests for Wave2 demo OutcomeTracker seed."""

from __future__ import annotations

from pathlib import Path

from c2g.dashboard_export import build_dashboard
from c2g.demo_seed import seed_demo_outcomes
from c2g.governance_feedback import build_proposals
from c2g.outcome_tracker import OutcomeTracker


def test_seed_creates_pitches(tmp_path: Path):
    s = seed_demo_outcomes(tmp_path)
    assert s["status"] == "ok"
    assert len(s["seeded"]) >= 5
    t = OutcomeTracker(tmp_path)
    assert len(t._outcomes) >= 5
    assert any(float(o.get("success_score") or 0) < 0.33 for o in t._outcomes.values())


def test_seed_idempotent_without_reset(tmp_path: Path):
    s1 = seed_demo_outcomes(tmp_path)
    s2 = seed_demo_outcomes(tmp_path, reset=False)
    assert len(s2["seeded"]) == 0
    assert len(s2["skipped"]) == len(s1["seeded"])
    t = OutcomeTracker(tmp_path)
    assert len(t._outcomes) == len(s1["seeded"])


def test_seed_reset_replaces(tmp_path: Path):
    seed_demo_outcomes(tmp_path)
    s = seed_demo_outcomes(tmp_path, reset=True)
    assert len(s["seeded"]) >= 5
    assert s["skipped"] == []


def test_seed_feeds_dashboard_and_proposals(tmp_path: Path):
    seed_demo_outcomes(tmp_path)
    dash = build_dashboard(tmp_path)
    assert dash["cards"]["pitch_count"] >= 5
    # critical or elevated should light up from failing demos
    assert (dash["cards"]["critical"] or 0) + (dash["cards"]["elevated"] or 0) >= 1
    props = build_proposals(OutcomeTracker(tmp_path)._outcomes)
    assert props["proposal_count"] >= 1
