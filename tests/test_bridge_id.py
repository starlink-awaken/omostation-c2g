"""Tests for c2g bridge_id (Phase/Wave 推断 + Task ID 生成)."""

from c2g.bridge_id import _generate_task_id, _infer_phase_wave


class TestGenerateTaskId:
    def test_returns_imported_prefix(self):
        tid = _generate_task_id("Test task")
        assert tid.startswith("IMPORTED-")
        assert len(tid) == len("IMPORTED-") + 6

    def test_stable_hash(self):
        # Same input → same hash
        assert _generate_task_id("Hello") == _generate_task_id("Hello")

    def test_different_inputs(self):
        assert _generate_task_id("A") != _generate_task_id("B")

    def test_unicode(self):
        tid = _generate_task_id("中文任务 🎉")
        assert tid.startswith("IMPORTED-")


class TestInferPhaseWave:
    def test_valid_pattern(self):
        phase, wave = _infer_phase_wave("P42-W0-MERGE-STATE")
        assert phase == 42
        assert wave == "W0"

    def test_double_digit(self):
        phase, wave = _infer_phase_wave("P100-W3-X")
        assert phase == 100
        assert wave == "W3"

    def test_no_match(self):
        phase, wave = _infer_phase_wave("not a phase")
        assert phase is None
        assert wave is None

    def test_partial_pattern(self):
        # Only P, no W → entire pattern doesn't match
        phase, wave = _infer_phase_wave("P42 only")
        assert phase is None
        assert wave is None

    def test_empty_string(self):
        phase, wave = _infer_phase_wave("")
        assert phase is None
        assert wave is None
