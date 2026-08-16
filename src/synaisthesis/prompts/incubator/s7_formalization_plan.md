# S7 Formalization Plan Prompt Asset

prompt_key: s7_formalization_plan
version: 1.0.0
stage_id: S7

## 目标

消费已批准 RQ2M 早期公式，生成独立的 FormalizationPlan：把理论命题组织为带对象域、量词与证伪见证的 Claim，规划 Lean/Z3 等工具的证明/反例路径。只产生 candidate；AI 产生的形式证明先标 `PROOF_CANDIDATE`。

## 必须覆盖

- object_domain / symbols / definitions / assumptions / quantifiers
- claims：每个 Claim 有 claim_id、statement、object_domain、quantifiers、falsification_witness
- dependency_graph：无环或显式声明递归
- proof_paths / counterexample_paths：证明与反例路径
- intended_tools：已选验证工具，或显式 `NOT_APPLICABLE`
- formalization_uncertainties：形式化不确定项
- proof_candidate_artifacts：AI 证明候选工件清单

## 禁止行为（forbidden behavior）

- 不得把早期公式误标成 Tool-verified
- 不得把 S1/S4 语义变化悄悄吸收；必须回退 S1/S4/RQ
- Claim 缺少对象域、量词或证伪见证时不得通过
- 依赖图有环且未显式声明递归时不得通过
- 模型不得代替用户批准

## golden inputs（示例）

对"迹计算库"场景，应给出 claims：`∀A,B ∈ M_n, tr(AB)=tr(BA)`（对象域=有限矩阵，量词=∀，证伪见证=非方阵/形状不符）、依赖图（claim1 ← 定义2）、intended_tools=["Lean 4"] 与 PROOF_CANDIDATE 工件。
