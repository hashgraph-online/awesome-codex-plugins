# Shared Skills

## 目的

本目录存放跨Agent复用的通用方法论和工作流程。这些skills不属于特定Agent，而是被多个Agent共同使用。

## 使用场景

当一个方法论或工作流程满足以下条件时，应放入shared目录：

1. **跨Agent复用**: 被2个或以上的Agent使用
2. **通用性强**: 不包含特定Agent的上下文或角色假设
3. **独立性好**: 可以独立使用，不依赖特定Agent的状态

## 预期的Shared Skills

### 技术相关
- `tech-stack-detection.md` - 技术栈检测方法
  - 使用者: Architect, Tech Lead, Frontend, Backend, QA
  - 用途: 检测项目的技术栈（package.json, pom.xml, Cargo.toml等）

- `code-review.md` - 代码审查方法
  - 使用者: Tech Lead, QA
  - 用途: 代码审查的通用标准和流程

### 文档相关
- `document-template-adaptation.md` - 文档模板适配方法
  - 使用者: 所有文档类Agent (PM, Architect, UI Designer等)
  - 用途: 文档结构检测、模板选择、内容填充

## 开发规范

### Frontmatter要求
```yaml
---
name: shared/{skill-name}
description: {一句话描述}
version: 1.0.0
agent: shared
type: {methodology|workflow|guideline}
user-invocable: false
agent-invocable: true
dependencies: []
triggers:
  - {触发场景描述}
---
```

注意：
- `agent` 字段必须为 `shared`
- `name` 必须以 `shared/` 开头
- 内容必须通用，不包含特定Agent的角色假设

### 内容组织
1. **适用场景**: 说明何时使用此方法
2. **核心方法**: 方法论的具体内容
3. **输出要求**: 使用此方法后应产出什么

### 命名规范
- 使用kebab-case命名
- 名称应清晰描述方法的用途
- 避免使用Agent特定的术语

## 维护指南

### 添加新的Shared Skill
1. 确认该方法确实被多个Agent使用
2. 使用 `_TEMPLATE.md` 创建新文件
3. 确保内容通用，不包含特定Agent的上下文
4. 更新本README，添加到"预期的Shared Skills"列表

### 更新现有Shared Skill
1. 检查所有使用该skill的Agent
2. 确保修改不会破坏现有Agent的功能
3. 更新version字段
4. 通知所有使用该skill的Agent维护者

### 删除Shared Skill
1. 检查dependencies，确认没有Agent依赖该skill
2. 如有依赖，先迁移到其他skill或Agent内部
3. 删除文件并更新本README
