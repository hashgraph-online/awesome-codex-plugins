# 协议 manifest

本文档是 Boss 子代理协议的轻量索引。编排器应优先加载本 manifest，并把稳定的公共规则作为 prefix 缓存复用；只有命中触发条件时才读取完整协议，避免每个 subagent 重复读取同一批长上下文。

---

## 公共 prefix 缓存

以下内容适合放入同一轮流水线的共享 prefix 缓存，所有 subagent 复用，不需要每次重复展开全文：

- 输出语言：文档类 Agent 使用中文；代码类 Agent 注释中文、代码英文。
- 产物优先级：项目模板 > Skill 内置模板 > Agent Prompt 兜底格式。
- 状态块：所有 Agent 必须用 `DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED / REVISION_NEEDED` 报告。
- 执行中会话层：使用 `ask / challenge / propose / request_change / escalate / huddle / resolve`；每条会话都必须 anchored，并在收敛后 materialize 为 single-owner todo 或正式修订循环。
- 摘要优先：先读上游产物的 `## 摘要`，需要细节时再读取全文。
- 技术栈缓存：先查 `.boss/<feature>/.meta/tech-stack.json`，缓存缺失或过期时才执行完整检测。

如果运行环境支持 prompt prefix / context cache / session memory，将以上 prefix 固定在共享上下文中；如果不支持，只向子代理注入本节摘要和必要模块引用。

---

## 按需加载矩阵

| 模块 | 文件 | 何时加载全文 |
|------|------|--------------|
| 通用协议 | `agents/shared/agent-protocol.md` | Agent 第一次接入、模板优先级/状态格式不清楚、或需要完整技术适配规则 |
| 技术检测 | `agents/shared/tech-detection.md` | `.meta/tech-stack.json` 缺失、缓存过期、项目结构变化、或 Agent 明确需要重新识别技术栈 |
| 子代理状态/反馈 | `agents/prompts/subagent-protocol.md` | orchestrator 处理状态机、执行中会话、反馈循环、Wave 校验、风险确认、或子代理返回异常状态 |
| 测试标准 | `references/testing-standards.md` | code / QA / gate 相关任务 |
| 产物保存 | `references/artifact-guide.md` | 保存或校验 `.boss/<feature>/` 产物路径时 |

默认不要把 `agent-protocol.md`、`tech-detection.md` 和自家 prompt 全文一起塞给每个 subagent。先给角色 prompt + 本 manifest 的公共 prefix；缺上下文时再按矩阵渐进式披露。

---

## 渐进式披露流程

1. **启动 Wave 前**：orchestrator 读取本协议 manifest，建立本轮 prefix 缓存。
2. **派发 Agent 时**：注入角色 Prompt、公共 prefix、任务输入、必要产物摘要，以及按需模块引用。
3. **缓存命中时**：若 `.meta/tech-stack.json` 可用，只注入技术栈摘要，不读取 `tech-detection.md` 全文。
4. **出现缺口时**：Agent 返回 `NEEDS_CONTEXT` 或明确说明缺少某协议细节后，orchestrator 再加载对应全文并重派。
5. **缓存失效时**：依赖清单、锁文件、构建配置、目录结构或运行环境发生变化，清理相关摘要并重新加载对应模块。
6. **执行中分歧时**：优先补充会话层摘要（参与方、anchor、todo 结论）；只有会话规则不清楚时才展开完整协议。

目标是让 12 个 subagent 共享同一份协议前缀，而不是产生 `12 × shared protocol` 的重复 context 成本。
