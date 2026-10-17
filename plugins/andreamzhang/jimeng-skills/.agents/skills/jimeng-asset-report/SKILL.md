---
name: jimeng-asset-report
description: Use when 统计资产/做资产表/分析人物/场景/道具。产出暖金主题HTML资产分析报告。
version: 1.1.0
author: 即梦分镜师工作台
license: MIT
platforms: [windows, linux, macos]
metadata:
  codex:
    tags: [即梦分镜师, 资产报告, echarts]
    related_skills: [jimeng-art-design]
---

# 资产分析报告生成技能（Codex 版）

> **工作区根**：Codex 项目根（AGENTS.md 所在目录；下文所有 `scripts/…`、`tools/…`、`config/…` 相对该根，可用环境变量 `JIMENG_ROOT` 显式指定）。
> **技能目录 `${SKILL_DIR}`**：本 SKILL.md 所在目录（`.agents/skills/<技能名>/`）；Codex 加载技能时会给出技能路径。

[触发]
仅用户明确要"统计资产/做资产表/分析人物/分析场景/分析道具/生成资产报告"时执行，不属标准分镜流程。前置：剧本已拆集到 `scripts/[剧名]/script/ep*.txt`。

[选项纪律]
阶段零全局风格必须给用户出 A-D 四个选项（≤4个，用户定稿后才落 config）；所有提问一次最多4个选项，不得自作主张替用户选。

[输出位置]
全部写到 `scripts/[剧名]/assets/`（不是 analysis/——用户纠正过）：
- `master-report.html` 总表（数据卡+四图+跳转卡+分阶段建议）
- `character-report.html` / `scene-report.html` / `prop-report.html`
- `_shared/js/echarts.min.js`（从 `${SKILL_DIR}/assets/_shared/js/` 复制，纯本地无CDN）
- 各报告内引用 `./_shared/js/echarts.min.js` 相对路径

权威源：`${SKILL_DIR}/references/table-template/`（分镜表/资产表 Excel 生成脚本与模板，随技能自带）。本技能覆盖黑道千金项目实操验证过的全部要点。

[数据流程]
1. 全剧本合并通读（不预设正则，先探明格式）——黑道千金格式：场号行`N-M 日/夜 内/外 地点`、人物行`人物：A、B`、对话行`角色（情绪）：台词`
2. 人物：人物行+对话冒号行双通道取并集；归一化：`.→·`、`*（错字）→·`、去 OS/VO/vo 后缀、`被绑女=安洁莉卡`、`手下*/保镖数名/干部若干`归并为群体名；验证一次性角色（杀手×3、童年瑞雯）只出现在人物行不丢失
3. 场景：场号行正则提取，别名合并（庭院角落/凉亭→别墅庭院；酒吧/夜总会/会所大厅→1个；焚化间内外部→1个）；区域分组 8-9 组
4. 道具：全剧通读后定关键词表逐集扫描；关键字叙事道具（渡鸦胎记、白色粉末、试纸）单集确认
5. 分级：核心≥15集/重要5-14/次要2-4/一次性1集/群体（无姓名泛指，不建资产）

[HTML 规范]
- 暖金主题 CSS 变量：`--bg:#faf6f0;--bg2:#f5efe6;--ink:#3c2415;--muted:#8b7355;--rule:#d4c5a9;--accent:#b8860b;--accent2:#6b4423`
- echarts `renderer:'svg'`、`animation:false`、颜色从 CSS 变量取（getComputedStyle）
- 人物卡：等级左边条 + 五要素小传 + EP药丸时间线 + 三阶段叙事 section + 完整清单表
- 场景区：每区「无人空景提示词」盒子 + 场景卡（内外/场次/集数/EP药丸）
- **铁律：pie 数据必须 `{name,value}` 对象数组**——`[[name,v],...]` 二维数组渲染成空图（实测踩坑）；写完用 node stub 实测所有 setOption data points > 0

[代码风格]
写 Python 生成器直接产出 HTML（f-string 内 CSS 双花括号转义）；f-string 表达式内不能有反斜杠——用字符串拼接。文件大时分段 append（整包重写委托子代理会超时败北的教训）。

[快速通道（2026-10-08 起，黑道千金规范版）]
若仓库已带 `tools/gen_asset_report.py`（暖金主题四联报告生成器），**优先直接跑它**，不要现写生成器：
  `tools/py.cmd tools/gen_asset_report.py "<剧名>"` → `master/character/scene/prop-report.html` + `_shared/js/echarts.min.js`
产出后校验：`node tools/check_asset_report.js <四份 report.html>`（echarts 引用/容器/init/data 一致），再用无头 Chrome 截图复核。
组件分层：报告视觉语言严格对标仓库根 `工作台.html`（深色 / 红黑 / 大圆框 / 药丸导航 / hero 卡），不要另起炉灶。
编辑层（人物小传/区域分组/分阶段建议）维护在脚本 `DRAMA_NOTES`；未配置 note 的剧自动降级为纯统计版，手工数据先落到 DRAMA_NOTES 再重跑。
仅当工具缺该剧专属编辑层且用户要求深度小传时，才按 [数据流程] 以子代理/主会话补齐数据后再生成。

[校验清单]
- echarts.init 数 = 图容器 div 数
- 类别块「(N种)」= 完整清单行分组计数逐一相等
- 图表数据条数逐图断言（node stub 跑一遍）
- scene 卡里不得有人物描述（场景名含人名如「唐·莫雷蒂卧室」允许）

[与人物提示词资产的关系]
分镜引用名的唯一来源是 `assets/character-prompts.md`（@引用名条目，art-design-skill 产出），HTML 报告是分析展示层，两者并存互补不替代。
