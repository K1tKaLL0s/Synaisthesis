# S3 — 相关研究映射 Prompt Asset

prompt_key: s3_prior_work_map
version: 1.0.0
stage_id: S3

## 目标

把 S2 机制草图映射到可追溯的相关研究。必须同时生成学术查询种子与工程查询种子；不得把“未发现”说成“不存在”，不得输出“绝对原创”。

## 输出 Schema（PriorWorkMap）

- search_queries：查询种子，稳定键 `academic` 与 `engineering` 各为查询字符串列表
- sources：来源列表
- nearest_theories：最近理论
- same_object_different_method：同对象不同方法
- same_method_different_object：同方法不同对象
- conflicts：冲突
- terminology_candidates：术语候选
- retrieval_scope：检索范围
- unsearched_areas：未检索区域
- literature_hits：文献命中
- mature_engineering_projects：成熟工程项目
- engineering_maturity_evidence：工程成熟度证据
- function_application_neighbors：功能/应用近邻
- metadata_verified：文献元数据是否经外部源验证（必须为 true）

## 必须字段（required fields）

以上全部 14 个字段缺一不可；`search_queries.academic` 与 `search_queries.engineering` 均不得为空。

## PASS 条件

- 查询和来源可追溯；
- 区分“未发现”与“不存在”；
- 至少给出最近邻类别；
- 文献元数据被外部源验证。

## 禁止行为（forbidden behavior）

- 不得把“未找到”说成“不存在”；
- 不得输出“绝对原创”；
- 不得只生成学术查询或只生成工程查询；
- 不得在 metadata_verified=false 时声称 PASS；
- 不得虚构来源或成熟度证据。

## golden inputs（示例）

search_queries.academic: ["trace cyclic property matrix proof"]
search_queries.engineering: ["numpy trace invariance numerical linear algebra"]
sources: ["arXiv:math/0000000", "GitHub:numpy/numpy"]
nearest_theories: ["矩阵迹理论"]
same_object_different_method: ["用指标缩并研究方阵迹"]
same_method_different_object: ["用循环性质研究其他矩阵函数"]
conflicts: ["某教材称迹交换仅对正整数幂成立"]
terminology_candidates: ["cyclic trace property", "trace invariance"]
retrieval_scope: "有限维实/复方阵的迹与循环性质"
unsearched_areas: ["专利库"]
literature_hits: ["迹的循环性质标准教材条目"]
mature_engineering_projects: ["NumPy"]
engineering_maturity_evidence: ["NumPy 发布与维护记录"]
function_application_neighbors: ["np.trace"]
metadata_verified: true
