# Shared Skills

## 目的

本目录存放跨 Agent 复用的通用方法论和工作流程。这些 skills 不属于特定 Agent，而是被多个 Agent 共同使用。

## 使用场景

当一个方法论或工作流程满足以下条件时，应放入 shared 目录：
1. **跨 Agent 复用**：被 2 个或以上的 Agent 使用
2. **通用性强**：不包含特定 Agent 的上下文或角色假设
3. **独立性好**：可以独立使用，不依赖特定 Agent 的状态

## 当前 Shared Skills

| Skill                | 路径                                   | 使用者                                      | 用途                                                   |
| -------------------- | -------------------------------------- | ------------------------------------------- | ------------------------------------------------------ |
| TDD                  | `shared/tdd/SKILL.md`                  | Frontend, Backend                           | Red-Green-Refactor 测试驱动开发铁律                    |
| Tech Stack Detection | `shared/tech-stack-detection/SKILL.md` | Architect, Tech Lead, Frontend, Backend, QA | 检测项目技术栈（package.json、pom.xml、Cargo.toml 等） |

## Frontmatter 规范

```yaml
---
name: shared/{skill-name}
description: { 一句话描述 }
version: 1.0.0
agent: shared
type: { methodology|workflow|guideline }
user-invocable: false
agent-invocable: true
dependencies: []
triggers:
  - { 触发场景描述 }
---
```

注意：
- `agent` 字段必须为 `shared`
- `name` 必须以 `shared/` 开头
- 内容必须通用，不包含特定 Agent 的角色假设
- 所有 skill 必须使用 bundle 布局：`shared/<name>/SKILL.md`，不要用平铺 `.md` 文件

## 内容组织

1. **适用场景**：说明何时使用此方法
2. **核心方法**：方法论的具体内容
3. **输出要求**：使用此方法后应产出什么

## 命名规范

- 使用 kebab-case 命名
- 名称应清晰描述方法的用途
- 避免使用 Agent 特定的术语

## 维护指南

### 添加新的 Shared Skill

1. 确认该方法确实被多个 Agent 使用
2. 使用 `skill/skills/_TEMPLATE.md` 创建新的 bundle 目录
3. 确保内容通用，不包含特定 Agent 的上下文
4. 更新本 README，添加到"当前 Shared Skills"表格

### 更新现有 Shared Skill

1. 检查所有使用该 skill 的 Agent
2. 确保修改不会破坏现有 Agent 的功能
3. 更新 version 字段

### 删除 Shared Skill

1. 检查 dependencies，确认没有 Agent 依赖该 skill
2. 如有依赖，先迁移到其他 skill 或 Agent 内部
3. 删除 bundle 目录并更新本 README
