# RQ2E Engineering Concept Prompt Asset

prompt_key: concept_engineering
version: 1.0.0
stage_id: RQ2E

## 目标

在用户已选择 TRY_ENGINEERING_PROJECT 后，把工程意图固定为可机器验收的 EngineeringConceptBundle。只能产生 candidate；不授权代码、采购、部署或生产变更。

## 必须覆盖

- system_boundary_model：Actors / ExternalSystems / TrustZones
- input_output_contracts：F: X × C → Y
- state_transition_formulas：s_{t+1}=T(s_t,u_t,e_t)
- requirement_predicates：R_i(z) ∈ {true,false}
- quality_metric_formulas：Q_j(z) comparator_j threshold_j
- architecture_graph_candidate：G_arch=(V,E,type)
- traceability_relation：Trace ⊆ Requirement × DesignElement × VerificationObligation
- verification_obligations：包含失败状态与恢复义务

未知阈值必须写 `UNRESOLVED_THRESHOLD`，不得虚构数字。

## 禁止行为（forbidden behavior）

- 不得把工程构想伪装成纯数学定理
- 不得写入 IMPLEMENTED / VALIDATED / PRODUCTION_READY / NOVEL
- 不得虚构阈值或成功证据
- 不得在 route hash 不匹配时构建
- 模型不得代替用户审批

## golden inputs（示例）

对“迹计算库”场景，应生成输入输出、状态转移、要求谓词、未决质量阈值、组件图、需求追踪与失败恢复义务。
