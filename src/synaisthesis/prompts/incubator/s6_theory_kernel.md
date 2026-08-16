# S6 Theory Kernel Prompt Asset

prompt_key: s6_theory_kernel
version: 1.0.0
stage_id: S6

## 目标

在 S5 最小案例与已确认 S1 基础上形成核心统一理论 TheoryKernel：提出候选机制、比较至少一个替代理论、保留反例、把预测与解释分开。只产生 candidate；不产生任何验证状态。

## 必须覆盖

- candidate_mechanism：核心机制的明确陈述
- competing_explanations：至少一个替代解释
- examples / counterexamples：正例与反例（反例必须保留，不得静默丢弃）
- invariants / boundaries：不变量与适用边界
- predictions：可检验的预测（与解释分栏）
- discarded_alternatives / discard_reasons：被放弃的替代方案及对应理由
- unresolved_conflicts：未解决冲突

## 禁止行为（forbidden behavior）

- 核心概念变化不得在 S6 静默修补，必须回 S1/S4
- 不得以解释流畅度代替证据
- 不得把预测写成解释，或把解释写成预测
- 不得丢弃反例
- 模型不得写入 PROVED / VERIFIED / TOOL_VERIFIED

## golden inputs（示例）

对"迹计算库"场景，应给出候选机制（tr(AB)=tr(BA) 的循环性质）、一个替代理论（逐元素求和假设）、保留数值反例、不变量（矩阵形状）、边界（有限矩阵）、预测（大矩阵下的数值稳定性）与放弃理由。
