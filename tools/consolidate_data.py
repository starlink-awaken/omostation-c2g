#!/usr/bin/env python3
"""收口散落的 c2g bets/tasks 到单一权威 .c2g_data 目录, 并回写 bet 状态.

修复 3 处 .c2g_data 漂移 (workspace 根 / c2g/.c2g_data / c2g/bets.json) 的运维工具。
只依赖 c2g.adapters_local (轻量, 无 bridge/cli 的 3.11+ 依赖), 便于任意环境执行与测试.

用法:
  python tools/consolidate_data.py --dest <authoritative_dir> \
      [--source <path> ...] \
      [--set-status GOAL_ID=STATUS ...] \
      [--dry-run]

示例 (把 c2g/.c2g_data + 遗留 c2g/bets.json 收口到 workspace 根, 并回写状态):
  python tools/consolidate_data.py \
      --dest /path/to/workspace/.c2g_data \
      --source /path/to/workspace/projects/c2g/.c2g_data \
      --source /path/to/workspace/projects/c2g \
      --set-status BET-xxxx=done --set-status BET-yyyy=deferred
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from c2g.adapters_local import (
    LocalStorageProvider,
    _dedup_by_key,
    consolidate_data,
)


def _preview(dest: Path, sources) -> dict:
    """不落盘, 预览合并/去重结果 (复用 _dedup_by_key)。"""
    report = {}
    for fname, key in (("bets.json", "goal_id"), ("tasks.json", "task_id")):
        target = dest / fname
        records = json.loads(target.read_text(encoding="utf-8")) if target.exists() else []
        used = []
        for sf in sources:
            sf = Path(sf)
            cand = sf if sf.name == fname else (sf / fname)
            if not cand.exists() or (target.exists() and cand.resolve() == target.resolve()):
                continue
            records = records + json.loads(cand.read_text(encoding="utf-8"))
            used.append(str(cand))
        merged, dropped = _dedup_by_key(records, key)
        report[fname] = {"total": len(merged), "dropped_duplicates": dropped, "sources": used}
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Consolidate c2g bets/tasks + writeback statuses")
    ap.add_argument("--dest", required=True, help="权威数据目录 (.c2g_data)")
    ap.add_argument("--source", action="append", default=[], help="待并入源 (目录或文件), 可重复")
    ap.add_argument("--set-status", action="append", default=[],
                    metavar="GOAL_ID=STATUS", help="回写 bet 状态, 可重复")
    ap.add_argument("--drop", action="append", default=[],
                    metavar="GOAL_ID", help="删除指定 goal_id 的 bet (清垃圾), 可重复")
    ap.add_argument("--dry-run", action="store_true", help="只预览不落盘")
    args = ap.parse_args(argv)

    dest = Path(args.dest)
    preview = _preview(dest, args.source)
    print(f"{'[DRY-RUN] ' if args.dry_run else ''}收口预览 → {dest}")
    for fname, r in preview.items():
        print(f"  {fname}: total={r['total']} 丢弃重复={r['dropped_duplicates']} "
              f"并入源={len(r['sources'])}")

    if args.dry_run:
        for gid in args.drop:
            print(f"  [dry] 将删除 bet: {gid}")
        for pair in args.set_status:
            print(f"  [dry] 将回写状态: {pair}")
        return 0

    report = consolidate_data(dest, args.source)
    store = LocalStorageProvider(str(dest))
    for gid in args.drop:
        n = store.delete_bet(gid)
        print(f"  {'🗑️' if n else '⚠️ 未命中'} 删除 {gid} ({n} 条)")
    status_results = []
    for pair in args.set_status:
        if "=" not in pair:
            print(f"⚠️ 跳过非法 --set-status: {pair}")
            continue
        gid, status = pair.split("=", 1)
        hit = store.update_bet_status(gid, status)
        status_results.append((gid, status, hit))
        print(f"  {'✅' if hit else '⚠️ 未命中'} {gid} → {status}")

    print("✅ 收口完成:", json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
