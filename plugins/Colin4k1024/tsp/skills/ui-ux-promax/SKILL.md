---
name: ui-ux-promax
description: >
  最强 UI/UX 设计智能技能（源自 UI UX Pro Max，github.com/nextlevelbuilder/ui-ux-pro-max-skill）。
  内置 67 种 UI 风格、161 个行业配色方案、57 套字体组合、161 条产品类型推理规则、99 条 UX 准则、
  25 种图表类型，覆盖 15 种技术栈（React、Next.js、Vue、Svelte、SwiftUI、React Native、Flutter、
  Tailwind、shadcn/ui、Angular、Laravel 等）。
  触发关键词：设计页面、创建 UI 组件、选配色、选字体、响应式布局、无障碍审查、
  动效设计、表单交互、落地页、dashboard、mobile app、UI review、build landing page、
  design dashboard、create component、styling、glassmorphism、minimalism 等任何 UI/UX 请求。
origin: UI UX Pro Max v2.0 (nextlevelbuilder/ui-ux-pro-max-skill, MIT License)
---

# UI/UX Pro Max — 设计智能技能

> 来源：[github.com/nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | MIT License  
> 版本：v2.0 | 67 UI 风格 · 161 配色方案 · 57 字体组合 · 161 推理规则 · 99 UX 准则

---

## 何时使用（When to Apply）

**必须使用（Must Use）：**
- 设计新页面（落地页、Dashboard、Admin、SaaS、移动 App）
- 创建或重构 UI 组件（按钮、弹窗、表单、表格、图表等）
- 选择配色方案、字体系统、间距规范或布局系统
- 审查 UI 代码的用户体验、无障碍性或视觉一致性
- 实现导航结构、动效或响应式行为
- 做产品级设计决策（风格、信息层级、品牌表达）
- 提升界面的感知质量、清晰度或可用性

**推荐使用（Recommended）：**
- UI 看起来"不够专业"但原因不明确
- 收到可用性或体验方面的反馈
- 发布前 UI 质量优化
- 跨平台设计对齐（Web / iOS / Android）
- 构建设计系统或可复用组件库

**不需要使用（Skip）：**
- 纯后端逻辑开发
- 仅涉及 API 或数据库设计
- 与界面无关的性能优化
- 基础设施或 DevOps 工作
- 非可视化脚本或自动化任务

---

## 设计系统推理引擎（v2.0 核心）

UI UX Pro Max v2.0 的核心是**智能设计系统生成**——基于产品关键词，5 路并行搜索后通过推理引擎输出完整设计方案。

### 工作流

```
1. 用户请求  →  "Build a landing page for my beauty spa"
2. 多域并行搜索（5路）
   • 产品类型匹配（161 类别）
   • 风格推荐（67 种风格）
   • 配色方案选择（161 套）
   • 落地页结构（24 种模式）
   • 字体组合（57 套）
3. 推理引擎
   • 产品→UI 类型规则映射
   • BM25 风格优先级排序
   • 过滤行业反模式
   • 处理 JSON 决策规则
4. 输出完整设计方案
   Pattern + Style + Colors + Typography + Effects
   + Anti-patterns to avoid + Pre-delivery checklist
```

### 设计系统输出示例（Beauty Spa）

```
TARGET: Serenity Spa — RECOMMENDED DESIGN SYSTEM
─────────────────────────────────────────────────
PATTERN: Hero-Centric + Social Proof
  Sections: Hero → Services → Testimonials → Booking → Contact

STYLE: Soft UI Evolution
  Keywords: Soft shadows, subtle depth, calming, premium feel, organic shapes
  Best For: Wellness, beauty, lifestyle, premium services
  Performance: Excellent | Accessibility: WCAG AA

COLORS:
  Primary:    #E8B4B8  (Soft Pink)
  Secondary:  #A8D5BA  (Sage Green)
  CTA:        #D4AF37  (Gold)
  Background: #FFF5F5  (Warm White)
  Text:       #2D3436  (Charcoal)

TYPOGRAPHY: Cormorant Garamond / Montserrat
  Mood: Elegant, calming, sophisticated

KEY EFFECTS: Soft shadows + Smooth transitions (200–300ms) + Gentle hover states

ANTI-PATTERNS TO AVOID:
  Bright neon colors · Harsh animations · Dark mode · AI purple/pink gradients
```

---

## 规则优先级矩阵

| 优先级 | 类别 | 影响 | 关键检查项 | 反模式 |
|--------|------|------|-----------|--------|
| 1 | **无障碍性** | CRITICAL | 对比度 4.5:1、Alt text、键盘导航、Aria 标签 | 移除 focus ring、仅图标按钮无标签 |
| 2 | **触控与交互** | CRITICAL | 最小 44×44px、8px+ 间距、加载反馈 | 仅 hover、0ms 状态切换 |
| 3 | **性能** | HIGH | WebP/AVIF、懒加载、预留空间（CLS < 0.1） | 布局抖动、累积布局偏移 |
| 4 | **风格选择** | HIGH | 匹配产品类型、一致性、SVG 图标（禁 emoji） | 混搭扁平与写实、emoji 作图标 |
| 5 | **布局与响应式** | HIGH | 移动优先断点、viewport meta、禁横向滚动 | 固定 px 容器、禁用缩放 |
| 6 | **字体与配色** | MEDIUM | 基础 16px、行高 1.5、语义色彩 token | 正文 <12px、灰色叠灰色、组件内裸 hex |
| 7 | **动效** | MEDIUM | 150–300ms、transform/opacity only、运动表意 | 纯装饰性动画、animating width/height |
| 8 | **表单与反馈** | MEDIUM | 可见标签、字段旁错误提示、提交反馈 | 仅 placeholder 作标签、顶部堆错误 |
| 9 | **导航模式** | HIGH | 可预测返回、底导 ≤5 项、深度链接 | 导航过载、返回路径中断 |
| 10 | **图表与数据** | LOW | 图例、Tooltip、无障碍配色 | 仅用颜色传达信息 |

---

## 快速参考（Quick Reference）

### 1. 无障碍性（CRITICAL）

- `color-contrast` — 正文最小 4.5:1（大字 3:1）
- `focus-states` — 交互元素可见焦点环（2–4px）
- `alt-text` — 有意义图片的描述性替代文字
- `aria-labels` — 仅图标按钮需要 aria-label
- `keyboard-nav` — Tab 顺序与视觉顺序一致
- `form-labels` — 使用带 for 属性的 label
- `skip-links` — 为键盘用户提供跳转到主内容的链接
- `heading-hierarchy` — 顺序 h1→h6，不跳级
- `color-not-only` — 不仅靠颜色传达信息（配合图标/文字）
- `reduced-motion` — 遵守 `prefers-reduced-motion`

### 2. 触控与交互（CRITICAL）

- `touch-target-size` — 最小 44×44pt（Apple）/ 48×48dp（Material）
- `touch-spacing` — 触控目标间最小 8px 间距
- `hover-vs-tap` — 主要交互用 click/tap，不仅依赖 hover
- `loading-buttons` — 异步操作期间禁用按钮并显示 spinner
- `cursor-pointer` — 可点击元素加 cursor-pointer（Web）
- `press-feedback` — 按下 150ms 内提供视觉反馈
- `safe-area-awareness` — 主要触控目标远离刘海、手势条

### 3. 性能（HIGH）

- `image-optimization` — WebP/AVIF + srcset + 懒加载
- `image-dimension` — 声明 width/height 或 aspect-ratio 防 CLS
- `font-loading` — `font-display: swap` 避免 FOIT
- `bundle-splitting` — 按路由/功能代码分割
- `virtualize-lists` — 50+ 项列表虚拟化
- `main-thread-budget` — 每帧 ~16ms 以内；重任务移出主线程

### 4. 风格选择（HIGH）

- `style-match` — 风格与产品类型匹配
- `consistency` — 所有页面使用同一风格
- `no-emoji-icons` — 使用 SVG 图标（Heroicons、Lucide），禁 emoji
- `color-palette-from-product` — 从产品/行业选择配色方案
- `effects-match-style` — 阴影、模糊、圆角对齐所选风格
- `elevation-consistent` — 卡片、弹窗、Modal 使用一致的层级/阴影

### 5. 布局与响应式（HIGH）

- `viewport-meta` — `width=device-width initial-scale=1`（不禁用缩放）
- `mobile-first` — 移动端优先设计
- `breakpoint-consistency` — 统一断点（375 / 768 / 1024 / 1440）
- `readable-font-size` — 移动端正文最小 16px
- `horizontal-scroll` — 禁止移动端横向滚动
- `spacing-scale` — 4pt/8dp 递进间距系统
- `container-width` — 桌面端统一 max-width（max-w-6xl / 7xl）
- `z-index-management` — 定义层级 z-index 规模（0/10/20/40/100/1000）

### 6. 字体与配色（MEDIUM）

- `line-height` — 正文行高 1.5–1.75
- `line-length` — 每行 65–75 字符
- `font-pairing` — 标题/正文字体气质匹配
- `font-scale` — 统一字号梯度（12 14 16 18 24 32）
- `color-semantic` — 定义语义色彩 token（primary / secondary / error / surface）
- `color-dark-mode` — 暗色模式使用降饱和/较亮色调变体，不做简单颜色反转
- `color-accessible-pairs` — 前景/背景满足 4.5:1（AA）或 7:1（AAA）

### 7. 动效（MEDIUM）

- `duration-timing` — 微交互 150–300ms；复杂过渡 ≤400ms
- `transform-performance` — 仅 transform/opacity，禁止动画 width/height/top/left
- `loading-states` — 加载超 300ms 显示骨架屏或进度指示
- `easing` — 进入用 ease-out，退出用 ease-in
- `motion-meaning` — 每个动画必须传达因果关系，非纯装饰
- `exit-faster-than-enter` — 退出动画约为进入时长的 60–70%
- `spring-physics` — 优先弹簧/物理曲线，自然感更强
- `interruptible` — 动画必须可中断；用户操作立即取消进行中的动画

### 8. 表单与反馈（MEDIUM）

- `input-labels` — 每个输入项有可见标签（非仅 placeholder）
- `error-placement` — 错误信息显示在相关字段下方
- `submit-feedback` — 提交后展示加载→成功/错误状态
- `inline-validation` — 失焦后验证（非按键时）；仅在用户完成输入后显示错误
- `progressive-disclosure` — 渐进式披露复杂选项
- `toast-dismiss` — Toast 3–5 秒后自动消失
- `confirmation-dialogs` — 破坏性操作前二次确认
- `sheet-dismiss-confirm` — 有未保存更改时确认后关闭
- `undo-support` — 破坏性或批量操作提供撤销

### 9. 导航模式（HIGH）

- `bottom-nav-limit` — 底部导航最多 5 项（图标+标签）
- `back-behavior` — 返回导航可预测且一致
- `deep-linking` — 所有核心页面可深度链接
- `nav-state-active` — 当前位置高亮显示
- `adaptive-navigation` — ≥1024px 偏好侧边栏；小屏用底/顶导航
- `modal-escape` — 弹窗/底部表单有明确的关闭/取消操作
- `navigation-consistency` — 所有页面导航位置保持一致

### 10. 图表与数据（LOW）

- `chart-type` — 图表类型与数据类型匹配（趋势→折线，对比→柱状，占比→饼/环）
- `legend-visible` — 始终显示图例，位置靠近图表
- `tooltip-on-interact` — hover（Web）或 tap（移动端）显示精确值
- `responsive-chart` — 小屏上图表自适应重排或简化
- `empty-data-state` — 无数据时显示有意义的空态
- `no-pie-overuse` — >5 个类别禁用饼/环图，改用柱状图

---

## 161 行业推理规则覆盖范围

| 领域 | 覆盖类型 |
|------|---------|
| 科技 / SaaS | SaaS、Micro SaaS、B2B、开发工具、AI/Chatbot、网络安全 |
| 金融 | Fintech/Crypto、银行、保险、个人财务、账单工具 |
| 医疗 | 诊所、药房、牙科、兽医、心理健康、用药提醒 |
| 电商 | 综合、奢侈品、P2P 市场、订阅盒、食品配送 |
| 服务 | 美容/SPA、餐厅、酒店、法律、家政、预约 |
| 创意 | 作品集、代理商、摄影、游戏、音乐流媒体 |
| 生活方式 | 习惯追踪、食谱、冥想、天气、日记、情绪追踪 |
| 新兴技术 | Web3/NFT、空间计算、量子计算、无人机 |

每条规则包含：推荐模式 · 风格优先级 · 配色情绪 · 字体气质 · 关键效果 · **反模式**（例如：银行类禁用"AI 紫粉渐变"）

---

## 支持的技术栈（15 种）

| 栈 | 关注点 |
|----|-------|
| React | 状态、hooks、性能模式 |
| Next.js | SSR、路由、API routes |
| Vue / Nuxt.js / Nuxt UI | Composition API、Pinia |
| Svelte / Astro | Runes、SvelteKit |
| **Tailwind / HTML+CSS** | 默认栈，utilities、响应式 |
| shadcn/ui | 组件搜索与示例 |
| Angular | 组件、服务、RxJS |
| Laravel | Blade、Livewire、Inertia.js |
| SwiftUI | Views、State、Navigation |
| React Native | 组件、导航、列表 |
| Flutter | Widget、State、Theming |
| Jetpack Compose | Composable、Navigation |

**默认栈为 HTML + Tailwind CSS**，在 prompt 中指定栈名即可切换。

---

## 使用工作流

### 新项目 / 新页面（Step 1 → Step 2 必选）

1. **分析需求**：提取产品类型、目标用户、风格关键词、技术栈
2. **生成设计系统**（REQUIRED）：输出完整 Pattern + Style + Colors + Typography + Anti-patterns
3. **补充领域搜索**（按需）：深入某个维度（风格/配色/字体/UX/图表）
4. **获取栈指南**（按需）：针对具体栈的最佳实践

### 场景→入口映射

| 场景 | 触发示例 | 起点 |
|------|---------|------|
| 新项目 / 页面 | "Build a landing page" | Step 1 → Step 2 |
| 新组件 | "Create a pricing card" | Step 3（domain: style, ux） |
| 选风格 / 配色 / 字体 | "What style fits fintech?" | Step 2（设计系统） |
| 审查现有 UI | "Review this page for UX" | Quick Reference 清单 |
| 修复 UI 问题 | "Button hover is broken" | Quick Reference → 相关章节 |
| 优化改进 | "Improve mobile experience" | Step 3（domain: ux, react） |
| 深色模式 | "Add dark mode support" | Step 3（domain: style "dark mode"） |
| 图表/数据可视化 | "Add analytics dashboard" | Step 3（domain: chart） |
| 栈最佳实践 | "React performance tips" | Step 4（stack search） |

---

## 设计系统持久化（Master + Overrides 模式）

为跨会话保留设计决策，使用以下目录结构：

```
design-system/
├── MASTER.md           # 全局真相源（颜色、字体、间距、组件）
└── pages/
    ├── dashboard.md    # 页面级覆盖规则（仅与 Master 不同的部分）
    └── checkout.md
```

**分层检索规则：**
1. 构建特定页面时，先检查 `design-system/pages/[page-name].md`
2. 若页面文件存在，其规则**覆盖** Master 文件
3. 若不存在，独立使用 `design-system/MASTER.md`

---

## 交付前检查清单（Pre-Delivery Checklist）

### 必检项（CRITICAL）
- [ ] 无障碍：正文对比度 ≥4.5:1（亮色和暗色模式分别测试）
- [ ] 触控目标：可点击元素 ≥44×44pt（iOS）/ ≥48×48dp（Android/Web）
- [ ] 无 emoji 图标（统一使用 SVG：Heroicons / Lucide）
- [ ] 所有可点击元素有 `cursor-pointer`
- [ ] hover/focus/active/disabled 状态可见且平滑（150–300ms）
- [ ] 焦点环可见，键盘导航可用
- [ ] `prefers-reduced-motion` 已考虑

### 布局与响应式
- [ ] 已在 375px / 768px / 1024px / 1440px 验证
- [ ] 移动端无横向滚动
- [ ] 安全区（刘海、底部手势条）已预留间距
- [ ] 滚动内容不被固定栏遮挡

### 设计一致性
- [ ] 全局使用语义 token（无散落 hex 值）
- [ ] 图标风格统一（描边宽度、角点半径一致）
- [ ] 阴影/层级系统统一
- [ ] 亮色和暗色模式均已测试

### 表单与交互
- [ ] 每个输入项有可见标签（非仅 placeholder）
- [ ] 错误信息靠近字段，说明原因和修复方法
- [ ] 长表单有自动保存或草稿保护
- [ ] 破坏性操作有二次确认

---

## 常见反模式（必须避免）

| 反模式 | 正确做法 |
|--------|---------|
| emoji 作功能图标 | SVG 图标（Heroicons、Lucide） |
| 仅颜色传达状态 | 颜色 + 图标 + 文字三重编码 |
| placeholder 代替 label | 可见 label + placeholder 作提示 |
| 仅 hover 交互 | click/tap 作主要交互 |
| 0ms 状态切换 | 150–300ms 过渡动画 |
| 动画 width/height | transform/opacity only |
| 无限期不过期缓存图片 | 声明 width/height，防 CLS |
| 组件内裸 hex 值 | 语义 token（CSS 变量/Tailwind token） |
| 混搭图标风格 | 统一图标集，统一描边/填充风格 |
| 暗色模式 = 颜色反转 | 降饱和/较亮色调变体，独立测试对比度 |
| 仅 AI 紫粉渐变（金融/医疗） | 遵循行业推理规则的配色 |

---

## 与仓库现有规则的映射

本 skill 是以下仓库规则的**可执行主技能**，完全兼容并增强：

| 仓库规则 | 本 skill 对应能力 |
|---------|-----------------|
| `frontend-ui-ux-standards.md` | Quick Reference §1–§10 完整覆盖 |
| `frontend-quality-gates.md` | Pre-Delivery Checklist 直接对应 |
| `frontend-engineering-standards.md` | 15 种栈的最佳实践指南 |
| `frontend-design-knowledge-base.md` | 本 skill 即设计知识库的可执行层 |

**使用建议：**
- `tech-lead` 在 `/team-intake` 或 `/team-plan` 阶段调用本 skill 锁定设计系统
- `frontend-engineer` 在实施前调用本 skill 生成设计系统，再按模式编码
- `qa-engineer` 在评审时使用本 skill 的 Pre-Delivery Checklist 作为评审依据
