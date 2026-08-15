# S1 — 自然语言定义 Prompt Asset

prompt_key: s1_natural_language_spec
version: 1.0.0
stage_id: S1

## 目标

把用户原始表达转成结构化自然语言定义，且不偷换定义。S1 是后续数学化工作的最高自然语言语义权威。

## 输出 Schema（NaturalLanguageSpec）

- core_definition：核心定义
- positive_examples：正例
- non_examples：非例
- boundary_conditions：边界条件
- object_candidates：对象候选
- ambiguous_terms：歧义术语
- explicit_non_goals：明确非目标
- expected_functions：预期功能
- target_applications：目标应用
- intended_users：目标用户
- operational_constraints：运行约束
- success_metrics：成功指标
- assistant_proposed：助手提案标记（提案时 true）
- user_confirmed：用户确认标记（只可由真实用户事件置 true）

## 必须字段（required fields）

以上全部 13 个内容字段缺一不可。

## PASS 条件

- 至少一个正例；
- 至少一个非例；
- 至少一个边界；
- 用户明确确认。

## 禁止行为（forbidden behavior）

- 不得偷换 S0 原文定义（core_definition 必须与原文语义一致）
- 不得在正例/非例/边界任一为空时声称完成
- 不得在没有真实用户事件时置 user_confirmed=true
- 模型不能代替用户确认；assistant 只能提案
- 不得把 S1 写成定理证明或形式化公式（那是后续阶段的工作）

## golden inputs（示例）

core_definition: 迹是方阵对角元之和，tr(AB)=tr(BA) 对可相乘的方阵成立。
positive_examples: tr(AB)=tr(BA)；tr(ABC)=tr(BCA)
non_examples: det(AB)=det(A)det(B) 不涉及交换对称
boundary_conditions: A 与 B 必须可相乘且乘积为方阵；仅对迹成立
