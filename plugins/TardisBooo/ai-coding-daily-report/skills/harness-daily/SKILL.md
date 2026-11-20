---
name: harness-daily
description: >
  将本机 AI 编码会话汇总为 Markdown 日报。用于用户明确要求收集、预览或生成编码日报。
argument-hint: "[--date YYYY-MM-DD] [--backfill N]"
---

# AI 编程日报

先检查本机 `harness-daily --version`。如果缺少程序，请让用户按
[校验发布包的安装步骤](https://github.com/TardisBooo/ai-coding-daily-report/blob/main/docs/install.zh-CN.md#安装二进制) 安装。
首次配置时，确认写作 CLI 和输出目录，再运行 `harness-daily init --host <已选 CLI> --out "<日报目录>"` 和
`harness-daily doctor`。已有配置时，只在用户要求修改时重新初始化。

普通报告会把日期、项目名、项目路径和提问片段交给选定的写作 CLI。每个项目最多 12 条，每条最多
180 字符。该 CLI 可能把这些字段发给已配置的模型服务。用户只要求检查采集结果时，使用 `--dry-collect`。

## 生成昨天的日报

```bash
harness-daily report
```

指定日期：

```bash
harness-daily report --date YYYY-MM-DD
```

只采集不调用模型（调试）：

```bash
harness-daily report --date YYYY-MM-DD --dry-collect
```

## 定时生成

仅当用户要求自动生成日报时，再登记定时任务：

```bash
harness-daily schedule install --time 08:00
```

## 规则

- 「今日工作总结」只按项目写工作内容，不要写工具名和时间。
- 同一项目下各 harness / session 的提问要合并。
- 定时任务走操作系统，不依赖当前会话是否开着。
