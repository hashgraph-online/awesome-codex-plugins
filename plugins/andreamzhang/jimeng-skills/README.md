# 即梦分镜师 · 完整制片调度流程

这是一个给 **Codex（AGENTS.md 规则 + 六角色子代理）** 使用的完整分镜流程包。
它不是 npm 包，也不是散装技能列表；克隆后直接用 Codex 打开仓库根，Codex 会自动加载 `AGENTS.md`、角色定义和技能。

它也已经按 Codex 插件格式补齐：

```text
.codex-plugin/plugin.json
./.agents/skills/
./assets/logo.svg
```

想从远端安装，可以直接加marketplace：

```powershell
codex plugin marketplace add https://github.com/andreamzhang/jimeng-skills.git
codex plugin add jimeng-skills@jimeng-skills
```

安装后验证插件已被识别：

```powershell
codex plugin list --source jimeng-skills
```

如果列出的插件名不是 `jimeng-skills@jimeng-skills`，用这个全名重试安装。

## 一键上手

```powershell
git clone git@github.com:andreamzhang/jimeng-skills.git
cd jimeng-skills
copy tools\python-path.txt.example tools\python-path.txt
notepad tools\python-path.txt
```

把 `tools\python-path.txt` 内容改成你本机的 Python 绝对路径。之后所有 Python 调用统一走：

```powershell
tools\py.cmd tools\run_all_checks.py "<剧名>" ep01
```

接着在仓库根启动 Codex，并按 `AGENTS.md` 让制片人协调六个子代理。

## 开始一部新剧

```powershell
tools\py.cmd tools\new_drama_memory.py "<剧名>" --dirs
```

这会生成：

```text
scripts/<剧名>/script/
scripts/<剧名>/assets/
scripts/<剧名>/config/
scripts/<剧名>/outputs/
.codex/memory/<剧名>-script-handler.md
.codex/memory/<剧名>-dialogue-assistant.md
.codex/memory/<剧名>-director.md
.codex/memory/<剧名>-art-designer.md
.codex/memory/<剧名>-storyboard-artist.md
.codex/memory/<剧名>-review.md
```

把源稿放进 `scripts/<剧名>/` 后，直接对 Codex 说：

> 用 `AGENTS.md` 的制片人流程，把这部剧本派给拆剧本专家入库拆集。

## 六角色流程

| 阶段 | 执行方 | 主要产物 |
|------|--------|----------|
| 零前 · 剧本入库拆集 | `script-handler` | `script/epXX.txt` |
| 零 · 全局风格 | 制片人主会话 | `config/global-style.md` |
| 一 · 台词本生成/核对 | 制片人脚本 + `dialogue-assistant` | `epXX-dialogue-list.md` |
| 二 · 导演分析 | `director` | `01-director-analysis.md` |
| 三 · 服化道 | `art-designer` | `assets/{character,scene,prop}-prompts.md` |
| 四 · 全景站位 | `storyboard-artist` | `00-panorama-blocking.md` |
| 五 · 分镜要点卡 | 制片人脚本 | `episode-brief.md` |
| 六 · 分镜填写 | `storyboard-artist` | `02-jimeng-prompts.md` |
| 七 · 校验/派生 | 制片人脚本 | `02-jimeng-prompts-clean.txt`、HTML、Excel |
| 八 · 终审 | `review` | `03-final-review.md` |

## 路径口径

- `AGENTS.md` 所在目录 = 项目根。
- 技能：`.agents/skills/<技能名>/SKILL.md`。
- 角色定义：`.codex/agents/*.toml`。
- 身份记忆：`.codex/memory/<剧名>-<role>.md`。
- 剧本与产出：`scripts/<剧名>/...`。
- 校验脚本：`.agents/skills/jimeng-storyboard/scripts/`。

`scripts/` 不进 Git。请不要再把剧本或剧产出推送上去。

## 人物提示词唯一格式

每条人物提示词独立成段，方便直接复制出图，固定为六段：

```text
出图要求：竖屏9:16，纯白背景，上1下3四格排版，分割构图。顶部面板：该角色特写肖像，保持面部特征和发型完全一致。底部面板：三个无头全身人体模特视图并排排列，在颈部截断，没有头部，仅展示服装，从左到右依次为正面、侧面、背面。顶部肖像与底部服装必须是同一角色、同一套服装。
角色信息：<角色名，身份定位，年龄/性别，气质，情节背景>。
面部特征：<脸型，眼型/眉毛/鼻/唇，肤色，发型发色，佩戴物，表情>。
服装细节：上衣为...；下装为...；鞋为...；配饰为...；颜色以...为主；材质为...；图案为...；标志性元素为...。
画质要求：真人实拍质感，高清真人摄影画质，8K超高清，专业影棚柔和无影柔光，均匀漫射光，无强烈硬阴影。画面不能出现3D建模感、CG渲染感、二次元动漫感、手绘插画感、油画感、雕塑感、塑料假肤感；真人实拍必须有真实皮肤次表面散射纹理，可看清毛孔、细小绒毛、轻微肤色不均，但不磨皮不加磨皮滤镜，也不能有肿胀填充面部的网红整容脸。干净商业角色设定图，纯白背景，无文字，无水印，无logo，无杂乱背景。
避免：多余头部、错误人体结构、多手多脚、服装不一致。
```

群像也是“每个角色一段、独立可复制”，不要把多个角色合并到同一段。

## 30s / Seedance 2.5

当前流程只走 **Seedance 2.0 / 常规母镜头链**。
30s 直出链技能与脚本未随分发包携带，当前禁用，不新增、不派遣。

## 常用校验

```powershell
tools\py.cmd tools\run_all_checks.py "<剧名>" ep01
tools\py.cmd tools\finish_ep.py "<剧名>" ep01
```

四道校验全绿后才可进入派生文件生成或下一集。
