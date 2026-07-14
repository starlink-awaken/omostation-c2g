
"""测试 OutcomeTracker"""

from pathlib import Path
from tempfile import TemporaryDirectory

from c2g.outcome_tracker import OutcomeTracker


def test_basic_tracking():
    with TemporaryDirectory() as tmpdir:
        tracker = OutcomeTracker(Path(tmpdir))
        tracker.track_pitch_creation("test-pitch-1", "/test/pitch.md")
        lifecycle = tracker.track_pitch_lifecycle("test-pitch-1")
        assert lifecycle is not None
        assert lifecycle.pitch_id == "test-pitch-1"


def test_task_completion():
    with TemporaryDirectory() as tmpdir:
        tracker = OutcomeTracker(Path(tmpdir))
        tracker.track_pitch_creation("p-2", "/test.md")
        tracker.track_task_generation("p-2", ["t1", "t2", "t3"])
        tracker.track_task_completion("p-2", "t1", True)
        lifecycle = tracker.track_pitch_lifecycle("p-2")
        assert len(lifecycle.completed_tasks) == 1
        assert lifecycle.success_score == 1/3


def test_leaderboard():
    with TemporaryDirectory() as tmpdir:
        tracker = OutcomeTracker(Path(tmpdir))
        tracker.track_pitch_creation("p1", "/1.md")
        tracker.track_task_generation("p1", ["t1"])
        tracker.track_task_completion("p1", "t1", True)
        tracker.track_pitch_creation("p2", "/2.md")
        leaderboard = tracker.get_leaderboard()
        assert len(leaderboard) == 2
