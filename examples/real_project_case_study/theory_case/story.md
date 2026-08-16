# 理论路线案例研究：循环迹不变性（tr(AB)=tr(BA)）

本案例是 **真实项目案例研究**（`examples/real_project_case_study/theory_case`），依据
`19 §5 M15.CASE_STUDY.EVAL` 要求记录：至少一次失败、一次修复、一次 Gate、
真实工具证据和完整 RQ0–RQ4 流程。所有导出 Bundle 均可复算（`evals/case_study_eval`）。

## 输入

- 自然语言设计（S1/S2/S4 冻结内容）：`design.json`
  - 核心定义：矩阵乘积的迹在因子循环置换下保持不变。
  - 对象域：有限方阵上的迹代数。
  - 核心主张：`tr(AB)=tr(BA)`（与一条证明义务对应）。
  - 失败条件：不可乘形状；停止条件：出现反例。

## RQ0–RQ4 流程

1. **RQ0 能力确认**：`case-profile`（capability_tier=ADVANCED、formalization_eval_score=92、
   math_schema_valid_rate=0.98、来源引用与结构化输出支持、上下文预算充足、评估未过期）
   → `CAPABILITY_READY`。证据：`phase2_approved_export.json.capability.status`。
2. **RQ1 检索**：学术（OpenAlex/Crossref/arXiv fixture）与工程（GitHub/PyPI fixture）
   双向查询；去重后 ≥5 学术近邻、≥3 工程近邻 → `coverage_status=COMPLETE`。
   证据：`phase2_approved_export.json.sources`。
3. **RQ2F 可行性分流**：理论与工程谓词全 PASS → `HYBRID_FIT`（默认走理论 RQ2M）。
   证据：`phase2_approved_export.json.feasibility_matrix`。
4. **RQ2M 早期形式化**：生成公式 Bundle（对象域/假设/核心主张/失败见证/应用映射，
   全部 LaTeX 公式，含来源映射与依赖图）。
5. **RQ3M 用户审查 —— 失败与修复**：
   - **失败**：`phase1_revision_export.json` 记录用户以 `REQUEST_REVISION` 驳回第一版
     Bundle（`EARLY_FORMALIZATION_REVIEW` Gate，状态 `RESOLVED`，决策 `REQUEST_REVISION`）。
   - **修复**：用户修订后，`phase2_approved_export.json` 记录第二版 Bundle 经
     `APPROVE` 批准（同一 Gate 类型，RESOLVED）。不允许在未批准 hash 下启动 RQ4。
6. **RQ4M 新颖性审验（理论 50 + 应用 50）**：两个隔离 Reviewer（不同模型家族）
   保守聚合 `q_i=min(primary, auditor)`：
   - T1–T4 评 4 → 理论 40 分；A1–A5 评 3 → 应用 30 分；**总分 70**。
   - 每个评分项引用 RQ1 近邻（`NoveltyItemEvidence` 强制）。
7. **固定路由**：`review_valid ∧ total=70 ≥ 70 ∧ route=THEORY` →
   `NOVELTY_QUALIFIED`，`next_target=S5`，自动进入 S5（无需额外普通确认）。

## 真实工具证据

- `lean/trace_cyclic.lean`：迹不变性的最小类比（2 元组循环旋转保和），
  由真实 Lean 4 二进制编译（`run_lean`），`lean_evidence_ok` 仅接受 exit 0。
  评估测试 `evals/case_study_eval/test_case_study_eval.py::test_theory_case_real_lean_tool`
  每次真实执行并记录 statement hash 与 receipt。
- 本仓库既有真实工具回执（案例背景）：Z3 5.0.0（M8.1）、Lean 4.32.2（M8.3/M9.1）、
  Docker 29.7.2 沙箱（M8.2）均以真实 smoke 记录在 `IMPLEMENTATION_STATUS.md`。

## Gate 清单（本案例）

| Gate | 阶段 | 状态 |
|---|---|---|
| `EARLY_FORMALIZATION_REVIEW`（v1） | RQ3M | RESOLVED / REQUEST_REVISION（失败） |
| `EARLY_FORMALIZATION_REVIEW`（v2） | RQ3M | RESOLVED / APPROVE（修复） |
| S5 前置（incubation service） | 进入 S5 | 由 `EARLY_QUALIFICATION_REQUIRED` 守卫验证 |

## 可复算性

`phase1_revision_export.json` 与 `phase2_approved_export.json` 由
`run_qualification_pipeline`（固定 run_id、固定时间、fixture Provider）确定性生成；
评估测试逐字段重算比对，任何输入或实现变化都会使比对失败。
