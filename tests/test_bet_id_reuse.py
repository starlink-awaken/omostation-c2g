"""Tests for BET ID reuse detection (graceful skip)."""
import pytest
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Workspace root: c2g's parent
WORKSPACE_ROOT = PROJECT_ROOT.parent.parent
PITCH_FILE = "runtime/sandbox/pitches/Pitch-Valid.md"


def test_bet_id_reuse_graceful_skip():
    """
    Running c2g bet twice on the same Pitch should skip gracefully
    with a friendly ⏭ message, not ❌ error.
    """
    result = subprocess.run(
        ["uv", "run", "--project", "projects/c2g", "c2g", "--adapter", "ecos", "bet", PITCH_FILE],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
    )
    # Should succeed (returncode 0) even on reuse
    assert result.returncode == 0, f"Expected 0, got {result.returncode}: {result.stderr}"
    # Should NOT contain the ❌ error message for already-exists
    assert "❌" not in result.stdout, f"Unexpected error in output: {result.stdout}"
    # Should contain the friendly skip message
    assert "⏭" in result.stdout and "already exists" in result.stdout, \
        f"Expected graceful skip message, got: {result.stdout}"
    # Should contain the success footer
    assert "✅ Bet 下注成功" in result.stdout


def test_bet_id_reuse_no_new_task():
    """
    Re-running bet should create 0 new tasks (skip path).
    """
    result = subprocess.run(
        ["uv", "run", "--project", "projects/c2g", "c2g", "--adapter", "ecos", "bet", PITCH_FILE],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
    )
    # "0 个执行计划" confirms skip path
    assert "0 个执行计划" in result.stdout