# S4 — 研究方向再规范 Prompt Asset

prompt_key: s4_research_scope_spec
version: 1.0.0
stage_id: S4

## 目标

在 S1–S3 基础上再规范研究方向。主问题唯一、对象域与非目标明确；每个中心主张必须有证据需求；失败也要有可学习输出。S4 只有在真实用户事件确认后，才与已确认 S1 一起支持派生 `NATURAL_LANGUAGE_DESIGN_READY`。

## 输出 Schema（ResearchScopeSpec）

- main_question：主问题
- object_domain：对象域
- non_goals：非目标列表
- nearest_neighbor_difference：与最近邻工作的差异
- central_claims：中心主张列表
- evidence_requirements：证据需求列表（与 central_claims 按下标一一对应）
- failure_learning_plan：失败学习计划
- engineering_relevance：工程相关性
- stop_conditions：停止条件列表
- user_confirmed_scope：用户确认标记（只可由真实用户事件置 true）

## 必须字段（required fields）

以上全部 10 个字段缺一不可；central_claims 与 evidence_requirements 数量必须一致。

## PASS 条件

- 主问题唯一；
- 对象域明确；
- 非目标明确；
- 每个中心主张有证据需求；
- 失败也有可学习输出。

## 禁止行为（forbidden behavior）

- 不得在没有真实用户事件时置 user_confirmed_scope=true；
- 模型不能代替用户确认 scope；
- 不得让中心主张没有对应证据需求；
- 不得把范围改写为与已确认 S1 语义冲突的新问题；
- 不得在重大文献冲突未处理时声称完成。

## golden inputs（示例）

main_question: 迹的循环不变性在什么边界条件下保持？
object_domain: 有限维实/复方阵
non_goals: 不研究行列式的类似性质
nearest_neighbor_difference: 与已有教材相比，本方向明确转置反例边界
central_claims: ["tr(AB)=tr(BA)", "转置会打破该对称性"]
evidence_requirements: ["给出方阵可相乘时的证明", "给出具体转置反例"]
failure_learning_plan: 若边界反例不成立，则收窄对象域并回 S1/S3
engineering_relevance: 数值线性代数中迹的快速计算与验证
stop_conditions: ["无法给出任何非平凡反例", "中心主张全部被推翻"]
user_confirmed_scope: false
