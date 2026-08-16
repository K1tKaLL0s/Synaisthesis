# ENG2 Requirements Baseline Prompt Asset

prompt_key: eng2_requirements
version: 1.0.0
stage_id: ENG2

## 目标

把已批准 ConOps 的意图转化为可追踪、可测试的 EngineeringRequirement 集合，形成 RequirementsBaseline。只能产生 candidate；不授权代码、采购、部署或生产变更。

## 必须覆盖

- 每个 requirement：稳定 requirement_id、单一可测试 statement、source_refs、priority、rationale、precondition/input/expected behavior、measurement method/unit/threshold/tolerance、verification_method、acceptance criterion、owner、dependency/conflict refs
- type 取自 FUNCTIONAL/INTERFACE/DATA/QUALITY/SAFETY/SECURITY/PRIVACY/COMPLIANCE/OPERATIONS/CONSTRAINT
- ConOps intent 双向覆盖 100%（每个 intent 至少被一个 requirement 引用）
- Critical requirement 必须有数值阈值或布尔验收
- 无法确定阈值必须写 `UNRESOLVED_THRESHOLD`，不得虚构数字

## 禁止行为（forbidden behavior）

- 禁止"尽量""适当""快速""友好""高性能"等无阈值形容词
- 不得声称"符合 ISO"却没有逐项证据
- 不得虚构来源引用、阈值或验收方法
- 不得绕过 ConOps 覆盖检查
- 模型不得代替用户审批

## golden inputs（示例）

对"迹计算库"场景，应生成：功能（trace 计算）、质量（p95 延迟阈值）、安全（输入校验）、数据（矩阵格式）、接口（CLI 参数）等 requirement，并全部绑定 ConOps intent。
