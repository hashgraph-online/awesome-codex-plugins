---

name: boss:ui
description: "从 UI 设计开始：UI Designer 产出 ui-spec.md + ui-design.json，默认自动续跑后续环节（评审 → 任务 → 开发 → 测试 → 部署）。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:ui — UI 设计（UI Designer）

`/boss:ui` 是专家小队的**UI 设计入口**。以 UI Designer 身份产出 `ui-spec.md` 和 `ui-design.json`。

**默认行为**：UI 设计完成后自动续跑后续所有环节，除非用户主动叫停。

## 适合 / 不适合

| 适合 `/boss:ui`          | 不适合                                             |
| ------------------------ | -------------------------------------------------- |
| 有需求，需要 UI 设计规范 | 纯 API/CLI 项目（用 `--skip-ui` 或直接从架构开始） |
| 给已有项目补 UI 规范     | 只想做技术评审                                     |

## 前置输入

- 优先读取 `.boss/<slug>/prd.md`
- 若 `prd.md` 不存在，可用用户直接描述的需求替代

## 执行步骤

1. **Feature slug 归一化**：确定 feature slug。
2. **读取输入**：优先读 `prd.md`，不存在则用用户需求。
3. **派发 UI Designer Agent**：读取 `agents/boss-ui-designer.md`，产出：
   - `.boss/<slug>/ui-spec.md` — UI 规范文档
   - `.boss/<slug>/ui-design.json` — 机器可渲染设计契约
   - `.boss/<slug>/prototype/` — 可交互 HTML 原型（可选，需用户同意）
4. **自检**：对照 UI Designer 的硬性要求检查（设计系统完整、组件状态齐全、无障碍达标）。
5. **续跑**：读取 `references/continuation-chain.md`，按链执行下一步（review），除非用户叫停。

## HTML 原型

UI Designer 在设计前会询问用户是否需要可交互 HTML 原型：
- 用户同意 → 生成 `.boss/<slug>/prototype/`，启动本地服务，用户在浏览器中查看并点击选择方案
- 用户拒绝 → 直接用文字描述 + JSON 交付

原型服务在设计确认后自动停止，原型文件保留供参考。

## 用法

```
/boss:ui 做一个面向设计师的素材管理工具
/boss:ui user-auth
```

## 选项

| 参数                  | 说明                |
| --------------------- | ------------------- |
| `--stop-after <环节>` | 跑到指定环节后停    |
| `--lang <zh\|en>`     | 产物语言（默认 zh） |
