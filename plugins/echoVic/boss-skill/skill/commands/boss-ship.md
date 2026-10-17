---
name: boss:ship
description: "只跑部署环节：DevOps 构建部署 + 上线前门禁 + 部署报告。对已通过测试的项目单独可用，产出 deploy-report.md，门禁不可绕过。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:ship — 单环节：构建部署（DevOps）

`/boss:ship` 是 Boss 流水线的**部署环节独立入口**。以 DevOps 身份完成构建、部署、健康检查，运行上线前门禁（Gate 2），产出 `deploy-report.md`。

> 对标 gstack `/ship`。Boss 版本在部署前强制跑 Gate 2（Lighthouse / API P99），门禁不过不宣布上线成功。

## 适合 / 不适合

| 适合 `/boss:ship` | 不适合 |
|-------------------|--------|
| 已过测试、要构建部署 | 还没过 QA（先 `/boss:qa`） |
| 补一份可追溯部署报告 | 只是本地跑一下（直接 `npm run dev`） |

## 执行步骤

1. 读取 `SKILL.md` 不变量与 `references/quality-gate.md`（Gate 2）。
2. 前置检查：确认 `qa-report.md` 存在且 Gate 1 已过（无则提示先跑 `/boss:qa`）。
3. 读取 `agents/boss-devops.md` 与 `skills/devops/deployment-process/SKILL.md`、`skills/devops/monitoring-alerting/SKILL.md`、`skills/devops/changelog-generation/SKILL.md`。
4. 以 DevOps 身份执行构建 + 部署 + 健康检查，产出 `deploy-report.md`（模板 `templates/deploy-report.md.template`）。
5. 运行 Gate 2：`boss runtime evaluate-gates <feature> gate-2`。无 CLI 时按 `references/no-cli-fallback.md` 记录到 STATE.md。
6. 收尾：`boss runtime generate-summary <feature>`。输出：部署 URL、健康检查、门禁结果、changelog。

## 用法

```
/boss:ship                  # 部署当前项目
/boss:ship user-auth        # 部署已有 feature
```

## 选项

| 参数 | 说明 |
|------|------|
| `--lang <zh\|en>` | 部署报告语言（默认 zh） |
