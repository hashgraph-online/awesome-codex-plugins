---
name: boss:upgrade
description: "更新 Boss Skill 到市场最新版本，并重新合并 hooks。"
allowed-tools: Bash, Read, Write
---

# /boss:upgrade — 更新 Boss Skill

Boss 只通过 skill 市场分发（Claude Code / Codex 插件市场、skills.sh），没有 npm 包。
更新 = 让市场重新拉取仓库；随后用自带 CLI 重新合并 hooks 配置。

## 执行步骤

1. 检查当前安装的版本（读安装副本 `SKILL.md` 的 frontmatter `version:`）
2. 按安装方式更新：
   - Claude Code 插件：`/plugin marketplace update boss-skill`
   - Codex 插件：`codex plugin marketplace upgrade boss-skill`
   - skills.sh：`npx skills update boss`
   - git 安装：在 skill 源仓库 `git pull`
3. 用自带 CLI 重新合并 hooks（Codex 等复制式安装）：`node <skill>/cli/bin/boss.mts install`
4. 显示升级前后的版本和变更摘要

## 用法

```
/boss:upgrade
```

## 执行脚本

```bash
# 解析 skill 根（按常见安装位置；插件安装取 CLAUDE_PLUGIN_ROOT/skill）
SKILL_DIR=""
for d in "${CLAUDE_PLUGIN_ROOT:+$CLAUDE_PLUGIN_ROOT/skill}" ~/.claude/skills/boss ~/.codex/skills/boss ~/.openclaw/skills/boss ~/.hermes/skills/boss .agents/skills/boss; do
  if [ -n "$d" ] && [ -f "$d/SKILL.md" ]; then SKILL_DIR="$d"; break; fi
done
CLI="node $SKILL_DIR/cli/bin/boss.mts"

echo "📦 正在检查当前版本..."
OLD_VERSION=$($CLI --version 2>/dev/null || echo "未知")
echo "  当前版本: $OLD_VERSION"

echo ""
echo "⬆️  请按安装方式更新："
echo "  Claude Code 插件: /plugin marketplace update boss-skill"
echo "  Codex 插件:       codex plugin marketplace upgrade boss-skill"
echo "  skills.sh:        npx skills update boss"

echo ""
echo "🔄 重新合并 hooks..."
$CLI install

NEW_VERSION=$($CLI --version 2>/dev/null || echo "未知")
echo ""
if [ "$OLD_VERSION" = "$NEW_VERSION" ]; then
  echo "✅ 当前已是最新版本 ($NEW_VERSION)"
else
  echo "✅ 已更新: $OLD_VERSION → $NEW_VERSION"
fi
```
