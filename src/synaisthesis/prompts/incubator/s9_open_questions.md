# S9 Open Question Registry Prompt Asset

prompt_key: s9_open_questions
version: 1.0.0
stage_id: S9

## 目标

登记开放问题与猜想，形成 OpenQuestionRegistry。只登记不解决；来源标记不可改写。

## 必须覆盖

每条记录：
- question_id / statement
- origin：USER | AI_GENERATED | DERIVED | LITERATURE | TOOL_FAILURE
- why_open / known_failed_attempts / falsification_path / next_action
- dependency_claims / status

## 禁止行为（forbidden behavior）

- AI 生成问题必须保留 AI_GENERATED 标记，不得改写为 USER 或 DERIVED
- 不得在登记时静默修改猜想语义
- 不得省略已知失败尝试或证伪路径

## golden inputs（示例）

对"迹计算库"场景，应登记："浮点实现下 tr(AB)=tr(BA) 的误差界"（AI_GENERATED，失败尝试=逐项比较方案，证伪路径=构造病态矩阵）。
