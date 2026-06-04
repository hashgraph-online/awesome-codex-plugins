<div align="center">
  <img src="./assets/icon.png" alt="Team Skills Platform" width="128" height="128"/>
  <h1>Team Skills Platform</h1>
</div>

面向团队协作与平台治理的开源 Team Skills Platform，用于把单代理执行模式升级成“`Tech Lead` 编排 + 专业角色协作”的虚拟研发团队工作模型，并叠加 ECC 风格的 harness layer、specialist 命令与运行时增强能力。当前平台同时支持 `team mode` 与 `solo mode`，前者强调多人交接，后者强调单人闭环但保留同样的关键门禁。

> English: Team Skills Platform (TSP) is an open-source framework for role-based AI delivery workflows. It packages role prompts, shared skills, commands, rules, hooks, examples, and install tooling for Claude Code, Codex, and OpenCode. Custom extensions can be layered on top via the overlay mechanism; the public repository ships only public capabilities.

## Quick Start / 最小安装

适合第一次体验公开能力的最短路径：

```bash
node scripts/build-platform-artifacts.js
node scripts/install-apply.js --profile team --target claude
node scripts/install-apply.js --profile full --target codex
```

## Who It's For / 适合谁

- 想把 AI 编码从“单代理乱跑”升级成“角色分工 + 明确 handoff + 明确 gate”的团队
- 需要一套可安装、可验证、可迁移的 prompts、skills、commands、rules 与 hooks 底座
- 想在公开能力之上，叠加自定义 overlay 扩展的团队

## Community / 社区协作

- 贡献方式：见 [CONTRIBUTING.md](CONTRIBUTING.md)
- 行为准则：见 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- 安全报告：见 [SECURITY.md](SECURITY.md)
- 支持边界：见 [SUPPORT.md](SUPPORT.md)

## 平台目标

- 用角色边界替代单线流程技能，统一产品、架构、研发、测试、运维的协作方式。
- 在仓库内维护平台无关的 canonical 定义，并自动生成 Codex / Claude 需要的角色技能、agent prompt、命令面和插件清单。
- 提供可安装、可校验、可迁移的团队能力底座，而不是一次性的项目脚手架。
- 内置 React/Next 优先的前端工程规范与 UI/UX 治理能力，用统一规则承接页面、交互和体验质量。
- 内置 ECC 风格的 specialist agents、快捷 commands、rules packs、runtime hooks、contexts 与 examples，提升整体可用性。
- npm 安装包内置 `crates/oris-claude-bridge` 与多平台预构建二进制，安装时按用户操作系统自动选择 bridge，无需本机 Rust 工具链。
- **持续净化原则**：每次大版本升级，目标是尽可能移除当前版本引入的所有补丁程序与临时绕行方案——补丁是现实妥协，不是长期设计；每一轮演进都应让平台比上一版更干净。

## 框架说明

### 平台架构

TSP 采用 **角色 + 技能 + Agent + 规则 + Hooks + Workflow 引擎** 六层架构：

| 层 | 目录 | 职责 |
|---|---|---|
| 角色定义 | `roles/` | 8 个专业角色的 canonical YAML 定义（tech-lead 编排） |
| 技能层 | `skills/` | 195+ 平铺技能，覆盖调试、编排、学习、前端、后端、安全等 |
| Agent 层 | `agents/specialists/` | 27 个 specialist agents（规划、review、build-fix、语言专项） |
| 规则层 | `rules/` | common 规则 + 13 语言规则包（TS/Python/Go/Java/Kotlin/Rust/Swift/C++/C#/PHP/Perl + 中文） |
| Hooks 层 | `hooks/` + `scripts/hooks/` | 37 个运行时 hook（prompt guard、context monitor、memory persistence 等） |
| 命令面 | `commands/` | 80+ 命令（团队主链 8 个 + specialist + 工具链） |
| Workflow 引擎 | `workflows/` + `scripts/workflow-*.js` | YAML DAG 工作流，支持依赖解析、状态持久化、失败恢复 |

安装工具链公开主线支持 **3 个 code agent**：Claude Code、Codex、OpenCode。其他历史 target 保留为隐藏兼容路径，不再作为公开 onboarding 主线。

发布为 npm 包 `@colin4k1024/tsp`，内置 Rust bridge 预构建二进制，安装零依赖。

### 集成的开源框架与方法论

TSP 整合了多个社区开源框架的精华能力，而非从零构建：

| 框架 | 来源 | 集成的核心能力 |
|------|------|--------------|
| **ECC** (Everything Claude Code) | 社区 | 125+ specialist skills、27 specialist agents、language rules packs、runtime hooks、安装工具链 |
| **BMAD** | 方法来源（已吸收） | 单入口主链（`/team-help`）、Requirement Challenge、Design Review、Implementation Readiness、Story Slice、`artifact:persist` 落盘、Release→Closeout 收口 |
| **CodeGraph** | 社区（`colbymchenry/codegraph`） | 默认内置 MCP-backed 代码图谱能力（符号搜索、调用链、impact、focused context），以官方 standalone installer + target-scoped wrapper + Claude 自动初始化 hook 接入 |
| **Graphify** | 社区（`safishamsi/graphify`） | 可选知识图谱能力（brownfield 结构扫描、依赖路径分析、架构问答证据），以 runbook + 本地 skill 接入，不替换 workflow-engine |
| **GitNexus** | 社区（`abhigyanpatwari/GitNexus`） | 受控可选代码智能能力（MCP 查询、impact、detect_changes、多仓图谱证据），以 runbook + thin skill 接入，不内置依赖 |
| **Open Design** | 社区（`nexu-io/open-design`） | 受控可选设计工作台能力（本地优先原型、deck、dashboard、mobile flow、`DESIGN.md`、导出 artifact），以 runbook + thin skill 接入，不内置 daemon |
| **GSD** (Getting Shit Done) | 社区 | Quality Gates 分类法（4 类 gate）、wave-execution、session-continuity、discuss-phase、quick-execution、context-engineering、workflow-forensics |
| **gstack** | 社区 | brainstorming 苏格拉底式创意探索、cross-model-review 跨模型交叉审查、multi-perspective-review 多视角评审（CEO/Design/Eng/DevEx） |
| **Superpowers** | 社区 | session-continuity 会话暂停/恢复、subagent-driven-development 子 agent 驱动开发、git-worktree-isolation 任务隔离 |
| **Oris bridge runtime** | 项目内组件 | evolution-core 相关运行时资产、`oris-claude-bridge` Rust bridge |
| **rtk** (Rust Token Killer) | 社区 | CLI 代理透明命令重写，60-90% token 节约，100+ 命令支持（git/gh/cargo/npm/docker/kubectl/aws） |
| 社区贡献 | 多方 | UI/UX Pro Max 设计系统、vertical workflow examples、Santa Method 对抗验证、Ralph RFC Pipeline |

### 外部设计能力接入

TSP 当前支持把第三方设计能力作为外部扩展接入使用。设计工具负责高保真 artifact，TSP 负责团队协作、角色分工、handoff、quality gate 与发布收口。

[Open Design](https://github.com/nexu-io/open-design) 是当前已纳入安装面导航的受控可选设计工作台：它提供本地优先 web/daemon、coding-agent CLI 调度、31 个设计 skills、设计系统库、sandbox preview 与 HTML/PDF/PPTX/ZIP/MP4 等导出链路。TSP 侧落点是 [skills/open-design/SKILL.md](skills/open-design/SKILL.md) 与 [docs/runbooks/open-design-integration.md](docs/runbooks/open-design-integration.md)，并通过 `design-prototyping` module 进入 `team` / `full` profile。其中 `full` profile 会自动执行 [scripts/install-open-design.js](scripts/install-open-design.js)，把 Open Design clone/update 到 `~/.tsp/open-design`，并在 `corepack` / `pnpm` 可用时安装依赖；如果 GitHub 网络不可达，该步骤只警告并继续完成 TSP 核心安装。TSP 不 vendoring Open Design 源码、daemon、skills、design-systems 或 SQLite 数据。

[huashu-design](https://github.com/alchaincyf/huashu-design) 仍作为文档级协同能力保留：它偏向高保真设计产出，覆盖 HTML 原生交互原型、浏览器演讲幻灯片、时间轴动画、信息图与 5 维度设计评审。

推荐的组合方式是：让 TSP 管任务链路，让外部设计工具管最终视觉和动效交付。典型场景包括：

- `frontend-engineer` 先在 TSP 流程内收敛页面目标、状态边界和验收标准，再调用 Open Design 或 huashu-design 做高保真原型或动画样机。
- `tech-lead` / `qa-engineer` 在评审阶段把 HTML demo、deck、dashboard、mobile flow 或动画作为 UI 证据补充到 review / release 资料里。
- `product-manager` / `architect` 在方案讨论阶段借助设计方向顾问、设计评审与 deck 产出，加速多方案对比。

上游安装方式：

```bash
npx skills add alchaincyf/huashu-design
```

当前仓库对 huashu-design 的接入是文档级集成，而不是内置分发：

- TSP 不会把 huashu-design 自动打包进 `skills/`、install profile、npm 包或 overlay 清单。
- 你需要单独从上游安装和更新该 skill，再在 TSP 任务流里按需调用。
- 由于上游 README 明确写明企业/商用/工具链集成需先获得授权，本仓库目前只提供接入说明与致谢，不 vendoring 上游 `SKILL.md`、assets、scripts 或 references。

### 核心依赖

| 依赖 | 用途 |
|------|------|
| `sql.js` | Workflow 引擎 SQLite 状态存储 |
| `ajv` | JSON Schema 校验（workflow 定义、状态校验） |
| `js-yaml` | YAML 解析（workflow、manifest、role 定义） |
| `@iarna/toml` | TOML 配置解析 |
| `@inquirer/prompts` | 交互式 CLI 安装向导 |
| `vitepress` | 文档静态站点生成 |
| `eslint` + `markdownlint-cli` | 代码与文档质量门禁 |

## 目录结构

```text
.
├── .claude-plugin/            # Claude plugin 与 marketplace manifests
├── roles/                     # 唯一事实源：每个角色一个 role.yaml
├── skills/                    # 当前正式技能目录（统一平铺）
│   └── roles/                 # 生成产物：角色型 skills
├── agents/
│   ├── roles/                 # 生成产物：角色 agent prompt
│   └── specialists/           # ECC 风格 specialist agents
├── commands/                  # 团队命令面 + ECC 快捷命令
├── rules/                     # 团队工作规则 + common/language packs
├── hooks/                     # hooks 配置入口
├── contexts/                  # 动态上下文模板
├── examples/                  # 项目/用户配置样例
├── mcp-configs/               # MCP 服务器配置模板
├── templates/                 # 标准交付物模板 + 生成模板
├── tests/                     # skeleton 与目录回归校验
├── scripts/                   # JS 主导的 build / validate / install / runtime 工具
├── .codex-plugin/plugin.json  # Codex 插件入口
├── marketplace.json           # Claude marketplace config
├── .agents/plugins/marketplace.json
└── docs/                      # 平台使用与迁移说明
```

## 角色清单

| 角色 ID | 说明 |
|---------|------|
| `tech-lead` | 统一 intake、拆解、分派、冲突决策与最终收口 |
| `product-manager` | 需求澄清、PRD、用户故事、验收标准 |
| `project-manager` | 排期、依赖、风险、里程碑推进 |
| `architect` | 方案设计、接口契约、数据边界 |
| `frontend-engineer` | 前端实现与自测 |
| `backend-engineer` | 后端实现与自测 |
| `qa-engineer` | 测试计划、回归验证、放行建议 |
| `devops-engineer` | 发布、监控、回滚与运行保障 |

## 命令面

- 主链：`/team-help`、`/team-intake`、`/team-plan`、`/handoff`、`/team-execute`、`/team-review`、`/team-release`、`/team-closeout`
- Specialist：`/plan`、`/tdd`、`/code-review`、`/build-fix`、`/verify`、`/multi-frontend`、`/multi-backend`
- 快捷执行：`/quick`、`/pause`、`/resume`
- 进阶能力：`/pua`、`/model-route`、`/evolve`、`/learn`、`/agent-dev`

> 以上为核心命令，完整 80+ 命令列表见 `commands/` 目录。

`/team-help` 是新的单入口导航命令，用于根据当前阶段、已有 artifacts 和阻塞项推荐下一步，支持 brownfield 补齐建议与 story-sized execution 提示，优先减少“现在该跑哪个命令”的判断成本。

## ECC Harness Layer

- `agents/specialists/` 提供规划、review、build-fix、验证、文档和语言专项能力。
- `skills/` 当前承载 195+ 技能，覆盖六大类：
	- 调试与验证：browser-smoke-testing、pairwise-test-design、testcontainers-integration-testing、systematic-debugging、eval-harness 等
  - 高能动性与压力协议：pua、pua-p7、pua-p9、pua-pro、pua-loop、pua-yes、pua-mama
	- 编排与效率：parallel-execution、wave-execution、strategic-compact、cost-aware-llm-pipeline、subagent-driven-development
	- 学习与记忆：continuous-learning-v2、error-experience-library、evolution-core
	- 上下文工程：context-engineering、git-worktree-isolation、workflow-forensics、session-continuity
	- 设计与协作：brainstorming、discuss-phase、multi-perspective-review、cross-model-review、quick-execution、karpathy-guidelines
	- 语言与框架：springboot-patterns、django-patterns、golang-patterns、kotlin-patterns、rust-patterns、swiftui-patterns 等
- `karpathy-guidelines` 已默认进入 TSP 主流程的推荐行为层：`/team-help` 到 `/team-release` 会优先用它来暴露假设、收敛最小范围、限制改动边界并锁定成功标准，但它不是新的硬门禁。
- 公开 `skills/` 只承载通用能力；自定义扩展通过 custom overlay 叠加交付。
- GitLab 手动流水线、Langfuse 追踪、前端公司样式 profile、业务服务设计 toolkit 等配套能力改由 `docs/runbooks/`、`docs/toolkits/` 与 `scripts/` 承接。
- `rules/common/` 与语言规则目录为 specialists 提供统一判断标准。
- `hooks/`、`contexts/`、`examples/`、`mcp-configs/` 作为可扩展运行时入口；当前仓库已提供 session persistence、tool observation、cost tracking、context budget、instinct learning、context compaction 与 archive 相关脚本。

## 当前能力地图

### 公开命令

- 主链：`/team-help`、`/team-intake`、`/team-plan`、`/handoff`、`/team-execute`、`/team-review`、`/team-release`、`/team-closeout`
- specialist：`/plan`、`/tdd`、`/code-review`、`/build-fix`、`/verify`、`/multi-frontend`、`/multi-backend`
- 快捷执行：`/quick`、`/pause`、`/resume`
- 进阶能力：`/pua`、`/model-route`、`/evolve`、`/learn`、`/agent-dev`
- 平台体检：`/harness-audit`

### 运行时增强

- 会话持久化：`hooks/memory-persistence/`（会话摘要、待办与决策回存）
- 上下文管理：`hooks/strategic-compact/`（budget、compact、archive 与 trigger-based 重组）
- Prompt 防护：`hooks/harness-prompt-guard.js`
- 上下文监控：`hooks/harness-context-monitor.js`
- 持续学习：`skills/continuous-learning-v2/`（instinct 观察与模式提取）
- 成本感知：`skills/cost-aware-llm-pipeline/`（任务复杂度分级与模型路由）

完整矩阵见 [docs/runbooks/command-and-capability-matrix.md](docs/runbooks/command-and-capability-matrix.md) 和 [docs/runbooks/runtime-capabilities-overview.md](docs/runbooks/runtime-capabilities-overview.md)。

## 致谢 / Acknowledgements

TSP 的公开能力是在多个社区项目、技能仓库和工程方法论的基础上吸收、裁剪和重组出来的。以下仓库是当前根 README 主叙事里直接引用或明确协同的社区 GitHub：

| 仓库 | 在 TSP 中的关系 | 说明 |
|------|------|------|
| [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | 上游能力来源 | ECC harness layer、specialist agents、skills、runtime hooks 与安装工具链的重要参考来源 |
| [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) | 默认内置接入 | 为 brownfield 符号搜索、调用链、impact 和 focused context 提供本地 MCP-backed 代码图谱能力；TSP 通过 target-scoped wrapper 调用上游 standalone installer |
| [safishamsi/graphify](https://github.com/safishamsi/graphify) | 已吸收并本地化 | 为 brownfield 结构扫描、依赖路径分析与架构问答补充知识图谱能力 |
| [abhigyanpatwari/GitNexus](https://github.com/abhigyanpatwari/GitNexus) | 受控可选接入 | 为 brownfield MCP 查询、impact、detect_changes 和多仓代码图谱证据提供外部能力；因许可证与 Node 20 要求，不内置依赖 |
| [nexu-io/open-design](https://github.com/nexu-io/open-design) | 受控可选接入 | 为本地优先原型、deck、dashboard、mobile flow、`DESIGN.md` 与可导出视觉 artifact 提供外部设计工作台；不内置 daemon 或上游源码 |
| [rtk-ai/rtk](https://github.com/rtk-ai/rtk) | 已集成运行时能力 | CLI 透明命令重写与 token 优化能力来源 |
| [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) | 设计资产来源 | 为 `DESIGN.md` 品牌风格扩展提供参考品牌库 |
| [alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design) | 外部协同能力 | 提供高保真原型、HTML slides、动画与设计评审能力；当前仅做文档级接入说明，不内置分发 |

### 已吸收并落地的外部能力来源

以下上游项目已经通过 intake / runbook / skill 适配进入当前仓库的公开能力面；对应的采用边界、落地状态与本地化结果见 [docs/runbooks/external-capability-intake.md](docs/runbooks/external-capability-intake.md)。

| 分组 | 上游项目 | 当前在仓库中的落点 |
|------|------|------|
| 协作与行为技能 | [anthropics/skills](https://github.com/anthropics/skills), [Colin4k1024/andrej-karpathy-skills](https://github.com/Colin4k1024/andrej-karpathy-skills), [tanweai/pua](https://github.com/tanweai/pua), [obra/superpowers](https://github.com/obra/superpowers), [omkamal/pypict-claude-skill](https://github.com/omkamal/pypict-claude-skill), [testcontainers/testcontainers-java](https://github.com/testcontainers/testcontainers-java) | 浏览器 smoke、Karpathy 行为护栏、PUA 闭环、systematic debugging、pairwise-test-design、Testcontainers 集成测试 |
| PR、发布与 API 治理 | [qodo-ai/pr-agent](https://github.com/qodo-ai/pr-agent), [reviewdog/reviewdog](https://github.com/reviewdog/reviewdog), [reviewdog/action-eslint](https://github.com/reviewdog/action-eslint), [semantic-release/release-notes-generator](https://github.com/semantic-release/release-notes-generator), [semantic-release/semantic-release](https://github.com/semantic-release/semantic-release), [OpenAPITools/openapi-diff](https://github.com/OpenAPITools/openapi-diff), [stoplightio/spectral](https://github.com/stoplightio/spectral) | AI PR review、reviewdog 门禁、release notes 自动化、API breaking change / lint runbooks |
| 供应链、安全与 provenance | [actions/dependency-review-action](https://github.com/actions/dependency-review-action), [github/codeql-action](https://github.com/github/codeql-action), [aquasecurity/trivy-action](https://github.com/aquasecurity/trivy-action), [ossf/scorecard-action](https://github.com/ossf/scorecard-action), [anchore/sbom-action](https://github.com/anchore/sbom-action), [actions/attest-build-provenance](https://github.com/actions/attest-build-provenance), [sigstore/cosign-installer](https://github.com/sigstore/cosign-installer), [slsa-framework/slsa-verifier](https://github.com/slsa-framework/slsa-verifier), [sigstore/policy-controller](https://github.com/sigstore/policy-controller), [pact-foundation/pact-jvm](https://github.com/pact-foundation/pact-jvm), [slsa-framework/slsa-github-generator](https://github.com/slsa-framework/slsa-github-generator), [in-toto/attestation](https://github.com/in-toto/attestation), [in-toto/witness](https://github.com/in-toto/witness) | dependency review、CodeQL、Trivy、Scorecard、SBOM、attestation、签名、SLSA 验证、policy controller、contract testing 等发布前后治理 runbooks |
| 平台治理与基础设施门禁 | [renovatebot/renovate](https://github.com/renovatebot/renovate), [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks), [step-security/harden-runner](https://github.com/step-security/harden-runner), [rhysd/actionlint](https://github.com/rhysd/actionlint), [zizmorcore/zizmor](https://github.com/zizmorcore/zizmor), [open-policy-agent/conftest](https://github.com/open-policy-agent/conftest), [bridgecrewio/checkov](https://github.com/bridgecrewio/checkov), [yannh/kubeconform](https://github.com/yannh/kubeconform), [GitHubSecurityLab/actions-permissions](https://github.com/GitHubSecurityLab/actions-permissions), [kyverno/kyverno](https://github.com/kyverno/kyverno), [helm-unittest/helm-unittest](https://github.com/helm-unittest/helm-unittest) | 依赖升级、secret scanning、runner hardening、workflow lint / audit、policy-as-code、IaC 校验、Kubernetes schema / policy / chart 测试 |

### 技能与工具参考来源

以下项目主要出现在 `skills/`、参考资料或配套文档中，作为具体 skill、范式、工具链或示例来源，同样在此统一致谢：

| 分组 | 上游项目 | 当前用途 |
|------|------|------|
| UI/UX 与设计智能 | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | `ui-ux-promax` 的上游来源与方法库 |
| 测试与评估 | [google/googletest](https://github.com/google/googletest), [joaquinhuigomez/agent-eval](https://github.com/joaquinhuigomez/agent-eval) | C++ testing / GoogleTest 参考、agent evaluation 方法与任务评测参考 |
| 仓库分析与记忆 | [haibindev/repo-scan](https://github.com/haibindev/repo-scan), [sreedhargs89/context-keeper](https://github.com/sreedhargs89/context-keeper) | repo-scan、ck / context keeper 相关能力来源 |
| 多 agent 编排 | [humanplane](https://github.com/humanplane), [standardagents/dmux](https://github.com/standardagents/dmux) | RFC pipeline 分解思路、dmux 多 pane agent orchestration |
| Agent 开发框架与媒体参考 | [cloudwego/eino](https://github.com/cloudwego/eino), [cloudwego/eino-ext](https://github.com/cloudwego/eino-ext), [video-db/videodb-cookbook](https://github.com/video-db/videodb-cookbook) | ADK framework adapters 的 EINO 参考、VideoDB cookbook 示例 |

### 全仓 README 与文档 GitHub 引用补充清单

以下仓库同样出现在本仓库其他 `README*.md`、skill 文档或参考资料中，主要用于示例、教程、生态说明或补充参考。它们被纳入致谢归档，但不等于 TSP 的核心依赖或正式内置能力：

| 分组 | 仓库 | 主要出现位置 | 用途 |
|------|------|------|------|
| GoFrame 生态 | [gogf/gf](https://github.com/gogf/gf) | `skills/goframe-v2/examples/**/README*.MD` | GoFrame 框架本体及 contrib 模块引用 |
| GoFrame 示例 | [gogf/examples](https://github.com/gogf/examples) | `skills/goframe-v2/examples/**/README*.MD` | 示例仓库、教学与 clone 指引 |
| 依赖注入 | [samber/do](https://github.com/samber/do) | `skills/goframe-v2/examples/practices/injection/README*.MD` | DI 示例依赖 |
| JWT | [golang-jwt/jwt](https://github.com/golang-jwt/jwt) | `skills/goframe-v2/examples/httpserver/jwt/README*.MD` | JWT 认证示例依赖 |
| MongoDB | [mongodb/mongo-go-driver](https://github.com/mongodb/mongo-go-driver) | `skills/goframe-v2/examples/nosql/mongodb/README*.MD` | MongoDB 官方 Go 驱动参考 |
| Redis | [redis/go-redis](https://github.com/redis/go-redis) | `skills/goframe-v2/examples/nosql/redis/README*.MD` | Redis Go 客户端参考 |
| 服务治理 | [polarismesh/polaris](https://github.com/polarismesh/polaris) | `skills/goframe-v2/examples/config/polaris/README.MD` | Polaris 服务发现 / 配置生态参考 |

如果后续有新的 README 引用了社区 GitHub 仓库，默认也应同步补入本节，保持主入口文档的致谢口径完整可追溯。

## BMAD 方法论（当前口径）

当前仓库对 BMAD 的使用不是并行命令体系，而是吸收到 `/team-*` 主链中的执行方法。主链口径统一为：`/team-help -> challenge -> design -> readiness -> story-slice execute -> release -> closeout`。

1. 单入口：任何正式任务先从 `/team-help` 判定阶段与入口，避免跳步骤。
2. 先挑战再设计：`/team-plan` 内先完成 Requirement Challenge，再进入 Design Review 收口。
3. 先就绪再执行：`/team-execute` 必须消费 readiness proof，不满足就回退补证据。
4. 小切片交付：实现按 story-sized execution units 拆分，确保可独立验收与 handoff。
5. 证据落盘：主链产出统一通过 `artifact:persist` 写入 `docs/artifacts/`、`docs/adr/`、`docs/memory/`。
6. 发布后收口：必须经过 `/team-release -> /team-closeout`，完成观察窗口、残余风险和 backlog 回写。

文档治理也按同一方法约束：

- 入口权威层固定为 `README + AGENTS + runbooks(quick-start/onboarding/usage/troubleshooting)`。
- `docs/guides/*` 为薄入口，避免与 runbooks 双写漂移。
- 文档生命周期字段用于明确责任与新鲜度：`doc_tier`、`owner`、`updated`、`last_verified`、`source_of_truth`。
- 历史资料通过 `doc_tier: historical` 分层，避免与现行操作手册并列误用。

## 代码图谱能力（CodeGraph + Graphify + GitNexus）

- 定位：CodeGraph 作为默认内置 MCP-backed 代码图谱能力，Graphify 作为轻量结构证据层，GitNexus 作为受控可选深代码智能层；三者都不替代 workflow-engine 或 `/team-*` 主链。
- 入口：CodeGraph 先执行 `npm run codegraph:doctor`，Graphify 先执行 `npm run graphify:doctor`，GitNexus 先执行 `npm run gitnexus:doctor`；详细操作见 [codegraph-code-intelligence-usage.md](docs/runbooks/codegraph-code-intelligence-usage.md)、[graphify-knowledge-graph-usage.md](docs/runbooks/graphify-knowledge-graph-usage.md) 与 [gitnexus-code-intelligence-usage.md](docs/runbooks/gitnexus-code-intelligence-usage.md)。
- 分发：通过安装模块 `knowledge-graph` 与组件 `capability:knowledge-graph` 提供；默认纳入 `developer`、`team`、`research` 与 `full` profile，`core` 保持轻量。
- 治理边界：TSP 通过 `scripts/install-codegraph.js` 使用 CodeGraph 官方 standalone installer，不使用 `--target=auto`；Claude `SessionStart` 可在新项目静默执行 `codegraph init -i`，Codex/OpenCode 仅写入说明和诊断边界；Graphify/GitNexus 的自动 setup 类命令仍不在本仓库执行。

## 近期新增功能（v2.0.0 → v2.3.0）

### Karpathy Main-Flow Defaults & Release Hardening（v2.3.0）

- 新增本地 skill：`karpathy-guidelines`，并纳入 `workflow-quality` 安装基线。
- `/team-help`、`/team-intake`、`/team-plan`、`/team-execute`、`/team-review`、`/team-release` 现在会默认带上这层行为护栏，但它仍然不是新的阻塞 gate。
- `tech-lead`、`architect`、`frontend-engineer`、`backend-engineer`、`qa-engineer`、`devops-engineer` 角色默认推荐 `karpathy-guidelines`，而 `product-manager` 与 `project-manager` 保持不变。
- `post-install-bridge` 恢复 prebuilt hydrate fallback：当包内 bridge 缺失时，会先尝试回填当前平台二进制，再决定是否降级到 source mode。
- workflow CLI / readiness CLI 测试改为使用临时 HOME，避免被本机 `~/.claude/ecc/state.db` 或本地权限状态污染。
- `v2.3.0` 发布包已按本地 tarball 校验通过，包含 5 个平台的 `bin/prebuilt/` bridge 二进制。

### BMAD Source Adoption v2.2（v2.2.0）

- `/team-help` 改为优先消费构建产物 `scripts/lib/workflow-help-catalog.json`，并在 `--json` 输出中新增稳定字段：`routerSource`、`decisionEvidence`、`nextCommandCandidates`
- `/team-help` 把 `docs/memory/project-context.md` 提升为硬依赖输入：若缺少“当前活跃任务 / 当前阶段 / 关键依赖 / 活跃风险 / 下一步建议”任一段，会优先提示补齐 `artifact:persist write-project-context`
- `install-apply` 扩展为子命令：`plan|status|doctor|repair|uninstall`，其中 `repair/uninstall` 默认 dry-run，仅在 `--apply` 时真正落盘
- 安装流程新增 machine-readable `install-manifest`（SHA-256），`doctor` 会联合 `install-state + install-manifest` 检测声明与实际漂移
- 新增独立校验器：`scripts/validate-file-references.js`（跨文件引用）、`scripts/validate-skill-structure.js`（skill 结构）与 `scripts/validate-doc-freshness.js`（入口文档新鲜度）；并接入提交流程
- 入口文档层完成 BMAD 收口：`README + AGENTS + runbooks` 作为权威层，`docs/guides/*` 退化为薄入口
- 文档生命周期与历史分层落地：`doc_tier`、`last_verified`、`source_of_truth` 字段生效，历史文档显式标记 `historical`
- 历史遗留风险说明：`install-plan --profile full --target codex` 曾出现 `commands-core` selective-install 缺口；该缺口已在 2026-04-21 收口

BMAD Source Adoption v2.2 的回归与验收证据：

```bash
node scripts/build-platform-artifacts.js
node scripts/validate-library.js
node scripts/validate-doc-freshness.js
node tests/test_workflow_readiness.js
node tests/test_session_start.js
node tests/test_team_command_persistence.js
node tests/test_workflow_help_catalog.js
node tests/test_install_apply_lifecycle.js
node tests/test_install_manifest_hash.js
node tests/test_validation_scripts.js
node scripts/install-platform.js claude --claude-home /tmp/claude-smoke-bmad-v2
node scripts/install-plan.js --profile full --target codex
```

安装生命周期子命令速查：

```bash
node scripts/install-apply.js --profile team --target claude
node scripts/install-apply.js --profile team --target claude --overlay enterprise
node scripts/install-apply.js status --target claude
node scripts/install-apply.js doctor --target claude
node scripts/install-apply.js repair --target claude          # dry-run 默认
node scripts/install-apply.js repair --target claude --apply  # 实际修复
node scripts/install-apply.js uninstall --target claude        # dry-run 默认
node scripts/install-apply.js uninstall --target claude --apply
```

`enterprise overlay` 是公开仓保留的私有扩展入口；公开 npm 包不内置公司专属 skills、rules 或 profile。

### BMAD Absorption v2（v2.1.12）

- `/team-help` 继续收口为 `/team-*` 唯一公开入口，不新增 `/bmad-*` 并行命令面
- `team-plan` 与 `team-execute` 的 readiness 叙述进一步统一：先 challenge/design 收口，再消费 readiness proof 进入实现
- Claude legacy 安装链路已对齐当前 JS runtime，移除对旧 `.py` hooks 的公开契约
- active docs 完成 JS runtime / `artifact:persist` / `/team-help` 一致性收口
- 历史说明：Codex selective-install 的 `commands-core` manifest 缺口曾作为已知风险记录，后续已在 2026-04-21 修复

BMAD Absorption v2 的回归与验收证据：

```bash
node scripts/build-platform-artifacts.js
node scripts/validate-library.js
node scripts/validate-doc-freshness.js
node tests/test_workflow_readiness.js
node tests/test_session_start.js
node tests/test_team_command_persistence.js
node tests/test_install_platform_regression.js
node tests/test_active_surface_docs.js
node scripts/install-platform.js claude --claude-home /tmp/claude-smoke-bmad-v2
node scripts/install-plan.js --profile full --target codex
```

其中 Claude smoke 的验收点是：`settings.json` 不再出现 `.py` hooks，并且注册项明确指向 JS 入口（`session-start-bootstrap.js`、`governance-capture.js`、`session-end.js`、`cost-tracker.js`）。

### Tarball Gate & Install Hydration（v2.1.5）

- 发布工作流现在会在 `npm pack` 后校验最终 tgz，确保 `bin/prebuilt/` 的 5 个平台二进制都已进入包体。
- npm 发布时的 prebuilt source of truth 是 workflow/release staging 和最终 npm tarball，不是 Git 仓库里被长期跟踪的 `bin/prebuilt/` 目录。
- 本地 `npm pack` / `prepublishOnly` 当前只会校验 `bin/prebuilt/` 是否齐全；若工作区还没有这些二进制，需要先显式执行 `npm run prebuilt:sync`，再继续 pack/publish。
- `tsp-create` 安装时若未命中 bundled prebuilt，会先尝试同步当前平台 bridge，再回退到本地 Rust 构建。
- bridge provisioning 改为完整等待异步步骤结束，避免安装进程提前退出。

### Artifact Persistence & Prebuilt Sync（v2.1.4）

- 新增 `artifact:persist` CLI，统一创建 task、artifact、handoff、memory 和 session summary。
- `/team-intake` 到 `/team-closeout` 的命令文档已切换为通过 `artifact:persist` 落盘，而不是只描述手工步骤。
- 本地发布前若工作区缺少 prebuilt bridge，需要先显式执行 `npm run prebuilt:sync`，随后 `prepublishOnly` 只负责校验 `bin/prebuilt/`。

### BMAD Absorption MVP（v2.1.3）

- 新增 `/team-help` 作为主链单入口，用于根据当前阶段、brownfield 现状和现有 artifacts 推荐下一步。
- execute gate 现在显式要求 implementation-readiness、readiness proof、`docs/memory/project-context.md` 与 `Story Slice Plan`。
- 既有项目（brownfield）场景已纳入 `/team-plan`、`/update-codemaps`、`doc-architecture` 与 onboarding 文档。
- `readiness_status` 已改为按阶段取值：`execute -> handoff-ready`、`review -> ready-for-review`、`release -> release-ready`、`closeout -> accepted`。

### PUA 高压闭环（v2.1.2）

- 新增 `/pua` 命令，支持核心模式与 `p7 / p9 / p10 / pro / yes / mama / loop` 七种子模式
- 失败升级、成功重置、PreCompact 快照、Stop journal 已接入 hooks 链
- `SessionStart` 支持恢复 `~/.claude/pua/` 的 Always-On 状态
- 新增 `tests/test_pua_hooks.js`，覆盖 PUA 运行时行为回归

### Workflow 执行引擎

YAML 驱动的 DAG 工作流执行 CLI，内置于 npm 包：

- 命令：`workflow:list`、`workflow:run`、`workflow:readiness`、`workflow:runs`、`workflow:validate`
- SQLite 状态存储（基于 sql.js），支持 run 历史查询与失败恢复（`--resume-run-id`）
- 团队阶段 Readiness Gate：execute / review / release / closeout
- 模板注入（`--var key=value`）、bash 节点超时（`timeout_ms`）
- 安全防护：模板注入与路径穿越保护

### Pure-Host CLI

独立任务执行引擎，无需 AI 平台即可运行任务编排：

- YAML manifest 驱动、依赖图解析、重试处理
- Git 管理的执行状态（自动 commit / revert）
- 命令：`--manifest`、`--resume`、`--revert`、`--status`、`--report`

### Phase 1-3 — Superpowers / gstack / GSD 集成

- 新增 8 个技能：brainstorming、cross-model-review、discuss-phase、multi-perspective-review、quick-execution、session-continuity、subagent-driven-development、wave-execution
- Model Profiles：任务类型自动识别 + 模型路由（`manifests/model-profiles.json`）
- Quality Gates Taxonomy：4 类门禁统一语言（`rules/common/quality-gates-taxonomy.md`）
- 新增命令：`/pause`、`/resume`、`/quick`、`/pua`

### Phase 4 — 上下文工程与隔离

- `context-engineering`：4 层文档（PROJECT / REQUIREMENTS / ROADMAP / STATE）+ token 预算
- `git-worktree-isolation`：一任务一 worktree 隔离
- `workflow-forensics`：失败分析与时间线重建
- 安装目标扩展到 10 个（新增 Augment、Copilot/Windsurf）

### Bridge 打包（v2.1.1）

- npm 包内置 `oris-claude-bridge` 源码 + 5 平台预构建二进制（darwin-arm64、darwin-x64、linux-x64、linux-arm64、win32-x64）
- 安装时按 OS 自动选择，不可用时回退到本地 Rust 编译

### Python → JavaScript 迁移（v2.1.0）

- `scripts/` 目录 100% JavaScript 化，34 个 Python 脚本完成迁移/删除
- 新增 JS smoke tests 和统一测试 runner（`tests/run-all.js`）
- 全量测试 97 个用例通过

### VitePress 文档站

- 支持 `npm run docs:dev` / `docs:build` / `docs:preview`
- 配置位于 `docs/.vitepress/config.mts`

### rtk Token Optimization

- 集成 [rtk](https://github.com/rtk-ai/rtk)（Rust Token Killer）— CLI 代理透明重写 Bash 命令，降低 60-90% token 消耗
- 适配版 PreToolUse hook（`hooks/rtk-rewrite.sh`），兼容现有安全 hooks 链
- 注册为 `rtk-optimization` install module，加入 `full` 和 `team` profiles
- 前置依赖：`brew install rtk` + `jq`；未安装时 hook 静默跳过

## 前端能力包

- `frontend-engineering`：React/Next 优先的前端工程规范，覆盖组件结构、状态分层、语义化、可访问性与性能。
- `frontend-ui-ux-system`：系统化 UI/UX 设计知识库，覆盖产品类型、视觉方向、设计 token、交互、响应式与交付门禁。
- `rules/frontend-quality-gates.md`：把前端需求纳入 `/team-intake -> /team-plan -> /team-execute -> /team-review -> /team-release` 的强制门禁。- **DESIGN.md 设计执行层**：项目根目录内置默认 `DESIGN.md`（Notion 风格，含完整 color / typography / component / spacing / elevation token），前端 agent 读取后直接生成视觉一致的 UI。支持通过 `npx getdesign@latest add <brand>` 覆盖为 69+ 品牌风格（来源：[awesome-design-md](https://github.com/VoltAgent/awesome-design-md)）。
## 核心工作流

1. `product-manager` 产出 PRD 与验收标准。
2. `project-manager` 输出排期、依赖与风险。
3. `architect` 产出 ADR、接口/数据契约。
4. `frontend-engineer` / `backend-engineer` 实施并自测。
5. `qa-engineer` 回归验证并输出放行建议。
6. `devops-engineer` 执行发布准备与运行保障。
7. `tech-lead` 收口交付、仲裁冲突并决定是否放行。
8. 发布后由 `/team-closeout` 结束观察窗口、确认最终验收状态并回写 backlog。

## 常用命令

### 开源发布收尾

- 统一检查公开发布面：`npm run release:health`
- 若已执行 `npm pack --json | tee .npm-pack.json`，可带 tarball 校验一起跑：`npm run release:health -- --pack-json .npm-pack.json`
- 人工发布清单见 [docs/runbooks/open-source-release-checklist.md](docs/runbooks/open-source-release-checklist.md)

### Bridge 预构建制品

- `oris-claude-bridge` 的 crate 源码随 npm 包一起分发：`crates/oris-claude-bridge/`
- 预构建二进制位于 `bin/prebuilt/<platform>/`
- 发布工作流会先构建 `darwin-arm64`、`darwin-x64`、`linux-x64`、`linux-arm64`、`win32-x64` 的 bridge，再组装并发布 npm 包
- `bin/prebuilt/` 是打包时的 staging 目录，不作为 Git 仓库中的长期 source of truth 回写
- 可手工校验预构建目录：`npm run validate:prebuilt`
- 若本地 `npm pack` / `npm publish` 前工作区没有这些二进制，可先执行 `npm run prebuilt:sync` 从 GitHub 仓库回填 `bin/prebuilt/`
- `prepack` 与 `prepublishOnly` 当前只运行 `npm run validate:prebuilt`，不会自动同步 prebuilt
- 如需指定同步来源 ref，可用 `TSP_PREBUILT_REF=v2.1.5 npm run prebuilt:sync`；若主 ref 缺失，可再配合 `TSP_PREBUILT_FALLBACK_REF=main`

### Workflow CLI

- 列出当前可发现的 workflow：`npm run workflow:list`
- 按名称查看单个 workflow：`npm run workflow:list -- --name team-release-readiness`
- 用主链包装入口检查 readiness：`npm run workflow:readiness -- --phase release --task-dir docs/artifacts/foo --json`
- phase 支持别名：`exec` / `rev` / `rel` / `close`
- 校验当前 workflow 定义：`npm run workflow:validate -- --json`
- 运行默认 readiness gate workflow：`npm run workflow:run -- --name team-execute-readiness --var taskDir=tests/fixtures/workflow-valid --var targetPhase=execute --json`
- 运行 review readiness workflow：`npm run workflow:run -- --name team-review-readiness --var taskDir=/path/to/task-dir --var targetPhase=review --json`
- 运行 release readiness workflow：`npm run workflow:run -- --name team-release-readiness --var taskDir=/path/to/task-dir --var targetPhase=release --json`
- 运行 closeout readiness workflow：`npm run workflow:run -- --name team-closeout-readiness --var taskDir=/path/to/task-dir --var targetPhase=closeout --json`
- 查看最近 workflow runs：`npm run workflow:runs -- --limit 5 --json`
- 按 workflow 名称筛选 runs：`npm run workflow:runs -- --workflow-name team-release-readiness --limit 5 --json`
- 按状态筛选 runs：`npm run workflow:runs -- --status failed --limit 10 --json`
- 查看单个 run 详情：`npm run workflow:runs -- --run-id <run_id> --json`
- 预览 workflow 渲染结果而不执行：`npm run workflow:run -- --name team-release-readiness --preview --var taskDir=docs/artifacts/foo --var targetPhase=release --json`
- 对 bash 节点可声明超时：`timeout_ms: 300000`
- 用 readiness wrapper 代替手写 `--name` + `--var`：`npm run workflow:readiness -- --phase closeout --task-dir docs/artifacts/foo --preview --json`
- 批量检查多个任务目录：`npm run workflow:readiness -- --phase close --task-dir docs/artifacts/foo --task-dir docs/artifacts/bar --json`

`workflow:run` 同时支持：

- `--file <path>` 直接执行某个 workflow 文件
- `--resume-run-id <id>` 从失败 run 恢复
- `--var key=value` 给 workflow 节点模板注入运行时变量
- `--help` 查看完整参数说明

典型输出示例：

```text
$ npm run workflow:list
Workflows:
- team-execute-readiness [bundled] (2 nodes)
  Validate whether an artifact task directory is ready to enter the execute phase.
  Required vars: targetPhase, taskDir
- team-closeout-readiness [bundled] (2 nodes)
  Validate whether an artifact task directory is ready to enter the closeout phase.
  Required vars: targetPhase, taskDir
```

```text
$ npm run workflow:list -- --name team-release-readiness
Workflows:
- team-release-readiness [bundled] (2 nodes)
  Validate whether an artifact task directory is ready to enter the release phase.
  Required vars: targetPhase, taskDir
```

```text
$ npm run workflow:run -- --name team-release-readiness --json
Error: Workflow "team-release-readiness" is missing required variables: targetPhase, taskDir.
Provide them with --var key=value. Required vars for this workflow: targetPhase, taskDir.
Tip: run "npm run workflow:list" to inspect workflow requirements.
```

```text
$ npm run workflow:run -- --name team-release-readiness --preview --var taskDir=docs/artifacts/workflow-valid --var targetPhase=release
Workflow preview: team-release-readiness [bundled]
File: workflows/defaults/team-release-readiness.yaml
Required vars: targetPhase, taskDir
Input context: targetPhase=release, taskDir=docs/artifacts/workflow-valid
Nodes:
- validate-readiness [bash] dependsOn=none
- summarize-gate [prompt] dependsOn=validate-readiness
```

```text
$ npm run workflow:readiness -- --phase release --task-dir docs/artifacts/workflow-valid --preview
Workflow preview: team-release-readiness [bundled]
File: /.../workflows/defaults/team-release-readiness.yaml
Required vars: targetPhase, taskDir
Input context: targetPhase=release, taskDir=/.../docs/artifacts/workflow-valid
Nodes:
- validate-readiness [bash] dependsOn=none
- summarize-gate [prompt] dependsOn=validate-readiness
```

```text
$ npm run workflow:readiness -- --phase close --task-dir docs/artifacts/foo --task-dir docs/artifacts/bar
Workflow readiness batch:
- /.../docs/artifacts/foo [succeeded]
- /.../docs/artifacts/bar [succeeded]
```

```yaml
version: ecc.workflow.v1
name: timeout-example
description: Fail a bash node if it hangs too long.
nodes:
  - id: slow-bash
    bash: node -e "setTimeout(() => process.stdout.write('done'), 1000)"
    timeout_ms: 250
```

```text
$ npm run workflow:runs -- --limit 2
Workflow runs:
- cli-closeout-vars-1 team-closeout-readiness [succeeded] vars=targetPhase=closeout, taskDir=/tmp/workflow-closeout-valid started=2026-04-12T03:10:00.000Z source=bundled
- resume-run-2 resume-smoke [succeeded] vars=none started=2026-04-12T03:15:00.000Z resumedFrom=resume-run-1 source=file
```

```text
$ npm run workflow:runs -- --workflow-name resume-smoke --status succeeded --limit 5
Workflow runs:
- resume-run-2 resume-smoke [succeeded] vars=none resumedFrom=resume-run-1 source=file
```

```bash
# 生成角色 skills、agents、commands 与插件清单
node scripts/build-platform-artifacts.js

# 校验 canonical 定义、链接和生成产物是否一致
node scripts/validate-library.js
node scripts/validate-doc-freshness.js

# 安装到 Codex（可通过环境变量覆盖目标目录）
CODEX_HOME_DIR=/tmp/codex AGENTS_HOME_DIR=/tmp/agents ./scripts/install-codex.sh

# 安装到 Claude（可通过环境变量覆盖目标目录）
CLAUDE_HOME_DIR=/tmp/claude ./scripts/install-claude.sh

# 安装到 OpenCode（可通过环境变量覆盖目标目录）
OPENCODE_CONFIG_DIR=/tmp/opencode ./scripts/install-opencode.sh
```

## 使用 npx 安装（推荐）

无需克隆仓库，直接通过 npx 一键安装到目标平台。npm 包已包含所有平台（macOS/Linux/Windows）的预编译二进制文件，无需 Rust 工具链，无需 GitHub 访问：

- `tsp` 当前公开支持的 targets：`claude`（Claude Code）、`codex`、`opencode`；`claude-code` / `claudecode` 是 `claude` 的兼容别名
- 当前公开支持的 profiles：`core`、`developer`、`security`、`research`、`team`、`full`
- 自定义能力通过 overlay 机制扩展，不作为公开 `tsp` profile 暴露

公开支持深度按三类 code agent 收敛，当前建议按下面理解：

| Support level | Targets | `team` profile depth | Notes |
|------|---------|----------------------|-------|
| Recommended | `claude`, `codex`, `opencode` | 完整主链；仅跳过 target-intentional runtime gaps | 完整公开 workflow 链路、quick-start、安装验证与回归覆盖 |
| Hidden compatibility | `cursor`, `antigravity`, `gemini`, `codebuddy`, `copilot`, `windsurf`, `augment` | 不作为公开承诺 | 适配器可继续存在以兼容旧用户，但不进入公开 wizard / release matrix |

当前公开 quick-start / recipes / examples 聚焦 `claude`、`codex`、`opencode`。其他 targets 属于隐藏兼容，不应按 full parity 预期使用。

```bash
# 交互式向导（推荐首次使用）
npx @colin4k1024/tsp

# 非交互式，直接指定目标和 profile
npx @colin4k1024/tsp --target claude --profile full
npx @colin4k1024/tsp --target claude-code --profile team
npx @colin4k1024/tsp --target codex --profile full
npx @colin4k1024/tsp --target opencode --profile full

# 预览安装计划（不写入文件）
npx @colin4k1024/tsp --dry-run

# 从源码安装（开发者模式，需要 git）
npx @colin4k1024/tsp --from-source
```

安装时会自动完成：
- 根据操作系统选择对应的 prebuilt 二进制文件（darwin-arm64/x64, linux-arm64/x64, win32-x64）
- 部署 oris-claude-bridge 到目标目录
- 初始化 claude-mem 插件（仅 claude target）
- 配置 self-evolution hooks（仅 claude target）
- 安装后项目根目录内置默认 `DESIGN.md`（Notion 风格），可通过 `npx getdesign@latest add <brand>` 覆盖为其他品牌风格

## 5 分钟上手

如果你是第一次使用这个平台，建议按下面的顺序进入：

1. 运行 `node scripts/build-platform-artifacts.js` 生成最新产物。
2. 根据使用端执行对应的安装脚本：`./scripts/install-claude.sh`、`./scripts/install-codex.sh` 或 `./scripts/install-opencode.sh`。
3. 打开你的项目仓库，在对话中先跑一次 `/team-help` 判断入口，再按建议进入 `/team-intake`、`/team-plan`、`/team-execute`、`/team-review`、`/team-release` 或 `/team-closeout`。
4. specialist 命令只负责给出专项结论，最终决策回到 `/handoff` 或 `/team-*` 主链。

## 按你的情况选

- 第一次安装，准备在 Claude 中试跑：看 [docs/runbooks/claude-quick-start.md](docs/runbooks/claude-quick-start.md)
- 第一次安装，准备在 Codex 中试跑：看 [docs/runbooks/codex-quick-start.md](docs/runbooks/codex-quick-start.md)
- 想在 OpenCode 中上手：看 [docs/runbooks/opencode-quick-start.md](docs/runbooks/opencode-quick-start.md)
- 想按场景查 Claude 怎么用：看 [docs/runbooks/claude-usage-scenarios.md](docs/runbooks/claude-usage-scenarios.md)
- 想按场景查 Codex 怎么用：看 [docs/runbooks/codex-usage-scenarios.md](docs/runbooks/codex-usage-scenarios.md)
- 想直接复制高频提示与并行说法：看 [docs/runbooks/claude-conversation-prompt-recipes.md](docs/runbooks/claude-conversation-prompt-recipes.md) 和 [docs/runbooks/codex-parallel-prompt-recipes.md](docs/runbooks/codex-parallel-prompt-recipes.md)
- 想按角色直接复制常用说法：看 [docs/runbooks/role-prompt-recipes.md](docs/runbooks/role-prompt-recipes.md)
- 想创建自定义扩展 overlay：看 [docs/runbooks/custom-overlay.md](docs/runbooks/custom-overlay.md)
- 想按任务类型快速抄一页速查：看 [docs/runbooks/frontend-bugfix-one-page.md](docs/runbooks/frontend-bugfix-one-page.md)、[docs/runbooks/release-closure-one-page.md](docs/runbooks/release-closure-one-page.md)
- 想直接看成品对话示例：看 [docs/runbooks/claude-end-to-end-conversation-example.md](docs/runbooks/claude-end-to-end-conversation-example.md) 和 [docs/runbooks/codex-end-to-end-conversation-example.md](docs/runbooks/codex-end-to-end-conversation-example.md)
- 想按角色看成品交接对话：看 [docs/runbooks/qa-review-conversation-example.md](docs/runbooks/qa-review-conversation-example.md)、[docs/runbooks/devops-release-conversation-example.md](docs/runbooks/devops-release-conversation-example.md)、[docs/runbooks/tech-lead-closure-conversation-example.md](docs/runbooks/tech-lead-closure-conversation-example.md)
- 想看上游角色怎么澄清、排期和出方案：看 [docs/runbooks/product-manager-clarification-conversation-example.md](docs/runbooks/product-manager-clarification-conversation-example.md)、[docs/runbooks/project-manager-planning-conversation-example.md](docs/runbooks/project-manager-planning-conversation-example.md)、[docs/runbooks/architect-design-conversation-example.md](docs/runbooks/architect-design-conversation-example.md)
- 已安装，准备长期接入一个新项目：看 [docs/runbooks/project-onboarding.md](docs/runbooks/project-onboarding.md)
- 一人开发，想看最短闭环：看 [docs/runbooks/solo-delivery-mode.md](docs/runbooks/solo-delivery-mode.md) 和 [docs/runbooks/solo-delivery-one-page.md](docs/runbooks/solo-delivery-one-page.md)
- 想直接完整走一遍主链演练：看 [docs/runbooks/first-team-workflow-walkthrough.md](docs/runbooks/first-team-workflow-walkthrough.md)
- 想看完整命令和结构规范：看 [docs/runbooks/team-skills-usage.md](docs/runbooks/team-skills-usage.md)

快速导航：

- 初次试跑：看 [docs/runbooks/claude-quick-start.md](docs/runbooks/claude-quick-start.md) 或 [docs/runbooks/codex-quick-start.md](docs/runbooks/codex-quick-start.md)
- 按任务场景选择：看 [docs/runbooks/claude-usage-scenarios.md](docs/runbooks/claude-usage-scenarios.md) 和 [docs/runbooks/codex-usage-scenarios.md](docs/runbooks/codex-usage-scenarios.md)
- 正式接入项目：看 [docs/runbooks/project-onboarding.md](docs/runbooks/project-onboarding.md)
- 想完整走一遍主链：看 [docs/runbooks/first-team-workflow-walkthrough.md](docs/runbooks/first-team-workflow-walkthrough.md)
- 安装或使用异常：看 [docs/runbooks/troubleshooting.md](docs/runbooks/troubleshooting.md)
- 想快速看完这轮都优化了什么：看 [docs/runbooks/batch-optimization-completion-checklist.md](docs/runbooks/batch-optimization-completion-checklist.md)
- 想看 ECC 运行时能力、记忆持久化和并行执行：看 [docs/runbooks/ecc-harness-usage.md](docs/runbooks/ecc-harness-usage.md)、[docs/runbooks/error-experience-usage.md](docs/runbooks/error-experience-usage.md)、[docs/runbooks/parallel-execution-usage.md](docs/runbooks/parallel-execution-usage.md)
- 想先搞清楚现在到底有哪些命令、skills 和 runtime：看 [docs/runbooks/command-and-capability-matrix.md](docs/runbooks/command-and-capability-matrix.md) 和 [docs/runbooks/runtime-capabilities-overview.md](docs/runbooks/runtime-capabilities-overview.md)
- 想直接查本地 audit jsonl：运行 `node scripts/query-audit-logs.js --summary-only`
- 想把 audit 查询结果导出成文件：运行 `node scripts/query-audit-logs.js --session-id <session_id> --export-json audit.json --export-md audit.md`
- 想导出适合周报/复盘的 Markdown 表格：运行 `node scripts/query-audit-logs.js --component script --export-md audit.md`
- 想看完整演示场景与执行记录：看 [docs/runbooks/demo-scenario.md](docs/runbooks/demo-scenario.md) 和 [docs/runbooks/demo-execution-log.md](docs/runbooks/demo-execution-log.md)
- 想看汇报材料与生成脚本：看 [docs/presentation/README.md](docs/presentation/README.md)
- 示例怎么选：看 [examples/INDEX.md](examples/INDEX.md)
- 想直接复制 examples 里的会话脚本：看 [examples/claude-conversation-script.md](examples/claude-conversation-script.md)、[examples/codex-conversation-script.md](examples/codex-conversation-script.md)、[examples/role-conversation-scripts.md](examples/role-conversation-scripts.md)
- 想按任务类型直接复制示例：看 [examples/claude-scenario-playbook.md](examples/claude-scenario-playbook.md) 和 [examples/codex-scenario-playbook.md](examples/codex-scenario-playbook.md)
- 想创建自定义扩展 overlay：看 [docs/runbooks/custom-overlay.md](docs/runbooks/custom-overlay.md)

## 文档入口

**入门与场景**

- [CLAUDE.md](CLAUDE.md)
- [docs/runbooks/claude-usage-scenarios.md](docs/runbooks/claude-usage-scenarios.md)
- [docs/runbooks/codex-usage-scenarios.md](docs/runbooks/codex-usage-scenarios.md)
- [docs/runbooks/project-onboarding.md](docs/runbooks/project-onboarding.md)
- [docs/runbooks/first-team-workflow-walkthrough.md](docs/runbooks/first-team-workflow-walkthrough.md)
- [docs/runbooks/team-skills-usage.md](docs/runbooks/team-skills-usage.md)

**协作与样例**

- [examples/INDEX.md](examples/INDEX.md)
- [examples/user-CLAUDE.md](examples/user-CLAUDE.md)
- [examples/project-CLAUDE.md](examples/project-CLAUDE.md)
- [examples/claude-scenario-playbook.md](examples/claude-scenario-playbook.md)
- [examples/codex-scenario-playbook.md](examples/codex-scenario-playbook.md)
- [docs/runbooks/project-claude-design-rationale.md](docs/runbooks/project-claude-design-rationale.md)
- [docs/runbooks/handoff-filling-guide-with-examples.md](docs/runbooks/handoff-filling-guide-with-examples.md)

**工程规范与门禁**

- [docs/runbooks/team-command-output-contracts.md](docs/runbooks/team-command-output-contracts.md)
- [docs/runbooks/git-pr-workflow.md](docs/runbooks/git-pr-workflow.md)
- [docs/runbooks/frontend-governance.md](docs/runbooks/frontend-governance.md)
- [docs/runbooks/karpathy-guidelines-usage.md](docs/runbooks/karpathy-guidelines-usage.md)
- [docs/runbooks/api-breaking-change-gates.md](docs/runbooks/api-breaking-change-gates.md)
- [docs/runbooks/api-lint-gates.md](docs/runbooks/api-lint-gates.md)
- [docs/runbooks/contract-testing-playbook.md](docs/runbooks/contract-testing-playbook.md)

**安全与发布门禁**

- [docs/runbooks/reviewdog-pr-gates.md](docs/runbooks/reviewdog-pr-gates.md)
- [docs/runbooks/codeql-pr-security-gates.md](docs/runbooks/codeql-pr-security-gates.md)
- [docs/runbooks/secret-scanning-gates.md](docs/runbooks/secret-scanning-gates.md)
- [docs/runbooks/checkov-iac-gates.md](docs/runbooks/checkov-iac-gates.md)
- [docs/runbooks/trivy-security-gates.md](docs/runbooks/trivy-security-gates.md)
- [docs/runbooks/sbom-generation-gates.md](docs/runbooks/sbom-generation-gates.md)
- [docs/runbooks/artifact-attestation-gates.md](docs/runbooks/artifact-attestation-gates.md)

**运维与进阶**

- [docs/runbooks/custom-overlay.md](docs/runbooks/custom-overlay.md)
- [docs/runbooks/external-capability-intake.md](docs/runbooks/external-capability-intake.md)
- [docs/runbooks/command-and-capability-matrix.md](docs/runbooks/command-and-capability-matrix.md)
- [docs/runbooks/ecc-harness-usage.md](docs/runbooks/ecc-harness-usage.md)
- [docs/runbooks/error-experience-usage.md](docs/runbooks/error-experience-usage.md)
- [docs/runbooks/parallel-execution-usage.md](docs/runbooks/parallel-execution-usage.md)
- [docs/runbooks/runtime-capabilities-overview.md](docs/runbooks/runtime-capabilities-overview.md)
- [docs/plans/team-skills-platform-migration.md](docs/plans/team-skills-platform-migration.md)

**演示与材料**

- [docs/runbooks/demo-scenario.md](docs/runbooks/demo-scenario.md)
- [docs/runbooks/demo-execution-log.md](docs/runbooks/demo-execution-log.md)
- [docs/presentation/README.md](docs/presentation/README.md)

**排障与台账**

- [docs/runbooks/troubleshooting.md](docs/runbooks/troubleshooting.md)
- [docs/runbooks/document-execution-audit.md](docs/runbooks/document-execution-audit.md)
