"""测试 PitchAnalyzer"""

from pathlib import Path
from tempfile import TemporaryDirectory

from c2g.outcome_tracker import OutcomeTracker
from c2g.pitch_analyzer import PitchIntelligenceAnalyzer


def test_success_prediction():
    with TemporaryDirectory() as tmpdir:
        tracker = OutcomeTracker(Path(tmpdir))
        analyzer = PitchIntelligenceAnalyzer(tracker)

        good_pitch = (
            "# Test Pitch\n> **Upstream**: Improve efficiency\n> **Appetite**: 1 day"
        )
        score = analyzer.predict_pitch_success_probability(good_pitch)
        assert 0.0 <= score <= 1.0


def test_extract_intent():
    with TemporaryDirectory() as tmpdir:
        tracker = OutcomeTracker(Path(tmpdir))
        analyzer = PitchIntelligenceAnalyzer(tracker)

        content = "# My Big Idea\n## Objectives\n- Do X\n- Do Y"
        intent = analyzer.extract_strategic_intent(content)
        assert "Big Idea" in intent.core_goal


def test_suggestions():
    with TemporaryDirectory() as tmpdir:
        tracker = OutcomeTracker(Path(tmpdir))
        analyzer = PitchIntelligenceAnalyzer(tracker)

        bad_pitch = "# Pitch only title"
        suggestions = analyzer.suggest_pitch_improvements(bad_pitch)
        assert len(suggestions) > 0
