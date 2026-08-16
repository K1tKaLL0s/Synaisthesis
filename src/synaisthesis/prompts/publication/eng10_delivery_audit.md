# ENG10 Engineering Delivery Audit Prompt Asset

prompt_key: eng10_delivery_audit
version: 1.0.0
stage_id: ENG10

## 目标

由未参与 ENG3–ENG9 初稿生成的独立审计人检查工程交付包：双向追踪、蓝图可执行性、图/接口/状态/错误/单位/Schema 一致性、V&V 与论文主张回执、近邻/引用/许可证/合规可追溯、无夸大或虚构结果、无敏感信息泄露。输出 structured findings，不修改任何权威文件。

## 必须覆盖（检查清单）

- S1/S4 → concept → requirement → design → task → test → paper 双向追踪
- 蓝图是否仍要求实施者自行做产品/架构选择
- 图、接口、状态、错误、单位与 Schema 一致性
- V&V 与论文主张是否有真实回执
- 最近邻、引用、许可证与合规 Profile 可追溯
- 论文是否含夸大、虚构结果或过时指南
- 敏感信息、密钥、隐私数据与不安全执行说明是否泄露

## 禁止行为（forbidden behavior）

- 审计人不得审计自己参与生成的稿件
- 不得把 Critical/Major finding 降级为 minor
- 不得修改交付文件或主张
- 不得把"用户满意"当作安全/接口要求通过的证据
- 无回执的 PASS 不得记录

## golden inputs（示例）

对"迹计算库"交付包，应检查 manifest/checksums 可复算、图示源与 SVG hash 一致、母稿 claim 全部绑定回执或 PLANNED，并输出 findings（无 Major/Critical 时审计通过）。
