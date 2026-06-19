> **Upstream**: MS-COGNITIVE-001
> **Appetite:** 2 weeks

# Pitch: 认知卡带动态挂载机制

## 背景
当前 MetaOS 通过硬编码方式支持固定执行范式，缺乏灵活性。

## 目标
设计并实现 Cognitive Cartridges 动态挂载机制，允许将独立的执行流（如 GSD、Superpowers）通过配置注入 MetaOS，无需硬编码。

## 技术要求
- 架构设计方案（Schema + Extension Point）
- 2 个概念验证卡带：GSD、Superpowers
- 通过 `mof-schema-validate` 校验
- 能在 bridge.py 或 MetaOS 中成功解析并加载

## 验收标准
1. 挂载 GSD 卡带并跑通一遍 OMO Bet 流程
2. 挂载 Superpowers 卡带并验证多 Agent 协作