"""Tests for c2g.ports — Protocol structural conformance via inspect.

ports.py 是 Protocol 定义 (IGovernanceProvider / IStorageProvider),
无 @runtime_checkable, 所以 isinstance 检查在 runtime 不可用。
本测试通过 inspect.signature 验证契约结构, 并通过 mock 实现验证行为。
"""

from __future__ import annotations

import inspect

from c2g.domain import BetSchema, PitchSchema, TaskSchema
from c2g.ports import IGovernanceProvider, IStorageProvider

# ── Mock 实现用于 Protocol 契约测试 ──


class _ValidGovernanceProvider:
    """完全符合 IGovernanceProvider 契约"""

    def validate_pitch(self, pitch: PitchSchema) -> bool:
        return bool(pitch.title) and len(pitch.title) >= 3

    def validate_task(self, task: TaskSchema) -> bool:
        return bool(task.title)

    def get_current_phase(self) -> str:
        return "phase_test"


class _ValidStorageProvider:
    def __init__(self) -> None:
        self._pitches: dict[str, PitchSchema] = {}
        self._bets: dict[str, BetSchema] = {}

    def save_bet(self, bet: BetSchema) -> str:
        self._bets[bet.goal_id] = bet
        return bet.goal_id

    def save_task(self, task: TaskSchema) -> str:
        return task.task_id

    def get_pitches(self) -> list[PitchSchema]:
        return list(self._pitches.values())

    def delete_pitch(self, pitch_id: str) -> bool:
        return self._pitches.pop(pitch_id, None) is not None

    def get_active_bets(self) -> list[BetSchema]:
        return [b for b in self._bets.values() if b.status == "active"]


class _BrokenGovernanceProvider:
    """故意缺一个方法 — validate_pitch 缺失"""

    def validate_task(self, task: TaskSchema) -> bool:
        return True

    def get_current_phase(self) -> str:
        return "broken"


class _BrokenStorageProvider:
    """save_task 签名错误 (无参数)"""

    def save_bet(self, bet: BetSchema) -> str:
        return bet.goal_id

    def save_task(self) -> str:  # wrong signature
        return ""

    def get_pitches(self) -> list[PitchSchema]:
        return []

    def delete_pitch(self, pitch_id: str) -> bool:
        return False

    def get_active_bets(self) -> list[BetSchema]:
        return []


class _ValidPitch(PitchSchema):
    pass


class _ValidTask(TaskSchema):
    pass


class _ValidBet(BetSchema):
    pass


# ── Helper ──


def _non_self_params(protocol_cls, method_name: str) -> list[str]:
    """Return non-self parameters of a Protocol method."""
    sig = inspect.signature(getattr(protocol_cls, method_name))
    return [p for p in sig.parameters if p != "self"]


# ── IGovernanceProvider 契约 ──


class TestIGovernanceProviderStructuralContract:
    """通过 inspect.signature 验证 Protocol 契约 (静态检查)"""

    def test_protocol_has_3_methods(self):
        methods = [m for m in dir(IGovernanceProvider) if not m.startswith("_")]
        assert len(methods) == 3

    def test_validate_pitch_signature(self):
        params = _non_self_params(IGovernanceProvider, "validate_pitch")
        assert params == ["pitch"]
        sig = inspect.signature(IGovernanceProvider.validate_pitch)
        assert sig.return_annotation is bool

    def test_validate_task_signature(self):
        params = _non_self_params(IGovernanceProvider, "validate_task")
        assert params == ["task"]
        sig = inspect.signature(IGovernanceProvider.validate_task)
        assert sig.return_annotation is bool

    def test_get_current_phase_signature(self):
        params = _non_self_params(IGovernanceProvider, "get_current_phase")
        assert params == []
        sig = inspect.signature(IGovernanceProvider.get_current_phase)
        assert sig.return_annotation is str

    def test_valid_mock_has_all_methods(self):
        provider = _ValidGovernanceProvider()
        for method in ("validate_pitch", "validate_task", "get_current_phase"):
            assert hasattr(provider, method)

    def test_broken_mock_missing_methods(self):
        provider = _BrokenGovernanceProvider()
        assert not hasattr(provider, "validate_pitch")
        assert hasattr(provider, "validate_task")
        assert hasattr(provider, "get_current_phase")


class TestIGovernanceProviderBehavior:
    def test_validate_pitch_accepts_valid(self):
        provider = _ValidGovernanceProvider()
        p = _ValidPitch(
            pitch_id="P-1", title="Valid title", content="X", created_at="2026-06-22"
        )
        assert provider.validate_pitch(p) is True

    def test_validate_pitch_rejects_empty(self):
        provider = _ValidGovernanceProvider()
        p = _ValidPitch(pitch_id="P-1", title="", content="X", created_at="2026-06-22")
        assert provider.validate_pitch(p) is False

    def test_validate_task_accepts_valid(self):
        provider = _ValidGovernanceProvider()
        t = _ValidTask(
            task_id="T-1",
            title="Task",
            description="d",
            created_at="2026-06-22",
            updated_at="2026-06-22",
        )
        assert provider.validate_task(t) is True

    def test_get_current_phase_returns_string(self):
        provider = _ValidGovernanceProvider()
        phase = provider.get_current_phase()
        assert isinstance(phase, str)
        assert phase == "phase_test"


# ── IStorageProvider 契约 ──


class TestIStorageProviderStructuralContract:
    """通过 inspect.signature 验证 Storage Provider 契约"""

    def test_protocol_has_5_methods(self):
        methods = [m for m in dir(IStorageProvider) if not m.startswith("_")]
        assert len(methods) == 5
        for expected in (
            "save_bet",
            "save_task",
            "get_pitches",
            "delete_pitch",
            "get_active_bets",
        ):
            assert expected in methods

    def test_save_bet_signature(self):
        params = _non_self_params(IStorageProvider, "save_bet")
        assert params == ["bet"]
        sig = inspect.signature(IStorageProvider.save_bet)
        assert sig.return_annotation is str

    def test_save_task_signature(self):
        params = _non_self_params(IStorageProvider, "save_task")
        assert params == ["task"]
        sig = inspect.signature(IStorageProvider.save_task)
        assert sig.return_annotation is str

    def test_get_pitches_signature(self):
        sig = inspect.signature(IStorageProvider.get_pitches)
        assert sig.return_annotation == list[PitchSchema]

    def test_delete_pitch_signature(self):
        params = _non_self_params(IStorageProvider, "delete_pitch")
        assert params == ["pitch_id"]
        sig = inspect.signature(IStorageProvider.delete_pitch)
        assert sig.return_annotation is bool

    def test_valid_mock_has_all_methods(self):
        store = _ValidStorageProvider()
        for method in (
            "save_bet",
            "save_task",
            "get_pitches",
            "delete_pitch",
            "get_active_bets",
        ):
            assert hasattr(store, method)

    def test_broken_mock_wrong_save_task_signature(self):
        store = _BrokenStorageProvider()
        sig = inspect.signature(store.save_task)
        # 故意错误签名: 缺 task 参数
        assert "task" not in sig.parameters


class TestIStorageProviderBehavior:
    def test_save_bet_roundtrip(self):
        store = _ValidStorageProvider()
        bet = _ValidBet(
            goal_id="G-1", title="B", description="d", created_at="2026-06-22"
        )
        returned_id = store.save_bet(bet)
        assert returned_id == "G-1"
        active = store.get_active_bets()
        assert len(active) == 1
        assert active[0].goal_id == "G-1"

    def test_save_and_get_pitches_roundtrip(self):
        store = _ValidStorageProvider()
        pitch = _ValidPitch(
            pitch_id="P-1", title="X", content="content", created_at="now"
        )
        store._pitches[pitch.pitch_id] = pitch
        pitches = store.get_pitches()
        assert len(pitches) == 1
        assert pitches[0].pitch_id == "P-1"

    def test_delete_pitch_removes(self):
        store = _ValidStorageProvider()
        pitch = _ValidPitch(
            pitch_id="P-1", title="X", content="content", created_at="now"
        )
        store._pitches[pitch.pitch_id] = pitch
        assert store.delete_pitch("P-1") is True
        assert store.get_pitches() == []

    def test_delete_pitch_idempotent(self):
        store = _ValidStorageProvider()
        assert store.delete_pitch("nonexistent") is False

    def test_get_active_bets_filters(self):
        store = _ValidStorageProvider()
        active_bet = _ValidBet(
            goal_id="G-1", title="A", description="d", status="active", created_at="now"
        )
        archived_bet = _ValidBet(
            goal_id="G-2",
            title="B",
            description="d",
            status="archived",
            created_at="now",
        )
        store.save_bet(active_bet)
        store.save_bet(archived_bet)
        active = store.get_active_bets()
        assert len(active) == 1
        assert active[0].goal_id == "G-1"

    def test_save_task_returns_id(self):
        store = _ValidStorageProvider()
        task = _ValidTask(
            task_id="T-1",
            title="X",
            description="d",
            created_at="now",
            updated_at="now",
        )
        assert store.save_task(task) == "T-1"


# ── Protocol 行为文档化 ──


class TestProtocolBehaviorDocs:
    """固化 Protocol 契约的语义, 防回归"""

    def test_governance_provider_duck_typing(self):
        """Protocol 不强制 registration, 任何符合方法签名的类都满足"""

        class _Duck:
            def validate_pitch(self, pitch):
                return True

            def validate_task(self, task):
                return True

            def get_current_phase(self):
                return "duck"

        duck = _Duck()
        assert hasattr(duck, "validate_pitch")
        assert hasattr(duck, "validate_task")
        assert hasattr(duck, "get_current_phase")
        assert callable(duck.validate_pitch)
        assert callable(duck.get_current_phase)

    def test_storage_provider_5_methods_signature(self):
        methods = [m for m in dir(IStorageProvider) if not m.startswith("_")]
        assert len(methods) == 5

    def test_governance_provider_3_methods_signature(self):
        methods = [m for m in dir(IGovernanceProvider) if not m.startswith("_")]
        assert len(methods) == 3

    def test_protocols_have_docstrings(self):
        """每个 method 都有 docstring — 防契约文档漂移"""
        for method in ("validate_pitch", "validate_task", "get_current_phase"):
            doc = getattr(IGovernanceProvider, method).__doc__
            assert doc and len(doc.strip()) > 5, f"{method} missing or short docstring"
        for method in (
            "save_bet",
            "save_task",
            "get_pitches",
            "delete_pitch",
            "get_active_bets",
        ):
            doc = getattr(IStorageProvider, method).__doc__
            assert doc and len(doc.strip()) > 5, f"{method} missing or short docstring"
