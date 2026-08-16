# RQ2M Early Formalization Prompt Asset

prompt_key: early_formalization
version: 1.0.0
stage_id: RQ2M

## 目标

把已冻结的理论型 S1/S4 翻译为可审查的数学候选。Bundle 只能处于 candidate 状态；不得声称已证明、已验证或可被 Lean/Z3 执行。

## 必须覆盖的公式类型

- OBJECT_DOMAIN
- INPUT_OUTPUT_MAP
- STATE_TRANSITION
- ASSUMPTION
- INVARIANT
- CORE_CLAIM
- OBJECTIVE
- FAILURE_WITNESS
- THEORY_APPLICATION_MAP
- VERIFICATION_OBLIGATION

对象域、假设、至少一个核心主张、至少一个失败/证伪公式以及应用映射不得标记为不适用。

## 禁止行为（forbidden behavior）

- 不得用自然语言段落代替核心公式
- 不得写入 PROVED / VERIFIED / NOVEL 等越权状态
- 不得使用未在 notation_table 定义的符号
- 不得让核心主张缺少失败/证伪公式
- 不得改写 S1/S4 语义或伪造来源

## golden inputs（示例）

对“迹循环性质”的冻结设计，应生成 object domain、assumption、core claim、failure witness、application map 五类必选公式，符号闭合，依赖无环，hash 可复算。
