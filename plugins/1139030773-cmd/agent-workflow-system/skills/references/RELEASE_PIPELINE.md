# 发布流水线

保证每次改动都送达用户，不出现"改了但没人知道"的情况。

---

## 判定标准

一个改动完成必须同时满足 4 条才算"发布完成"：

| # | 条件 | 验证方式 |
|------|------|------|
| 1 | git push main | GitHub 能看到最新 commit |
| 2 | git tag + Release notes | GitHub Releases 页面能看到 |
| 3 | README 反映最新能力 | 首页描述不落后于代码 |
| 4 | 双平台可搜索并使用 | Codex `/plugins` 和 Claude Code `/` 都能找到 |
| 5 | 社区市场已更新 | awesome-codex-plugins + n-skills 条目已同步 |

缺一条 = 没发布完。

---

## 触发规则

### 什么情况必须发 Release

| 触发条件 | 示例 |
|------|------|
| 累积 ≥3 个来自真实摩擦的改进 | 今天的提问规范 + 能力前置 + 扩展审查 |
| 宪法层改动（前六章任一条） | 改了职能隔离、纠错机制等 |
| 用户可感知的功能变化 | 新增技能、新增机制文件 |
| 修复阻塞用户的 bug | 插件搜不到、市场加载失败 |
| README 描述的安装方式变化 | 仓库改名、安装命令变化 |

### 什么情况不用发

- 错别字 → 直接 push
- 格式微调 → 直接 push
- README 小修 → 直接 push
- 单条内部引用修正 → 直接 push

---

## 发布步骤（强制顺序）

```
1. 审计通过（drift-auditor 或快速自检）
2. git add + commit + push main
3. 判断是否需要 Release → 否 → 结束
4. 确定版本号（见版本规则）
5. git tag -a vX.Y.Z + push tag
6. GitHub Release notes
7. README 更新（如有新功能/新机制）
8. 双平台验证（Codex + Claude Code）
9. 社区市场同步（awesome-codex-plugins + n-skills）
10. 完成
```

---

## 版本号规则

```
v主版本.次版本.补丁

主版本: 系统定位变化、不向后兼容（宪法层大改）      例: v1→v2
次版本: 新功能、新机制、新技能（可感知的变化）      例: v1.0→v1.1
补丁:   修 bug、补引用、改错字（不可感知的修正）    例: v1.1.0→v1.1.1
```

---

## 双平台更新方式

### Claude Code

用户获取更新的方式：
1. **自动**（推荐）：配置 SessionStart hook，每次启动自动 `git pull`
2. **手动**：`cd .claude/skills/ && git pull`

系统应在 README 中提供 hook 配置方式。

### Codex

用户获取更新的方式：
1. **CLI**：`codex plugin marketplace remove agent-workflow-system && codex plugin marketplace add 1139030773-cmd/agent-workflow-system`
2. 重新安装插件：`codex plugin add agent-workflow-system@agent-workflow-system`

系统应在 README 和 Release notes 中写清楚更新命令。

### 社区市场（让新用户发现你）

每次大版本发布后，同步更新社区市场中的条目：

| 市场 | 方式 | 链接 |
|------|------|------|
| **awesome-codex-plugins** | 提 PR 更新 README 条目 | https://github.com/hashgraph-online/awesome-codex-plugins |
| **n-skills** | 开 Issue 申请收录 | https://github.com/numman-ali/n-skills |

用户添加这些市场后即可搜到你的插件：
```bash
codex plugin marketplace add hashgraph-online/awesome-codex-plugins
codex plugin marketplace add numman-ali/n-skills
```

> 注意：官方 curated 市场暂未开放自主提交。开放后优先迁移。

---

## Release notes 模板

```markdown
## vX.Y.Z — [一句话概括]

### 新增
- ...

### 改进（来自真实摩擦）
- ...

### 修复
- ...

### 更新方式
- Claude Code: 重启即更新（如配了 hook）或 git pull
- Codex: `codex plugin marketplace remove agent-workflow-system && codex plugin marketplace add 1139030773-cmd/agent-workflow-system`
```

---

## 反模式（禁止）

- ❌ 改了代码不 push
- ❌ push 了不打 tag
- ❌ 打 tag 不写 Release notes
- ❌ 发布了不更新 README
- ❌ 只测了一个平台就当发布了
- ❌ 用户问"新功能在哪"时才发现没发 Release
