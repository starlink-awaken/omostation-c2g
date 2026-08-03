"""Tests for bets/tasks upsert dedup, status writeback, and data consolidation.

Covers the fix for the 3-way .c2g_data drift + duplicate-goal_id junk accumulation.
"""

import json
from pathlib import Path

from c2g.adapters_local import LocalStorageProvider, _dedup_by_key, consolidate_data
from c2g.domain import BetSchema, TaskSchema


def _bet(goal_id, status="active", title="T"):
    return BetSchema(
        goal_id=goal_id, title=title, description="d", status=status, created_at="now"
    )


class TestUpsert:
    def test_save_bet_upsert_no_duplicate(self, tmp_path: Path):
        store = LocalStorageProvider(base_dir=str(tmp_path / "c2g"))
        store.save_bet(_bet("BET-1", title="v1"))
        store.save_bet(_bet("BET-1", title="v2"))  # same goal_id → replace
        data = json.loads((tmp_path / "c2g" / "bets.json").read_text())
        assert len(data) == 1
        assert data[0]["title"] == "v2"

    def test_save_bet_distinct_appends(self, tmp_path: Path):
        store = LocalStorageProvider(base_dir=str(tmp_path / "c2g"))
        store.save_bet(_bet("BET-1"))
        store.save_bet(_bet("BET-2"))
        assert len(json.loads((tmp_path / "c2g" / "bets.json").read_text())) == 2

    def test_save_task_upsert(self, tmp_path: Path):
        store = LocalStorageProvider(base_dir=str(tmp_path / "c2g"))
        t1 = TaskSchema(
            task_id="T-1",
            title="a",
            description="d",
            created_at="now",
            updated_at="now",
        )
        t2 = TaskSchema(
            task_id="T-1",
            title="b",
            description="d",
            created_at="now",
            updated_at="now",
        )
        store.save_task(t1)
        store.save_task(t2)
        data = json.loads((tmp_path / "c2g" / "tasks.json").read_text())
        assert len(data) == 1 and data[0]["title"] == "b"


class TestStatusWriteback:
    def test_update_bet_status(self, tmp_path: Path):
        store = LocalStorageProvider(base_dir=str(tmp_path / "c2g"))
        store.save_bet(_bet("BET-1", status="active"))
        assert store.update_bet_status("BET-1", "done") is True
        assert store.get_active_bets() == []
        allb = store.get_all_bets()
        assert len(allb) == 1 and allb[0].status == "done"

    def test_update_bet_status_miss(self, tmp_path: Path):
        store = LocalStorageProvider(base_dir=str(tmp_path / "c2g"))
        store.save_bet(_bet("BET-1"))
        assert store.update_bet_status("BET-NOPE", "done") is False

    def test_delete_bet(self, tmp_path: Path):
        store = LocalStorageProvider(base_dir=str(tmp_path / "c2g"))
        store.save_bet(_bet("BET-1"))
        store.save_bet(_bet("BET-2"))
        assert store.delete_bet("BET-1") == 1
        assert store.delete_bet("BET-NOPE") == 0
        remaining = [b.goal_id for b in store.get_all_bets()]
        assert remaining == ["BET-2"]


class TestConsolidation:
    def test_dedup_drops_duplicate_goal_id(self):
        recs = [{"goal_id": "X"}, {"goal_id": "X"}, {"goal_id": "Y"}]
        kept, dropped = _dedup_by_key(recs, "goal_id")
        assert dropped == 1 and len(kept) == 2

    def test_consolidate_merges_and_dedups(self, tmp_path: Path):
        dest = tmp_path / "dest"
        src = tmp_path / "legacy"
        # dest already has BET-A
        LocalStorageProvider(str(dest)).save_bet(_bet("BET-A"))
        # legacy source has BET-B + a duplicate junk BET-J twice
        (src).mkdir(parents=True)
        (src / "bets.json").write_text(
            json.dumps(
                [
                    {
                        "goal_id": "BET-B",
                        "title": "b",
                        "description": "d",
                        "status": "active",
                        "vector": "V2",
                        "appetite": "1 week",
                        "created_at": "now",
                    },
                    {
                        "goal_id": "BET-J",
                        "title": "junk",
                        "description": "d",
                        "status": "active",
                        "vector": "V2",
                        "appetite": "1 week",
                        "created_at": "now",
                    },
                    {
                        "goal_id": "BET-J",
                        "title": "junk",
                        "description": "d",
                        "status": "active",
                        "vector": "V2",
                        "appetite": "1 week",
                        "created_at": "now",
                    },
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (src / "tasks.json").write_text("[]", encoding="utf-8")

        report = consolidate_data(dest, [src])
        merged = json.loads((dest / "bets.json").read_text())
        gids = sorted(b["goal_id"] for b in merged)
        assert gids == ["BET-A", "BET-B", "BET-J"]  # 3 unique
        assert report["bets.json"]["dropped_duplicates"] == 1
        assert report["bets.json"]["total"] == 3

    def test_consolidate_skips_dest_as_own_source(self, tmp_path: Path):
        dest = tmp_path / "dest"
        LocalStorageProvider(str(dest)).save_bet(_bet("BET-A"))
        # passing dest itself as source must not double-count
        report = consolidate_data(dest, [dest])
        assert report["bets.json"]["total"] == 1
        assert report["bets.json"]["dropped_duplicates"] == 0
