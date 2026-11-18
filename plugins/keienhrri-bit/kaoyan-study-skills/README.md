# kaoyan-study-skills

给 Claude Code 和 Codex 用的考研备考 skill：讲题先让你自己做，交卷判分有转录、评分点和一次独立复判，计划只给选项。

[English](README.en.md)

```
/plugin marketplace add keienhrri-bit/kaoyan-study-skills
/plugin install kaoyan-study-skills@kaoyan-study-skills
```

Codex、`gh skill` 和手动安装见 [安装](#安装)。

<img src="docs/img/report-p1.png" width="49%" alt="合成示例报告第 1 页：分数、结论和逐问得分"> <img src="docs/img/report-p2.png" width="49%" alt="合成示例报告第 2 页：错在哪一步、标准解答、评分点">

一共 9 个 skill：讲题、交卷判分、阶段复盘、调计划、学习记录归档、每日资料包、PDF 报告排版、纠错复盘、物理画图讲解。适合几个月的长周期备考，不是考前突击。每个环节都能核对：判分有转录稿、评分点和一次独立复判；数字用脚本重算；计划写成选项，由你来定。

上图是仓库自带的合成示例：一道原创的力学计算题，从布置、交卷、转录、判分、复判到出报告的完整记录，见 [`examples/synthetic-mechanics/`](examples/synthetic-mechanics/)。

---

## 里面有什么

| skill | 做什么 | 什么时候用 |
|---|---|---|
| `kaoyan-setup` | 建备考工作区：目录结构、`AGENTS.md`、`CLAUDE.md`、状态卡、决定表、教训表、配置文件 `kaoyan.yaml` | 第一次用；其他 skill 找不到配置时也会转到这里 |
| `kaoyan-tutor` | 讲题老师：沿知识主线讲，先让你自己做，再指出错在哪一步 | “讲一下这一章”“继续”“我哪里错了” |
| `kaoyan-grading` | 交卷判分：照片 → 转录 → 你本人确认 → 按评分点判分（两种尺度）→ 一次独立复判 → 报告 | “交卷”“批改”“看看我错在哪” |
| `kaoyan-plan` | 阶段复盘和周计划：读状态卡，写两套方向不同的方案，让你选 | “阶段复盘”“明天学什么”“计划要不要调” |
| `kaoyan-archive` | 把从各个 AI 导出的学习记录按科目、轮次归档，先出方案再移动，重复的不删 | “整理学习记录” |
| `kaoyan-daily-pack` | 给政治这类“背诵 + 选择题”科目出当天的资料包和提示词，交给任意聊天 AI 带学 | “出明天的资料包” |
| `kaoyan-report` | Markdown → PDF 的固定排版，构建后自动检查公式有没有渲染、有没有空白页、有没有内容超出版心 | “出个报告”“出 PDF” |
| `kaoyan-retro` | 纠错复盘：AI 出错后找根因、记一条教训、提议最小改动，你批准才改 | “复盘”“为什么又错了” |
| `physics-svg-tutor` | 物理画图讲几何：用 SVG 示意图讲装置、角度、光路，例子以光学干涉为主 | “画图讲清楚”“这个角是相对谁的” |

另有 4 个子代理定义（在 `agents/`，Claude Code 插件安装时自动带上）：

| 子代理 | 做什么 |
|---|---|
| `transcriber` | 一页答卷照片转成文字稿和公式核对表，不解题、不判对错 |
| `regrader` | 只拿题面、转录稿和评分点做一次独立复判，看不到主会话的分数 |
| `writer` | 照大纲和核过的数字写长讲义、长报告，不改数字 |
| `finder` | 只读地在工作区里找文件、抽原文片段 |

---

## 安装

任选一种。

**Claude Code 插件**（skill 和子代理一起装）：

```
/plugin marketplace add keienhrri-bit/kaoyan-study-skills
/plugin install kaoyan-study-skills@kaoyan-study-skills
```

**Codex 插件**：

```bash
codex plugin marketplace add keienhrri-bit/kaoyan-study-skills
codex plugin add kaoyan-study-skills@kaoyan-study-skills
```

`agents/` 里是 Claude Code 的子代理定义。在 Codex 里，转录和复判用 `codex exec` 另起进程跑，`kaoyan-grading` 里写了命令。

**只装 skill**，用 GitHub CLI 的 `gh skill`（预览功能，用 gh 2.101 测过）：

```bash
gh skill install keienhrri-bit/kaoyan-study-skills --all --agent claude-code --scope user
```

`--agent` 也可以写 `codex` 等；`--scope project` 装进当前项目。或者用 [skills.sh](https://skills.sh) 的命令行（这条作者没有实测过）：

```bash
npx skills add keienhrri-bit/kaoyan-study-skills
```

这两种方式不带子代理，各 skill 会退回用内置的通用子代理，把对应的任务书全文放进提示词。

**手动**：把 `skills/` 下的目录复制到 `~/.claude/skills/`（或项目的 `.claude/skills/`）；想要子代理，再把 `agents/*.md` 复制到 `~/.claude/agents/`。

### 依赖

- Python 3.10 以上。脚本大多只用标准库；`kaoyan-report` 要 `pypdf`、`pypdfium2`、`pillow`，脚本头里写了依赖，用 [uv](https://docs.astral.sh/uv/) 运行时会自动装。
- `kaoyan-report` 还要 [pandoc](https://pandoc.org/installing.html) 和一个 Chromium 系浏览器（Chrome、Edge 或 Chromium）。找不到浏览器时用 `--chrome <路径>` 或环境变量 `KAOYAN_CHROME` 指定。
- 公式用 KaTeX 0.16.22，已经随仓库打包，不联网。

---

## 开始用

1. 在 Claude Code（或 Codex）里说：“用 kaoyan-setup 帮我建一个备考工作区。”它会一次问清考什么、哪天考、几科、复盘日定在哪几天、答卷照片放在哪，然后先演练再建目录：

   ```bash
   uv run skills/kaoyan-setup/scripts/init_workspace.py <工作区> --subject 10_数学 --subject 20_英语 --dry-run
   ```

   脚本只新建文件，不覆盖、不删除。已有自己的目录结构的，只补一份 `kaoyan.yaml`，指向现有文件夹。

2. 平时这样说：

   | 你说 | 走哪个 skill |
   |---|---|
   | “讲一下 XX 这一节”“继续” | `kaoyan-tutor` |
   | 把答卷照片放进收件夹，说“交卷” | `kaoyan-grading` |
   | “整理学习记录” | `kaoyan-archive` |
   | “出明天政治的资料包” | `kaoyan-daily-pack` |
   | 到了复盘日，说“阶段复盘” | `kaoyan-plan` |
   | “出个 PDF” | `kaoyan-report` |
   | AI 讲错或判错了，说“复盘” | `kaoyan-retro` |

工作区长这样（科目名和编号在 `kaoyan.yaml` 里改）：

```
备考/
├── kaoyan.yaml            所有 skill 先读它：考试日期、复盘日、科目、收件夹、谁来转录和复判
├── AGENTS.md / CLAUDE.md  给 AI 的规矩：学习证据怎么记、文件不永久删除
├── 00_总控/               状态卡、决定、每日进度
├── 10_数学/               每科一个：A_资料（只读）、B_学习记录、C_试卷与批改、D_讲义与报告、学习日志.md
├── …
└── 99_整理记录/           变更记录、教训表、归档日志、隔离区
```

---

## 交卷判分怎么走

这是套件里最完整的一条流水线，每一步都留下能核对的文件：

| 步 | 谁做 | 做什么 | 留下什么 |
|---|---|---|---|
| 0 | 主会话 | 在收件夹里挑出这次交卷的照片，列给你确认，复制进任务目录 | `img/`、`exam.md` |
| 1a | 转录者 | 一页一单，把照片原样转成文字，另交公式核对表；看不清的写〔?〕 | 每页一份转录稿 |
| 1b | 主会话 | 转录在跑的同时写标准解答和评分点，用 SymPy 重算每问的答案 | `solution.md`、核对脚本 |
| 2 | 主会话 | 只读转录稿。〔?〕和“把握低”的地方先问你本人，再按正常、宽松两种尺度判分 | `grading.md` |
| 3 | 复判者 | 只拿题面、转录稿、评分点，独立再判一次，另列评分点本身的问题 | 两张分数表 + 问题清单 |
| 4 | 主会话 | 逐条决定采不采复判意见，写出“错在哪一步”，出报告 | 解析集、PDF |

转录者和复判者可以是 Claude Code 子代理，也可以是另一家模型（比如 Codex CLI），在 `kaoyan.yaml` 的 `roles` 里选；没有外援就全部在主会话里做。

两种尺度的差，说明丢的分里有多少是“过程不全、前错后连”，有多少是真正的知识缺口。

---

## 方法

这些规矩写在各个 skill 和工作区模板里，换别的工具也能照着用：

1. **先让学生自己做，再指出错在哪一步。** 布置了练习就等你作答；评价时先说哪里对，再定位到具体哪一步错、为什么错。
2. **讲解给推导和依据。** 每一步说明凭什么成立，不用“显然可得”跳过关键环节。
3. **讲过不等于会。** 学习证据只记五类：独立首答、提示后作答、订正后独立复做、仅阅读解析、听讲讨论。听懂了、看过解析，都不登记为掌握。
4. **照片不进主会话。** 答卷照片交给转录者，主会话只读文字稿；看不清的地方先问本人，不猜着判。
5. **外援的文字不进成稿。** 转录者、复判者和其他模型只交转录稿、问题清单和独立算出的数字；给你看的成稿由主会话写。唯一的例外是约 5000 字以上、不需要新推导的长讲义或手册：主会话备好大纲、底稿和核过的数字，交 `writer` 子代理照着写，写完主会话核数字、查〔待核〕、看版面机检再交付。不想要这个例外，把 `kaoyan.yaml` 的 `roles.long_writer` 设成 `main`。
6. **一份成稿只审一次。** 复判和审稿都只做一次，复判者看不到主会话的分数。
7. **数字用脚本核，不靠再问一个模型。** 答案用 SymPy 重算；资料包里“讲义原话”用脚本回讲义逐字查；报告里同一个数全文一致。
8. **计划给选项，不替你定。** 涉及时间分配的地方写成“推荐 / 另一种”；计划没完成只照实记，不催。
9. **纠错先记一条，第二次才立规则。** 能用脚本或测试挡住的，不写成给模型看的规则；改任何规则都要你批准。
10. **会话很长了就写交接、开新会话。** 长会话里每一步都要把整个上下文重读一遍。
11. **不永久删除文件。** 要去掉的先移到隔离区，每次新建、移动、修改都记一行变更和撤销方法。

---

## 和其他备考 skill 的区别

| 项目 | star（2026-11-16，GitHub API） | 侧重 |
|---|---|---|
| [ZeKaiNie/universal-examprep-skill](https://github.com/ZeKaiNie/universal-examprep-skill) | 390 | 期末突击：按课件讲、带页码引用、错题本、小抄 |
| [KaguraNanaga/kaogong-study-tracker](https://github.com/KaguraNanaga/kaogong-study-tracker) | 342 | 考公错题整理和定时总结 |
| [2362094903-ops/study-assistant-skills](https://github.com/2362094903-ops/study-assistant-skills) | 39 | 按教材章节学习：讲义、真题风格卷、错题本、掌握度 |
| [Treasoni/kaoyan_skills](https://github.com/Treasoni/kaoyan_skills) | 24 | 考研学习和知识管理的技能集合 |

本仓库的侧重：几个月的长周期（讲题 → 交卷判分 → 阶段复盘 → 调计划 → 记录归档），以及一条每步留档、能核对的批改流水线（转录 → 本人确认 → 按评分点判分 → 独立复判）。侧重一栏取自各仓库自己的简介。

---

## 合成示例

[`examples/synthetic-mechanics/`](examples/synthetic-mechanics/) 里是一道原创的斜面加弹性碰撞计算题，不来自任何真题或教材：

| 文件 | 是什么 |
|---|---|
| `exam.md` | 题面，三问 15 分 |
| `tutor-assign.md` | 讲完一个单元后布置这道题（合成对话） |
| `transcript.md` | 转录稿，含一处看不清的〔?〕 |
| `solution.md` | 标准解答和评分点 |
| `check_answers.py` | 用 SymPy 重算三问答案，并核对 `solution.md` 里写的一致 |
| `grading.md` | 两种尺度的判分表和错因代号 |
| `regrade_task.md`、`regrade_result.md` | 复判任务书和复判回报 |
| `report.md`、`report.pdf` | 报告源文件和构建出的 PDF |
| `tutor-correct.md` | 看完报告后订正第 3 问（合成对话） |

自己构建一次：

```bash
uv run skills/kaoyan-report/scripts/build_report.py examples/synthetic-mechanics/report.md out/report.pdf "斜面—碰撞综合题答卷分析" "合成示例" examples/synthetic-mechanics/figs.py --strict
```

最后一行是版面机检结果：`unrendered_math`、`blank_pages`、`overflow`、`missing_images` 都为空就算合格。构建目录是输出 PDF 旁边的 `_build/`；每次构建的浏览器临时配置放在其中单独的子目录里，构建完自动删掉。

---

## 隐私

- 工作区里的教材、真题、讲义原件放在各科 `A_资料/`，工作区模板的规矩是不上传 GitHub 或任何公开网站。
- `tools/privacy_scan.py` 是发布前用的扫描脚本：查邮箱、手机号、本机用户路径、常见 token、像真实成绩的分数写法和 git 提交作者。个人的词（姓名、院校等）写在不提交的 `.work/privacy-extra.txt` 里，一行一个正则。你 fork 之后放自己的东西进来，也可以先跑一遍：

  ```bash
  python tools/privacy_scan.py
  ```

---

## 开发和测试

```bash
uv venv
uv pip install -r requirements-lock.txt
uv run pytest -q
```

`requirements-lock.txt` 是 `requirements-dev.txt` 锁定版本后的结果（`uv pip compile --universal --python-version 3.10 requirements-dev.txt -o requirements-lock.txt`），CI 用它安装。

测试包括：skill 和插件清单的格式、归档和建工作区脚本、句子打标、示例答案核对、隐私扫描，以及用合成示例真跑一次 PDF 构建（没有 pandoc 或浏览器时跳过）。GitHub Actions 在 Ubuntu 和 Windows 上跑同样的测试和隐私扫描。

---

## 限制

- 没有评测过照片转录的准确率。仓库里只有合成示例，没有真实手写答卷；转录质量取决于你用的模型和照片清晰度，所以流水线要求看不清的地方先问本人。
- 本地只在 Windows 11 上实际跑过（Python 3.12、pandoc 3.12.1、Chrome）；CI 覆盖 Ubuntu 和 Windows，没有测过 macOS。
- `kaoyan-daily-pack` 不提供任何讲义或题目，资料要用你自己合法拥有的。
- `physics-svg-tutor` 的案例库和示范图以光学干涉为主。
- skill 只规定流程，考试内容以你的教材和考纲为准。

## 许可证

MIT，见 [LICENSE](LICENSE)。随仓库打包的 KaTeX 也是 MIT 许可证，见 `skills/kaoyan-report/assets/katex/LICENSE`。
