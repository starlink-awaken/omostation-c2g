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
