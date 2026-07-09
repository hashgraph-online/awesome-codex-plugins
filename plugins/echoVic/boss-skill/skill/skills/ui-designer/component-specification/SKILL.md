---
name: ui-designer/component-specification
description: UI组件规范，定义按钮、输入框、卡片等基础组件的变体、尺寸、状态
version: 1.0.0
agent: ui-designer
type: guideline
user-invocable: false
agent-invocable: true
dependencies:
  - ui-designer/design-system
triggers:
  - 需要设计组件时
  - 需要定义组件规范时
  - 前端开发需要组件文档时
---

# UI组件规范

## 适用场景

基于设计系统，定义可复用的UI组件规范，确保组件在不同场景下的一致性和完整性。

## 组件设计原则

1. **完整性**：考虑所有状态（默认、悬停、按下、聚焦、禁用、加载、错误）
2. **一致性**：同类组件使用相同的设计语言
3. **可访问性**：支持键盘导航、屏幕阅读器
4. **响应式**：适配不同屏幕尺寸

## 基础组件规范

### 1. 按钮 (Button)

#### 变体

| 变体 | 用途 | 视觉特征 |
|------|------|----------|
| Primary | 主要操作（每个区域最多1个） | 实心，品牌色背景，白色文字 |
| Secondary | 次要操作 | 描边，透明背景，品牌色文字 |
| Ghost | 低优先级操作 | 无边框，透明背景，灰色文字 |
| Danger | 危险操作（删除、清空） | 实心，红色背景，白色文字 |
| Link | 文本链接 | 无背景，品牌色文字，下划线 |

#### 尺寸

| 尺寸 | 高度 | 内边距 | 字号 | 圆角 | 最小宽度 |
|------|------|--------|------|------|----------|
| sm | 32px | 12px 16px | 14px | 6px | 64px |
| md | 40px | 12px 20px | 16px | 8px | 80px |
| lg | 48px | 16px 24px | 16px | 8px | 96px |

#### 状态

| 状态 | Primary 背景 | Primary 文字 | 边框 | 其他 |
|------|--------------|--------------|------|------|
| 默认 | `Primary` | `White` | - | - |
| 悬停 | `Primary-hover` | `White` | - | cursor: pointer |
| 按下 | `Primary-active` | `White` | - | transform: scale(0.98) |
| 聚焦 | `Primary` | `White` | 2px Primary 外发光 | outline |
| 禁用 | `Gray-200` | `Gray-400` | - | cursor: not-allowed, opacity: 0.6 |
| 加载 | `Primary` | - | - | 显示 spinner，文字隐藏 |

#### 图标按钮

| 属性 | 值 |
|------|-----|
| 尺寸 | 32px / 40px / 48px（正方形） |
| 图标大小 | 16px / 20px / 24px |
| 圆角 | radius-md 或 radius-full（圆形） |

#### 代码示例

```tsx
// 主按钮
<Button variant="primary" size="md">确认</Button>

// 次要按钮
<Button variant="secondary" size="md">取消</Button>

// 危险按钮
<Button variant="danger" size="md">删除</Button>

// 禁用状态
<Button variant="primary" size="md" disabled>确认</Button>

// 加载状态
<Button variant="primary" size="md" loading>提交中</Button>

// 带图标
<Button variant="primary" size="md" icon={<IconCheck />}>保存</Button>

// 图标按钮
<IconButton variant="ghost" size="md" icon={<IconClose />} />
```

### 2. 输入框 (Input)

#### 尺寸

| 尺寸 | 高度 | 内边距 | 字号 | 圆角 |
|------|------|--------|------|------|
| sm | 32px | 8px 12px | 14px | 6px |
| md | 40px | 10px 14px | 16px | 8px |
| lg | 48px | 12px 16px | 16px | 8px |

#### 状态

| 状态 | 边框颜色 | 背景色 | 其他 |
|------|----------|--------|------|
| 默认 | `Gray-300` | `White` | - |
| 悬停 | `Gray-400` | `White` | - |
| 聚焦 | `Primary` | `White` | 2px Primary 外发光 |
| 错误 | `Error` | `White` | 显示错误提示 |
| 禁用 | `Gray-200` | `Gray-50` | cursor: not-allowed |
| 只读 | `Gray-200` | `Gray-50` | - |

#### 组成部分

```
┌─────────────────────────────────────────┐
│ [图标]  [输入内容]            [清除按钮] │
└─────────────────────────────────────────┘
  前缀      输入区域               后缀
```

- **前缀**：图标、文字（如"https://"）
- **输入区域**：用户输入的内容
- **后缀**：清除按钮、单位（如"元"）、操作按钮

#### 变体

| 变体 | 说明 |
|------|------|
| Text | 单行文本输入 |
| Textarea | 多行文本输入 |
| Password | 密码输入（带显示/隐藏切换） |
| Number | 数字输入（带增减按钮） |
| Search | 搜索输入（带搜索图标和清除按钮） |

#### 代码示例

```tsx
// 基础输入框
<Input placeholder="请输入用户名" />

// 带标签
<Input label="用户名" placeholder="请输入用户名" />

// 带前缀图标
<Input prefix={<IconUser />} placeholder="请输入用户名" />

// 带后缀清除按钮
<Input clearable placeholder="请输入关键词" />

// 错误状态
<Input error="用户名不能为空" />

// 禁用状态
<Input disabled value="已禁用" />

// 多行文本
<Textarea rows={4} placeholder="请输入描述" />

// 密码输入
<Input type="password" placeholder="请输入密码" />

// 搜索输入
<Input type="search" placeholder="搜索..." />
```

### 3. 选择器 (Select)

#### 尺寸

与Input保持一致（sm / md / lg）

#### 状态

与Input保持一致

#### 下拉菜单

| 属性 | 值 |
|------|-----|
| 最大高度 | 256px（超出滚动） |
| 背景 | `White` |
| 阴影 | `shadow-lg` |
| 圆角 | `radius-md` |
| 选项高度 | 40px |
| 选项内边距 | 10px 14px |

#### 选项状态

| 状态 | 背景色 | 文字颜色 |
|------|--------|----------|
| 默认 | `White` | `Gray-700` |
| 悬停 | `Gray-50` | `Gray-900` |
| 选中 | `Primary-light` | `Primary` |
| 禁用 | `White` | `Gray-400` |

### 4. 复选框 (Checkbox)

#### 尺寸

| 尺寸 | 大小 | 勾选图标 |
|------|------|----------|
| sm | 16px | 12px |
| md | 20px | 14px |
| lg | 24px | 16px |

#### 状态

| 状态 | 边框 | 背景 | 勾选图标 |
|------|------|------|----------|
| 未选中 | `Gray-300` | `White` | - |
| 选中 | `Primary` | `Primary` | `White` |
| 半选中 | `Primary` | `Primary` | `White`（横线） |
| 禁用-未选中 | `Gray-200` | `Gray-50` | - |
| 禁用-选中 | `Gray-300` | `Gray-300` | `White` |

### 5. 单选框 (Radio)

#### 尺寸

与Checkbox保持一致

#### 状态

| 状态 | 边框 | 背景 | 内圆 |
|------|------|------|------|
| 未选中 | `Gray-300` | `White` | - |
| 选中 | `Primary` | `White` | `Primary`（8px圆点） |
| 禁用-未选中 | `Gray-200` | `Gray-50` | - |
| 禁用-选中 | `Gray-300` | `Gray-50` | `Gray-300` |

### 6. 开关 (Switch)

#### 尺寸

| 尺寸 | 宽度 | 高度 | 圆点大小 |
|------|------|------|----------|
| sm | 32px | 18px | 14px |
| md | 44px | 24px | 20px |
| lg | 56px | 30px | 26px |

#### 状态

| 状态 | 背景 | 圆点位置 |
|------|------|----------|
| 关闭 | `Gray-300` | 左侧 |
| 开启 | `Primary` | 右侧 |
| 禁用-关闭 | `Gray-200` | 左侧 |
| 禁用-开启 | `Primary`（opacity: 0.5） | 右侧 |

### 7. 卡片 (Card)

#### 规格

| 属性 | 值 |
|------|-----|
| 背景 | `White` |
| 圆角 | `radius-lg` (12px) |
| 阴影 | `shadow-md` |
| 内边距 | `space-6` (24px) |
| 边框 | 可选，1px `Gray-200` |

#### 变体

| 变体 | 特征 | 用途 |
|------|------|------|
| 默认 | 阴影 | 普通内容卡片 |
| 描边 | 1px Gray-200 边框，无阴影 | 表单区域 |
| 可点击 | hover 时阴影加深，cursor: pointer | 列表项、导航卡片 |
| 可选中 | 选中时边框变为 Primary | 选择卡片 |

#### 组成部分

```
┌─────────────────────────────────────┐
│  [图片/图标]                         │
│                                     │
│  标题                                │
│  描述文字                            │
│                                     │
│  [操作按钮]                          │
└─────────────────────────────────────┘
```

### 8. 标签 (Tag)

#### 尺寸

| 尺寸 | 高度 | 内边距 | 字号 |
|------|------|--------|------|
| sm | 20px | 4px 8px | 12px |
| md | 24px | 6px 10px | 14px |
| lg | 28px | 8px 12px | 14px |

#### 变体

| 变体 | 背景 | 文字 | 边框 |
|------|------|------|------|
| 默认 | `Gray-100` | `Gray-700` | - |
| Primary | `Primary-light` | `Primary` | - |
| Success | `Success-light` | `Success` | - |
| Warning | `Warning-light` | `Warning` | - |
| Error | `Error-light` | `Error` | - |
| 描边 | `White` | `Gray-700` | 1px `Gray-300` |

### 9. 徽章 (Badge)

#### 尺寸

| 尺寸 | 大小 | 字号 |
|------|------|------|
| sm | 16px | 10px |
| md | 20px | 12px |
| lg | 24px | 14px |

#### 变体

| 变体 | 背景 | 文字 |
|------|------|------|
| Primary | `Primary` | `White` |
| Success | `Success` | `White` |
| Warning | `Warning` | `White` |
| Error | `Error` | `White` |
| 圆点 | 纯色圆点，无文字 | - |

### 10. 提示框 (Tooltip)

#### 规格

| 属性 | 值 |
|------|-----|
| 背景 | `Gray-900` |
| 文字 | `White` |
| 字号 | 14px |
| 内边距 | 6px 12px |
| 圆角 | `radius-md` |
| 最大宽度 | 320px |
| 箭头大小 | 6px |

#### 位置

- top / bottom / left / right
- 自动调整位置避免溢出

## 输出要求

在UI设计文档中，应包含以下组件规范章节：

```markdown
## 5. 组件规范

### 5.1 按钮 (Button)
[变体、尺寸、状态表格 + 代码示例]

### 5.2 输入框 (Input)
[尺寸、状态、变体表格 + 代码示例]

### 5.3 [其他组件...]
[根据具体需求补充]
```

## 关键原则

1. **状态完整**：每个组件都要考虑所有状态
2. **一致性**：同类组件使用相同的设计语言
3. **可访问性**：支持键盘导航、屏幕阅读器
4. **文档化**：提供清晰的代码示例

## 常见误区

❌ **状态不全**：只设计默认状态，忽略悬停、禁用等
❌ **尺寸不统一**：不同组件的尺寸不对齐
❌ **缺少文档**：只有视觉稿，没有规范说明
❌ **不考虑边界**：没有考虑长文本、空状态等边界情况
