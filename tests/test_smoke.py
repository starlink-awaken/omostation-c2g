import subprocess
from collections import Counter
from pathlib import Path

import yaml

from c2g.adapters import EcosGovernanceProvider, EcosStorageProvider
from c2g.adapters_local import LocalGovernanceProvider
from c2g.bridge_import import _write_ecos_task
from c2g.bridge_utils import get_omo_dir
from c2g.domain import PitchSchema
from c2g.strategy import _check_anomalies
from c2g.task_builder import build_ecos_task

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


def test_build_ecos_task_includes_governance_refs():
    task = build_ecos_task(
        "T1",
        "治理任务",
        source_docs=["doc.md"],
        evidence_required=["evidence"],
        test_plan=["pytest"],
    )
    assert ".omo/standards/omo-governance-surfaces.md" in task["governance_refs"]
    assert ".omo/_truth/registry/omo-governance-surfaces.yaml" in task["governance_refs"]
    assert task["metadata"]["ingress_plane"] == "projects/c2g"


def test_ecos_governance_provider_reads_real_phase_from_omo_state(tmp_path: Path):
    omo_dir = tmp_path / ".omo"
    state_dir = omo_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "system.yaml").write_text(
        yaml.dump({"current_phase": 43}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    provider = EcosGovernanceProvider(str(omo_dir))
    assert provider.get_current_phase() == "43"


def test_get_omo_dir_prefers_outermost_shadow_free_root(tmp_path: Path):
    workspace_omo = tmp_path / ".omo"
    workspace_omo.mkdir()
    nested = tmp_path / "projects" / "c2g" / "src"
    nested.mkdir(parents=True)
    inner_omo = tmp_path / "projects" / ".omo"
    inner_omo.mkdir()

    assert get_omo_dir(nested) == workspace_omo


def test_check_anomalies_uses_supplied_omo_dir_for_recent_done(tmp_path: Path):
    omo_dir = tmp_path / ".omo"
    done_dir = omo_dir / "tasks" / "done"
    done_dir.mkdir(parents=True)
    (done_dir / "recent.yaml").write_text("id: DONE-1\n", encoding="utf-8")

    metrics = {
        "priority": Counter({"P1": 1}),
        "risk_level": Counter({"L0": 1}),
        "owner": Counter({"unassigned": 1}),
        "phase": Counter({"42": 1}),
        "status": Counter({"done": 1}),
    }

    warnings = _check_anomalies(metrics, 1, omo_dir=omo_dir)
    assert not any("最近 7 天无 done task 完成" in warning for warning in warnings)


def test_ecos_storage_provider_save_bet_uses_omo_ingress(tmp_path: Path):
    omo_dir = tmp_path / ".omo"
    goals_dir = omo_dir / "goals"
    goals_dir.mkdir(parents=True, exist_ok=True)
    (goals_dir / "current.yaml").write_text(
        yaml.dump({"phase": 44, "goals": []}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    store = EcosStorageProvider(str(omo_dir))
    bet = __import__("c2g.domain", fromlist=["BetSchema"]).BetSchema(
        goal_id="BET-aa11",
        title="统一 broker",
        description="统一 broker",
        appetite="1 week",
        created_at="2026-06-18T02:00:00Z",
    )
    store.save_bet(bet)

    goals_payload = yaml.safe_load((goals_dir / "current.yaml").read_text(encoding="utf-8"))
    assert any(goal["id"] == "BET-aa11" for goal in goals_payload["goals"])
    # omo 2026-07-01 迁移: ingress artifacts 从 .omo/_delivery/ → runtime/omo/_delivery/
    assert (omo_dir.parent / "runtime" / "omo" / "_delivery" / "ingress" / "goals" / "BET-aa11.yaml").exists()


def test_write_ecos_task_uses_omo_ingress_broker(tmp_path: Path):
    omo_dir = tmp_path / ".omo"
    task_data = build_ecos_task(
        "IMPORTED-broker",
        "通过 broker 落任务",
        source_docs=["spec.md"],
        evidence_required=["evidence"],
        test_plan=["pytest"],
    )

    _write_ecos_task(omo_dir, "IMPORTED-broker", task_data)

    assert (omo_dir / "tasks" / "planned" / "IMPORTED-broker.yaml").exists()
    # omo 2026-07-01 迁移: ingress artifacts 从 .omo/_delivery/ → runtime/omo/_delivery/
    assert (omo_dir.parent / "runtime" / "omo" / "_delivery" / "ingress" / "tasks" / "IMPORTED-broker.yaml").exists()


def test_scenarios_registry():
    """BET-6: 6 场景注册表完整 (gongwen/vault/research/family/health/finance)."""
    from c2g.scenarios import SCENARIOS, get_scenario

    assert set(SCENARIOS) == {
        "gongwen",
        "vault",
        "research",
        "family",
        "health",
        "finance",
    }
    for key, sc in SCENARIOS.items():
        assert sc.key == key
        assert sc.label  # 非空中文标签
        assert sc.upstream_hint
        assert len(sc.nogos) >= 2  # YAGNI 禁区
        assert len(sc.sections) >= 2  # 场景专属小节
    assert get_scenario("finance").label == "财务"  # type: ignore[reportOptionalMemberAccess]
    assert get_scenario(None) is None
    assert get_scenario("nonexistent") is None


def test_cli_brainstorm_scenario():
    """BET-6: brainstorm --scenario finance 生成场景化 Pitch (Scenario 行 + 场景专属小节)."""
    import os

    pitch_file = PROJECT_ROOT / ".c2g_data" / "pitches" / "Idea-test-bet6-scenario.md"
    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "--project",
                ".",
                "c2g",
                "brainstorm",
                "test-bet6-scenario",
                "--scenario",
                "finance",
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "[场景: 财务]" in result.stdout
        assert pitch_file.exists()
        content = pitch_file.read_text(encoding="utf-8")
        assert "> **Scenario**: finance (财务)" in content
        assert "## 财务场景" in content  # 场景专属小节
        assert "## NoGos (YAGNI)" in content
    finally:
        if pitch_file.exists():
            os.remove(pitch_file)


def test_parse_pitch_frontmatter_scenario():
    """BET-7: _parse_pitch_frontmatter 解析 Scenario 字段 (三元组, 向后兼容)."""
    from c2g.bridge_import import _parse_pitch_frontmatter

    # 有 Scenario 的场景化 Pitch (c2g brainstorm --scenario finance 生成)
    content_with_scenario = (
        "# 月度预算\n\n"
        "> **Scenario**: finance (财务)\n"
        "> **Upstream**: MS-FINANCE-001\n"
        "> **Appetite:** 1 week\n\n"
        "## 背景\n...\n"
    )
    upstream, appetite, scenario = _parse_pitch_frontmatter(content_with_scenario)
    assert upstream == "MS-FINANCE-001"
    assert appetite == "1 week"
    assert scenario == "finance"

    # 无 Scenario 的通用 Pitch (向后兼容, scenario=None)
    content_generic = "# 通用点子\n\n> **Upstream**: MS-001\n> **Appetite:** 2 hours\n\n## 背景\n...\n"
    upstream2, appetite2, scenario2 = _parse_pitch_frontmatter(content_generic)
    assert upstream2 == "MS-001"
    assert appetite2 == "2 hours"
    assert scenario2 is None
