---
name: jimeng-script-intake
description: Use when 新剧本入库即梦分镜师工作空间并拆集。
version: 1.1.0
author: 即梦分镜师工作台
license: MIT
platforms: [windows, linux, macos]
metadata:
  codex:
    tags: [短剧, 剧本入库, 拆集, 即梦分镜师]
    related_skills: [jimeng-character-assets, docx]
---

# 短剧剧本入库与拆集（即梦分镜师工作空间）

## When to Use

- 用户丢来一本新剧本（.docx/.txt/.doc/.pdf）说「这是新剧本，放在他应该在的位置」「开始处理这部」。
- 需要在即梦分镜师工作空间新建一部剧的剧本仓库（骨架 + 源稿存档 + 分集 txt）。
- 已入库剧本的场景行/叙述行格式被质疑、或下游脚本报「未命名场景（场景标题缺失）」、终审伪报台词「改写」时（看 `references/script-format-contract.md` 定位是哪条格式规则）。

不适用：已经在跑的剧本单集分镜生产（那是 AGENTS.md 的阶段一～八）。

**工作区根**：Codex 项目根（AGENTS.md 所在目录；所有 `scripts/…`、`tools/…` 相对该根，可用环境变量 `JIMENG_ROOT` 显式指定）。
**权威规则**：工作区根 `AGENTS.md`（阶段零前 / 文件结构 / 硬约束）。本技能只补它没写的操作细节与解析器坑。

## 目标位置（放错＝后续全流程读不到剧本）

```
scripts/<剧名>/
├── <剧名> 1-N.docx         # 源稿存档，原字节不动（既有各剧源稿都放这一层）
├── script/
│   ├── 00-剧本概要.txt      # 剧名 + 人物简表等「第1集」标题之前的前言
│   ├── ep01.txt … epNN.txt  # ★ 分镜全流程唯一读的剧本形态
│   ├── assets/  config/  outputs/
```

`.codex/memory/<剧名>-<role>.md` 五份身份文件必须在首次派子代理前存在，否则子代理按派遣契约 abort。

## 步骤

1. **定剧名**：取剧本首行标题去掉《》或用户给的名字，作为 `scripts/` 目录名（不含《》、标点）。
2. **建骨架＋身份文件**（一条命令）：`python tools/new_drama_memory.py "<剧名>" --dirs`
3. **存档源稿**：把用户上传件原样复制为 `scripts/<剧名>/<剧名> 1-N.docx`（N=总集数），`md5sum` 与上传件比对确认字节一致；不转码、不另存、不改内容。通用的 `剧本(2).docx` 这类文件名要换成「剧名 1-N」再入库。
4. **拆集**：`python tools/split_script_episodes.py "scripts/<剧名>/<剧名> 1-N.docx" --name "<剧名>"`
   产出 `script/ep01.txt …` + `script/00-剧本概要.txt`；重复执行幂等（覆盖同名文件）。
   - **整本多集、纯中文** → 用上面这条。
   - **单集稿 / 中韩对照（双语）稿** → 用 `python tools/docx_script_import.py "<docx路径>" "<剧名>" --ep N`：一次落 `script/epNN.txt`（中文正文）+ `epNN-中韩对照.txt`（双语留档）+ `00-剧本概要.txt` + `_source/` 源稿。**别拿 `split_script_episodes.py` 处理双语稿**：它按行保留韩文，韩文台词会被当成中文台词进台词本与终审对照。
   - 双语稿落库后把 `_source/` 里的源稿按本节约定挪到剧根、命名成 `<剧名> 1-N.docx`（全库一致，换新版时能一键重跑）。
5. **验证**（必做，不要只信脚本自报）：见下节。
6. **报告**：产出清单＋验证数字＋下一步。
   - **阶段零（`config/global-style.md`）**：风格 A-D 选项必须交用户敲定，不得代定；**画幅也必须先问**（短剧默认 9:16 竖屏，别写成 16:9）。用户偏好：**光线从句从简**（写「日间自然光，室内光线柔和」「夜晚，室内以油灯烛火作局部照明」这种粒度，不写光源方向与明暗细节）、**不加角色与面孔强化子句**——面孔铁律/画内文字这类纪律改记在人物资产条目里，不在 config 重复。
   - 人物资产（阶段零点五）走 `jimeng-character-assets` 技能。

## 台词正文一字不改，只做标记类规范化

四项都由 `tools/split_script_episodes.py` 默认完成（`--no-fix` 关闭，仅用于排查）：

1. **场景行**去行首「场」、非断字连字符(U+2010‑2014)统一为 ASCII `-`：`场12‑3 青云宗山门 日 外` → `12-3 青云宗山门 日 外`。
   why：`gen_dialogue_list.is_scene_title()` 要求行首是数字编号；否则整集台词被归入「未命名场景（场景标题缺失）」，而 `check_dialogue` 还会把该场景行并进上一条台词 → 终审伪报「改写」。
2. **无标记叙述行补 `△`**（原稿多数叙述行本来就带 △，属标记不一致）。
   why：`check_dialogue` 把任何无法识别的行并进上一条台词，且空行不重置合并状态 → 台词被污染。
3. **台词后紧贴的【…】行（钩子/字幕）前补空行**。
   why：`gen_dialogue_list` 把紧贴上一句的普通文本行当作台词折行续接。
4. **前言（剧名/人物简表）独立成 `script/00-剧本概要.txt`，绝不并入 ep01**。
   why：人物简表每行都形如 `角色：介绍`，会被解析成 ep01 的台词，污染台词本与终审对照。

## 拆集（整本 → 分集）与人物清点

- 拆集：`python tools/split_script_episodes.py "scripts/<剧名>/<剧名> 1-N.docx" --name "<剧名>"`（章节见下）。
- 人物清点：`python tools/gen_character_inventory.py "<剧名>" --alias assets/_character-aliases.json` —— 阶段零点五 第 1 步，逐集出场表 + 有台词/无台词分列；别名表按剧维护。
  新剧首次清点时最常见的漏项是**「角色名 + 动作描述」的台词行**（`弟子甲厉声反驳：…`、`清月收回手掌面向众人：…`）与**单字序号简写**（`人物：守山弟子甲、乙、丙`），两者不并回角色名就会多出几个幽灵角色，后续分镜 @引用名分裂。

## 验证（两步，都真跑）

- **逐行回环比对**：源稿非空行数 == 写出行数，且序列逐行相等（用 `normalize()` 重算期望序列），只允许上面三类标记差异 —— 证明没有丢字/串行。
- **镜像试跑台词本**：把 `script/ep*.txt` 复制到 scratch 的 `<剧名>/script/` 下，对每集跑 `.agents/skills/jimeng-storyboard/scripts/gen_dialogue_list.py`，然后核对：全部集解析成功、台词总条数 == 源稿独立计数（减去人物简表行数）、0 集出现「未命名场景」、无台词含 `△` 或异常长（>90 字多为被叙述/钩子污染）。
  在 scratch 里跑，别直接生成项目 `outputs/`（那是分镜生产产物）。
  现成片段与解析器契约见 `references/script-format-contract.md`。

## 坑

- **自写 docx 段落抽取正则：用 `<w:t(?:\s[^>]*)?>(.*?)</w:t>`**（`w:t` 后必须是空白或 `>`）。写成 `<w:t[^>]*>` 会连 `<w:textAlignment .../>` 一起匹配，把大段 XML 当成正文抽出来，表现为「剧本里混进了标签」，排查半天。`tools/split_script_episodes.py` 已按前者实现。
- **集号标题与场景行格式两大类都要容错**：正文标题可能是「第N集」或「第N集」（阿拉伯/中文数字），解析器两都收；场景编号可能是 `1-1 地点 日 内`、`场1‑1 …`、`36-1 地点｜午后｜外`，去「场」+连字符统一后都满足「行首数字」契约。
- **native python 读不了 MSYS 的 `/tmp/...`**：`$TMPDIR` 在 bash 里可能展开成 `/tmp/...`，直接传给 python 会 `file not found`。scratch 一律用原生路径 `C:/Users/<user>/AppData/Local/Temp/jimeng-scratch/...`。
- **中韩对照 / 双语稿**：进流水线的 `epXX.txt` 只留中文行，韩文行另存 `epXX-中韩对照.txt`。韩文台词行同样满足 `角色(情绪): 台词` 形态（半角括号与冒号也在正则里），混进 `epXX.txt` 会让台词本与终审对照凭空多出一整套「缺失/改写」。双语档案同时是后续韩国本地化（人名/称谓/物件）的依据。
- **台词本总时长异常（约为合理值的两倍）、且某说话人台词后粘着一整段叙述** = 那段叙述没打 `△`（解析器把无法识别的行并进上一条台词）。入库后先核总秒数与逐条字数，别只看「N 条台词」。
- 逐字校验要**对着源稿算**：把源 docx 抽出的（角色, 台词）序列与 `script/epXX.txt` 的序列**逐对**比较，只有这样才能证明「只加标记、没改一个字」；只比行数证明不了。片段见 `references/script-format-contract.md` §5。
- **别把源稿只留在 `docs/`**：`docs/` 是暂存区，管道只读 `scripts/<剧名>/script/epXX.txt`。
- **不要手改 `script/epXX.txt`** 的台词文字来「修格式」；只加标记（△/空行/场景行前缀），台词逐字是终审硬判据。
- 拆集规则（规范化项）改动后，要在旧剧上跑一次 `tools\py.cmd tools/run_all_checks.py <剧名> epXX` 回归对比。
