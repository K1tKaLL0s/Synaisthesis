# Synaisthesis Implementation Status

## Current milestone
`M0`

## Current task
`M0_COMPLETE_PENDING_HUMAN_REVIEW`

## Last verified commit
`NONE`（M0 代码提交待进行）

## Blueprint baseline
正式文档基线为 `V2.4`（2026-08-14）：用户已整体采纳 V2.3 的 RQ2F 理论/工程可行性分流、强制工程路线决定、工程概念/新颖性审验及 ENG0–ENG10 设计；V2.4 进一步加入纯理论论文固定交付、双路线母稿独立审计、母稿交付后的正式稿决策，以及理论四刊、工程四刊和双路线 arXiv Profile。该基线只表示文档语义，不表示相关产品功能已实现。

## Active work unit
- Stable Task ID: `M0_COMPLETE_PENDING_HUMAN_REVIEW`
- Document Task: `DOC-V2.4_DUAL_TRACK_PUBLICATION_BASELINE`
- 本轮只设计、同步和核验蓝图文档与生成型索引；没有进入任何代码 WorkUnit。
- External workstation task: `EXTERNAL.WORKSTATION.DSH.2026-08-14`；DSH 安装、服务和 Chrome app 壳已验证；桌面 `.lnk` 改为直接调用 `wsl.exe` 后持久性验证 PASS。

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

## Implemented
- 工程骨架：`pyproject.toml`（uv、requires-python >=3.11）、`src/synaisthesis` 布局、`configs/`、`tests/unit/`、`.github/workflows/ci-core.yml`（CI matrix 3.11 / 3.14）
- `get_version`（version.py）、`load_settings`（config/loaders.py）、`validate_settings`（config/validation.py，Pydantic v2 严格校验，拒绝未知键/越界端口/非法枚举/类型错误）
- CLI `synaisthesis --version`（interfaces/cli/main.py，Typer）
- 项目文件：README、LICENSE（Apache-2.0）、SECURITY、CONTRIBUTING、.gitignore
- `docs/adr/0001-python-compatibility-311-plus.md`
- AGENTS.md：新增 N 盘 `N:\CodexData` 记录与不得修改 Codex 理论仓库条款
- 蓝图文档：`03A` 已升级为路线化可行性/形式化/新颖性合同；`03B` 定义工程转化与机械蓝图；新增 `03C_THEORY_PUBLICATION_AND_DUAL_TRACK_VENUE_PROFILES.md`，定义理论论文固定交付、双路线母稿审计/用户决策、八种期刊 Profile 与两种 arXiv 预印本 Profile，并同步数据、API/CLI/MCP、Gate、实施、测试、配置、路线、参考与机械 Task（不代表功能已实现）

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

## Known failures
- 当前无安装阻断。原先以隐藏 PowerShell 为目标的 `C:\Users\27499\Desktop\DeepSeek Harness.lnk` 会被外部环境自动移除；本轮改为直接调用 `C:\Windows\System32\wsl.exe` 与现有 WSL runner 后，快捷方式字段回读一致且连续 30 秒存在。Computer Use 仍因 Codex 本地目录 `EPERM` 不可用，因此未执行真实桌面双击。

## Pending Human Gates
- M0 人工确认。

## Next allowed task
- 文档方面：V2.4 已冻结；后续只有新需求或实现中发现 `BLUEPRINT_GAP/CONFLICT` 时再变更。
- 代码方面：仍等待 M0 确认后进入 Stage 1；开始前必须按 AGENTS.md 和文档 19 建立完整 WorkUnitContract。

## Notes
- 原计划 Pyright（npm 版）在无 Node 的 WSL 环境中安装失败且极慢，按蓝图「Pyright 或 mypy」改用 basedpyright（Pyright 兼容实现）；检查命令为 `uv run basedpyright`。
- drvfs（`/mnt/e`）上 venv 反复损坏且性能差，venv 实际建在 WSL ext4（`~/.venvs/synaisthesis`），仓库 `.venv` 为符号链接；`uv run` 已验证可用。
- 仅记录真实执行结果；未执行的内容（如 Lean/Z3 调用）不记录为已验证。
- DOC-V2.4 只改文档与生成型蓝图资产，未修改 Python、运行配置或 CI，因此未重复运行代码测试、类型检查和构建；上面的 M0 代码验证记录保持历史事实，不视为本轮重跑。
- DSH 位于 `/mnt/e` drvfs；依赖安装约 13 分钟，Web profile 每次冷启动实测约 2 分 49 秒。启动器使用 240 秒有界健康等待；若后续体验不可接受，应另建迁移到 WSL ext4/VHDX 的独立 WorkUnit，不得静默移动到 C 盘或 N 盘。
