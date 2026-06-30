# C2G 能力地图

> 战略需求引擎 (Concept → Pitch → Bet → Governance Task) · X 层横切

---

## 一、架构定位

```
┌─────────────────────────────────────────────────────────────┐
│                    C2G — 战略需求引擎                          │
├─────────────────────────────────────────────────────────────┤
│  Concept  │  Pitch  │  Bet  │  Bridge  │  Strategy  │  Task  │
│  概念输入  │  价值陈述 │  押注  │  桥接    │  策略审计   │  任务  │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、核心功能

| 功能 | 说明 |
|------|------|
| Pitch 解析 | Markdown frontmatter 契约解析 → Bet 物化 |
| Bet 押注 | 押注 ID 分配 / 依赖链解析 / 导入 |
| OMO 桥接 | 向 `.omo/` 物化 planned task (走 c2g/omo broker) |
| 策略审计 | strategy-audit / strategy-gc BOS 服务 |
| 任务构建 | task_builder 从 Bet 生成治理任务 |

---

## 三、模块结构

| 模块 | 职责 |
|------|------|
| `cli.py` | CLI 入口 (argparse) |
| `bridge.py` | 核心桥接逻辑 |
| `bridge_depend.py` | Bet 依赖链解析 |
| `bridge_id.py` | Bet ID 分配 |
| `bridge_import.py` | Pitch 导入 + frontmatter 剥离 |
| `domain.py` | 领域模型 |
| `strategy.py` | 策略审计 / radar |
| `task_builder.py` | 任务构建器 |
| `adapters.py` / `adapters_local.py` | 外部适配器 |
| `mcp_server.py` | MCP 服务端 |

---

## 四、BOS 服务

| BOS URI | 用途 |
|---------|------|
| `bos://governance/strategy-audit` | 策略审计 |
| `bos://governance/strategy-gc` | 策略垃圾回收 |

---

## 五、关键文件

- `pitches/` — Pitch 源文件目录
- `bets.json` — Bet 物化存储
- `tasks.json` — 任务物化存储

---

*项目元数据: [`../../docs/project-registry.yaml`](../../docs/project-registry.yaml)*
