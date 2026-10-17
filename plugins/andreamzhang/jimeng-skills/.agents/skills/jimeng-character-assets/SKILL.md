---
name: jimeng-character-assets
description: 给短剧建人物资产库（阶段零点五·即梦分镜师）。
version: 1.2.0
author: 即梦分镜师工作台
license: MIT
platforms: [windows, linux, macos]
metadata:
  codex:
    tags: [短剧, 人物资产, 单图人物提示词, 即梦分镜师]
    related_skills: [jimeng-script-intake, jimeng-art-design]
---

# 短剧人物资产建库（即梦分镜师 · 阶段零点五）

## 使用场景

- 新剧要建 `scripts/<剧名>/assets/character-prompts.md`；或既有剧要补人物/加状态变体。
- 用户说「人物资产跑一下」「按统一口径建人物库」时。

不适用：单集分镜生产（AGENTS.md 阶段一～八）；场景/道具库（同流程，见末节）。

**工作区根**：Codex 项目根（AGENTS.md 所在目录）。所有 `scripts/…`、`tools/…`、`config/…` 相对该根。
**前置**：剧本已拆集（`scripts/<剧名>/script/epXX.txt`）＋ 本剧身份记忆文件存在。

## 输出格式（唯一口径 · 2026-10-09 起生效）

按 `templates/character-entry.md` 输出，每套路人一块，跨集复用同一格式。
关键口径：
1. 出图要求固定为「竖屏9:16，纯白背景，上1下3四格排版，分割构图…」，一字不改。
2. 每位角色一段，不得多人合并到同一段。
3. 面部/服装细节要具体；服装按“款式 + 颜色 + 材质 + 细节”逐件写全。
4. 画质要求固定为“真人实拍质感”那一段，不得换风格。
5. 负面口径统一用「避免：多余头部、错误人体结构、多手多脚、服装不一致」。
6. 严禁重新引入旧版“骨相/锚定句/库路线”等历史口径。

## 建库流程

1. 清点：`python tools/gen_character_inventory.py "<剧名>"` 产出 `assets/_character-inventory.md`。
2. 派美术子代理按 `templates/character-entry.md` 生成各角色提示词，直接写入 `assets/character-prompts.md`。
3. 状态变体在同条目下注明关联与差异，不另起 @名。
4. 合并后逐条核对无关键信息缺失即可，不再跑 face standard 校验。

## 接续

- 场景/道具库同法：`scene-prompts.md`（一个场景一条独立提示词）、`prop-prompts.md`。
- 分镜阶段只准引用资产库里已登记的 `@引用名`，分镜师不得自造。
