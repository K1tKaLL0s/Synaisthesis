# TP2 Theory Manuscript Audit Prompt Asset

prompt_key: theory_manuscript_audit
version: 1.0.0
stage_id: TP2

## 目标

由未参与初稿生成的 THEORY_MANUSCRIPT_AUDITOR 独立审计理论母稿，输出 structured findings；Critical/Major 必须一轮定向返工后重审。

## 必须检查

- 题目、摘要、引言、定理与结论忠于冻结 ResearchSpec
- object domain、quantifier、assumption、conclusion 与 statement hash 一致
- 定理/引理/引用的 proof/evidence 状态没有越权（INCOMPLETE 不得标 THEOREM）
- Proof Dependency Graph 闭合且外部定理适用条件完整
- 反例、失败尝试、限制和 Scope 没有被隐藏
- citation 可解析且没有捏造
- TeX/PDF 在锁定环境真实编译（真实编译回执）
- 作者责任字段没有被模型虚构

## 禁止行为（forbidden behavior）

- 审计人不得审计自己参与生成的稿件
- 不得把 Critical/Major finding 降级
- 不得修改稿件或主张
- 无回执的 PASS 不得记录

## golden inputs（示例）

对"迹计算库"理论母稿：应检查 statement hash 一致性、THEOREM 的 Lean 回执、依赖图闭合、未解决义务已列出、citation 完整；无 Critical/Major 时审计通过。
