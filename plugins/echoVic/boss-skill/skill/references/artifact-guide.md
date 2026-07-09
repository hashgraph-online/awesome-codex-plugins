# 产物保存规范

## 保存规则

每个阶段的产物 **必须** 使用 Write 工具保存到 `.boss/<feature>/` 目录。

**保存前，先按模板优先级为当前产物准备文档骨架，再基于该骨架生成内容。**

推荐顺序：
1. 若 `.boss/<feature>/` 尚不存在，先执行 `boss project init <feature-name>` 创建占位文件和 `.meta/execution.json`
2. 对当前要产出的单个文档执行 `boss artifact prepare <feature-name> <artifact-name>`
3. 读取刚准备好的目标产物文件，以其结构为基础填充真实内容

不要在初始化阶段一次性把所有模板正文落入 `.boss/<feature>/`，只为当前阶段需要的产物逐个准备骨架。

模板查找优先级：
1. 项目级模板：`.boss/templates/<name>.template`
2. Skill 内置模板：`templates/<name>.template`

如果项目级模板存在，**必须优先使用**，以便用户按项目规范自定义文档结构。

**每个 Markdown 产物必须在正文最开头包含 `## 摘要` section**，用 3-5 条简短结论概括核心内容。下游 Agent 读取上游 Markdown 产物时，优先读取 `## 摘要`，仅在需要细节时读取完整内容，以节省 Token。

Markdown 产物是权威内容源。保存并记录 Markdown 产物后，Boss runtime 会自动生成同名 HTML companion（例如 `prd.md` → `prd.html`）。Agent 不需要、也不应该手写整页 HTML；HTML 页面由 `artifact.html.template` 和 runtime renderer 统一生成。

HTML 模板查找优先级：
1. 项目级模板：`.boss/templates/artifact.html.template`
2. Skill 内置模板：`templates/artifact.html.template`

机器可读 JSON 产物（如 `ui-design.json`）必须保持合法 JSON，不要求 `## 摘要`，也不得为了摘要在 JSON 前后追加 Markdown。

| 阶段 | 必须保存的产物 | 模板 |
|------|----------------|------|
| 阶段 1 | `prd.md`（自动生成 `prd.html`） | `templates/prd.md.template` |
| 阶段 1 | `architecture.md`（自动生成 `architecture.html`） | `templates/architecture.md.template` |
| 阶段 1 | `ui-spec.md`（如有界面，自动生成 `ui-spec.html`） | `templates/ui-spec.md.template` |
| 阶段 1 | `ui-design.json`（如有界面） | `templates/ui-design.json.template` |
| 阶段 2 | `tech-review.md`（自动生成 `tech-review.html`） | `templates/tech-review.md.template` |
| 阶段 2 | `tasks.md`（自动生成 `tasks.html`） | `templates/tasks.md.template` |
| 阶段 3 | `qa-report.md`（自动生成 `qa-report.html`） | `templates/qa-report.md.template` |
| 阶段 4 | `deploy-report.md`（自动生成 `deploy-report.html`） | `templates/deploy-report.md.template` |

默认产物流：

```text
design-brief → prd.md ─┬→ architecture.md → tech-review.md → tasks.md → [code] → qa-report.md → deploy-report.md
                       ├→ ui-spec.md(opt) ┘
                       └→ ui-design.json(opt) ┘
```

## 保存格式

```
boss artifact prepare <feature-name> prd.md
Write(".boss/<feature>/prd.md", ...)
boss artifact prepare <feature-name> architecture.md
Write(".boss/<feature>/architecture.md", ...)
boss artifact prepare <feature-name> ui-spec.md
Write(".boss/<feature>/ui-spec.md", ...)
boss artifact prepare <feature-name> ui-design.json
Write(".boss/<feature>/ui-design.json", ...)
boss design preview <feature>
```

## 检查清单

保存产物后，问自己：
- [ ] 文件是否保存到了正确的 `.boss/<feature>/` 目录？
- [ ] 文件名是否与规范一致？
- [ ] 内容是否使用了中文？
- [ ] 是否先为当前产物执行了 `boss artifact prepare`？
- [ ] 是否优先读取了 `.boss/templates/` 中的项目级模板？
- [ ] 是否基于对应的 template 生成？
- [ ] 是否只准备了当前阶段需要的产物，而不是一次性渲染全部模板？
- [ ] 如写入 `ui-design.json`，是否运行或提示了 `boss design preview <feature>`？
