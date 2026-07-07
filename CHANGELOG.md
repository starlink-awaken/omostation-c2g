# C2G Changelog

All notable changes to the C2G (Concept-to-Governance) strategy ingress engine are documented in this file.

## [Unreleased]

### Added
- **CAPABILITY-MAP.md**: strategic demand engine capability map.

### Fixed
- **Radar `pending_metrics` None fallback**: when `planned` is empty, `pending_metrics=None` caused the fallback to include done metrics, incorrectly warning done L3 items as "needs review". Fixed in `strategy.py` and `bin/compass_radar.py`; health restored from 85 to 100.
- **`get_omo_dir` home interference**: outer workspace scan could pick `~/.omo` from the home directory, causing bets to miss `goals/current.yaml`. Iteration now skips `Path.home()/.omo/` while preserving nested workspace semantics.
- **P45 frontmatter YAML corruption**: data files received `--- frontmatter ---` markers and became multi-document YAML, breaking `yaml.safe_load`. Added `strip_frontmatter()` helper in `bridge_utils.py` and applied it in `bridge_import.py` without touching human-editable `goals/current.yaml`.

### Tests
- 152 tests passed, including regression `test_done_l3_not_warned_when_planned_empty` to prevent the None fallback bug from recurring.

## [0.3.0] - 2026-06-15

### Added (C2G v3 Cybernetic Solutions)
- **SSOT Write-back**: `context_uri` write-back mechanism appends audit results to original Markdown designs after task completion, preventing context collapse.
- **Fast-Track Compaction**: `omo worker gc` automatically aggregates tiny delivery tasks (`FAST-*`) into consolidated reports.
- **Agent Tactical Yield**: `omo_yield_task` mechanism addresses long-tail blocking during agent execution.
- **L0 Governance**: C2G v3 L0 X1 gate constraints (`CR-C2G-V3-01~03`) ensure self-healing flows.
