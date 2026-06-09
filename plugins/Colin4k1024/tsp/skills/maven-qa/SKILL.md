---
name: maven-qa
description: Maven 编码质量闸口（编译 + 单测 + 静态分析 + 启动检测），只做验证不做修复，问题统一记录到 qa-pending.md。当编码完成后需要执行质量门禁时使用，也可单独触发。关键词：QA、质量验证、编译检查、单测、静态分析、启动检测、mvn verify、质量闸口。
---

# Maven QA 质量闸口

## 职责

编码完成后的四阶段质量验证：**编译 → 单测 → 静态分析 → 启动检测**。

**只检查，不修复。** 任何阶段失败，将问题记录到统一遗留文件后继续执行下一阶段，确保四个阶段的结果都能完整收集。

## 执行合同

### 适用前提

- 已有可验证的代码或配置变更，需要统一收集编译、单测、静态分析和启动结果。
- 若任务只是设计或 intake 阶段，没有可执行对象，不应提前运行本 skill。

### 任务变量

- `workspaceDir`：当前工作区根目录。
- `projectName`：目标项目名；未提供时取 `workspaceDir` 目录名。
- `projectDir`：`workspaceDir / projectName`。
- `subModule`：要执行 `mvn test` / 启动检查的子模块，默认 `.`。
- `subModuleDir`：`projectDir / subModule`。
- `triggerMethod`：此次 QA 对应的方法、模块或任务标识。
- `<skill_dir>`：当前安装环境中的 `maven-qa` 技能目录，用于解析脚本路径。

### 变量来源

- `workspaceDir` 默认取当前工作区。
- `projectName`、`subModule`、`triggerMethod` 优先来自 `/team-plan`、`/team-execute`、上游 `/handoff`；未提供时按默认值执行并在输出中注明假设。
- `<skill_dir>` 始终指向当前 skill 安装目录，不需要用户提供，也不能写死绝对路径。
- 若多模块项目无法判断 `subModule`，应在开始前把候选模块写入 `待确认项`，而不是盲跑全仓。

### 执行入口

1. 先确认是在正确的 `projectDir` / `subModuleDir` 执行。
2. 若是某个具体实现任务触发，优先把 `triggerMethod` 写成 `ClassName.methodName` 或 `module:task`，便于后续追踪。
3. 运行四阶段验证前不做修复；修复应回到对应编码 skill。
4. 缺少 Maven、依赖或模块定位信息时，先在输出中显式记录，再决定是否继续。

### 输出回落

- QA 失败时追加 `docs/coding-issues/qa-pending.md`，但这不是最终交付。
- 最终摘要必须回落到 `/team-review`、`/team-release` 或 `/handoff` 的质量结论中。
- 若本次 QA 是 company skill 执行链的一部分，还要同步写入 `领域扩展约束核对结果`。

---

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `projectName` | 项目名（可选，不填时使用当前仓库目录名） | 当前目录 |
| `branch` | 切换分支（可选） | 不切换 |
| `workspaceDir` | 工作区根目录 | 当前工作区 |
| `subModule` | 子模块名或相对路径（可选） | `.` |
| `triggerMethod` | 触发来源（编码场景填 `ClassName.methodName`） | `手动触发` |

派生路径：
- `projectDir = workspaceDir / projectName`
- `subModuleDir = projectDir / subModule`

**可选切换分支**：若提供 `branch` 且非空，先执行 `git checkout <branch>`，失败则终止所有阶段。

脚本示例中的 `<skill_dir>` 指当前安装环境里的 `maven-qa` 技能目录。

---

## Phase 1：编译

```bash
cd <projectDir>
mvn clean install -Dcheckstyle.skip=true -Dpmd.skip=true -Dspotbugs.skip=true
```

- 超时：5 分钟
- **成功**（退出码 0）：记录 `compile: pass`，进入 Phase 2
- **失败**：提取所有 `[ERROR]` 关键行，记录到 [统一遗留文件](#统一遗留文件-qa-pendingmd)，**继续执行 Phase 2**

---

## Phase 2：单测

```bash
cd <subModuleDir>
mvn test
```

- 超时：10 分钟
- 命令完成后（不论退出码）解析报告：

```bash
python3 <skill_dir>/scripts/parse_surefire.py \
  --report-dir <subModuleDir>/target/surefire-reports
```

- **通过**（`success=true`，通过率 >95%）：记录 `test: pass`，进入 Phase 3
- **失败**：将 `failureDetails`（类名、方法名、message）记录到 [统一遗留文件](#统一遗留文件-qa-pendingmd)，**继续执行 Phase 3**
- 报告目录不存在（命令直接崩溃）：记录"单测命令执行失败，无报告"，继续

---

## Phase 3：静态分析

```bash
cd <projectDir>
mvn clean verify
```

- 超时：5 分钟
- 命令完成后解析报告：

```bash
python3 <skill_dir>/scripts/parse_static_analysis.py \
  --report-dir <subModuleDir>/target/static-analysis
```

- **通过**（`criticalIssues == 0`）：记录 `static: pass`，进入 Phase 4
- **失败**：将 `criticalViolations`（PMD）和 `criticalBugs`（SpotBugs）记录到 [统一遗留文件](#统一遗留文件-qa-pendingmd)，**继续执行 Phase 4**
- 代码风格类（命名、注释格式）不属于 critical，不记录

---

## Phase 4：启动检测

```bash
cd <subModuleDir>
mvn spring-boot:run \
  -Dspring-boot.run.jvmArguments=-Dserver.port=<随机端口8081~9079> \
  -Dspring.profiles.active=test
```

- 执行方式：异步，合并 stdout/stderr
- **等待 30 秒**判断结果：
  - 30 秒内进程退出且退出码非 0 → **启动失败**，提取 `APPLICATION FAILED TO START` 或 `BUILD FAILURE` 段落（无则取末尾 60 行），记录到 [统一遗留文件](#统一遗留文件-qa-pendingmd)
  - 30 秒内进程退出且退出码 0 → 视为正常结束，记录 `run: pass`
  - 30 秒后进程仍运行 → 记录 `run: pass`，关闭该进程

---

## 统一遗留文件 `qa-pending.md`

路径：`docs/coding-issues/qa-pending.md`（相对于 `projectDir`）

- 文件不存在时自动创建；已存在时末尾**追加**，禁止覆盖历史

```markdown
## {yyyy-MM-dd HH:mm:ss} | QA 遗留 | {triggerMethod}

**编译**：{pass / 失败摘要}
```
{[ERROR] 关键行列表，无则省略此块}
```

**单测**：{pass / 失败 N 个}
```
- {ClassName}.{methodName} — {message}
```

**静态分析**：{pass / critical N 个}
```
- PMD {规则名} @ {文件}:{行} — {message}
- SpotBugs {type} @ {类名}:{行} — {message}
```

**启动**：{pass / 失败摘要}
```
{失败日志摘要，无则省略此块}
```

---
```

四个阶段全部通过时，**不写入**此文件。

---

## 输出摘要

```
✅/❌ 编译   {pass / 失败 N 个错误}
✅/❌ 单测   {totalTests} 个，通过率 {passRate}%
✅/❌ 静态   总问题 {totalIssues}，critical {criticalIssues}
✅/❌ 启动   {pass / 30s 内异常退出}
```

有遗留问题时补充：`→ 已记录到 docs/coding-issues/qa-pending.md`

---

## Overview

执行编码完成后的四阶段 Maven 质量门禁验证：**编译 → 单测 → 静态分析 → 启动检测**，每阶段失败均记录到 `qa-pending.md` 后继续执行，确保四阶段结果完整收集。

本 skill **只检查，不修复**。问题修复请回到对应编码 skill 处理。
