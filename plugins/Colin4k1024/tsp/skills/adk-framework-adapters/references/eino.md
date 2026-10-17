---
framework: eino
version: "0.3.x"
language: go
verified_date: "2025-01-15"
---

# EINO (ByteDance) 适配器

## 框架概述

- **语言**: Go
- **核心库**: `github.com/cloudwego/eino`, `github.com/cloudwego/eino-ext`
- **特点**: Go 原生、高性能、类型安全、字节跳动开源
- **适用**: 对性能和类型安全有高要求的场景

## 项目模板

```
{project_name}/
├── go.mod
├── go.sum
├── .env.example
├── README.md
├── cmd/
│   └── main.go            # 入口
├── internal/
│   ├── agent/
│   │   └── agent.go       # Agent 定义
│   ├── tools/
│   │   └── tools.go       # 工具定义
│   ├── prompts/
│   │   └── prompts.go     # Prompt 模板
│   ├── memory/
│   │   └── memory.go      # Memory 配置
│   └── config/
│       └── config.go      # 配置管理
├── tests/
│   ├── agent_test.go
│   └── tools_test.go
└── scripts/
    └── run.sh
```

## 依赖配置

```go
// go.mod
module {project_name}

go 1.22

require (
    github.com/cloudwego/eino v0.3.0
    github.com/cloudwego/eino-ext v0.3.0
)
```

## Agent 创建模式

### ReAct Agent

```go
package agent

import (
    "context"
    
    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/flow/agent"
    "github.com/cloudwego/eino/flow/agent/react"
    "github.com/cloudwego/eino/components/model"
    "github.com/cloudwego/eino-ext/components/model/openai"
)

func NewReActAgent(ctx context.Context) (agent.Agent, error) {
    // 创建 LLM
    llm, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        Model:       "gpt-4o",
        Temperature: ptr(float32(0)),
    })
    if err != nil {
        return nil, err
    }
    
    // 创建工具
    tools := buildTools()
    
    // 创建 ReAct Agent
    ag, err := react.NewAgent(ctx, &react.AgentConfig{
        Model:         llm,
        ToolsConfig:   tools,
        MaxStep:       10,
        SystemPrompt:  systemPrompt,
    })
    if err != nil {
        return nil, err
    }
    
    return ag, nil
}
```

### Graph 工作流

```go
package agent

import (
    "github.com/cloudwego/eino/compose"
)

func NewWorkflow(ctx context.Context) (*compose.Graph[*State, *Result], error) {
    graph := compose.NewGraph[*State, *Result]()
    
    graph.AddLambdaNode("retrieve", retrieveNode)
    graph.AddLambdaNode("generate", generateNode)
    graph.AddLambdaNode("review", reviewNode)
    
    graph.AddEdge(compose.START, "retrieve")
    graph.AddEdge("retrieve", "generate")
    graph.AddBranch("review", routeFunc, map[string]string{
        "retry": "generate",
        "done":  compose.END,
    })
    
    return graph.Compile(ctx)
}
```

## 工具定义模式

```go
package tools

import (
    "context"
    
    "github.com/cloudwego/eino/components/tool"
    "github.com/cloudwego/eino/components/tool/utils"
)

type SearchOrdersParams struct {
    Query  string `json:"query" jsonschema:"description=搜索关键词"`
    Status string `json:"status,omitempty" jsonschema:"description=按状态过滤,enum=pending|shipped|delivered"`
}

type Order struct {
    OrderID  string  `json:"order_id"`
    Customer string  `json:"customer"`
    Status   string  `json:"status"`
    Total    float64 `json:"total"`
}

func NewSearchOrdersTool() tool.BaseTool {
    return utils.NewTool(
        &utils.ToolConfig{
            Name:        "search_orders",
            Description: "按订单号或客户名搜索订单",
        },
        func(ctx context.Context, params *SearchOrdersParams) ([]*Order, error) {
            // 实现
            return orders, nil
        },
    )
}
```

## Memory 配置

```go
package memory

import (
    "github.com/cloudwego/eino/components/memory"
)

func NewConversationMemory() memory.Memory {
    return memory.NewConversationBufferMemory(&memory.ConversationBufferConfig{
        MaxTokens:  4000,
        HumanKey:   "human",
        AIKey:      "assistant",
    })
}
```

## Multi-Agent 模式

```go
// EINO 的多 Agent 通过 Graph 组合实现
func NewMultiAgentWorkflow(ctx context.Context) (*compose.Graph[*TeamState, *TeamResult], error) {
    graph := compose.NewGraph[*TeamState, *TeamResult]()
    
    researcher, _ := NewResearcherAgent(ctx)
    analyst, _ := NewAnalystAgent(ctx)
    
    graph.AddLambdaNode("router", routerNode)
    graph.AddLambdaNode("researcher", wrapAgent(researcher))
    graph.AddLambdaNode("analyst", wrapAgent(analyst))
    
    graph.AddEdge(compose.START, "router")
    graph.AddBranch("router", routeToAgent, map[string]string{
        "researcher": "researcher",
        "analyst":    "analyst",
        "done":       compose.END,
    })
    
    return graph.Compile(ctx)
}
```

## 运行入口

```go
package main

import (
    "bufio"
    "context"
    "fmt"
    "os"
    "strings"

    "{project_name}/internal/agent"
)

func main() {
    ctx := context.Background()
    
    ag, err := agent.NewReActAgent(ctx)
    if err != nil {
        fmt.Fprintf(os.Stderr, "初始化失败: %v\n", err)
        os.Exit(1)
    }
    
    scanner := bufio.NewScanner(os.Stdin)
    fmt.Println("Agent 就绪，输入 exit 退出")
    
    for {
        fmt.Print("You: ")
        if !scanner.Scan() {
            break
        }
        input := strings.TrimSpace(scanner.Text())
        if input == "exit" || input == "quit" {
            break
        }
        
        result, err := ag.Run(ctx, input)
        if err != nil {
            fmt.Printf("错误: %v\n", err)
            continue
        }
        fmt.Printf("Agent: %s\n", result)
    }
}
```

## 注意事项

- EINO 基于 CloudWeGo 生态，与 Hertz/Kitex 天然集成
- Go 的类型系统使工具参数验证更严格
- `eino-ext` 包含第三方模型集成（OpenAI, Anthropic, Ollama 等）
- Graph 编排是 EINO 的推荐 Agent 实现方式
