---
name: ui-designer/design-variants
description: 设计变体模式，产出2-3个设计方案及 tradeoff 分析，供用户选择后确定最终方案
version: 1.0.0
agent: ui-designer
type: workflow
user-invocable: false
agent-invocable: true
dependencies:
  - ui-designer/design-system
triggers:
  - PRD 中明确要求提供多个设计方案对比时
  - 用户显式要求"给几个方案选"或"设计变体"时
  - 设计方向存在明显分歧需要决策时
---

# 设计变体模式

## 适用场景

当设计方向不确定、存在多种合理方案、或用户希望看到不同风格的对比时，启用变体模式。
**不建议在简单功能或设计方向明确时使用**——避免决策疲劳。

## 核心方法

### 步骤 1：变体策略确定

分析 PRD 后确定变体差异维度。常见维度组合：

| 策略 | 维度 | 适用场景 |
|------|------|----------|
| 风格变体 | 简约 vs 丰富 vs 极简 | 品牌/调性不确定 |
| 布局变体 | 单栏 vs 双栏 vs 卡片 | 内容组织方式不确定 |
| 交互变体 | 步骤式 vs 单页式 vs 对话式 | 用户流程不确定 |
| 复杂度变体 | MVP vs 标准 vs 豪华 | 功能范围不确定 |

**原则：每个变体应该有清晰的设计理念差异，而非仅仅是颜色/字体的不同。**

### 步骤 2：变体设计

为每个变体（2-3个）产出：

1. **设计理念**：一句话说明这个方案的核心思路
2. **视觉方案**：基于 design-system 的具体实现
3. **组件选择**：使用哪些组件、如何组合
4. **交互流程**：用户的操作路径
5. **Tradeoff 分析**：优势和劣势

### 步骤 3：对比矩阵

生成结构化对比，帮助用户快速决策：

| 维度 | 方案 A | 方案 B | 方案 C |
|------|--------|--------|--------|
| 视觉复杂度 | 高/中/低 | - | - |
| 开发成本 | X 天 | - | - |
| 用户学习曲线 | 陡/平/无 | - | - |
| 可扩展性 | 高/中/低 | - | - |
| 品牌一致性 | 高/中/低 | - | - |
| 移动端适配 | 优/良/差 | - | - |

### 步骤 4：推荐与等待

1. 给出推荐方案及推荐理由
2. 将变体输出到 `.boss/<feature>/ui-design-variants.json`
3. 设置状态为 `NEEDS_CONTEXT`，等待用户选择
4. 用户选择后，将选中方案写入正式的 `ui-design.json` 和 `ui-spec.md`

## 输出要求

### JSON 产物格式

输出到 `.boss/<feature>/ui-design-variants.json`：

```json
{
  "schemaVersion": "1.0.0",
  "artifact": "ui-design-variants",
  "feature": "<feature-name>",
  "updatedAt": "<ISO-8601>",
  "strategy": "风格变体|布局变体|交互变体|复杂度变体",
  "variants": [
    {
      "variantId": "A",
      "name": "方案A: [名称]",
      "concept": "[一句话设计理念]",
      "tradeoffs": {
        "pros": ["优势1", "优势2", "优势3"],
        "cons": ["劣势1", "劣势2"]
      },
      "designData": {
        "mode": "wireframe",
        "pages": [],
        "components": [],
        "prototype": {},
        "implementationHints": {}
      }
    }
  ],
  "comparison": {
    "dimensions": ["视觉复杂度", "开发成本", "用户学习曲线", "可扩展性", "品牌一致性", "移动端适配"],
    "matrix": [
      {"dimension": "视觉复杂度", "A": "中", "B": "低", "C": "高"}
    ]
  },
  "recommendation": {
    "variantId": "A",
    "reason": "[推荐理由]"
  },
  "selectedVariantId": null
}
```

### 状态报告

```
[BOSS_STATUS]
status: NEEDS_CONTEXT
summary: 已产出 N 个设计变体，等待用户选择最终方案
missing: 用户尚未选择设计方案（方案A/B/C）
[/BOSS_STATUS]
```

### 用户选择后的行为

收到用户选择后：
1. 更新 `ui-design-variants.json` 的 `selectedVariantId` 字段
2. 将选中方案的 `designData` 写入正式 `ui-design.json`
3. 基于选中方案生成完整的 `ui-spec.md`
4. 报告 `DONE` 状态
