---

name: ui-designer/design-system
description: 设计系统方法论，基于 Refactoring UI、Material Design 3、HIG、Laws of UX、WCAG 等开源设计原则，指导如何建立有设计方向、可落地的设计令牌体系
version: 2.0.0
agent: ui-designer
type: methodology
user-invocable: false
agent-invocable: true
dependencies: []
triggers:
- 开始UI设计时
- 需要定义视觉规范时
- 确保设计一致性时
  metadata:
  internal: true
  references:
  - "Refactoring UI (Steve Schoger & Adam Wathan): https://www.refactoringui.com/"
  - "Material Design 3: https://m3.material.io/"
  - "Apple Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines/"
  - "Laws of UX (Jon Yablonski): https://lawsofux.com/"
  - "Ant Design: https://ant.design/docs/spec/introduce"
  - "Carbon Design System (IBM): https://carbondesignsystem.com/"
  - "WCAG 2.1: https://www.w3.org/WAI/WCAG21/quickref/"

---

# 设计系统方法论

## 适用场景

在开始具体的页面和组件设计前，先建立统一的设计系统。本方法论不提供「一套固定的默认值」，而是教你**如何根据产品定位做出设计决策**，并将决策物化为可复用的设计令牌。

## 设计思维基础

### 核心原则（来自 Refactoring UI）

设计不是把内容塞进布局里，而是**用视觉手段引导用户注意力**。记住以下原则：
1. **从功能出发，不从布局出发** — 先想清楚用户要完成什么任务，再决定界面怎么排布。不要上来就画三栏布局。
2. **先灰阶，后上色** — 先用灰度建立层次和对比度，确认信息架构没问题后再引入颜色。颜色是锦上添花，不是救命稻草。
3. **字号不超过 3 种** — 正文、小标题、大标题。更多字号只会造成混乱，用字重和颜色来区分层次。
4. **颜色不超过 2-3 种** — 一种主色 + 一种强调色已足够。语义色（成功/警告/错误）不算在内。
5. **留白是设计元素** — 空白不是「没填满」，而是呼吸感和层次感的来源。不要害怕留白。
6. **用对比建立层次** — 重要的东西更大、更粗、更亮；不重要的东西更小、更浅、更灰。
7. **一致性 > 完美** — 一处不完美但全产品一致，胜过每处都「最优」但风格不一。

### 设计方向决策

在定义令牌之前，先确定产品的**设计人格**。回答以下问题：

| 维度     | 选项                                           | 决策依据                |
| -------- | ---------------------------------------------- | ----------------------- |
| **调性** | 专业 / 亲和 / 活力 / 极简                      | 目标用户群体 + 品牌定位 |
| **密度** | 紧凑（数据密集型）/ 舒适（消费级）             | 用户使用时长 + 信息密度 |
| **圆角** | 直角（严谨）/ 中圆角（友好）/ 大圆角（童趣）   | 品牌调性                |
| **阴影** | 无阴影（扁平）/ 轻阴影（层次）/ 重阴影（拟物） | 设计风格                |
| **动效** | 克制（专业工具）/ 适度（通用）/ 丰富（娱乐）   | 产品类型                |

**参考**：Material Design 3 提供了「风格表达」（Expressive / Functional）的二元模型；HIG 强调「清晰、遵从、深度」三原则。

---

## 颜色系统

### 颜色理论基础

- **主色（Primary）**：代表品牌，用于主要操作和关键元素。选择时考虑品牌联想（蓝=信任，绿=成长，橙=活力）。
- **强调色（Accent）**：可选，用于次要强调。通常是主色的互补色或相邻色。
- **中性色（Neutral）**：文字、背景、边框。是层次的主要载体。
- **语义色（Semantic）**：成功（绿）、警告（橙）、错误（红）、信息（蓝）。必须与主色区分开。

### 如何选择主色

1. 从品牌色出发，若无品牌色则根据产品调性选择
2. 确保主色在浅色和深色背景上都有足够对比度
3. 生成主色的色阶（50-900），用于悬停、按下等状态
4. **参考**：Material Design 3 的「Color Roles」模型将颜色分为 primary、secondary、tertiary、error 四类角色，每类都有 on-* 变体（用于文字）

### 色阶生成

主色阶（以 Primary 为例）：

| Token         | 用途         | 生成方法      |
| ------------- | ------------ | ------------- |
| `primary-50`  | 极浅背景     | 主色 + 95% 白 |
| `primary-100` | 浅背景、标签 | 主色 + 85% 白 |
| `primary-200` | 边框、禁用   | 主色 + 70% 白 |
| `primary-300` | 次强调       | 主色 + 50% 白 |
| `primary-400` | 悬停态       | 主色 + 25% 白 |
| `primary-500` | **基础主色** | 选定的品牌色  |
| `primary-600` | 按下态       | 主色 + 15% 黑 |
| `primary-700` | 深色背景上   | 主色 + 30% 黑 |
| `primary-800` | 极深         | 主色 + 45% 黑 |
| `primary-900` | 最深         | 主色 + 60% 黑 |

> **工具**：可使用 [Material Theme Builder](https://m3.material.io/theme-builder) 或 [coolors.co](https://coolors.co/) 生成色阶。

### 中性色系

不要用纯灰（#808080）。在中性灰中混入主色相，让整体色调更统一。

| Token         | 用途               |
| ------------- | ------------------ |
| `neutral-50`  | 页面背景           |
| `neutral-100` | 卡片悬浮背景、悬停 |
| `neutral-200` | 浅边框、分割线     |
| `neutral-300` | 边框               |
| `neutral-400` | 占位文字、禁用     |
| `neutral-500` | 辅助文字           |
| `neutral-600` | 次要文字           |
| `neutral-700` | 正文文字           |
| `neutral-800` | 重要文字、标题     |
| `neutral-900` | 大标题、强调文字   |

### 语义色

| Token     | 色值范围               | 用途           |
| --------- | ---------------------- | -------------- |
| `success` | 绿色系（#10B981 附近） | 成功状态、通过 |
| `warning` | 橙色系（#F59E0B 附近） | 警告、需注意   |
| `error`   | 红色系（#EF4444 附近） | 错误、危险操作 |
| `info`    | 蓝色系（#3B82F6 附近） | 信息提示       |

每个语义色都应有对应的浅色背景变体（用于 toast、badge 背景）和深色文字变体。

### 无障碍要求（WCAG 2.1）

- **正文文字**：对比度 ≥ 4.5:1（AA 级）
- **大字号文字**（≥ 18pt 或 ≥ 14pt bold）：对比度 ≥ 3:1
- **UI 组件和图形对象**：对比度 ≥ 3:1
- **不要仅靠颜色传达信息** — 必须同时使用图标、文字或形状
- **色盲友好**：避免红绿组合作为唯一区分手段

> **验证工具**：[WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

---

## 字体系统

### 字体选择原则

1. **可读性优先** — 正文用无衬线体（sans-serif），代码用等宽体（monospace）
2. **字体族不超过 2 种** — 一种无衬线 + 一种等宽。标题和正文用同一字体族，通过字重区分
3. **系统字体优先** — 使用平台原生字体栈，加载快、体验好
4. **参考**：HIG 推荐 SF Pro；Material Design 推荐 Roboto；中文场景推荐 PingFang SC / Noto Sans SC

### 字体栈

```css
--font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
             "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
--font-mono: "SF Mono", "JetBrains Mono", "Fira Code", "Cascadia Code",
             "Roboto Mono", Menlo, Monaco, "Courier New", monospace;
```

### 字号阶梯（Type Scale）

使用**模块化比例**（Modular Scale）生成字号，而非随意取值。推荐比例：
- **1.250（Major Third）**：保守、专业，适合工具类产品
- **1.333（Perfect Fourth）**：平衡，适合大多数产品
- **1.500（Perfect Fifth）**：大胆、有冲击力，适合营销页

以 16px 为基准（正文），1.250 比例：

| Token       | 字号 | 行高 | 字重 | 用途               |
| ----------- | ---- | ---- | ---- | ------------------ |
| `text-xs`   | 12px | 1.5  | 400  | 辅助说明、标签     |
| `text-sm`   | 14px | 1.5  | 400  | 次要文字、表单标签 |
| `text-base` | 16px | 1.6  | 400  | **正文**           |
| `text-lg`   | 20px | 1.4  | 600  | 卡片标题、小标题   |
| `text-xl`   | 24px | 1.3  | 600  | 区块标题           |
| `text-2xl`  | 30px | 1.25 | 700  | 页面标题           |
| `text-3xl`  | 36px | 1.2  | 700  | 大标题（Hero）     |

**原则**（来自 Refactoring UI）：
- 正文不小于 14px，理想 16px
- 行高：正文 1.5-1.7，标题 1.2-1.3
- 用**字重**和**颜色**区分层次，而非无限增加字号
- 标题字重 600-700，正文 400，不要用 500（区别不明显）

---

## 间距系统

### 8pt 网格

所有间距和尺寸都是 **4px 或 8px 的倍数**。这是行业标准（Material Design、HIG、Ant Design 均采用）。

| Token      | 值   | 典型用途                    |
| ---------- | ---- | --------------------------- |
| `space-0`  | 0    | 无间距                      |
| `space-1`  | 4px  | 图标与文字、紧凑元素        |
| `space-2`  | 8px  | 相关元素间距（标签+输入框） |
| `space-3`  | 12px | 组内元素间距                |
| `space-4`  | 16px | 默认内边距、组件间距        |
| `space-5`  | 20px | 卡片内边距                  |
| `space-6`  | 24px | 区块内间距                  |
| `space-8`  | 32px | 区块间距                    |
| `space-10` | 40px | 大区块间距                  |
| `space-12` | 48px | 页面级间距                  |
| `space-16` | 64px | 超大间距、Hero 区域         |

### 间距使用原则（来自 Refactoring UI）

1. **相关元素近，不相关元素远** — 用间距表达分组关系
2. **先确定大间距，再填小间距** — 先定区块间距（24-32px），再定组内间距（8-16px）
3. **留白不是浪费** — 内容越重要，周围留白越多
4. **避免奇数间距** — 5px、7px 会打破网格节奏
5. **触控目标**：移动端至少 44×44px（HIG），Material Design 要求 48×48dp

### 布局容器

| 断点  | 宽度     | 容器最大宽 | 用途   |
| ----- | -------- | ---------- | ------ |
| `sm`  | ≥ 640px  | 100%       | 手机   |
| `md`  | ≥ 768px  | 720px      | 平板   |
| `lg`  | ≥ 1024px | 960px      | 小桌面 |
| `xl`  | ≥ 1280px | 1200px     | 桌面   |
| `2xl` | ≥ 1536px | 1400px     | 大桌面 |

---

## 圆角系统

### 圆角的语义

- **直角**（0px）：严谨、专业、技术感。适合数据工具、开发者工具
- **小圆角**（4-8px）：友好、现代。适合大多数 SaaS 产品
- **中圆角**（12-16px）：柔和、亲切。适合消费级应用
- **大圆角**（20-24px）：童趣、温暖。适合面向儿童或娱乐的产品

| Token         | 值     | 用途                 |
| ------------- | ------ | -------------------- |
| `radius-none` | 0      | 直角元素             |
| `radius-sm`   | 4px    | 标签、徽章、小输入框 |
| `radius-md`   | 8px    | 按钮、输入框、卡片   |
| `radius-lg`   | 12px   | 大卡片、弹窗         |
| `radius-xl`   | 16px   | 模态框、大面板       |
| `radius-2xl`  | 24px   | 超大卡片             |
| `radius-full` | 9999px | 圆形、胶囊按钮、头像 |

**原则**：
- 同一产品圆角风格统一，不要混用直角和大圆角
- 嵌套元素圆角递减（外层 12px，内层 8px，最内层 4px）
- **Material Design 3** 引入了「形状 scale」（none / extra-small / small / medium / large / extra-large / full），可参考

---

## 阴影与层级

### 阴影的作用

阴影表达**层级关系**（z-axis）。元素越「浮起」，阴影越大。

| Token       | 值                                                           | 用途             |
| ----------- | ------------------------------------------------------------ | ---------------- |
| `shadow-xs` | `0 1px 2px rgba(0,0,0,0.05)`                                 | 输入框、分隔感   |
| `shadow-sm` | `0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)`      | 按钮悬停、小卡片 |
| `shadow-md` | `0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)`     | 卡片、下拉菜单   |
| `shadow-lg` | `0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05)`    | 弹窗、悬浮面板   |
| `shadow-xl` | `0 20px 25px rgba(0,0,0,0.15), 0 10px 10px rgba(0,0,0,0.04)` | 模态框           |

**原则**：
- 阴影要**柔和** — 用多层小阴影模拟真实光照，不要用单个大黑影
- 阴影颜色带一点主色相，比纯黑更自然
- 悬停时加深阴影暗示可交互
- **Material Design 3** 用「Elevation」token 表达层级（0-5），建议参考其语义化命名

### 边框 vs 阴影

- 浅色背景上用**边框**区分卡片（`1px solid neutral-200`）
- 深色背景或需要更强层级感时用**阴影**
- 不要同时用粗边框和重阴影

---

## 动效系统

### 动效原则（来自 Material Design Motion）

1. **动效要有意义** — 解释状态变化、引导注意力、反馈操作。不为炫技而动画
2. **时长要短** — 微交互 100-200ms，大动画 200-400ms。超过 500ms 用户会觉得慢
3. **缓动要自然** — 用 ease-out（进入）、ease-in（退出）、ease-in-out（状态切换）
4. **可禁用** — 尊重 `prefers-reduced-motion` 系统设置

### 时长

| Token             | 值    | 用途                           |
| ----------------- | ----- | ------------------------------ |
| `duration-fast`   | 150ms | 微交互（hover、focus、开关）   |
| `duration-normal` | 250ms | 状态切换、展开收起、卡片变换   |
| `duration-slow`   | 350ms | 页面过渡、模态框进出、大型动画 |

### 缓动函数

| Token         | 值                                  | 用途                       |
| ------------- | ----------------------------------- | -------------------------- |
| `ease-out`    | `cubic-bezier(0, 0, 0.2, 1)`        | 元素进入（从快到慢）       |
| `ease-in`     | `cubic-bezier(0.4, 0, 1, 1)`        | 元素退出（从慢到快）       |
| `ease-in-out` | `cubic-bezier(0.4, 0, 0.2, 1)`      | 状态切换（慢-快-慢）       |
| `spring`      | `cubic-bezier(0.34, 1.56, 0.64, 1)` | 弹性效果（按钮按下、弹出） |

> **参考**：Material Design 3 推荐的标准缓动是 `cubic-bezier(0.2, 0, 0, 1)`（Standard），强调用 `cubic-bezier(0.2, 0, 0, 1)`。

### 减少动效

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 无障碍设计（A11y）

### 必须遵守的 WCAG 2.1 要求

| 准则                 | 要求                     | 实现方式                                   |
| -------------------- | ------------------------ | ------------------------------------------ |
| **1.4.3 对比度**     | 正文 ≥ 4.5:1，大字 ≥ 3:1 | 所有文字颜色必须通过对比度检查             |
| **1.4.1 颜色用途**   | 不只靠颜色传达信息       | 错误状态同时显示图标和文字                 |
| **2.1.1 键盘**       | 所有功能可键盘操作       | Tab 顺序合理，焦点可见                     |
| **2.4.7 焦点可见**   | 焦点指示器清晰可见       | 自定义 focus ring，不要用 `outline: none`  |
| **2.4.6 标题和标签** | 标题描述主题             | 语义化 `<h1>-<h6>`                         |
| **3.3.2 标签**       | 表单控件有标签           | `<label for>` 或 `aria-label`              |
| **4.1.2 名称和角色** | 组件有正确语义           | button 用 `<button>`，不用 `<div onclick>` |

### 焦点管理

```css
:focus-visible {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
}
```

- 不要移除默认焦点样式而不提供替代
- 用 `:focus-visible` 而非 `:focus`，避免鼠标点击时显示焦点环

### 屏幕阅读器

- 所有交互元素有可访问名称（`aria-label` 或可见文字）
- 图片有 `alt` 文本（装饰性图片用 `alt=""`）
- 表单错误与控件关联（`aria-describedby`）
- 动态内容更新用 `aria-live` 通知

---

## 设计令牌输出格式

设计系统的输出必须是**机器可读的令牌**，供前端直接引用。

### CSS 自定义属性

```css
:root {
  /* Colors */
  --color-primary-50: #eff6ff;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-neutral-100: #f3f4f6;
  --color-neutral-700: #374151;
  --color-success: #10b981;
  --color-error: #ef4444;

  /* Typography */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --text-base: 16px;
  --text-lg: 20px;

  /* Spacing */
  --space-2: 8px;
  --space-4: 16px;
  --space-6: 24px;

  /* Radius */
  --radius-md: 8px;
  --radius-lg: 12px;

  /* Shadow */
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);

  /* Motion */
  --duration-fast: 150ms;
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
}
```

### ui-design.json 中的令牌结构

```json
{
  "tokens": {
    "colors": {
      "primary": { "50": "...", "500": "...", "600": "..." },
      "neutral": { "100": "...", "700": "..." },
      "semantic": { "success": "...", "error": "..." }
    },
    "typography": {
      "fontFamily": { "sans": "...", "mono": "..." },
      "fontSize": { "sm": "14px", "base": "16px", "lg": "20px" },
      "fontWeight": { "regular": 400, "semibold": 600, "bold": 700 }
    },
    "spacing": { "2": "8px", "4": "16px", "6": "24px" },
    "radius": { "md": "8px", "lg": "12px" },
    "shadow": { "md": "0 4px 6px rgba(0,0,0,0.07)" },
    "motion": { "duration-fast": "150ms", "ease-out": "cubic-bezier(0,0,0.2,1)" }
  }
}
```

---

## 自检清单

- [ ] 主色有完整色阶（50-900），悬停/按下态有对应 token
- [ ] 中性色在主色相中，不是纯灰
- [ ] 所有文字颜色对比度 ≥ 4.5:1（正文）/ ≥ 3:1（大字）
- [ ] 字号不超过 7 档，基于模块化比例
- [ ] 间距全部是 4px 的倍数
- [ ] 圆角风格统一，嵌套递减
- [ ] 阴影柔和（多层），不粗暴
- [ ] 动效尊重 `prefers-reduced-motion`
- [ ] 设计令牌输出为 CSS 变量或 JSON，无裸值
- [ ] 设计人格（调性/密度/圆角/阴影/动效）已确定并文档化

## 常见误区

❌ **上来就选蓝色当主色** — 先想品牌调性，蓝色不是默认选项
❌ **用纯灰当中性色** — 混入主色相更统一
❌ **定义 10 种以上字号** — 3 种足够，用字重和颜色区分
❌ **间距用 5px、7px、13px** — 必须是 4px 倍数
❌ **只靠颜色表示状态** — 必须配图标或文字
❌ **移除 focus outline 不替代** — 必须提供自定义焦点样式
❌ **到处都加阴影** — 阴影表达层级，不是装饰
