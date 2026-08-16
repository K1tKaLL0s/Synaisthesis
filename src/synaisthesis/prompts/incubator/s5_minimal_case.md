# S5 — 最小范例 Prompt Asset

prompt_key: s5_minimal_case
version: 1.0.0
stage_id: S5

## 目标

在 RQ4M 理论资格通过后，把核心主张压缩为最小可复现范例。DEMONSTRATED ≠ PROVED。

## 输出 Schema（MinimalCaseBundle）

- input
- control_or_baseline
- expected_output
- failure_condition
- reproduction_steps
- actually_executed
- execution_receipt_id
- toy_or_real
- limitations

## 禁止行为（forbidden behavior）

- 不得把未运行范例标为 EXECUTED
- actually_executed=true 必须提供 execution_receipt_id
- 不得声称 PROVED
- 不得绕过 RQ3M/RQ4M 前置

## golden inputs（示例）

input: A,B finite matrices；expected_output: tr(AB)=tr(BA)；actually_executed: false。
