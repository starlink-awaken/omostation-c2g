import pytest
from pathlib import Path
from c2g.domain import PitchSchema
from c2g.adapters_local import LocalGovernanceProvider, LocalStorageProvider
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def test_domain_schema():
    pitch = PitchSchema(pitch_id="1", title="Test", content="Data", created_at="2026-06-15")
    assert pitch.title == "Test"

def test_local_governance():
    gov = LocalGovernanceProvider()
    pitch = PitchSchema(pitch_id="1", title="Test", content="Data", created_at="2026-06-15")
    assert gov.validate_pitch(pitch) is True
    pitch_short = PitchSchema(pitch_id="1", title="Te", content="Data", created_at="2026-06-15")
    assert gov.validate_pitch(pitch_short) is False

def test_cli_help():
    result = subprocess.run(
        ["uv", "run", "--project", ".", "c2g", "--help"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "brainstorm" in result.stdout

def test_cli_local_radar():
    result = subprocess.run(
        ["uv", "run", "--project", ".", "c2g", "--adapter", "local", "radar"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Strategic Audit" in result.stdout or "Task Inventory" in result.stdout

def test_cli_local_gc():
    result = subprocess.run(
        ["uv", "run", "--project", ".", "c2g", "--adapter", "local", "gc"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "GC 完成" in result.stdout
