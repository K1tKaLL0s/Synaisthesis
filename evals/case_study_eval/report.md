# M15.CASE_STUDY.EVAL — evaluation report

真实执行记录（2026-08-17，本工作区）。

## 生成与复算

- 冻结导出由 `run_qualification_pipeline` 确定性生成：
  - 理论 phase1（RQ3M REQUEST_REVISION）：`next_target=null`，
    gate=EARLY_FORMALIZATION_REVIEW / RESOLVED —— **失败阶段**
  - 理论 phase2（RQ3M APPROVE）：`next_target=S5`，`novelty_total=70` —— **修复阶段**
  - 工程（TRY_ENGINEERING_PROJECT）：`next_target=ENG0`，`novelty_total=70`
- 复算测试：`evals/case_study_eval/test_case_study_eval.py`
  重跑两个案例的全部 Bundle 并与冻结 JSON 逐字段比对（可复算）。

## 真实工具

- Lean：`~/.elan/bin/lean` 真实编译 `trace_cyclic.lean` → `LEAN_OK`（exit 0），
  评估测试通过 `run_lean` 再次真实执行并断言 `lean_evidence_ok`。

## 检查命令（全部通过）

- focused：`workspace/.venv-m13/bin/python -m pytest evals/case_study_eval/test_case_study_eval.py`
- 全套：`workspace/.venv-m13/bin/python -m pytest`
- `ruff check --no-cache`、`ruff format --check`、`basedpyright`、`git diff --check`

## 停止条件核对

- 案例不含未授权私密研究（全部为公开的确定性合成设计：矩阵迹不变性与验证工具）。
- 案例可复现（Bundle 逐字段重算比对；Lean 每次真实执行）。
