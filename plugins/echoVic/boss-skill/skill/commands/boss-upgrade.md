---
name: boss:upgrade
description: "升级 @blade-ai/boss-skill 到最新版本，并重新安装 hooks。"
allowed-tools: Bash, Read, Write
---

# /boss:upgrade — 升级 Boss Skill

升级 `@blade-ai/boss-skill` npm 包到最新版本，并将最新的 hooks 配置同步到当前项目。

## 执行步骤

1. 检查当前安装的版本
2. 运行 `npm update @blade-ai/boss-skill` 升级到最新版
3. 运行 `npx boss-skill install` 重新安装 hooks 到 `.claude/settings.json`
4. 显示升级前后的版本和变更摘要

## 用法

```
/boss:upgrade
```

## 执行脚本

```bash
echo "📦 正在检查当前版本..."
OLD_VERSION=$(node -e "try{console.log(require('@blade-ai/boss-skill/package.json').version)}catch{console.log('未安装')}" 2>/dev/null)
echo "  当前版本: $OLD_VERSION"

echo ""
echo "⬆️  正在升级..."
npm update @blade-ai/boss-skill 2>&1

NEW_VERSION=$(node -e "try{console.log(require('@blade-ai/boss-skill/package.json').version)}catch{console.log('升级失败')}" 2>/dev/null)
echo "  最新版本: $NEW_VERSION"

if [ "$OLD_VERSION" = "$NEW_VERSION" ]; then
  echo ""
  echo "✅ 已是最新版本 ($NEW_VERSION)，无需升级"
else
  echo ""
  echo "🔄 正在同步 hooks..."
  npx boss-skill install
  echo ""
  echo "✅ 升级完成: $OLD_VERSION → $NEW_VERSION"
fi

echo ""
echo "📂 Skill 路径: $(npx boss-skill path)"
```
