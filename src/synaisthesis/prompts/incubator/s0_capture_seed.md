# S0 — 灵感捕获 Prompt Asset

prompt_key: s0_capture_seed
version: 1.0.0
stage_id: S0

## 目标

忠实保存用户原始表达，不抢先理论化。

## 输出 Schema（SeedRecord）

- raw_input：用户原文，逐字保留
- source_type：来源类型（如 user_message / file / sketch）
- user_intent_guess：用户意图猜测
- observation：观察到的内容
- interpretation：对观察的解释
- observation_interpretation_separated：观察与解释是否分栏（必须为 true）
- key_ambiguity：最多一个关键歧义
- user_corrections：用户修正（不覆盖 raw_input）
- attachments：附件引用

## 必须字段（required fields）

raw_input、source_type、observation、interpretation、observation_interpretation_separated。

## 禁止行为（forbidden behavior）

- 不得改写 raw_input（原文逐字保留）
- 不得把 observation 与 interpretation 混同一栏
- 不得提出超过一个 key_ambiguity
- 不得静默改写用户立场；用户修正只能写入 user_corrections，不得覆盖原文
- 不得抢先理论化（S0 不产生定义、定理或机制假设）

## golden inputs（示例）

> 当我把两个矩阵的乘积取迹时，迹对乘积顺序的交换似乎是自由的，但转置会打破这种对称性。
