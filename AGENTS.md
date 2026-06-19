# AGENTS.md — C2G Development Guide

> eCOS v5 X 横切框架 · 战略需求引擎 — Concept-to-Goal / Pitch → Bet → Task

## Quick Commands

```bash
cd projects/c2g

# 测试
uv run pytest tests/ -q

# lint / format
uv run ruff check src/
uv run ruff format src/

# install
uv sync
```

## Architecture

| Module | Responsibility |
|:--|:--|
| `src/c2g/cli.py` | CLI entry (`brainstorm` / `bet` / `radar` / `gc`) |
| `src/c2g/mcp_server.py` | FastMCP server |
| `src/c2g/bridge.py` | Legacy Pitch → Bet/Task import |
| `src/c2g/bridge_import.py` | [C2G v4] Pitch frontmatter parsing + Bet/Task materialization |
| `src/c2g/strategy.py` | radar audit + gc |
| `src/c2g/ports.py + adapters.py` | IOC + ecos/omo adapter |
| `src/c2g/llm.py` | LLM task extraction from pitch |
| `src/c2g/task_builder.py` | Task data builder |

## Adapters

- **`local`**: stores data under `.c2g_data/`
- **`ecos`**: writes to `.omo/goals/current.yaml` and `.omo/tasks/planned/`, validates via OMO M2 schema

## Pitch Frontmatter

Pitch markdown must start with a contiguous blockquote frontmatter block:

```markdown
> **Upstream**: MS-XXX
> **Appetite:** 3 days

# Pitch: ...
```

`Upstream` is required for `c2g bet`; `Appetite` defaults to `Unknown`.

## Key Constraints

- Do not bypass OMO M2 validation when using `ecos` adapter.
- Pitches without `Upstream` are rejected by CR-STRATEGY-01.
- `brainstorm` generates real Pitch files under `runtime/sandbox/pitches/` (ecos) or `.c2g_data/pitches/` (local).
