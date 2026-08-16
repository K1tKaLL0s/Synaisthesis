# ENG8 Engineering Master Manuscript Prompt Asset

prompt_key: eng8_master_manuscript
version: 1.0.0
stage_id: ENG8

## 目标

基于已冻结的 Requirements/Architecture/V&V 证据生成期刊中立 EngineeringMasterManuscript：每个实质主张分配 claim_id 并绑定来源 requirement、design element、证据回执、图/表与引用。只能产生 candidate；不授权投稿、公开或生产发布。

## 必须覆盖

- title、abstract、keywords、problem/stakeholders/statement of need
- related work 与最近学术/工程近邻
- requirements、ConOps 与设计目标；method、architecture、interfaces 与实现
- verification/validation/experiment methods
- results（只有真实证据时）；与基线的定量/定性比较
- threats to validity、limitations、failure modes；应用与扩展方向
- security/privacy/ethics/sustainability；data/code/materials availability
- reproducibility instructions；conclusion；references
- author contributions、AI-use disclosure、funding、conflicts、acknowledgements（未由用户提供必须写 `NEEDS_AUTHOR_INPUT`）

## 禁止行为（forbidden behavior）

- BLUEPRINT_ONLY 不得写已实现/优于基线/用户有效/生产可用，不得出现假造 benchmark
- 无证据主张不得使用完成时或确定性语言
- 不得生成虚构作者输入占位文本
- 不得把图纸/设计描述写成已验证结果
- 模型不得代替用户确认作者责任或利益冲突

## golden inputs（示例）

对"迹计算库"场景，BLUEPRINT_ONLY 证据等级下应生成 DESIGN_ARTICLE 母稿：设计目标、接口与蓝图描述齐全，结果章节仅 PLANNED claim，作者字段全部 NEEDS_AUTHOR_INPUT。
