---
name: jimeng-html-view
description: HTML 视图生成技能。将即梦分镜提示词（02-jimeng-prompts.md）转换为视觉增强的 HTML 阅读版。作为标准流程步骤，在生成 clean.txt 后自动执行。
version: 1.1.0
author: 即梦分镜师工作台
license: MIT
platforms: [windows, linux, macos]
metadata:
  codex:
    tags: [即梦分镜师, HTML视图, 派生文件]
    related_skills: [jimeng-storyboard]
---

# HTML 视图生成技能

> **工作区根**：Codex 项目根（AGENTS.md 所在目录；下文所有 `scripts/…`、`tools/…`、`config/…` 相对该根，可用环境变量 `JIMENG_ROOT` 显式指定）。
> **技能目录 `${SKILL_DIR}`**：本 SKILL.md 所在目录（`.agents/skills/<技能名>/`）；Codex 加载技能时会给出技能路径。

[技能说明]
    将即梦分镜提示词（02-jimeng-prompts.md）转换为视觉增强的 HTML 阅读版（02-jimeng-prompts-view.html）。

    本技能是**标准流程步骤**，在阶段七 第六步（生成 clean.txt）之后立即执行，
    与 clean.txt 同属最终输出环节。每次生成分镜时都会执行，无需用户单独触发。

    本技能同时负责**剧级档案视图**：将 config/global-style.md 转换为与
    工作台.html 同主题（深色 #141414 底 + #e5484d 红点缀 + 点阵背景）的
    global-style-view.html。阶段零（全局风格与制片批注）定稿落盘后执行；
    批注修改后重跑。成片文案区的固定头与光线从句带一键复制按钮。

    生成的 HTML 文件提供：
    - 浅色高对比度主题，字色清晰易读
    - 7字段色彩标签区分（景别=蓝, 运镜=紫, 机位=青, 画面=红, 微表情=橙, 台词=绿, 音效=灰）
    - 台词深绿加粗高亮，@角色名深蓝加粗
    - 每个子镜头带一键复制按钮（复制纯文本7字段）
    - 每个母镜头带"复制全部"按钮
    - 左侧窄导航栏（190px）：母镜头跳转列表 + 每项独立复制按钮，☰ 可收起/展开
    - 侧边栏视图切换器：分镜视图 / 全景站位 Tab 切换，切换时侧边栏导航列表同步切换
    - 全景站位视图：信息卡片 + 可点击时间轴条 + 镜头卡片，带"复制全部"和单镜头复制按钮
    - 纯前端，无外部依赖

[文件架构]
    输入路径：
    - 即梦分镜提示词：scripts/[剧本名]/outputs/epXX/02-jimeng-prompts.md
    - 全景站位分镜（可选，自动检测同目录）：scripts/[剧本名]/outputs/epXX/00-panorama-blocking.md
    - 剧级档案（阶段零视图用）：scripts/[剧本名]/config/global-style.md

    输出路径：
    - HTML 视图版：scripts/[剧本名]/outputs/epXX/02-jimeng-prompts-view.html
    - 剧级档案视图：scripts/[剧本名]/config/global-style-view.html

    脚本路径（随技能自带，加载时 ${SKILL_DIR} 替换为技能目录绝对路径）：
    - ${SKILL_DIR}/scripts/gen_html_view.py
    - ${SKILL_DIR}/scripts/gen_global_style_html.py（剧级档案视图）

[执行流程]

    第一步：确认前置条件
        - 确认 02-jimeng-prompts.md 已存在且通过时长校验和画面字段校验
        - 确认 02-jimeng-prompts-clean.txt 已生成（HTML 生成在 clean.txt 之后）

    第二步：运行生成脚本
        python ${SKILL_DIR}/scripts/gen_html_view.py scripts/[剧本名]/outputs/epXX/02-jimeng-prompts.md

        可选传入全景站位文件（不传则自动检测同目录下的 00-panorama-blocking.md）：
        python ${SKILL_DIR}/scripts/gen_html_view.py scripts/[剧本名]/outputs/epXX/02-jimeng-prompts.md scripts/[剧本名]/outputs/epXX/00-panorama-blocking.md

        脚本会：
        1. 解析 02-jimeng-prompts.md，提取标题、素材对应表、母镜头、子镜头结构
        2. 为每个子镜头提取7个字段内容
        3. 生成色彩标签化的 HTML 卡片
        4. 为每个子镜头、母镜头、左侧导航项生成 base64 编码的复制文本
        5. 生成左侧窄导航栏（母镜头跳转 + 每项复制按钮）
        6. 若检测到 00-panorama-blocking.md，解析全景站位数据，生成全景站位视图
        7. 在侧边栏头部下方添加视图切换器（分镜视图 / 全景站位），切换时同步切换导航列表和内容区
        8. 全景站位视图包含：信息卡片（场景/人物/时长 + 复制全部按钮）、可点击时间轴条、镜头卡片（带单镜头复制按钮）
        9. 输出 02-jimeng-prompts-view.html 到同目录

    第三步：验证输出
        - 确认 HTML 文件已生成
        - 确认文件大小 > 0
        - 向用户展示文件链接

[剧级档案视图（global-style-view.html）]
    用法：python ${SKILL_DIR}/scripts/gen_global_style_html.py <global-style.md路径>

    脚本会：
    1. 解析 global-style.md 的标题、五段式分节（风格类型/通用设定/成片文案/制片批注/备注）
    2. 按 H3/H4 拆卡片，列表/引用/段落按工作台样式渲染（水平线自动跳过）
    3. 「三、成片文案」区内所有文本块（固定头、光线从句）附一键复制（原始文本，base64 传递）
    4. 输出 global-style-view.html 到 config/ 同目录

    样式主题：深色工作台同款（--bg:#141414 / --panel:#1c1c1c / --acc:#e5484d），
    圆角卡片、点阵背景、响应式。

[HTML 样式规范]

    主题：浅色高对比度
    - 页面背景：#f1f5f9
    - 正文颜色：#1a1a1a
    - 字体：Noto Sans CJK SC, Microsoft YaHei, PingFang SC
    - 行高：1.7

    7字段色彩配置：
    | 字段 | 标签背景 | 内容背景 | 图标 |
    |------|----------|----------|------|
    | 景别 | #1e40af（蓝） | #eff6ff | 📷 |
    | 运镜 | #6d28d9（紫） | #f5f3ff | 🎬 |
    | 机位 | #0f766e（青） | #f0fdfa | 🎯 |
    | 画面 | #b91c1c（红） | #fef2f2 | 🖼️ |
    | 微表情 | #c2410c（橙） | #fff7ed | 😐 |
    | 台词 | #15803d（绿） | #f0fdf4 | 💬 |
    | 音效 | #4b5563（灰） | #f9fafb | 🔊 |

    特殊元素高亮：
    - @角色名：深蓝加粗（#1d4ed8）
    - 台词内容「」：深绿加粗（#15803d）
    - 情绪标签（）：橙色（#c2410c）

    场景类型颜色：
    | 场景类型 | 颜色 |
    |----------|------|
    | 对话场景 | #1e40af |
    | 动作场景 | #b91c1c |
    | 情绪场景 | #6d28d9 |
    | 揭示场景 | #c2410c |
    | 过渡场景 | #4b5563 |

    布局特性：
    - 左侧固定导航栏（190px 窄栏，占竖向空间）：
      - 视图切换器（分镜视图 / 全景站位两个按钮，切换时同步导航列表和内容区）
      - 分镜视图导航：每个母镜头一项，编号+时长一行、标题一行，色条标识场景类型，带独立 📋 复制按钮
      - 全景站位导航：顶部"全景"总项（整集调度关系，带 📋 复制全部按钮），下方按时间片段列出各镜头导航项（镜头1 0-3秒、镜头2 3-6秒…），每项可点击跳转到对应镜头卡片，带独立 📋 复制按钮，子项缩进+浅色边条区分层级
      - ☰ 按钮收起/展开导航栏（在顶部标题栏下方，top:92px）
      - 移动端（<768px）默认收起
    - 顶部粘性标题栏（含标题 + 素材引用标签，低调灰色显示）
    - 锚点跳转偏移：html 设 scroll-padding-top:110px，避免标题栏遮挡母镜头标题
    - 统计栏（母镜头数 / 子镜头数 / 总时长）
    - 母镜头卡片：场景类型色条 + 标题 + 时长徽章 + 复制全部按钮
    - 分镜过渡：紫色标签 + 过渡文本
    - 全局风格设定：可折叠（<details>）
    - 资产声明行：等宽字体显示，| 分隔符高亮
    - 子镜头卡片：编号 + 时长 + 复制按钮 + 7字段网格
    - 全景站位视图：信息卡片（场景/人物/时长 + 复制全部）、可点击时间轴条（按时间段等分）、镜头卡片（时间徽章+景别+时长+复制按钮+人物站位+画面描述）
    - 响应式：768px 以下自适应

    复制功能：
    - 使用 base64 编码传递文本，避免引号/换行转义问题
    - JS 端用 atob() + TextDecoder 解码 UTF-8 中文
    - 优先使用 navigator.clipboard API，降级到 execCommand

[字段格式化策略]
    - 台词：不分行，高亮角色名和台词内容
    - 画面：按 @ 标记分行，每段是一个完整的视觉描述
    - 音效：按 ] 分行，每个声音类别独占一行
    - 其他字段（景别/运镜/机位/微表情）：不分行，只高亮 @引用

[约束]
    - 不修改 02-jimeng-prompts.md 原文件
    - HTML 文件输出到与 md 文件相同的目录
    - 纯前端 HTML，无外部依赖（无 CDN、无 JS 库）
    - 资产声明行必须完整显示人物、场景、道具信息（正则用 [^\n]+ 匹配到行尾）
