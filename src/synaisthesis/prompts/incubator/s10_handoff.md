# S10 Research Handoff Prompt Asset

prompt_key: s10_handoff
version: 1.0.0
stage_id: S10

## 目标

形成 ResearchHandoffBundle 研究交接包：无未归属证据、每个下游任务有输入/输出/门槛、可形成 FrozenClaim 候选。成熟门先检查理论 route 的 RQ4M 状态。

## 必须覆盖

- frozen_terms / current_versions：冻结术语与各 Artifact 当前版本
- evidence_summary：每条证据必须标注 @来源（未归属证据不允许）
- open_questions / verification_thresholds
- downstream_tasks：每个任务有 task_id/title/track/input/output/threshold
- proof_track / experiment_track / engineering_track / writing_track
- artifact_manifest / unresolved_gates

## 禁止行为（forbidden behavior）

- 不得存在未归属证据
- 下游任务缺输入、输出或门槛时不得通过
- 不得伪造 FrozenClaim 候选
- 工程 route 不得进入理论 S10（成熟门只接受理论 RQ4M）

## golden inputs（示例）

对"迹计算库"场景，应给出 frozen_terms（trace、cyclic invariant）、证据（"tr(AB)=tr(BA) 已由最小案例验证 @s5-1"）、下游任务（Lean 形式化：输入=S7 plan、输出=proof candidate、门槛=kernel accepted）与四类 track。
