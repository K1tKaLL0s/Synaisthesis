# ENG5 Mechanical Engineering Blueprint Prompt Asset

prompt_key: eng5_blueprint
version: 1.0.0
stage_id: ENG5

## 目标

基于已由用户批准的 ArchitectureBaseline，生成可机械执行的 MechanicalEngineeringBlueprint：足以让合格开发者与主流代码执行模型在不补产品决策的前提下逐项实施。只能产生 candidate；不授权代码、采购、部署或生产变更。

## 必须覆盖

- 规范项目树及每个目录责任
- 文件级新增/修改/禁止清单
- 模块、组件、服务、接口、Schema 与关键符号
- 依赖与版本锁定策略；配置、密钥引用、环境与 feature flag 策略
- 数据创建、迁移、回滚、备份与兼容策略
- 每个运行流程的状态、事件、错误码与恢复动作
- 性能、安全、隐私、可观测性与运维要求
- 构建、测试、部署、验证与回滚命令模板
- requirement→design→task→test 双向追踪（Critical 100%）
- 风险登记表、停止条件与升级条件
- 应生成但尚未生成的源码/配置/IaC/测试/文档清单

每个 `EngineeringWorkUnitContract` 必须包含 14 项：稳定 Task ID 与唯一目标、权威输入文档及精确章节、前置 Task/Gate/环境、allowed files/modules/symbols、forbidden files/actions、输入输出/接口/Schema/状态/事件、不变量、逐步修改动作、错误/边界/兼容/回滚、focused tests、full checks、每项验收标准、失败停止/升级条件、交付 diff/命令/回执格式。

## 禁止行为（forbidden behavior）

- 禁止"适当修改""完善相关""视情况"等模糊动作措辞
- 不得让实施者自行决定公开接口 Schema、数据边界或安全边界
- 不得把命名/格式等普通实现选择上抛为产品/架构决策
- 不得存在未决 Critical 需求或未绑定测试的 Critical requirement
- 未满足 Blueprint Completeness Gate 时不得宣称可执行
- 模型不得代替用户批准架构或产品决策

## golden inputs（示例）

对"迹计算库"场景，应生成项目树、模块符号表、CLI/计算内核接口 Schema、运行流程状态/错误/恢复、pytest 命令模板、R1→design-1→task-1→test-1 追踪与两个原子 WorkUnit（各含 14 项合同字段）。
