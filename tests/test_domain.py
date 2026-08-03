"""Tests for c2g domain models (Pydantic schemas)."""

import pytest
from c2g.domain import BetSchema, PitchSchema, TaskSchema


class TestPitchSchema:
    def test_minimal_pitch(self):
        p = PitchSchema(
            pitch_id="P-001",
            title="AI 代码审查",
            content="做 AI 代码审查工具",
            created_at="2026-06-20T00:00:00Z",
        )
        assert p.pitch_id == "P-001"
        assert p.upstream_ref is None
        assert p.appetite is None

    def test_pitch_with_upstream(self):
        p = PitchSchema(
            pitch_id="P-002",
            title="X",
            content="Y",
            created_at="2026-06-20",
            upstream_ref="P42-W0-W1-COMBO",
            appetite="2h",
        )
        assert p.upstream_ref == "P42-W0-W1-COMBO"
        assert p.appetite == "2h"

    def test_pitch_optional_fields_omit(self):
        p = PitchSchema(pitch_id="x", title="T", content="C", created_at="now")
        assert p.upstream_ref is None
        assert p.appetite is None

    def test_pitch_serializable(self):
        p = PitchSchema(
            pitch_id="P-003", title="Test", content="Data", created_at="now"
        )
        d = p.model_dump()
        assert isinstance(d, dict)
        assert d["title"] == "Test"


class TestBetSchema:
    def test_default_status(self):
        b = BetSchema(goal_id="G-001", title="Bet", description="d", created_at="now")
        assert b.status == "active"
        assert b.vector == "V2"
        assert b.appetite == "1 week"

    def test_explicit_status(self):
        b = BetSchema(
            goal_id="G-002",
            title="Bet",
            description="d",
            status="deferred",
            vector="V1",
            appetite="3d",
            created_at="now",
        )
        assert b.status == "deferred"
        assert b.vector == "V1"

    def test_bet_required_fields(self):
        with pytest.raises(Exception):
            BetSchema(
                goal_id="x"
            )  # missing title/description/created_at  # type: ignore[reportCallIssue]


class TestTaskSchema:
    def test_default_task(self):
        t = TaskSchema(
            task_id="T-001",
            title="Do",
            description="work",
            created_at="2026-06-20",
            updated_at="2026-06-20",
        )
        assert t.status == "planned"
        assert t.priority == "P1"
        assert t.assignee == "unassigned"
        assert t.tags == []
        assert t.metadata == {}

    def test_task_with_metadata(self):
        t = TaskSchema(
            task_id="T-002",
            title="X",
            description="Y",
            created_at="now",
            updated_at="now",
            priority="P0",
            status="in_progress",
            assignee="agent-1",
            tags=["governance", "lint"],
            metadata={"source_ref": "audit:lint:20260620"},
        )
        assert t.priority == "P0"
        assert "governance" in t.tags
        assert t.metadata["source_ref"] == "audit:lint:20260620"
