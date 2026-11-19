---
name: kaoyan-archive
description: 学习记录归档：把从 ChatGPT、Gemini、Codex 等导出到收件夹的学习记录（.md、.txt）按科目和轮次放进备考工作区对应的学习记录目录。用户说“整理学习记录”“归档学习记录”“把下载里的学习记录放好”时使用。脚本先出方案（逐字节查重），模型读每份开头判断科目和轮次，抽查后再执行移动；重复和拿不准的留在原处，不删除。
license: MIT
---

# 学习记录归档（kaoyan-archive）

很多人在别的 AI 里问问题、学章节，再把对话导出成 Markdown。这个 skill 把它们一句话归好位。

开工先读工作区 `kaoyan.yaml`：`inbox`（默认看哪个文件夹）、`archive.routes`（每科、每个轮次放哪）、`archive.log`（日志）。没有配置就转 `kaoyan-setup`。

## 流程

1. **出方案**（不动文件）：
   ```bash
   python <本 skill 目录>/scripts/archive.py scan --inbox <收件夹> --workspace <工作区> --days 3
   ```
   脚本找收件夹里最近 N 天的 .md / .txt，和工作区里已有文件逐字节比对，相同的标 `duplicate`，其余标 `classify`。最后一行是 `PLAN=<plan.json>`。
2. **判断科目和轮次**：对每个 `classify` 项，读文件开头 20 行左右（文件名常看不出科目），按 `archive.routes` 填 `subject`、`stage`、`dest`，把 `action` 改成 `move`。判断不了的改成 `pending`，在 `note` 写原因。份数多时派一个只读子代理（如插件的 `finder`）做这一步，让它交回“文件名 → 科目、轮次、依据（引一行原文）”的表，主会话核过再填。
3. **抽查**：从 `move` 里挑 3–4 份（优先文件名看不出科目的、轮次拿不准的），读开头核对。有错就改那一项。
4. **执行**：
   ```bash
   python <本 skill 目录>/scripts/archive.py apply <plan.json> --log <archive.log 的路径>
   ```
   移动前脚本会确认源文件还在、内容没变、目标在工作区里且没有同名文件；不满足的跳过并说明原因。
5. **汇报**：按科目说放了几份、放在哪；列出重复（和哪份相同，提醒用户自己决定删不删）和待确认（原因）。

## 规则

- 文件名不改。目标目录不存在时自动新建。
- 重复和待确认的文件留在原处，**不删除**；删除让用户自己做。
- 学习记录里如果有别人的隐私（聊天截图里的他人信息等），先问用户再处理，也不要发给外部模型。
- 不归档学习记录以外的文件；收件夹里的照片归 `kaoyan-grading` 处理。
