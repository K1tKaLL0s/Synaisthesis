# S8 Pre-Freeze Readiness Attack Prompt Asset

prompt_key: s8_prefreeze_attack
version: 1.0.0
stage_id: S8

## 目标

在冻结前执行一至两轮 readiness attack（一次内部攻击 + 一次独立外部攻击），输出 PreFreezeAttackReport。绝不启动正式十轮 Council。

## 必须覆盖

- attack_rounds：只允许 1 或 2
- internal_attacks / external_attacks：内部与独立外部攻击记录
- obvious_counterexamples / boundary_failures / definition_holes / quantifier_risks
- tool_feasibility / claim_atomicity / recommended_split
- freeze_readiness：Critical 问题全部已解决或明确阻断时才能 true
- critical_issues_resolved / critical_issues_blocked：二选一必须为真
- rollback_targets：定义问题→S1、研究范围→S4、理论问题→S6、形式结构→S7

## 禁止行为（forbidden behavior）

- 不得启动十轮 Council
- Critical 未解决且未阻断时不得 freeze_readiness=true
- 不得把外部攻击与内部攻击合并为一次
- 不得省略反例或边界失败

## golden inputs（示例）

对"迹计算库"场景，应给出 2 轮攻击：内部攻击发现浮点边界失败，独立外部攻击发现非方阵量词风险；Critical 已解决或明确阻断后才置 freeze_readiness。
