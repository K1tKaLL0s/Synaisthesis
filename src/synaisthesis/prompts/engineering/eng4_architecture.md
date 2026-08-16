# ENG4 Architecture Baseline Prompt Asset

prompt_key: eng4_architecture
version: 1.0.0
stage_id: ENG4

## 目标

基于已批准的 Requirements Baseline 与 Trade Study 形成 ArchitectureBaseline：机器可读设计对象为权威，图示只是投影视图。每张图必须有文本源、渲染 SVG、稳定 component ID 与渲染回执。只能产生 candidate；重大架构必须由用户通过 `ENGINEERING_ARCHITECTURE_REVIEW` 批准。

## 必须覆盖

- 设计视图：系统上下文、容器/子系统、组件及责任、运行时序列、数据模型/生命周期/流、状态机/错误恢复/幂等/并发边界、接口与版本策略、部署拓扑/环境/运维边界、信任边界/威胁模型/安全控制、可观测性/审计/备份/恢复/退役
- 工件：InterfaceContractSet（带 Schema）、DataContractSet、StateAndFailureModel、ThreatModel、DeploymentAndOperationsDesign、ADR 集
- 每张图：diagram_id、标题、版本、input hash、图例、节点/边语义、节点→稳定 component ID 映射、源文件与 SVG 双 hash、渲染回执、断链检查
- 图示源语言：`node <id> "<label>"` 与 `edge <from> <to>`

## 禁止行为（forbidden behavior）

- 图片不得成为唯一事实来源
- 图节点不得缺少稳定 component ID
- 不得虚构接口 Schema、状态或安全控制
- 不得在用户批准前宣称架构已定稿
- 模型不得代替用户批准架构

## golden inputs（示例）

对"迹计算库"场景，应生成组件（CLI、计算内核、校验器）、接口合同、状态模型、威胁模型与一张系统上下文图（文本源 + SVG），全部绑定稳定 ID。
