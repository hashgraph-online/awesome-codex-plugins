---
name: jimeng-dialogue-assistant
description: Use when 核对即梦分镜台词本（阶段一）。对照剧本原文校验一致性。
version: 1.1.0
author: 即梦分镜师工作台
license: MIT
platforms: [windows, linux, macos]
metadata:
  codex:
    tags: [即梦分镜师, 台词本, 校验]
---

# jimeng-dialogue-assistant — 台词本核对（阶段一）

> **工作区根**：Codex 项目根（AGENTS.md 所在目录；下文所有 `scripts/…`、`tools/…`、`config/…` 相对该根，可用环境变量 `JIMENG_ROOT` 显式指定）。

角色：台词助理。
> 先读 `<工作区根>/.codex/memory/<剧名>-dialogue-assistant.md` 身份文件（缺失 → 按派遣契约 abort）。

## 输入
- 剧本原文 `scripts/<剧名>/script/epXX.txt`
- 台词本 `outputs/epXX/epXX-dialogue-list.md`（gen_dialogue_list.py 生成）

## 核对清单
1. 逐字一致性（含语气词、标点、跨物理行折行合并）
2. 完整性（无遗漏）
3. 无改写（禁止概括/省略/同义替换）
4. 角色归属、场景归属

## 识别规则
- 剧本台词格式：`角色（情绪）：台词` 或 `角色：台词`
- 动作描述以 `△` 开头，**不是台词**；`【】` 行为括号标记（闪回等）不是台词
- 跨物理行折行需合并后比对

## 输出
- PASS 或 FAIL + 问题清单（含位置与差异），**不修改台词本文件**
- 返回一行摘要：PASS/FAIL + 问题数
