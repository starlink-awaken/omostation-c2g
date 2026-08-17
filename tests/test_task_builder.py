"""Tests for c2g task_builder — 消除 _import_bmad/_fast_track/_pitch 重复构造"""

from __future__ import annotations

from c2g.task_builder import (
    _governance_refs,
    build_ecos_task,
    build_local_task,
)


class TestGovernanceRefs:
    def test_returns_6_governance_ssot_paths(self):
        refs = _governance_refs()
        assert len(refs) == 6

    def test_includes_omo_governance_surfaces(self):
        refs = _governance_refs()
        assert ".omo/standards/omo-governance-surfaces.md" in refs

    def test_includes_x1_x4_truth_registry(self):
        refs = _governance_refs()
        for prefix in ("x1-", "x2-", "x3-", "x4-"):
            assert any(p.startswith(f".omo/_truth/{prefix}") for p in refs), f"missing {prefix} truth registry"

    def test_returns_fresh_list_each_call(self):
        """防止 governance_refs 被多次引用导致同一 list 反复 extend"""
        r1 = _governance_refs()
        r2 = _governance_refs()
        assert r1 is not r2


class TestBuildEcosTask:
    def test_minimal_required_fields(self):
        task = build_ecos_task(task_id="T-001", title="Minimal")
        assert task["id"] == "T-001"
        assert task["title"] == "Minimal"
        assert task["status"] == "candidate"
        assert task["task_type"] == "feature"
        assert task["risk_level"] == "L0"

    def test_default_lists_are_empty(self):
        task = build_ecos_task(task_id="T-001", title="X")
        assert task["depends_on"] == []
        assert task["source_docs"] == []
        assert task["deliverables"] == ["执行记录与源码修改"]
        assert task["evidence_required"] == []
        assert task["test_plan"] == []
        assert task["entry_gate"] == []
        assert task["knowledge_refs"] == []
        assert task["handoff_refs"] == []

    def test_governance_refs_auto_attached(self):
        task = build_ecos_task(task_id="T-001", title="X")
        assert len(task["governance_refs"]) == 6
        assert all(p.startswith(".omo/") for p in task["governance_refs"])

    def test_metadata_block(self):
        task = build_ecos_task(task_id="T-001", title="X")
        assert task["metadata"]["governance_stack"] == "state_plane.kernel_plane.ingress_plane"
        assert task["metadata"]["ingress_plane"] == "projects/c2g"

    def test_context_uri_default(self):
        task = build_ecos_task(task_id="T-007", title="X")
        assert task["context_uri"] == "bos://memory/tasks/T-007"

    def test_context_uri_override(self):
        task = build_ecos_task(task_id="T-007", title="X", context_uri="bos://custom/path")
        assert task["context_uri"] == "bos://custom/path"

    def test_explicit_dependencies(self):
        task = build_ecos_task(
            task_id="T-001",
            title="X",
            depends_on=["T-002", "T-003"],
            source_docs=["docs/spec.md", "docs/adr.md"],
            deliverables=["deliverable1"],
            evidence_required=["mof-version record"],
            test_plan=["uv run pytest"],
            entry_gate=["X2 freshness check"],
        )
        assert task["depends_on"] == ["T-002", "T-003"]
        assert task["source_docs"] == ["docs/spec.md", "docs/adr.md"]
        assert task["deliverables"] == ["deliverable1"]
        assert task["evidence_required"] == ["mof-version record"]
        assert task["test_plan"] == ["uv run pytest"]
        assert task["entry_gate"] == ["X2 freshness check"]

    def test_extra_overrides_top_level(self):
        task = build_ecos_task(
            task_id="T-001",
            title="X",
            extra={"title": "Overridden Title", "custom_field": "custom_value"},
        )
        assert task["title"] == "Overridden Title"
        assert task["custom_field"] == "custom_value"

    def test_extra_metadata_merged(self):
        task = build_ecos_task(
            task_id="T-001",
            title="X",
            extra={"metadata": {"extra_key": "extra_value"}},
        )
        assert task["metadata"]["extra_key"] == "extra_value"
        # existing keys preserved
        assert task["metadata"]["ingress_plane"] == "projects/c2g"

    def test_extra_metadata_non_dict_ignored(self):
        task = build_ecos_task(
            task_id="T-001",
            title="X",
            extra={"metadata": "not a dict"},
        )
        # metadata still has the original keys
        assert task["metadata"]["governance_stack"] == "state_plane.kernel_plane.ingress_plane"

    def test_extra_empty_dict_no_change(self):
        task = build_ecos_task(task_id="T-001", title="X", extra={})
        assert task["id"] == "T-001"

    def test_required_to_pending_state_machine(self):
        """ecos task 物化时 status=candidate, 需经过 active → done 流转"""
        task = build_ecos_task(task_id="T-001", title="X")
        assert task["status"] == "candidate"
        # 业务流程中由 omo governance ingress-task broker 流转到 active

    def test_assigned_to_none_unassigned(self):
        task = build_ecos_task(task_id="T-001", title="X")
        assert task["assigned_to"] is None
        assert task["dispatch_id"] is None
        assert task["run_ref"] is None

    def test_human_approval_required_default_false(self):
        task = build_ecos_task(task_id="T-001", title="X")
        assert task["human_approval_required"] is False

    def test_risk_level_override(self):
        task = build_ecos_task(task_id="T-001", title="X", risk_level="L3")
        assert task["risk_level"] == "L3"

    def test_task_type_override(self):
        task = build_ecos_task(task_id="T-001", title="X", task_type="refactor")
        assert task["task_type"] == "refactor"

    def test_imported_via_default(self):
        task = build_ecos_task(task_id="T-001", title="X")
        assert task["imported_via"] == "omo_bridge"


class TestBuildLocalTask:
    def test_minimal_required_fields(self):
        task = build_local_task(task_id="T-001", title="Local")
        assert task["task_id"] == "T-001"
        assert task["title"] == "Local"
        assert task["status"] == "planned"

    def test_local_uses_task_id_not_id(self):
        """local adapter schema 用 task_id 而非 id (区别于 ecos)"""
        task = build_local_task(task_id="T-001", title="X")
        assert "task_id" in task
        assert "id" not in task

    def test_local_has_timestamps(self):
        task = build_local_task(task_id="T-001", title="X")
        assert "created_at" in task
        assert "updated_at" in task
        assert task["created_at"] == task["updated_at"]

    def test_local_timestamp_is_utc_z_suffix(self):
        task = build_local_task(task_id="T-001", title="X")
        assert task["created_at"].endswith("Z")
        # parseable as UTC
        from datetime import datetime

        dt = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
        assert dt.tzinfo is not None

    def test_local_metadata_block(self):
        task = build_local_task(task_id="T-001", title="X")
        meta = task["metadata"]
        assert meta["governance_stack"] == "state_plane.kernel_plane.ingress_plane"
        assert meta["ingress_plane"] == "projects/c2g"
        assert len(meta["governance_refs"]) == 6

    def test_local_no_top_level_governance_refs(self):
        """local adapter schema 把它放 metadata 里, 不是顶层"""
        task = build_local_task(task_id="T-001", title="X")
        assert "governance_refs" not in task
        assert "governance_refs" in task["metadata"]

    def test_local_context_uri_default(self):
        task = build_local_task(task_id="T-007", title="X")
        assert task["metadata"]["context_uri"] == "bos://memory/tasks/T-007"

    def test_local_dependencies_in_metadata(self):
        task = build_local_task(task_id="T-001", title="X", depends_on=["T-002"])
        assert task["metadata"]["depends_on"] == ["T-002"]
        assert "depends_on" not in task

    def test_extra_merged_into_task(self):
        task = build_local_task(
            task_id="T-001",
            title="X",
            extra={"description": "detailed", "priority": "P0"},
        )
        assert task["description"] == "detailed"
        assert task["priority"] == "P0"

    def test_extra_metadata_merged_into_metadata(self):
        task = build_local_task(
            task_id="T-001",
            title="X",
            extra={"metadata": {"risk_level": "L2"}},
        )
        assert task["metadata"]["risk_level"] == "L2"
        # existing keys preserved
        assert task["metadata"]["governance_stack"] == "state_plane.kernel_plane.ingress_plane"

    def test_local_status_override(self):
        task = build_local_task(task_id="T-001", title="X", status="in_progress")
        assert task["status"] == "in_progress"


class TestEcosVsLocalSchemaDivergence:
    """ecos 与 local adapter schema 的关键差异 — 防回归"""

    def test_id_vs_task_id(self):
        ecos = build_ecos_task(task_id="T-001", title="X")
        local = build_local_task(task_id="T-001", title="X")
        assert "id" in ecos and "task_id" not in ecos
        assert "task_id" in local and "id" not in local

    def test_default_status(self):
        ecos = build_ecos_task(task_id="T-001", title="X")
        local = build_local_task(task_id="T-001", title="X")
        assert ecos["status"] == "candidate"
        assert local["status"] == "planned"

    def test_governance_refs_placement(self):
        """ecos 顶层, local 放 metadata"""
        ecos = build_ecos_task(task_id="T-001", title="X")
        local = build_local_task(task_id="T-001", title="X")
        assert ecos.get("governance_refs") is not None
        assert local.get("governance_refs") is None
        assert local["metadata"].get("governance_refs") is not None

    def test_both_have_same_governance_refs_content(self):
        ecos = build_ecos_task(task_id="T-001", title="X")
        local = build_local_task(task_id="T-001", title="X")
        assert ecos["governance_refs"] == local["metadata"]["governance_refs"]
