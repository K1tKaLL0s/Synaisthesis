# S2 — 机制草图 Prompt Asset

prompt_key: s2_mechanism_sketch
version: 1.0.0
stage_id: S2

## 目标

把 S1 的自然语言定义扩展为机制草图。机制草图只描述输入、状态变化、输出、不变量与失败条件；不得把相关性自动写成因果。

## 输出 Schema（MechanismSketch）

- inputs：输入列表
- state_change：状态变化
- outputs：输出列表
- invariants：不变量列表
- failure_conditions：失败条件列表
- causal_claims：因果主张列表
- merely_descriptive_relations：仅描述性关系列表
- uncertainty_register：不确定性登记列表

## 必须字段（required fields）

inputs、state_change、outputs、invariants、failure_conditions、causal_claims、merely_descriptive_relations、uncertainty_register。

## PASS 条件

- 输入、变化、输出齐全；
- 至少一个不变量；
- 至少一个失败条件；
- 同一关系不得同时出现在 causal_claims 与 merely_descriptive_relations。

## 禁止行为（forbidden behavior）

- 不得把相关性自动写成因果；
- 不得在无输入/无输出/无状态变化时声称机制草图完成；
- 不得在无不变量或失败条件时声称 PASS；
- 不得改写 S1 的 core_definition。

## golden inputs（示例）

inputs: ["方阵 A", "方阵 B"]
state_change: "取乘积 AB 与 BA 的迹"
outputs: ["tr(AB)", "tr(BA)"]
invariants: ["tr(AB)=tr(BA)"]
failure_conditions: ["A、B 不可相乘时无定义"]
causal_claims: ["循环置换使迹不变"]
merely_descriptive_relations: ["乘积交换与迹不变在样本中相关"]
uncertainty_register: ["转置是否打破该对称性未定"]
