# Phase 5: 代码生成（Code Generation）引导细则

## 入口条件

- Phase 4 的 `agent-prompts.md` 和 `agent-orchestration.md` 已确认
- 已知目标框架和所有设计文档

## 前置检查

### 加载框架适配器

1. 读取 `adk-framework-adapters` 中目标框架的 reference 文件
2. 检查 `verified_date` 字段：
   - 距今 ≤ 90 天：正常使用
   - 距今 > 90 天：提醒用户「框架 {name} 的适配器最后验证于 {date}，API 可能已变化。建议在生成后仔细检查 import 路径和 API 名称」
3. 从 reference 文件中加载：项目模板结构、依赖配置、惯用模式、示例代码片段

## 项目结构生成

### 通用结构（框架无关）

```
{agent_name}/
├── README.md
├── .env.example
├── .gitignore
├── {dependency_file}               # pyproject.toml / go.mod / package.json
├── src/
│   ├── __init__.py                 # Python only
│   ├── agent.{ext}                 # Agent 核心入口
│   ├── config.{ext}                # 配置加载
│   ├── tools/
│   │   ├── __init__.{ext}
│   │   ├── {tool_1}.{ext}
│   │   └── {tool_2}.{ext}
│   ├── prompts/
│   │   ├── system.txt              # System Prompt 文本
│   │   └── templates/              # 其他 Prompt 模板
│   ├── memory/
│   │   └── store.{ext}            # Memory 实现
│   └── orchestrator/               # Multi-Agent 时
│       ├── __init__.{ext}
│       ├── router.{ext}
│       └── workflow.{ext}
├── tests/
│   ├── test_agent.{ext}
│   ├── test_tools.{ext}
│   └── conftest.{ext}             # Python pytest fixture / Go testmain
├── configs/
│   └── default.yaml                # 默认运行配置
├── data/                           # RAG Agent 的知识库目录
│   └── .gitkeep
└── scripts/
    ├── run.sh                      # 启动脚本
    ├── ingest.sh                   # RAG 数据导入脚本（如适用）
    └── test.sh                     # 测试脚本
```

### 文件扩展名映射

| 框架 | 语言 | ext | 依赖文件 |
|------|------|-----|----------|
| LangChain | Python | py | pyproject.toml |
| LangChain.js | TypeScript | ts | package.json |
| EINO | Go | go | go.mod |
| AutoGen | Python | py | pyproject.toml |
| AgentScope | Python | py | pyproject.toml |
| CrewAI | Python | py | pyproject.toml |

## 代码生成规则

### 通用规则

1. **所有敏感配置通过环境变量**：API Key、数据库连接串、Token 等一律从 `.env` 读取，不硬编码
2. **`.env.example` 标注所有必需变量**：标注变量名、用途、格式要求
3. **类型标注**：Python 使用 type hints，Go 天然类型安全，TypeScript 使用严格类型
4. **错误处理**：每个工具调用都有 try-catch 和有意义的错误消息
5. **日志**：使用框架原生日志机制，关键节点有 INFO 级日志
6. **配置分层**：`.env` → `configs/default.yaml` → 代码默认值

### 框架特定规则

框架特定的代码模式、import 路径、初始化方式见对应的 `adk-framework-adapters/references/{framework}.md`。

### 代码生成顺序

1. 依赖文件（`pyproject.toml` / `go.mod` / `package.json`）
2. 配置文件（`.env.example`、`configs/default.yaml`）
3. 工具实现（`src/tools/*.{ext}`）— 最独立的部分
4. Memory 实现（`src/memory/store.{ext}`）
5. Prompt 文件（`src/prompts/system.txt`）
6. Agent 核心（`src/agent.{ext}`）— 串联工具 + memory + prompt
7. 编排逻辑（`src/orchestrator/`）— Multi-Agent 时
8. 入口脚本（`scripts/run.sh`）
9. 测试文件（`tests/`）
10. README.md

### 逐文件确认规则

对以下核心文件，生成后必须单独展示并等待用户确认：
- `src/agent.{ext}`（Agent 核心）
- `src/orchestrator/*.{ext}`（编排逻辑，如有）
- 每个工具的实现（`src/tools/*.{ext}`）

辅助文件（配置、脚本、.gitignore）可以批量展示确认。

## README.md 模板

```markdown
# {Agent Name}

{Agent Description}

## 架构

{从 agent-architecture.md 复制 Mermaid 图}

## 快速开始

### 前置条件

- {language} {version}
- {其他依赖}

### 安装

\`\`\`bash
{install_command}
\`\`\`

### 配置

复制环境变量模板并填写：

\`\`\`bash
cp .env.example .env
# 编辑 .env 填写 API Key 等配置
\`\`\`

### 运行

\`\`\`bash
{run_command}
\`\`\`

### 测试

\`\`\`bash
{test_command}
\`\`\`

## 工具列表

| 工具 | 描述 |
|------|------|
| {tool_name} | {tool_desc} |

## 项目结构

\`\`\`
{tree_output}
\`\`\`

## License

MIT
```

## --import 模式特殊处理

Phase 5 在 import 模式下的行为：
1. 对比原框架 vs 目标框架的关键差异，生成 `migration-diff.md`
2. 原 Agent 的每个工具在新框架中必须有等效实现
3. 原 Prompt 保持不变（除非框架要求调整格式）
4. 生成后展示 `migration-diff.md` 供用户确认

## 确认点

1. 先展示完整项目结构树
2. 逐个展示核心代码文件
3. 批量展示辅助文件
4. 用户整体确认后进入 Phase 6
