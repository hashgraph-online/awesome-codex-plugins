# Phase 3: 工具与能力定义（Tools & Capabilities）引导细则

## 入口条件

- Phase 2 的 `agent-architecture.md` 已确认
- 已知组件拓扑和 Agent 角色

## 工具定义流程

### Step 1: 工具清单推导

从 agent-spec.md 和 agent-architecture.md 中提取所有需要的工具：

1. 分析 Agent 核心能力 → 每个能力拆分为 1-N 个工具
2. 分析外部依赖 → 每个依赖封装为 1 个工具
3. Multi-Agent 场景 → 按角色列出各自的工具

示例推导：
| 核心能力 | 推导出的工具 |
|---------|------------|
| "能搜索网页" | `web_search(query: str) → results: list` |
| "能读写数据库" | `db_query(sql: str)`, `db_write(table, data)` |
| "能发送邮件" | `send_email(to, subject, body)` |

### Step 2: 逐工具交互确认

对每个工具，展示以下结构并让用户确认：

```yaml
- name: web_search
  description: "搜索网页并返回摘要结果"
  parameters:
    - name: query
      type: string
      required: true
      description: "搜索关键词"
    - name: max_results
      type: integer
      required: false
      default: 5
      description: "最大返回结果数"
  returns:
    type: array
    items:
      title: string
      url: string
      snippet: string
  implementation:
    strategy: api_call          # api_call / db_query / file_op / custom_logic / external_service
    endpoint: "https://api.example.com/search"
    auth: api_key
  error_handling:
    timeout: 10s
    retry: 2
    fallback: "返回空结果列表"
```

**交互规则**:
- 每次展示 1 个工具定义，等用户说"确认"或给出修改意见
- 用户可以随时添加额外的工具
- 用户可以合并或拆分工具

### Step 3: Memory 策略定义

根据 Agent 类型展示 Memory 选项：

| Memory 类型 | 适用场景 | 配置项 |
|------------|---------|--------|
| `conversation_buffer` | 短对话，直接保留全部 | `max_messages: 50` |
| `conversation_window` | 中等对话，滑动窗口 | `window_size: 20` |
| `conversation_summary` | 长对话，自动摘要 | `summary_model: gpt-4o-mini` |
| `entity_memory` | 需要跟踪实体状态 | `entity_types: [user, task]` |
| `vector_memory` | 大规模历史上下文召回 | `embedding_model, top_k` |

推荐组合：
- 简单对话 Agent → `conversation_buffer`
- 客服 Agent → `conversation_window` + `entity_memory`
- 知识问答 → `conversation_buffer` + `vector_memory`

### Step 4: RAG Pipeline 定义（如适用）

如果 Agent 包含 RAG 能力，逐步配置：

**4a. 数据源**:
```yaml
data_sources:
  - type: file           # file / api / database / url
    path: "./docs/"
    formats: [pdf, md, txt]
  - type: api
    endpoint: "https://..."
    auth: bearer_token
```

**4b. 文档处理**:
```yaml
processing:
  chunking:
    strategy: recursive    # recursive / character / token / semantic
    chunk_size: 1000
    chunk_overlap: 200
    separators: ["\n\n", "\n", " "]
  metadata:
    extract: [title, source, date]
```

**4c. Embedding**:
```yaml
embedding:
  model: text-embedding-3-small   # text-embedding-3-small / text-embedding-ada-002 / bge-large-zh
  dimensions: 1536
  batch_size: 100
```

**4d. 向量存储**:
```yaml
vector_store:
  backend: chroma          # faiss / chroma / milvus / weaviate / qdrant / pgvector
  collection: "{agent_name}_knowledge"
  distance_metric: cosine
```

**4e. 检索策略**:
```yaml
retrieval:
  strategy: hybrid         # similarity / mmr / hybrid
  top_k: 5
  score_threshold: 0.7
  reranker:                # 可选
    model: bge-reranker-large
    top_n: 3
```

## agent-tools.md 输出模板

```markdown
# Agent Tools & Capabilities

## 工具清单

| # | 名称 | 描述 | 输入 | 输出 | 实现策略 |
|---|------|------|------|------|----------|
| 1 | {name} | {desc} | {input} | {output} | {strategy} |

## 工具详细定义

### Tool 1: {name}

\`\`\`yaml
{complete_tool_definition}
\`\`\`

## Memory 配置

| 配置项 | 值 |
|--------|-----|
| 类型 | {type} |
| 存储后端 | {backend} |
| 窗口大小 | {window} |

## RAG Pipeline（如适用）

{rag_pipeline_config}

## 外部依赖清单

| 依赖 | 类型 | 用途 | 认证方式 |
|------|------|------|----------|
| {dep} | {type} | {purpose} | {auth} |
```

## 确认点

全部工具定义逐个确认后，展示完整 agent-tools.md，再次整体确认。
