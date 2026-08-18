---
name: frontend/component-development
description: 前端组件开发方法论，包括组件设计原则、状态管理、样式实现和性能优化
type: methodology
agent: boss-frontend
---

# 前端组件开发方法论

## 组件设计原则

### 单一职责原则
- 每个组件只负责一个功能模块
- 复杂组件拆分为多个子组件
- 容器组件（逻辑）与展示组件（UI）分离

### 可复用性设计
- 通过 Props/属性实现组件配置化
- 避免硬编码业务逻辑
- 提供合理的默认值
- 支持插槽/children 扩展

### 组件命名规范
- 使用 PascalCase 命名组件
- 名称应清晰描述组件功能
- 避免过于通用的名称（如 Item、Component）
- 文件名与组件名保持一致

## 状态管理策略

### 状态分类
| 状态类型 | 管理方式 | 适用场景 |
|----------|----------|----------|
| 本地状态 | useState/ref | 组件内部状态（表单输入、展开/收起） |
| 共享状态 | Context/Store | 跨组件共享（用户信息、主题） |
| 服务端状态 | Query库/SWR | API 数据缓存和同步 |
| URL 状态 | Router | 页面参数、筛选条件 |

### 状态提升原则
- 状态放在最近的公共父组件
- 避免过度提升导致不必要的重渲染
- 使用 Context 避免 Props 层层传递

### 副作用管理
- 使用框架的副作用 Hook（useEffect/onMounted）
- 清理订阅和定时器
- 依赖数组准确声明
- 避免在渲染函数中执行副作用

## 样式实现规范

### UI 规范优先级
```
ui-design.json > ui-spec.md > 项目现有样式 > 框架默认值
```

### ui-design.json 集成
当 `.boss/<feature>/ui-design.json` 存在时：
1. **读取 tokens**：映射为 CSS 变量或主题对象
   ```typescript
   // 示例：从 tokens 生成 CSS 变量
   const colors = uiDesign.tokens.colors;
   // --color-primary: #007AFF
   ```

2. **解析 pages 和 frames**：推导页面结构和布局
   - 从 `pages[].frames[]` 提取页面组件层级
   - 从 `frames[].layout` 获取布局约束（宽度、间距、对齐）

3. **实现 prototype.links**：推导导航和交互
   - 按钮点击跳转
   - 表单提交流程
   - 模态框打开/关闭

4. **复用 components**：提取可复用组件
   - 从 `components[]` 识别通用组件（Button、Input、Card）
   - 实现为独立组件文件

### 样式编写原则
- 使用项目约定的样式方案（CSS Modules/Tailwind/CSS-in-JS）
- 响应式设计：移动端优先或桌面端优先（按项目约定）
- 使用设计系统的间距、颜色、字体变量
- 避免魔法数字，使用语义化变量

### 无障碍实现
- 添加正确的 ARIA 属性（role、aria-label、aria-describedby）
- 确保键盘导航可用（tabindex、focus 样式）
- 表单元素关联 label
- 图片添加 alt 文本

## 性能优化技巧

### 渲染优化
- 使用 Memo/shouldComponentUpdate 避免不必要的重渲染
- 列表渲染使用稳定的 key
- 虚拟滚动处理长列表
- 避免在渲染函数中创建新对象/函数

### 代码分割
- 路由级别的懒加载
- 大型组件按需加载
- 第三方库按需引入

### 资源优化
- 图片懒加载和响应式图片
- 使用 WebP 等现代图片格式
- SVG 图标内联或雪碧图

## API 契约管理

### 契约来源
实现前端 API 调用前，必须阅读：
1. **architecture.md §5（API 设计）**：获取端点列表、请求/响应格式
2. **后端共享类型**（如有）：复用类型定义

### API 调用层设计
```typescript
// services/api/users.ts
export const userApi = {
  async getUser(id: string): Promise<User> {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
  },
  
  async createUser(data: CreateUserRequest): Promise<User> {
    const response = await fetch('/api/users', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.json();
  },
};
```

### 错误处理
- 统一错误处理：按 architecture.md 定义的错误格式
- 用户友好的错误提示
- 网络错误重试机制
- 加载和错误状态展示

### Mock 策略
后端未就绪时，基于 architecture.md §5 创建 Mock：
```typescript
// services/api/users.mock.ts
export const mockUserApi = {
  async getUser(id: string): Promise<User> {
    return { id, name: 'Mock User', email: 'mock@example.com' };
  },
};
```

## 组件测试策略

### 测试金字塔
| 测试类型 | 占比 | 工具示例 |
|----------|------|----------|
| 单元测试 | 70% | Jest + Testing Library |
| 集成测试 | 20% | Testing Library |
| E2E 测试 | 10% | Playwright/Cypress |

### 单元测试覆盖
- 组件渲染：关键元素是否存在
- Props 变化：不同 Props 下的渲染结果
- 用户交互：点击、输入、表单提交
- Hooks 逻辑：自定义 Hook 的状态变化

### 集成测试覆盖
- 组件间交互：父子组件通信
- 状态管理：全局状态变化对组件的影响
- 路由导航：页面跳转和参数传递

### E2E 测试覆盖（必须）
- 创建流程：填写表单 → 提交 → 验证结果
- 编辑流程：打开编辑 → 修改 → 保存 → 验证
- 删除流程：点击删除 → 确认 → 验证消失
- 列表展示：加载列表 → 筛选 → 分页
- 核心业务流程：完整用户路径

## 实现检查清单

实现组件前：
- [ ] 阅读 ui-design.json（如有）和 ui-spec.md
- [ ] 阅读 architecture.md §5 API 设计
- [ ] 探索项目现有组件模式和样式方案
- [ ] 确认状态管理方案（本地/共享/服务端）

实现组件后：
- [ ] 组件符合单一职责原则
- [ ] 添加必要的 Props 类型定义
- [ ] 实现响应式布局
- [ ] 添加无障碍属性
- [ ] 编写单元测试（70%）
- [ ] 编写集成测试（20%）
- [ ] 编写 E2E 测试（10%，必须）
- [ ] 测试覆盖率达标
- [ ] 代码通过 Lint 检查
