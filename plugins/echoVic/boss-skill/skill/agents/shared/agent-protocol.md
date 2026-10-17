# Agent 共享协议

本文档包含所有 Boss Agent 的通用规则。各 Agent Prompt 文件通过引用本文档来继承这些规则，避免重复定义。

> Context 预算规则：编排器应先读取 `agents/shared/protocol-manifest.md`，将稳定规则放入 prefix 缓存，并按需加载本文件全文。不要默认让每个 subagent 重复读取所有共享协议。

---

## 协议 manifest 与按需加载

- **协议 manifest**：`agents/shared/protocol-manifest.md` 是共享协议索引，列出公共 prefix、模块触发条件和渐进式披露流程。
- **prefix 缓存**：同一轮流水线中，语言规则、模板优先级、状态块、摘要优先和技术栈缓存规则应作为短前缀复用。
- **按需加载**：只有当 Agent 需要完整模板规则、技术适配规则或状态处理细节时，才展开对应协议全文。
- **禁止默认全量注入**：不要把 `agent-protocol.md`、`tech-detection.md` 和角色 prompt 全文无条件重复塞给每个 subagent。

## 语言规则

根据 Agent 角色自动适用对应规则：

- **文档类 Agent**（PM、Architect、UI Designer、Tech Lead、Scrum Master、QA、DevOps）：**所有输出必须使用中文**
- **代码类 Agent**（Frontend、Backend）：**注释使用中文，代码使用英文**

---

## 模板优先规则

当任务涉及生成文档产物时，遵循以下优先级：

1. 如果当前任务提供了目标产物文件或模板路径，必须先读取它们，并以其结构为准输出内容
2. 优先级：`.boss/templates/<name>.template` > Skill 内置 `templates/<name>.template` > Agent Prompt 中的默认输出格式
3. 如果目标产物已经通过 `boss artifact prepare` 准备好骨架，直接在该骨架上填充内容，不要改写成你自己的固定章节
4. Agent Prompt 中的"输出格式"仅在模板不存在或任务未提供骨架时作为兜底参考
5. **占位符约定**：`{{VAR}}` 表示由脚本/运行时替换的机器变量（如 FEATURE_NAME, DATE）；`[描述]` 表示由 Agent 根据上下文填写的内容

---

## 子代理状态协议

每个 Agent 执行完毕后，**必须**使用以下五种状态之一进行报告（详见 `agents/prompts/subagent-protocol.md`）：

| 状态 | 含义 | 后续处理 |
|------|------|---------|
| `DONE` | 任务完成，所有验证通过 | 产物传递给下游 |
| `DONE_WITH_CONCERNS` | 完成但有需关注的问题 | 记录 concerns，视严重性决定是否暂停 |
| `NEEDS_CONTEXT` | 缺少必要上下文，无法继续 | 编排器补充上下文后重新调用 |
| `BLOCKED` | 被阻塞，无法继续 | 暂停流水线，向用户报告阻塞原因 |
| `REVISION_NEEDED` | 需要上游产物修订 | 触发反馈循环，重派上游 Agent 修订（≤2轮） |

## 执行中会话层

文档仍是正式 source of truth，但执行过程中允许 Agent 之间做短会话对齐，而不是把所有问题都憋到最终报告里。

- Any agent may open an execution conversation with any other relevant agent.
- Every conversation must be anchored to an `artifact`、`task`、`scope` 或 `decision`。
- 统一会话原语：`ask`、`challenge`、`propose`、`request_change`、`escalate`、`huddle`、`resolve`。
- `resolve` 只有在结论已 materialized 为至少一个 executable、single-owner todo，或升级为正式 `RevisionRequested` 修订循环后才成立。
- 对话层负责执行中的判断与求助；正式文档、正式修订目标和最终裁决仍以产物层为准。

### 任务完成报告格式

```markdown
## 执行报告

- **状态**：[DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED / REVISION_NEEDED]
- **产物路径**：[生成的文件路径列表]
- **conversation_id**：[如本次任务参与了执行中会话]
- **resolution_summary**：[如会话已收敛，简述结论]
- **todo_ids**：[如会话产出了 follow-up todo，列出 todo ID]
- **关键决策**：[本次执行中的重要决策及理由]
- **revision_target**：[仅会话升级为正式修订或状态为 REVISION_NEEDED 时填写]
- **遗留风险**：[如有，列出风险项及建议的应对方案]
```

---

## 技术适配协议

### 技术栈缓存

执行技术栈检测前，先检查缓存：

1. 读取 `.boss/<feature>/.meta/tech-stack.json`
2. 如果文件存在且非空，直接使用缓存的检测结果
3. 如果文件不存在，执行 `agents/shared/tech-detection.md` 完整检测流程
4. 检测完成后，将结果写入 `.boss/<feature>/.meta/tech-stack.json` 供后续 Agent 复用

执行任务前，根据项目状态动态适配技术栈。根据场景选择对应流程：

### 场景 A：已有项目（项目中已有源代码）

1. **识别技术栈** — 执行 `agents/shared/tech-detection.md` 中的检测流程，确认语言、框架、测试框架、ORM/数据库、包管理器
2. **探索项目模式** — 搜索项目中已有的同类代码：
   - 组件/模块结构和命名约定
   - API 路由组织方式
   - 测试文件写法和断言风格
   - 错误处理模式
   - README、CONTRIBUTING、.editorconfig 等约定文件
3. **适配输出** — 生成的代码/文档**必须**与项目已有风格一致，不套用通用模板

### 场景 B：新项目（无现有代码）

1. **读取架构决策** — 从 `architecture.md` 的「技术选型」section 读取 Architect Agent 的技术栈设计
2. **搜索最佳实践** — 基于架构决策中指定的框架/语言，搜索该框架的官方推荐项目结构和编码约定
3. **按约定生成** — 基于搜索到的最佳实践生成代码和配置

### 优先级链

`项目已有模式` > `architecture.md 技术决策` > `框架官方推荐` > `Agent 通用原则`

---

## 摘要优先原则

读取上游产物时，优先读取文档开头的 `## 摘要` section；仅在需要细节时读取完整内容，以节省 Token。
