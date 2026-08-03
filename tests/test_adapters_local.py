"""Tests for c2g LocalGovernanceProvider + LocalStorageProvider."""

import json
from pathlib import Path

from c2g.adapters_local import LocalGovernanceProvider, LocalStorageProvider
from c2g.domain import BetSchema, PitchSchema, TaskSchema


class TestLocalGovernanceProvider:
    def test_validate_pitch_min_length(self):
        gov = LocalGovernanceProvider()
        # short title rejected
        p_short = PitchSchema(pitch_id="1", title="ab", content="X", created_at="now")
        assert gov.validate_pitch(p_short) is False
        # long enough accepted
        p_ok = PitchSchema(pitch_id="2", title="abc", content="X", created_at="now")
        assert gov.validate_pitch(p_ok) is True
        # empty rejected
        p_empty = PitchSchema(pitch_id="3", title="", content="X", created_at="now")
        assert gov.validate_pitch(p_empty) is False

    def test_validate_task_requires_title(self):
        gov = LocalGovernanceProvider()
        t_ok = TaskSchema(
            task_id="T1",
            title="work",
            description="d",
            created_at="now",
            updated_at="now",
        )
        assert gov.validate_task(t_ok) is True
        t_no_title = TaskSchema(
            task_id="T2", title="", description="d", created_at="now", updated_at="now"
        )
        assert gov.validate_task(t_no_title) is False

    def test_current_phase_default(self):
        gov = LocalGovernanceProvider()
        assert (
            "Phase" in gov.get_current_phase()
            or "phase" in gov.get_current_phase().lower()
        )


class TestLocalStorageProvider:
    def test_init_creates_dirs(self, tmp_path: Path):
        LocalStorageProvider(base_dir=str(tmp_path / "c2g"))
        assert (tmp_path / "c2g" / "pitches").is_dir()
        assert (tmp_path / "c2g" / "bets.json").exists()
        assert (tmp_path / "c2g" / "tasks.json").exists()

    def test_save_and_get_bet(self, tmp_path: Path):
        store = LocalStorageProvider(base_dir=str(tmp_path / "c2g"))
        bet = BetSchema(
            goal_id="G-001", title="Test Bet", description="d", created_at="now"
        )
        store.save_bet(bet)
        active = store.get_active_bets()
        assert len(active) == 1
        assert active[0].goal_id == "G-001"

    def test_save_task(self, tmp_path: Path):
        store = LocalStorageProvider(base_dir=str(tmp_path / "c2g"))
        task = TaskSchema(
            task_id="T-001",
            title="work",
            description="d",
            created_at="now",
            updated_at="now",
        )
        store.save_task(task)
        data = json.loads((tmp_path / "c2g" / "tasks.json").read_text())
        assert len(data) == 1
        assert data[0]["task_id"] == "T-001"

    def test_get_pitches_empty(self, tmp_path: Path):
        store = LocalStorageProvider(base_dir=str(tmp_path / "c2g"))
        assert store.get_pitches() == []

    def test_get_pitches_roundtrip(self, tmp_path: Path):
        store = LocalStorageProvider(base_dir=str(tmp_path / "c2g"))
        # write a fake pitch
        (tmp_path / "c2g" / "pitches" / "Idea-Test.md").write_text(
            "# Test\n\n> Upstream: G-1\n> Appetite: 1d\n",
            encoding="utf-8",
        )
        pitches = store.get_pitches()
        assert len(pitches) == 1
        assert pitches[0].title == "Idea-Test"

    def test_delete_pitch(self, tmp_path: Path):
        store = LocalStorageProvider(base_dir=str(tmp_path / "c2g"))
        target = tmp_path / "c2g" / "pitches" / "x.md"
        target.write_text("data", encoding="utf-8")
        assert store.delete_pitch("x.md") is True
        assert not target.exists()
        # idempotent
        assert store.delete_pitch("x.md") is False
