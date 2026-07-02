# c2g — System Boundary

> 本文档描述 c2g 与 eCOS 系统其他部分的边界：暴露的接口、依赖的上游、影响的下游。
>
> 系统全景参见：[`../../docs/PANORAMA.md`](../../docs/PANORAMA.md)

---

## 1. 暴露接口

### BOS URI



### 入口

- **CLI**: `c2g` brainstorm/draft/bet/radar/gc
- **MCP stdio**: `c2g-mcp` c2g_bet, c2g_radar, c2g_gc

## 2. 上游依赖

- ecos (L0)
- omo (L2)
- aetherforge-gateway (aetherforge/packages/gateway/)

## 3. 下游影响

- .omo/tasks/

## 4. 配置 / SSOT

- 项目源码：`projects/c2g/`
- 入口定义：`projects/c2g/pyproject.toml` 或 `package.json`
- 测试：`cd projects/c2g && uv run pytest tests/ -q`

## 架构演进与项目边界索引

参见工作区架构演进与项目边界：[`../../docs/ARCHITECTURE-EVOLUTION.md`](../../docs/ARCHITECTURE-EVOLUTION.md)
