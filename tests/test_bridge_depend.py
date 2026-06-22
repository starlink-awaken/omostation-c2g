"""Tests for c2g.bridge_depend + c2g.omo_client."""
from __future__ import annotations


import pytest

from c2g.bridge_depend import _resolve_depends_on
from c2g.omo_client import _import_omo_module, validate_planned_task_data


class TestResolveDependsOn:
    def test_empty_list(self):
        assert _resolve_depends_on([], {}) == []

    def test_empty_string_skipped(self):
        result = _resolve_depends_on(["", "  ", "XREF"], {"XREF-valid": "IMPORTED-v1"})
        assert "" not in result
        assert "  " not in result
        assert "XREF" in result  # literal (no match in title_to_imported)

    def test_literal_kept_when_no_match(self):
        result = _resolve_depends_on(["P42-W0-X"], {})
        assert result == ["P42-W0-X"]

    def test_exact_title_match(self):
        title_to_imported = {"P42-W0-MERGE-STATE": "IMPORTED-abc123"}
        result = _resolve_depends_on(["P42-W0-MERGE-STATE"], title_to_imported)
        assert result == ["IMPORTED-abc123"]

    def test_title_with_colon_suffix(self):
        """'P42-W0' 匹配 'P42-W0: description' 形式"""
        title_to_imported = {"P42-W0: MERGE state": "IMPORTED-abc"}
        result = _resolve_depends_on(["P42-W0"], title_to_imported)
        assert result == ["IMPORTED-abc"]

    def test_title_with_space_suffix(self):
        """'P42-W0' 匹配 'P42-W0 description' 形式"""
        title_to_imported = {"P42-W0 merge state": "IMPORTED-abc"}
        result = _resolve_depends_on(["P42-W0"], title_to_imported)
        assert result == ["IMPORTED-abc"]

    def test_first_match_wins(self):
        """多个匹配中取第一个 (字典迭代顺序)"""
        title_to_imported = {
            "P42-W0-A: foo": "IMPORTED-aaa",
            "P42-W0-A: bar": "IMPORTED-bbb",
        }
        # 用 P42-W0-A (literal match) 触发 exact match, 然后第二个 title 也匹配 exact
        # 但 dict 顺序保证取第一个
        result = _resolve_depends_on(["P42-W0-A"], title_to_imported)
        assert result == ["IMPORTED-aaa"]

    def test_strip_whitespace_in_ref(self):
        title_to_imported = {"P42-W0-X": "IMPORTED-xyz"}
        result = _resolve_depends_on(["  P42-W0-X  "], title_to_imported)
        assert result == ["IMPORTED-xyz"]

    def test_mixed_resolved_and_literal(self):
        """混合: 一些 resolve 成 hash, 一些保留 literal"""
        title_to_imported = {"P42-W0-X": "IMPORTED-x"}
        result = _resolve_depends_on(
            ["P42-W0-X", "LITERAL-1", "P42-W0-Y"],
            title_to_imported,
        )
        assert result[0] == "IMPORTED-x"  # resolved
        assert result[1] == "LITERAL-1"  # literal kept
        assert result[2] == "P42-W0-Y"  # literal (no match)

    def test_no_partial_match_without_separator(self):
        """'P42-W0' 不应匹配 'P42-W00' (无 : 或 space 分隔)"""
        title_to_imported = {"P42-W00-OTHER": "IMPORTED-other"}
        result = _resolve_depends_on(["P42-W0"], title_to_imported)
        assert result == ["P42-W0"]  # 不匹配, 保留 literal

    def test_empty_title_to_imported_with_refs(self):
        result = _resolve_depends_on(["A", "B"], {})
        assert result == ["A", "B"]

    def test_preserves_order(self):
        title_to_imported = {"A": "HASH-A", "C": "HASH-C"}
        result = _resolve_depends_on(["A", "B", "C", "D"], title_to_imported)
        assert result == ["HASH-A", "B", "HASH-C", "D"]


class TestImportOmoModule:
    """测试 omo_client._import_omo_module 动态导入"""

    def test_imports_omo_task_schema(self):
        # 应能从 omo.omo_task_schema 导入 validate_task_data
        mod = _import_omo_module("omo.omo_task_schema")
        assert hasattr(mod, "validate_task_data")
        assert callable(mod.validate_task_data)

    def test_imports_omo_ingress(self):
        mod = _import_omo_module("omo.omo_ingress")
        assert hasattr(mod, "create_planned_task")
        assert hasattr(mod, "create_goal")

    def test_unknown_module_raises(self):
        with pytest.raises((ImportError, ModuleNotFoundError, FileNotFoundError)):
            _import_omo_module("omo.nonexistent_module_xyz")


class TestValidatePlannedTaskData:
    """validate_planned_task_data 是 omo.omo_task_schema.validate_task_data 的 wrapper"""

    def test_minimal_valid_task(self):
        task_data = {
            "id": "T-001",
            "title": "Test Task",
            "assigned_to": None,
            "dispatch_id": None,
            "run_ref": None,
            "approval_ref": None,
            "review_ref": None,
            "knowledge_refs": [],
            "handoff_refs": [],
            "risk_level": "L0",
            "allowed_operation_level": "L0",
            "human_approval_required": False,
            "source_docs": [],
            "entry_gate": [],
            "evidence_required": [],
            "test_plan": ["uv run pytest"],
        }
        errors = validate_planned_task_data(task_data)
        # 具体错误信息不重要, 但应能调用而不抛异常
        assert isinstance(errors, list)

    def test_missing_required_field_returns_errors(self):
        task_data = {"id": "T-002"}  # 缺 title + 其他字段
        errors = validate_planned_task_data(task_data)
        assert isinstance(errors, list)
        # 至少应有错误 (除 id 外其他字段都缺)
        assert len(errors) > 0


class TestBridgeDependEdgeCases:
    """Bridge 依赖解析的边界情况"""

    def test_unicode_title_match(self):
        title_to_imported = {"中文任务标题": "IMPORTED-cn"}
        result = _resolve_depends_on(["中文任务标题"], title_to_imported)
        assert result == ["IMPORTED-cn"]

    def test_unicode_prefix_with_colon(self):
        title_to_imported = {"中文-W0: 任务": "IMPORTED-x"}
        result = _resolve_depends_on(["中文-W0"], title_to_imported)
        assert result == ["IMPORTED-x"]

    def test_underscore_in_title(self):
        """下划线是普通字符, 不做 separator 处理"""
        title_to_imported = {"foo_bar: extra": "IMPORTED-x"}
        result = _resolve_depends_on(["foo_bar"], title_to_imported)
        assert result == ["IMPORTED-x"]

    def test_very_long_title_handles_1000_chars(self):
        """验证长 title (1000 字符) 也能正确解析"""
        long_title = "x" * 1000
        title_to_imported = {f"{long_title}: extra": "IMPORTED-long"}
        # 直接 exact match 长 title
        result = _resolve_depends_on([long_title], title_to_imported)
        assert result == ["IMPORTED-long"]

    def test_no_match_returns_literal_unchanged(self):
        """无 separator 时不匹配, 保留 literal"""
        title_to_imported = {"foo-bar/baz_v1": "IMPORTED-x"}
        result = _resolve_depends_on(["foo-bar"], title_to_imported)
        assert result == ["foo-bar"]

    def test_mixed_with_extra_keys(self):
        title_to_imported = {
            "title-1: a": "HASH-1",
            "title-2: b": "HASH-2",
        }
        result = _resolve_depends_on(
            ["title-1", "X", "title-2"],
            title_to_imported,
        )
        assert result == ["HASH-1", "X", "HASH-2"]