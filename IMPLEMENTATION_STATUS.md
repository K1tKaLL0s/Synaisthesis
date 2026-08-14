# Synaisthesis Implementation Status

## Current milestone
`M1`（Stage 1 进行中）

## Current task
`M1.3.STORAGE.EVENT_ARTIFACT_COMPLETE`

## Last verified commit
`0e0605a`（M1.3 代码尚未提交）

## Blueprint baseline
正式文档基线为 `V2.4`（2026-08-14）：用户已整体采纳 V2.3 的 RQ2F 理论/工程可行性分流、强制工程路线决定、工程概念/新颖性审验及 ENG0–ENG10 设计；V2.4 进一步加入纯理论论文固定交付、双路线母稿独立审计、母稿交付后的正式稿决策，以及理论四刊、工程四刊和双路线 arXiv Profile。该基线只表示文档语义，不表示相关产品功能已实现。V2.4 已追加一处补丁：定义 `evidence.status` 枚举值 `ACTIVE`/`REVOKED`（`revoked_at` 为权威标记），并重建汇编版与 manifest。

## Active work unit
- Stable Task ID: `M1.3.STORAGE.EVENT_ARTIFACT`
- Milestone: `M1`（Stage 1：领域模型、Event Store、Artifact Store）
- 交付：SQLAlchemy 2 + Alembic 持久化底座：init_database、append_domain_event（稳定顺序）、save_artifact（内容寻址）、verify_artifact_hash（缺失/篡改可检测）、首个 migration（可 upgrade/downgrade）。
- 新增生产依赖：sqlalchemy>=2.0,<3.0、alembic>=1.13,<2.0（已单独获准）。

## Environment
- Project root: `E:\Synaisthesis`
- Primary engineering client: OpenCode or official DeepSeek DSH
- Primary engineering model: DeepSeek V4 Pro
- Python: 3.14.4（WSL2）；兼容目标 >=3.11，已在 3.11.15 实测通过
- uv: 0.12.3
- Git: 2.53.0
- Docker: 29.7.2
- Z3: 5.0.0（M0 未使用，仅记录）
- Lean: 4.32.2（Lake 5.0.0，M0 未使用，仅记录）
- Node.js: WSL 全局 `NOT_FOUND`（项目仍使用 basedpyright）；DSH 使用 E 盘隔离 Linux Node.js 24.19.0
- venv: `/home/chaos/.venvs/synaisthesis`（WSL ext4）；仓库内 `.venv` 为符号链接
- SQLAlchemy: 2.0.52（M1.3 新增生产依赖）；Alembic: 1.19.1（M1.3 新增生产依赖）

## Implemented
- 工程骨架：`pyproject.toml`（uv、requires-python >=3.11）、`src/synaisthesis` 布局、`configs/`、`tests/unit/`、`.github/workflows/ci-core.yml`（CI matrix 3.11 / 3.14）
- `get_version`（version.py）、`load_settings`（config/loaders.py）、`validate_settings`（config/validation.py，Pydantic v2 严格校验，拒绝未知键/越界端口/非法枚举/类型错误）
- CLI `synaisthesis --version`（interfaces/cli/main.py，Typer）
- 项目文件：README、LICENSE（Apache-2.0）、SECURITY、CONTRIBUTING、.gitignore
- `docs/adr/0001-python-compatibility-311-plus.md`
- AGENTS.md：新增 N 盘 `N:\CodexData` 记录与不得修改 Codex 理论仓库条款
- 蓝图文档：`03A` 已升级为路线化可行性/形式化/新颖性合同；`03B` 定义工程转化与机械蓝图；新增 `03C_THEORY_PUBLICATION_AND_DUAL_TRACK_VENUE_PROFILES.md`，定义理论论文固定交付、双路线母稿审计/用户决策、八种期刊 Profile 与两种 arXiv 预印本 Profile，并同步数据、API/CLI/MCP、Gate、实施、测试、配置、路线、参考与机械 Task（不代表功能已实现）
- M1.1 领域基元：`domain/enums.py`（StageId/ProgressKind/StageGateStatus/ProjectLifecycleStatus/ProvenanceType/EvidenceType/EvidenceStrength/IndependenceStatus，`StrictStrEnum` 严格拒绝未知值）、`domain/errors.py`（DomainError/ConflictError/InvalidEnumValueError，07 §19 统一错误对象）、`domain/event.py`（DomainEvent，确定性 SHA-256 内容 hash + 稳定 JSON 序列化）、`domain/policies.py`（IdempotencyContext + check_expected_version，expected_version 不匹配 → CONFLICT）
- M1.2 领域聚合：`domain/project.py`（Project，frozen + change_lifecycle）、`domain/research_spec.py`（ResearchSpec，确认后不可原地覆盖、改动必须 new_version）、`domain/stage.py`（StageRun，complete 一次性）、`domain/revision.py`（Revision，不可变链 + immutable_hash + create_child）、`domain/evidence.py`（Evidence，revoke 保留历史）；`domain/event.py` 公开 `canonicalize/canonical_json/sha256_hex` 供聚合复用
- 蓝图补丁（evidence.status 缺口）：06 §1 定义 `EvidenceStatus = ACTIVE | REVOKED`，同步 `domain/enums.py::EvidenceStatus` 与 `domain/evidence.py::Evidence.status`（派生属性，`revoked_at` 为权威标记）
- M1.3 持久化底座：`storage/database.py`（Base + init_database，不静默建表）、`storage/hashing.py`（sha256_bytes/sha256_file/verify_artifact_hash）、`storage/artifact_store.py`（ArtifactRecord + save_artifact 内容寻址）、`storage/repositories/event_repository.py`（DomainEventRecord + append_domain_event）、首个 Alembic migration（`storage/migrations/`，可 upgrade/downgrade）

## Verified
- `uv run pytest`：11 passed（Python 3.14.4 与 3.11.15 均通过）
- `uv run ruff check .`：通过；`uv run ruff format --check .`：通过
- `uv run basedpyright`：0 errors, 0 warnings
- `uv run synaisthesis --version`：输出 `0.1.0.dev0`
- 依赖零 LLM（pydantic / pydantic-settings / pyyaml / typer）
- DOC-V2.2 蓝图完整性：manifest 26 个记录全部 size/SHA-256 匹配；24 个权威分册与汇编版逐字重建一致；24 个 SOURCE marker 顺序匹配；分册无重复编号 H2
- DOC-V2.3-draft 蓝图完整性：manifest 27 个记录全部 size/SHA-256 匹配；25 个权威分册与汇编版逐字重建一致；25 个 SOURCE marker 顺序匹配；代码围栏平衡；分册无重复 H2；本地 Markdown 链接均可解析
- DOC-V2.4 蓝图完整性：manifest 28 个记录全部 size/SHA-256 匹配；26 个权威分册与汇编版逐字重建一致；26 个 SOURCE marker 顺序匹配；代码围栏平衡；分册无重复 H2；本地 Markdown 链接均可解析；活动状态文件无 V2.3 待确认残留
- 工程开发 Profile：允许 OpenCode 或 DeepSeek 官方 DSH 作为工程客户端；两者共享 `AGENTS.md`、WorkUnitContract、Human Gate 与验证规则
- DeepSeek Harness：E 盘隔离安装 `@deepseek-ai/dsh@0.1.0-rc.6`；Node 24.19.0 官方 SHA-256 PASS；530 个包 registry signature PASS、63 个 attestation PASS；`npm audit --omit=dev` 为 0 vulnerabilities
- DSH 桌面壳目标命令：systemd user service active、官方默认 `http://127.0.0.1:3080` 返回 HTTP 200（12109 bytes）、Chrome 顶层窗口标题为 `DeepSeek Harness`、单实例 keeper 持锁；桌面快捷方式改为直接调用 `wsl.exe` 后连续 30 秒持久性检查 PASS；未录入或读取 API key，未执行真实模型请求
- `git diff --check`：通过（仅有仓库既有的 LF→CRLF 提示，无 whitespace error）
- M1.1：`uv run --no-sync pytest tests/unit/domain/test_primitives.py` 36 passed；全套 `uv run --no-sync pytest` 47 passed；`uv run --no-sync ruff check .` 通过；`uv run --no-sync ruff format --check .` 通过；`uv run --no-sync basedpyright` 0 errors, 0 warnings（只读 venv 沙箱使用 `UV_CACHE_DIR` + `--no-sync`，见 CONTRIBUTING.md）
- M1.2：`uv run --no-sync pytest tests/unit/domain/test_aggregates.py` 20 passed；全套 `uv run --no-sync pytest` 67 passed；`uv run --no-sync ruff check .` 通过；`uv run --no-sync ruff format --check .` 通过；`uv run --no-sync basedpyright` 0 errors, 0 warnings
- 蓝图补丁（evidence.status）：重建汇编版后 manifest 全量完整性校验 `integrity ok: True`；代码侧全套 pytest 68 passed、ruff/basedpyright 通过
- M1.3：`pytest tests/integration/storage/test_event_artifact_store.py` 5 passed；全套 `pytest` 73 passed；`ruff check .` 通过；`ruff format --check .` 通过（72 files）；`basedpyright` 0 errors, 0 warnings（沙箱只读 venv 无法安装新依赖，改用 `workspace/.venv-m13` 独立 venv 运行，basedpyright 以 `--pythonpath` 指向该 venv）

## Known failures
- 当前无安装阻断。原先以隐藏 PowerShell 为目标的 `C:\Users\27499\Desktop\DeepSeek Harness.lnk` 会被外部环境自动移除；本轮改为直接调用 `C:\Windows\System32\wsl.exe` 与现有 WSL runner 后，快捷方式字段回读一致且连续 30 秒存在。Computer Use 仍因 Codex 本地目录 `EPERM` 不可用，因此未执行真实桌面双击。

## Pending Human Gates
- 无（「M0 人工确认」已于本轮由用户确认通过）。

## Next allowed task
- 文档方面：V2.4 已冻结；后续只有新需求或实现中发现 `BLUEPRINT_GAP/CONFLICT` 时再变更。
- 代码方面：`M1.4.PROJECT.VERTICAL_SLICE`（前置 M1.3 已 PASS）；开始前按 AGENTS.md 和文档 19 建立完整 WorkUnitContract。

## Notes
- 原计划 Pyright（npm 版）在无 Node 的 WSL 环境中安装失败且极慢，按蓝图「Pyright 或 mypy」改用 basedpyright（Pyright 兼容实现）；检查命令为 `uv run basedpyright`。
- drvfs（`/mnt/e`）上 venv 反复损坏且性能差，venv 实际建在 WSL ext4（`~/.venvs/synaisthesis`），仓库 `.venv` 为符号链接；`uv run` 已验证可用。
- 仅记录真实执行结果；未执行的内容（如 Lean/Z3 调用）不记录为已验证。
- 本沙箱 venv 只读，`uv run` 需 `--no-sync` 并把 `UV_CACHE_DIR` 指向可写路径（`/tmp`）；该命令形式已由 CONTRIBUTING.md 与提交 `f2640d0` 记录。
- M1.3 因只读 venv 无法新增 sqlalchemy/alembic，故在 `workspace/.venv-m13`（gitignored）另建独立 venv 运行集成测试与检查；`/tmp` 跨命令会被清空，venv 必须落在 workspace 内才持久。
- DOC-V2.4 只改文档与生成型蓝图资产，未修改 Python、运行配置或 CI，因此未重复运行代码测试、类型检查和构建；上面的 M0 代码验证记录保持历史事实，不视为本轮重跑。
- DSH 位于 `/mnt/e` drvfs；依赖安装约 13 分钟，Web profile 每次冷启动实测约 2 分 49 秒。启动器使用 240 秒有界健康等待；若后续体验不可接受，应另建迁移到 WSL ext4/VHDX 的独立 WorkUnit，不得静默移动到 C 盘或 N 盘。
