# 产物保存规范

## 保存规则

每个环节的产物 **必须** 使用 Write 工具保存到 `.boss/<feature>/` 目录。

**保存前，先按模板优先级读取对应模板，基于模板结构生成内容。**

推荐顺序：
1. 若 `.boss/<feature>/` 尚不存在，直接创建目录。
2. 读取对应模板（项目级优先，其次内置）。
3. 基于模板结构填充真实内容，用 Write 工具保存到 `.boss/<feature>/`。

模板查找优先级：
1. 项目级模板：`.boss/templates/<name>.template`
2. Skill 内置模板：`templates/<name>.template`

如果项目级模板存在，**必须优先使用**，以便用户按项目规范自定义文档结构。

## 摘要要求

**每个 Markdown 产物必须在正文最开头包含 `## 摘要` section**，用 3-5 条简短结论概括核心内容。下游 Agent 读取上游 Markdown 产物时，优先读取 `## 摘要`，仅在需要细节时读取完整内容，以节省 Token。

机器可读 JSON 产物（如 `ui-design.json`）必须保持合法 JSON，不要求 `## 摘要`。

## 产物清单

| 环节      | 产物               | 模板                                  |
| --------- | ------------------ | ------------------------------------- |
| pm        | `prd.md`           | `templates/prd.md.template`           |
| architect | `architecture.md`  | `templates/architecture.md.template`  |
| ui        | `ui-spec.md`       | `templates/ui-spec.md.template`       |
| ui        | `ui-design.json`   | `templates/ui-design.json.template`   |
| review    | `tech-review.md`   | `templates/tech-review.md.template`   |
| review    | `plan.md`          | `templates/plan.md.template`          |
| tasks     | `tasks.md`         | `templates/tasks.md.template`         |
| qa        | `qa-report.md`     | `templates/qa-report.md.template`     |
| ship      | `deploy-report.md` | `templates/deploy-report.md.template` |

产物流：

```text
prd.md ─┬→ architecture.md → tech-review.md → plan.md → tasks.md → [code] → qa-report.md → deploy-report.md
        ├→ ui-spec.md(opt) ┘
        └→ ui-design.json(opt) ┘
```

> `plan.md` 是 review 环节的第二个产物，定义模块划分、里程碑和任务拆解指引。tasks 环节基于 `plan.md` 细化到文件级别的原子任务。

## 检查清单

保存产物后，问自己：
- [ ] 文件是否保存到了正确的 `.boss/<feature>/` 目录？
- [ ] 文件名是否与规范一致？
- [ ] 内容是否使用了中文（除非 `--lang en`）？
- [ ] 是否优先读取了 `.boss/templates/` 中的项目级模板？
- [ ] 是否基于对应的 template 生成？
- [ ] Markdown 产物是否包含 `## 摘要` section？
