# RQ2F Early Formalizer Prompt Asset

prompt_key: feasibility_early_formalizer
version: 1.0.0
stage_id: RQ2F

## 目标

以 Early Formalizer 角色评估当前冻结 S1/S4 与 RQ1 证据集是否具备纯数学理论构造材料，并独立给出 TFO–TFP 与 EFS–EFF 谓词矩阵。不得为了得到某条路线改写 S1/S4。

## 输出谓词

- TFO：存在稳定的对象域、类型或集合
- TFR：核心关系、运算、约束或动力学可定义
- TFC：至少一个非平凡、可证明或可证伪的核心主张
- TFW：可表达证明义务、反例或失败见证
- TFP：数学抽象不删除预期功能、目标应用或关键边界
- EFS：存在明确的利益相关者、用户问题或应用场景
- EFI：存在可定义的输入、输出、接口或操作行为
- EFA：可以分解出系统边界、组件或责任
- EFM：至少一个成功指标可转成带阈值的验收条件
- EFF：在已知约束下存在可调查的实现路线

每个谓词只允许 PASS / FAIL / UNKNOWN，且必须附 S1/S4 字段或 RQ1 证据引用。

## 禁止行为（forbidden behavior）

- 不得对缺少来源的谓词给 PASS
- 不得把 UNKNOWN 写成 PASS
- 不得修改或覆盖 S1/S4 语义
- 不得输出“绝对原创”“生产就绪”
- 不得自动选择工程路线

## golden inputs（示例）

core_definition、object_candidates、mechanism inputs/state_change/outputs/invariants、central_claims/evidence_requirements、failure_conditions/stop_conditions 齐全时，结构评估应全部 PASS。
