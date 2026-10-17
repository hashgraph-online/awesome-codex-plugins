# Phase 6: 验证与迭代（Verification & Iteration）引导细则

## 入口条件

- Phase 5 的完整项目代码已生成并确认
- 项目文件已写入磁盘

## 验证步骤

### Step 1: 依赖安装

根据框架执行依赖安装：

| 框架 | 安装命令 |
|------|---------|
| LangChain (Python) | `cd {project_dir} && pip install -e .` 或 `pip install -r requirements.txt` |
| LangChain.js | `cd {project_dir} && npm install` |
| EINO (Go) | `cd {project_dir} && go mod tidy` |
| AutoGen | `cd {project_dir} && pip install -e .` |
| AgentScope | `cd {project_dir} && pip install -e .` |
| CrewAI | `cd {project_dir} && pip install -e .` |

**失败处理**：
- 依赖冲突 → 检查版本兼容性并调整
- 缺少系统依赖 → 提示用户安装（如 `libpq-dev`）
- 网络问题 → 建议使用镜像源

### Step 2: 语法与类型检查

| 语言 | 检查命令 |
|------|---------|
| Python | `python -m py_compile src/agent.py` + `mypy src/ --ignore-missing-imports`（如有 mypy） |
| TypeScript | `npx tsc --noEmit` |
| Go | `go build ./...` + `go vet ./...` |

### Step 3: 单元测试

执行生成的测试文件：

| 语言 | 测试命令 |
|------|---------|
| Python | `cd {project_dir} && python -m pytest tests/ -v` |
| TypeScript | `cd {project_dir} && npm test` |
| Go | `cd {project_dir} && go test ./... -v` |

**预期**：基础测试（工具函数、配置加载）应该在不需要真实 API Key 的情况下通过。

### Step 4: Smoke Test

模拟一轮 Agent 交互验证端到端可用性。

**前提**：用户需要先配置 `.env`（至少 LLM API Key）。

**Smoke Test 方式**：

```python
# Python 示例
from src.agent import create_agent

agent = create_agent()
response = agent.run("你好，请帮我...")
print(response)
```

```go
// Go 示例
agent := createAgent()
response, err := agent.Run(context.Background(), "你好，请帮我...")
fmt.Println(response)
```

**无 API Key 时的降级策略**：
- 提供 mock LLM 配置选项，返回固定响应
- 至少验证：Agent 初始化成功、工具注册成功、Prompt 加载成功

### Step 5: 失败定位与修复

如验证失败，按以下流程处理：

```
失败 → 读取错误信息
     → 分析根因（import 错误 / 类型错误 / 配置缺失 / API 变更）
     → 修复代码
     → 重跑验证
     → 最多 3 轮自动修复
     → 仍失败则暂停，向用户说明问题并寻求指引
```

如果错误复杂，可调用 `systematic-debugging` skill 进行系统化调试。

## --import 模式的额外验证

导入模式下需要额外验证行为一致性：

1. **工具等效性**：逐个工具验证输入/输出与原实现一致
2. **Prompt 保真度**：对比原 System Prompt 和新框架中的 Prompt 是否语义一致
3. **编排一致性**：模拟相同输入，验证 Agent 行为路径是否匹配
4. 生成 `migration-validation.md` 记录验证结果

## 验证报告模板

```markdown
# Agent Verification Report

## 基本信息

| 项目 | 值 |
|------|-----|
| Agent 名称 | {name} |
| 框架 | {framework} |
| 验证时间 | {timestamp} |

## 验证结果

| 步骤 | 状态 | 说明 |
|------|------|------|
| 依赖安装 | ✅/❌ | {detail} |
| 语法检查 | ✅/❌ | {detail} |
| 类型检查 | ✅/❌ | {detail} |
| 单元测试 | ✅/❌ | {passed}/{total} 通过 |
| Smoke Test | ✅/❌/⏭️ | {detail} |

## 问题与修复

| # | 问题 | 根因 | 修复方案 | 状态 |
|---|------|------|----------|------|
| 1 | {issue} | {root_cause} | {fix} | ✅/⏳ |

## 用户操作指引

### 运行你的 Agent

\`\`\`bash
{step_by_step_instructions}
\`\`\`

### 下一步建议

1. 配置 `.env` 文件
2. 运行 Smoke Test 验证端到端
3. 根据实际使用调整 Prompt
4. 添加更多测试用例
```

## 迭代循环

验证通过后：
1. 展示验证报告给用户
2. 告知用户如何运行和测试
3. 用户测试后如有反馈 → 回到对应 Phase 调整：
   - Prompt 调整 → Phase 4 → 重新生成 prompt 文件
   - 工具调整 → Phase 3 → 更新工具 + 重新生成
   - 架构调整 → Phase 2 → 较大改动
4. 每次迭代只影响变更点及其下游

## 完成条件

- 验证报告全部 ✅（Smoke Test 可以跳过但需说明）
- 用户确认 Agent 可用
- 更新 tracking.md Phase 6 为 ✅
