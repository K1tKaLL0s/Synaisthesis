# 真实项目案例研究（M15.CASE_STUDY.EVAL）

本目录收录两条路线的真实项目案例研究，依据 `19 §5 M15`：

- `theory_case/` — 理论路线：循环迹不变性 `tr(AB)=tr(BA)`。
  记录一次失败（RQ3M REQUEST_REVISION）、一次修复（v2 APPROVE）、Gate、
  真实工具（Lean 4 真实编译）与完整 RQ0–RQ4；两个冻结导出 Bundle 均可复算。
- `engineering_case/` — 工程路线：循环迹验证工具。
  记录用户分流（ENGINEERING_ROUTE_DECISION → TRY_ENGINEERING_PROJECT）、
  ENG0–ENG10 以 BLUEPRINT_ONLY 推进、无虚构结果；冻结导出 Bundle 可复算。

评估数据集、报告与复算测试位于 `evals/case_study_eval/`：

```text
workspace/.venv-m13/bin/python -m pytest evals/case_study_eval/test_case_study_eval.py
```

每个案例的 `design.json` 为冻结输入（S1/S2/S4）；`*_export.json` 为冻结输出
（M13.3 资格流程导出的完整载荷）。复算使用固定 run_id、固定时间戳与 fixture
Provider 语料，逐字段与冻结 JSON 比对。
