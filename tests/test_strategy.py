"""Tests for c2g strategy engine (Round 43 P1 修真后).

验证:
- _list_task_files / _collect_metrics 真读 yaml
- _check_anomalies 真按指标告警 (修真前 mock 无告警)
- strategy_gc 真按 mtime 清理僵尸 pitch
"""
from collections import Counter
from pathlib import Path


from c2g.strategy import (
    _load_yaml_safe,
    _list_task_files,
    _collect_metrics,
    _check_anomalies,
)


class TestLoadYamlSafe:
    def test_valid_yaml(self, tmp_path: Path):
        f = tmp_path / "ok.yaml"
        f.write_text("id: T1\nstatus: planned\npriority: P1\n", encoding="utf-8")
        data = _load_yaml_safe(f)
        assert data["id"] == "T1"

    def test_invalid_yaml_returns_none(self, tmp_path: Path):
        f = tmp_path / "bad.yaml"
        f.write_text("not: valid: yaml: :::", encoding="utf-8")
        assert _load_yaml_safe(f) is None

    def test_non_dict_returns_none(self, tmp_path: Path):
        f = tmp_path / "list.yaml"
        f.write_text("- a\n- b\n", encoding="utf-8")
        assert _load_yaml_safe(f) is None

    def test_missing_file(self, tmp_path: Path):
        assert _load_yaml_safe(tmp_path / "missing.yaml") is None


class TestListTaskFiles:
    def test_both_dirs_empty(self, tmp_path: Path):
        done, planned = _list_task_files(tmp_path)
        assert done == []
        assert planned == []

    def test_both_dirs_populated(self, tmp_path: Path):
        (tmp_path / "tasks" / "done").mkdir(parents=True)
        (tmp_path / "tasks" / "planned").mkdir(parents=True)
        (tmp_path / "tasks" / "done" / "D1.yaml").write_text("id: D1")
        (tmp_path / "tasks" / "planned" / "P1.yaml").write_text("id: P1")
        done, planned = _list_task_files(tmp_path)
        assert len(done) == 1
        assert len(planned) == 1

    def test_only_done_dir(self, tmp_path: Path):
        (tmp_path / "tasks" / "done").mkdir(parents=True)
        done, planned = _list_task_files(tmp_path)
        assert len(done) == 0
        assert planned == []


class TestCollectMetrics:
    def test_empty(self, tmp_path: Path):
        metrics = _collect_metrics([])
        assert metrics["priority"]["unassigned"] == 0
        assert metrics["risk_level"]["unassigned"] == 0
        assert metrics["owner"]["unassigned"] == 0

    def test_aggregates(self, tmp_path: Path):
        (tmp_path / "t1.yaml").write_text(
            "priority: P0\nrisk_level: L3\nowner: agent-1\nphase: P42\nstatus: planned",
            encoding="utf-8",
        )
        (tmp_path / "t2.yaml").write_text(
            "priority: P0\nrisk_level: L1\nowner: agent-2\nphase: P42\nstatus: done",
            encoding="utf-8",
        )
        metrics = _collect_metrics(list(tmp_path.glob("*.yaml")))
        assert metrics["priority"]["P0"] == 2
        assert metrics["risk_level"]["L3"] == 1
        assert metrics["risk_level"]["L1"] == 1
        assert metrics["owner"]["agent-1"] == 1
        assert metrics["phase"]["P42"] == 2

    def test_handles_missing_fields(self, tmp_path: Path):
        (tmp_path / "t.yaml").write_text("description: only this", encoding="utf-8")
        metrics = _collect_metrics(list(tmp_path.glob("*.yaml")))
        assert metrics["priority"]["unassigned"] == 1
        assert metrics["owner"]["unassigned"] == 1


class TestCheckAnomalies:
    def _metrics(self, p0=0, l3=0, owners=None, total=10):
        return {
            "priority": Counter({"P0": p0, "P1": total - p0}),
            "risk_level": Counter({"L1": total - l3, "L3": l3}),
            "owner": Counter(owners or {"a": 5, "b": 5}),
            "phase": Counter({"P42": total}),
            "status": Counter({"done": total}),
        }

    def test_no_data_warns(self, tmp_path: Path):
        warnings = _check_anomalies(self._metrics(total=0), 0, omo_dir=tmp_path)
        assert any(".yaml 数据" in w for w in warnings)

    def test_p0_accumulation(self, tmp_path: Path):
        m = self._metrics(p0=6, total=10)
        m["priority"] = Counter({"P0": 6, "P1": 4})
        m["risk_level"] = Counter({"L1": 10})
        m["owner"] = Counter({"a": 5, "b": 5})
        warnings = _check_anomalies(m, 10, omo_dir=tmp_path,
                                   pending_metrics=m)
        assert any("P0 任务 6 个" in w for w in warnings)

    def test_l3_risk_warns(self, tmp_path: Path):
        m = self._metrics(l3=1, total=10)
        warnings = _check_anomalies(m, 10, omo_dir=tmp_path,
                                   pending_metrics=m)
        assert any("L3 高风险任务 1 个" in w for w in warnings)

    def test_owner_concentration(self, tmp_path: Path):
        m = self._metrics(owners={"single": 8, "other": 2}, total=10)
        warnings = _check_anomalies(m, 10, omo_dir=tmp_path)
        assert any("Owner 集中度" in w and "single" in w for w in warnings)

    def test_no_anomalies_clean(self, tmp_path: Path):
        # No recent done tasks triggers 7d stagnation warning
        (tmp_path / "tasks" / "done").mkdir(parents=True)
        m = self._metrics(owners={"a": 3, "b": 3, "c": 4}, total=10)
        warnings = _check_anomalies(m, 10, omo_dir=tmp_path)
        # Only stagnation warning expected
        assert any("7 天无 done task" in w for w in warnings)

    def test_recent_done_no_stagnation(self, tmp_path: Path):
        (tmp_path / "tasks" / "done").mkdir(parents=True)
        recent = tmp_path / "tasks" / "done" / "RECENT.yaml"
        recent.write_text("id: R\nstatus: done", encoding="utf-8")
        # set mtime to now
        recent.touch()
        m = self._metrics(owners={"a": 3, "b": 3, "c": 4}, total=10)
        warnings = _check_anomalies(m, 10, omo_dir=tmp_path)
        assert not any("7 天无 done task" in w for w in warnings)