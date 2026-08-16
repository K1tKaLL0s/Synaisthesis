# 工程路线案例研究：循环迹验证工具（BLUEPRINT_ONLY）

本案例是 **真实项目案例研究**（`examples/real_project_case_study/engineering_case`），
依据 `19 §5 M15.CASE_STUDY.EVAL` 要求展示：用户分流（ENGINEERING_ROUTE_DECISION）、
ENG0–ENG10 以 BLUEPRINT_ONLY 模式推进、无虚构结果。导出 Bundle 可复算。

## 输入

- 自然语言设计（S1/S2/S4 冻结内容）：`design.json` —— 与理论案例同源，但
  `central_claims` 与 `evidence_requirements` 为空（缺少理论核心主张材料），
  工程材料完整（用户/场景/输入输出/状态/约束/成功指标/停止条件）。

## 用户分流与 RQ0–RQ4

1. **RQ0**：`CAPABILITY_READY`（同一能力 Profile）。
2. **RQ1**：`coverage_status=COMPLETE`（学术+工程双路检索）。
3. **RQ2F**：TFO/TFR/TFC/TFW/TFP 中 TFC=FAIL（无核心主张），
   工程 EFS/EFI/EFA/EFM/EFF 全 PASS → `ENGINEERING_PROJECT_CANDIDATE`。
   系统不得把“缺少数学对象”自动解释为工程路线：必须打开
   `ENGINEERING_ROUTE_DECISION` Gate 由用户明确选择。
4. **用户分流**：用户选择 `TRY_ENGINEERING_PROJECT`（`route_selection` 绑定
   feasibility assessment hash 与 input_spec_hash）。
5. **RQ2E 工程概念形式化**：公式化 I/O 契约、状态迁移、要求谓词、
   质量指标（阈值 UNRESOLVED_THRESHOLD 显式未定）、架构候选图与验证义务，
   全部带 traceability；校验通过 → `ENGINEERING_CONCEPT_CANDIDATE`。
6. **RQ3E 用户审查**：`APPROVE`（`EARLY_ENGINEERING_CONCEPT_REVIEW` RESOLVED）。
7. **RQ4E（工程 60 + 应用 40）**：保守聚合 E1=4,E2=4,E3=3,E4=3,E5=4（44）+ 
   EA1=3,EA2=3,EA3=3,EA4=4（26）＝ **总分 70** → `ENGINEERING_NOVELTY_QUALIFIED`，
   `next_target=ENG0`，自动进入 ENG0。

## ENG0–ENG10（BLUEPRINT_ONLY）

- **ENG0 使命宪章**：只有全部 03B §1.1 前置满足才创建
  （route selection、RQ3E 审批 hash、RQ4E 状态与 review hash 绑定；
  `eng0_entry_blockers` 任一不满足 → 结构化 Blocker，不允许自然语言备注绕过）。
- **ENG1–ENG5**：ConOps → Requirements Baseline（Critical 需求必须带数值/布尔阈值）
  → ENG3 参考方案与权衡（证据引用强制）→ 架构基线（稳定 component ID、
  interface contract 带 schema）→ 机械蓝图（Blueprint Completeness Gate：
  requirement→design→task→test 追踪全覆盖，任一缺口即阻断）。
- **ENG6–ENG10**：V&V 计划/回执、工程审计（Critical/Major 阻断交付）、
  应用与扩展路线、证据约束论文（`BLUEPRINT_ONLY` 模式禁止虚构 benchmark）。

## 无虚构结果

本案例是 **蓝图模式** 案例：`story.md` 与导出中不包含任何未执行的实验数字、
性能声明或“已验证”标注。所有验收条件在蓝图层面定义为带阈值或
`UNRESOLVED_THRESHOLD` 的谓词；执行代码/实验必须经过独立授权 Gate
（`BLUEPRINT_ONLY` 默认不运行）。评估测试断言故事文本不含虚构基准数字。

## 可复算性

`export.json` 由 `run_qualification_pipeline`（固定 run_id、固定时间、fixture Provider、
`route_decision=TRY_ENGINEERING_PROJECT`）确定性生成；评估测试逐字段重算比对。
