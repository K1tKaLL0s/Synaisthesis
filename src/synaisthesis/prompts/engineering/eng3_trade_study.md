# ENG3 Trade Study Prompt Asset

prompt_key: eng3_trade_study
version: 1.0.0
stage_id: ENG3

## 目标

针对已冻结 Requirements Baseline 进行工程深检索并形成 OptionTradeStudy：至少一个基线方案和一个有意义的替代方案；权重由 Baseline 派生并展示，不得事后修改。只能产生 candidate；不授权代码、采购、部署或生产变更。

## 必须覆盖

- 深检索来源：官方仓库（release/architecture/test/issue 证据）、官方文档/参考实现、标准/政府/行业指南、论文/技术报告/基准、包注册表/许可证/供应链
- 每个方案：Requirements 覆盖、关键组件/依赖/接口/数据路径、性能/可靠性/安全/可维护性/可扩展性预测、复杂度/人员/时间/成本/基础设施、许可证/供应链/锁定/弃用风险、原型/风险刺探、未知项与证据置信度
- 固定公式 weighted_score = Σ w_j × normalized_score，Σ w_j = 1
- Critical requirement 未覆盖的方案直接淘汰，不参与加权补偿

## 禁止行为（forbidden behavior）

- 不得为让推荐方案胜出而事后改权重
- 星标、下载量、宣传文案或单一 benchmark 不得单独构成成熟度证据
- 不得虚构候选方案或排除记录
- 不得把被淘汰方案列入推荐
- 模型不得代替用户选择

## golden inputs（示例）

对"迹计算库"场景，应生成两个候选（如纯 Python 实现 vs C 扩展绑定），记录各自对 Critical requirements 的覆盖，淘汰未覆盖者，并用冻结权重计算加权分。
