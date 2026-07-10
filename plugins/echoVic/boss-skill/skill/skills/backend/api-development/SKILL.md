---
name: backend/api-development
description: 后端API开发方法论，包括RESTful/GraphQL设计、请求验证、错误处理和安全实现
type: methodology
agent: boss-backend
---

# 后端 API 开发方法论

## API 契约管理

### 契约来源

实现 API 前，**必须**阅读 `architecture.md` §5（API 设计），获取：
- API 规范（RESTful/GraphQL）
- 接口列表（方法、路径、描述、认证要求）
- 请求/响应格式约定
- 错误码规范

### 契约遵守原则

1. **严格实现**：API 端点的方法、路径、参数必须与 architecture.md §5 一致
2. **响应格式**：遵循统一的成功/错误响应结构
3. **偏差记录**：如需偏离契约，必须在输出报告中标注原因
4. **类型导出**：将请求/响应类型导出到共享文件，供前端引用

## RESTful API 设计

### 资源命名规范

| 操作 | HTTP 方法 | 路径 | 说明 |
|------|-----------|------|------|
| 列表 | GET | `/api/users` | 获取用户列表 |
| 详情 | GET | `/api/users/:id` | 获取单个用户 |
| 创建 | POST | `/api/users` | 创建新用户 |
| 更新 | PUT/PATCH | `/api/users/:id` | 更新用户 |
| 删除 | DELETE | `/api/users/:id` | 删除用户 |

### 统一响应格式

**成功响应**：
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

**错误响应**：
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      { "field": "email", "message": "Invalid email format" }
    ]
  }
}
```

### 分页规范

**请求参数**：
```
GET /api/users?page=1&pageSize=20&sortBy=createdAt&order=desc
```

**响应格式**：
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 100,
      "totalPages": 5
    }
  }
}
```

## 请求验证

### 输入验证层级

1. **路由层**：验证路径参数和查询参数
2. **中间件层**：验证请求体格式和必填字段
3. **Service 层**：验证业务规则

### 验证示例

```typescript
// 使用验证库（如 Zod、Joi、class-validator）
import { z } from 'zod';

const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().min(0).max(150).optional(),
});

// 在路由处理器中验证
app.post('/api/users', async (req, res) => {
  try {
    const validatedData = CreateUserSchema.parse(req.body);
    const user = await userService.create(validatedData);
    res.json({ success: true, data: user });
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid input data',
          details: error.errors,
        },
      });
    }
  }
});
```

### 常见验证规则

- **必填字段**：确保关键字段存在
- **类型检查**：字符串、数字、布尔值、日期
- **格式验证**：邮箱、URL、手机号、UUID
- **范围限制**：最小/最大长度、数值范围
- **业务规则**：唯一性、外键存在性

## 错误处理

### 错误分类

| 错误类型 | HTTP 状态码 | 错误码 | 说明 |
|----------|-------------|--------|------|
| 验证错误 | 400 | VALIDATION_ERROR | 输入数据不合法 |
| 认证错误 | 401 | UNAUTHORIZED | 未登录或 Token 无效 |
| 权限错误 | 403 | FORBIDDEN | 无权限访问资源 |
| 资源不存在 | 404 | NOT_FOUND | 请求的资源不存在 |
| 冲突错误 | 409 | CONFLICT | 资源冲突（如重复创建） |
| 服务器错误 | 500 | INTERNAL_ERROR | 服务器内部错误 |

### 统一错误处理中间件

```typescript
// errorHandler.ts
export function errorHandler(err: Error, req: Request, res: Response, next: NextFunction) {
  console.error(err);
  
  if (err instanceof ValidationError) {
    return res.status(400).json({
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: err.message,
        details: err.details,
      },
    });
  }
  
  if (err instanceof NotFoundError) {
    return res.status(404).json({
      success: false,
      error: {
        code: 'NOT_FOUND',
        message: err.message,
      },
    });
  }
  
  // 默认 500 错误
  res.status(500).json({
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
    },
  });
}
```

## 安全实现

### 认证（Authentication）

**JWT Token 示例**：
```typescript
import jwt from 'jsonwebtoken';

// 生成 Token
export function generateToken(userId: string): string {
  return jwt.sign({ userId }, process.env.JWT_SECRET!, {
    expiresIn: '7d',
  });
}

// 验证 Token 中间件
export function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  
  if (!token) {
    return res.status(401).json({
      success: false,
      error: { code: 'UNAUTHORIZED', message: 'No token provided' },
    });
  }
  
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET!);
    req.user = decoded;
    next();
  } catch (error) {
    res.status(401).json({
      success: false,
      error: { code: 'UNAUTHORIZED', message: 'Invalid token' },
    });
  }
}
```

### 授权（Authorization）

**基于角色的访问控制（RBAC）**：
```typescript
export function requireRole(...roles: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        error: { code: 'FORBIDDEN', message: 'Insufficient permissions' },
      });
    }
    next();
  };
}

// 使用
app.delete('/api/users/:id', authMiddleware, requireRole('admin'), deleteUser);
```

### 输入消毒

- **SQL 注入防护**：使用参数化查询或 ORM
- **XSS 防护**：转义用户输入，使用 Content Security Policy
- **CSRF 防护**：使用 CSRF Token
- **文件上传**：验证文件类型和大小

### 速率限制

```typescript
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 分钟
  max: 100, // 最多 100 个请求
  message: 'Too many requests, please try again later',
});

app.use('/api/', limiter);
```

## 分层架构

### Controller 层

职责：处理 HTTP 请求和响应
```typescript
// controllers/userController.ts
export class UserController {
  async getUser(req: Request, res: Response) {
    try {
      const user = await userService.getById(req.params.id);
      res.json({ success: true, data: user });
    } catch (error) {
      next(error);
    }
  }
  
  async createUser(req: Request, res: Response) {
    const validatedData = CreateUserSchema.parse(req.body);
    const user = await userService.create(validatedData);
    res.status(201).json({ success: true, data: user });
  }
}
```

### Service 层

职责：业务逻辑封装
```typescript
// services/userService.ts
export class UserService {
  async getById(id: string): Promise<User> {
    const user = await userRepository.findById(id);
    if (!user) {
      throw new NotFoundError('User not found');
    }
    return user;
  }
  
  async create(data: CreateUserDto): Promise<User> {
    // 检查邮箱唯一性
    const existing = await userRepository.findByEmail(data.email);
    if (existing) {
      throw new ConflictError('Email already exists');
    }
    
    // 创建用户
    return userRepository.create(data);
  }
}
```

### Repository 层

职责：数据库操作
```typescript
// repositories/userRepository.ts
export class UserRepository {
  async findById(id: string): Promise<User | null> {
    return db.user.findUnique({ where: { id } });
  }
  
  async findByEmail(email: string): Promise<User | null> {
    return db.user.findUnique({ where: { email } });
  }
  
  async create(data: CreateUserDto): Promise<User> {
    return db.user.create({ data });
  }
}
```

## 日志记录

### 日志级别

| 级别 | 使用场景 |
|------|----------|
| ERROR | 错误和异常 |
| WARN | 警告信息 |
| INFO | 关键操作（登录、创建、删除） |
| DEBUG | 调试信息 |

### 日志示例

```typescript
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
  ],
});

// 使用
logger.info('User created', { userId: user.id, email: user.email });
logger.error('Database connection failed', { error: err.message });
```

## 性能优化

### 数据库查询优化

- 使用索引加速查询
- 避免 N+1 查询问题
- 使用连接（JOIN）代替多次查询
- 分页查询大数据集

### 缓存策略

```typescript
import Redis from 'ioredis';

const redis = new Redis();

async function getUserWithCache(id: string): Promise<User> {
  // 尝试从缓存获取
  const cached = await redis.get(`user:${id}`);
  if (cached) {
    return JSON.parse(cached);
  }
  
  // 从数据库获取
  const user = await userRepository.findById(id);
  
  // 写入缓存（5 分钟过期）
  await redis.setex(`user:${id}`, 300, JSON.stringify(user));
  
  return user;
}
```

### 连接池管理

- 配置合理的数据库连接池大小
- 及时释放连接
- 监控连接池使用情况

## 实现检查清单

实现 API 前：
- [ ] 阅读 architecture.md §5 API 设计
- [ ] 确认请求/响应格式约定
- [ ] 确认认证和授权方案
- [ ] 探索项目现有代码模式

实现 API 后：
- [ ] API 端点符合契约定义
- [ ] 实现请求验证
- [ ] 实现统一错误处理
- [ ] 添加认证和授权
- [ ] 编写单元测试（Service 层）
- [ ] 编写集成测试（API 端点）
- [ ] 编写 E2E 测试（完整流程）
- [ ] 添加日志记录
- [ ] 代码通过 Lint 检查
