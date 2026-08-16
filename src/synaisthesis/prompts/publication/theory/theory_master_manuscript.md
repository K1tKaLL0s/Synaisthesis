# TP1 Theory Master Manuscript Prompt Asset

prompt_key: theory_master_manuscript
version: 1.0.0
stage_id: TP1

## 目标

基于已冻结的 Theory Revision 与 Evidence Baseline 生成 TheoryMasterManuscript：定义/引理/定理/证明结构、证明依赖图、theorem/claim→statement/proof/evidence/citation 追踪与限制。只能产生 candidate；不授权投稿。

## 必须覆盖

- title、abstract、MSC、keywords；introduction（问题/背景/意义/贡献边界）
- related work 与最近邻差异；notation and preliminaries
- definitions and assumptions；main results；proof architecture 与依赖顺序
- complete proofs 或未完成部分的明确状态
- examples、counterexamples、boundary cases；formal/computational verification methods 与 Scope
- limitations、threats to correctness、unresolved obligations
- proof/code/data/materials availability；references
- 作者字段未提供必须写 `NEEDS_AUTHOR_INPUT`

每个 claim：manuscript_claim_id、kind（DEFINITION/ASSUMPTION/LEMMA/PROPOSITION/THEOREM/COROLLARY/CONJECTURE/COUNTEREXAMPLE/APPLICATION_CLAIM）、display_statement、normalized_statement_hash、object_domain、quantifiers、assumptions、conclusion、proof_status、proof_artifact_ids、tool_receipt_ids、semantic_status、citation_refs、limitations、manuscript_locations。

## 禁止行为（forbidden behavior）

- THEOREM/LEMMA/PROPOSITION/COROLLARY 证明未完成时必须降级为 CONJECTURE/OPEN_PROBLEM，不得只在脚注弱化
- 不得伪造证明、引用或隐藏未解决义务
- 不得改变冻结 statement/量词/假设/结论
- 不得虚构作者责任字段

## golden inputs（示例）

对"迹计算库"理论案例：THEOREM tr(AB)=tr(BA)（proof_status=COMPLETE、tool_receipt=lean）、引理（依赖图边）、反例（非方阵）、限制（浮点实现未覆盖），全部绑定 citation 与 statement hash。
