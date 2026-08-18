---
name: devops/changelog-generation
description: 自动生成 CHANGELOG，基于 git 提交历史和 pipeline 产物信息，遵循 Conventional Commits 和 Keep a Changelog 规范
version: 1.0.0
agent: devops
type: workflow
user-invocable: false
agent-invocable: true
dependencies:
  - devops/deployment-process
triggers:
  - 部署成功完成后
  - 需要生成版本变更日志时
  - 发布新版本时
---

# CHANGELOG 自动生成

## 适用场景

在部署成功完成后自动生成或追加 CHANGELOG，记录本次发布的所有变更。适用于：
- 部署完成后的发布记录
- 版本发布前的变更汇总
- 对外发布说明的自动生成

## 核心方法

### 步骤 1：信息收集

1. **Git 历史解析**：
   ```bash
   # 获取从上次 tag 到 HEAD 的所有提交
   git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --pretty=format:"%H|%s|%an|%ai"
   ```
   - 如果没有 tag，取最近 50 条提交
   - 解析 Conventional Commits 格式：`type(scope): description`

2. **Pipeline 产物读取**：
   - `.boss/<feature>/prd.md` → 功能描述和用户价值
   - `.boss/<feature>/deploy-report.md` → 部署环境和版本信息
   - `.boss/<feature>/tasks.md` → 完成的任务列表

3. **版本号确定**：
   - 优先使用 `package.json` 中的 version
   - 其次使用最新 git tag
   - 如无法确定，使用日期格式 `YYYY.MM.DD`

### 步骤 2：变更分类

按 Conventional Commits 规范分类：

| 类型 | CHANGELOG 分类 | 说明 |
|------|---------------|------|
| `feat` | **Added** | 新增功能 |
| `fix` | **Fixed** | 修复问题 |
| `perf` | **Performance** | 性能优化 |
| `refactor` | **Changed** | 重构（非功能变更） |
| `docs` | **Documentation** | 文档更新 |
| `style` | _(不记录)_ | 代码格式 |
| `test` | _(不记录)_ | 测试相关 |
| `chore` | _(不记录)_ | 构建/工具变更 |
| `BREAKING CHANGE` | **⚠️ Breaking Changes** | 破坏性变更（始终置顶） |

对于非 Conventional Commits 格式的提交：
- 根据关键词推断分类（add/new → Added, fix/bug → Fixed, update/change → Changed）
- 无法分类的归入 **Changed**

### 步骤 3：内容生成

#### 格式规范（Keep a Changelog）

```markdown
## [版本号] - YYYY-MM-DD

### ⚠️ Breaking Changes
- 破坏性变更描述 ([commit-hash])

### Added
- 新功能描述（来自 PRD 的用户价值说明） ([commit-hash])

### Changed
- 变更描述 ([commit-hash])

### Fixed
- 修复描述 ([commit-hash])

### Performance
- 优化描述 ([commit-hash])
```

#### 生成规则

1. 每条记录包含：清晰描述 + commit short hash 引用
2. 如有 PRD，用 PRD 中的功能描述替代 commit message（更面向用户）
3. Breaking Changes 始终置顶并用 ⚠️ 标记
4. 同一 scope 的多条提交合并为一条记录
5. 最多展示 20 条变更，超出部分汇总为 "及其他 N 项更新"

### 步骤 4：输出写入

**两种输出模式：**

1. **产物模式**（默认）：写入 `.boss/<feature>/changelog.md`
2. **追加模式**：如项目根目录已有 `CHANGELOG.md`，将新版本内容追加到文件顶部（在 `# Changelog` 标题之后）

**追加逻辑：**
```
读取现有 CHANGELOG.md
→ 找到第一个 ## [version] 行
→ 在其前面插入新版本内容
→ 写回文件
```

如果项目无 `CHANGELOG.md`，则创建包含标准头部的新文件：
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [版本号] - 日期
...
```

## 输出要求

1. 产物文件 `.boss/<feature>/changelog.md` 必须生成
2. 如项目根存在 `CHANGELOG.md`，同步更新
3. 变更内容必须准确反映实际代码变更
4. 面向用户的描述优先于面向开发者的 commit message
