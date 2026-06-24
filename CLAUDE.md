# CLAUDE.md — C2G (Concept-to-Goal)

> eCOS v5 战略需求引擎 · Pitch → Bet → Planned Task

## Project Identity

C2G 是 eCOS v5 的**战略需求管控框架**，负责把未经雕琢的意图 (Pitch) 转化为受治理的 Bet 和可执行的 OMO Planned Task。

- **唯一战略入口**：只能向 `.omo/tasks/planned/` 和 `.omo/goals/current.yaml` 物化
- **沙箱先行**：模糊意图先在 `runtime/sandbox/pitches/` 沉淀为结构化 Pitch
- **门控监督**：通过 OMO M2 schema 和 X1-X4 约束拦截不合规提案

## Core Pipeline

```
Topic / Vision
    │
    ▼
c2g brainstorm "..."  ──►  Idea-<slug>.md  (Pitch template)
    │
    ▼ (user fills background/boundaries/frontmatter)
c2g bet <pitch.md>    ──►  Bet in goals/current.yaml
    │                       Planned Task(s) in tasks/planned/
    ▼
OMO worker dispatch
```

## CLI

```bash
# V2P: generate a structured Pitch from a topic
c2g --adapter ecos brainstorm "AI 驱动的代码审查"

# C2G: convert Pitch to Bet + Planned Tasks
c2g --adapter ecos bet ./runtime/sandbox/pitches/Idea-ai-driven-de-code-review-assistant.md

# Strategy audit
c2g --adapter ecos radar

# Garbage collect stale pitches
c2g --adapter ecos gc --dry-run
```

## Pitch Format

```markdown
> **Upstream**: MS-001
> **Appetite:** 2 weeks

# Pitch: 认知卡带动态挂载机制

## 背景
...

## 目标
...

## 技术要求
...

## 验收标准
1. ...
```

## Agent Rules

1. **Never write to `.omo/` directly** — use `c2g bet` or `omo` CLI/MCP tools.
2. **Always declare `Upstream`** — orphan pitches are rejected.
3. **No TODO/TBD in bet-bound tasks** — OMO M2 validation rejects them.
4. **Prefer `ecos` adapter** in the OMOstation workspace; use `local` only for standalone experiments.

## Adapter Behavior

### `get_omo_dir(base_dir)` — workspace `.omo/` 定位 (P52 修)

向上遍历找 `.omo/`, 返回**最外层 (workspace 边界内)** 的:

- **外层优先** (`found[-1]`): workspace 内嵌套子项目 `.omo/` 时, 用外层主 workspace (shadow-free). `test_smoke::test_get_omo_dir_prefers_outermost_shadow_free_root` 覆盖.
- **排除 `Path.home()` 的 `.omo/`**: `~/.omo` 是系统级 omostation 安装, 非 workspace 候选. 否则 workspace 在 `~/` 下时会误返 home (曾导致 `test_bet_id_reuse` 找不到 `goals/current.yaml`).
- 未找到 → 返回 `base_dir / ".omo"` (默认).

### `strip_frontmatter(text)` — P45 frontmatter 兼容 (P52 修)

`.omo` 数据文件 (`goals/current.yaml` 等) 被 P45 doc-lifecycle 统一加了 `--- frontmatter ---`, 变成 multi-document YAML. `yaml.safe_load` 只支持 single document, 遇到第二个 `---` 会抛 `ComposerError`.

`strip_frontmatter()` 返回 frontmatter 之后的 body, 让 parser 正常解析. 读 `.omo` yaml 的代码 (如 `bridge_import.py` bet 流程) 应先 strip.

> 注: 数据文件 frontmatter 是 P45 治理设计 (不删), parser 侧适配.
