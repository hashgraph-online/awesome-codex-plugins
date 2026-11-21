---
name: kaoyan-setup
description: 建备考工作区和配置文件：第一次用这套考研 skill、或用户说“建一个备考目录”“初始化工作区”“配置考试和科目”“这套 skill 怎么开始用”时使用。问清考试、科目和日期，复制工作区模板（目录结构、AGENTS.md、CLAUDE.md、状态卡、决定、教训表），写好 kaoyan.yaml。其他 kaoyan-* skill 找不到配置文件时也先转到这里。
license: MIT
---

# 建备考工作区（kaoyan-setup）

其他 kaoyan-* skill 都读工作区根目录的 `kaoyan.yaml`：考试日期、科目、收件夹、记录放哪、谁来转录和复判。这个 skill 负责把它建起来。

## 步骤

1. **问清楚，一次问完**（写成选项，用户没说的用默认值）：
   - 考什么、哪天考、阶段复盘定在哪几天（建议每 2–4 周一次，考前一个月以后只在复盘日对表）；
   - 有几科，每科叫什么、要不要写科目代码（可留空）；
   - 工作区放在哪个目录；答卷照片和导出的学习记录平时放在哪（默认“下载”文件夹）；
   - 有没有第二个模型可用（比如装了 Codex CLI）。有就把复判、审稿设成 `codex`，没有就用子代理或 `none`。
2. **演练一遍再写**：先 `--dry-run` 看清单，确认不会覆盖用户已有的文件。
   ```bash
   uv run <本 skill 目录>/scripts/init_workspace.py <工作区> --subject 10_数学 --subject 20_英语 --dry-run
   ```
   没有 uv 就用 `python`（只用标准库）。脚本只新建，不覆盖、不删除。
3. **正式执行**，去掉 `--dry-run`。
4. **改配置**：编辑工作区里的 `kaoyan.yaml`，把第 1 步的答案填进去，替换掉 `<考试名称>` 和 `YYYY-MM-DD` 这些占位符；`subjects` 的 `dir` 要和建出来的文件夹同名，`archive.routes` 每科至少一条。
5. **交代用法**：用三五行告诉用户：资料原件放各科 `A_资料/`（只读）；交卷时把照片放进收件夹，说“交卷”；每次复盘日说“阶段复盘”。

## 已有工作区时

- 用户已有自己的目录结构，不要搬家。只在根目录补一份 `kaoyan.yaml`，把 `subjects.dir`、`records`、`archive.routes` 指向用户现有的文件夹。
- 用户已有 `AGENTS.md` / `CLAUDE.md` 时不覆盖；把模板里“记录分工”“学习证据”“文件规则”三节给用户看，问要不要并进去。

## 子代理

插件安装会带上 `transcriber`、`regrader`、`writer`、`finder` 四个子代理。用 `npx skills add` 只装了 skill 的，这几个子代理不在，各 skill 会这样退回：

- Claude Code：用内置的 general-purpose 子代理，把对应 skill 的 `references/` 里那份任务书全文放进它的提示词。图片和材料照样只进子代理的上下文。
- Codex：用 `codex exec` 另起一个进程跑那份任务书；或者请用户开一个新会话，只给指定的几份材料。

想要固定的子代理，也可以把仓库 `agents/` 下的文件复制到 `~/.claude/agents/` 或项目的 `.claude/agents/`。

## 不做

- 不往工作区里放任何资料原件，不替用户下载教材或真题。
- 不改用户已有的文件；要并进去的内容先给用户看。
