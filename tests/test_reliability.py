"""测试 Reliability 模块"""

from c2g.reliability import C2GSafetyGuard, FallbackTaskGenerator


def test_validation():
    guard = C2GSafetyGuard()

    result = guard.validate_pitch_format_loosely("")
    assert not result.valid

    result = guard.validate_pitch_format_loosely("# My Pitch\ncontent")
    assert result.valid


def test_fallback_generator():
    gen = FallbackTaskGenerator()
    task = gen.generate_fallback_task("# Test Idea", "/test/path.md")
    assert "task_id" in task
    assert "Test" in task["title"]
