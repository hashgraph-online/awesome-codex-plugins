---
name: llamaindex
description: Data framework for building LLM applications with RAG. Specializes in document ingestion (300+ connectors), indexing, and querying. Features vector indices, query engines, agents, and multi-modal support. Use for document Q&A, chatbots, knowledge retrieval, or building RAG pipelines. Best for data-centric LLM applications.
license: MIT
metadata:
  version: 1.0.0
  category: llm-applications
  maintainer: Kalaris Labs
  tags: Agents, LlamaIndex, RAG, Document Ingestion, Vector Indices, Query Engines, Knowledge Retrieval, Data Framework, Multimodal, Private Data, Connectors
  dependencies: llama-index, openai, anthropic
---

# LlamaIndex - Data Framework for LLM Applications

The leading framework for connecting LLMs with your data.

## When to use LlamaIndex

**Use LlamaIndex when:**
- Building RAG (retrieval-augmented generation) applications
- Need document question-answering over private data
- Ingesting data from multiple sources (300+ connectors)
- Creating knowledge bases for LLMs
- Building chatbots with enterprise data
- Need structured data extraction from documents

**Metrics**:
- **23,000+ repositories** use LlamaIndex
- **300+ data connectors** (LlamaHub)
- **1,715+ contributors**
- **v0.14.7** (stable)

**Use alternatives instead**:
- **LangChain**: More general-purpose, better for agents
- **Haystack**: Production search pipelines
- **txtai**: Lightweight semantic search
- **Chroma**: Just need vector storage

## Quick start

### Installation

```bash
# Starter package (recommended)
pip install llama-index

# Or minimal core + specific integrations
pip install llama-index-core
pip install llama-index-llms-openai
pip install llama-index-embeddings-openai
```

### 5-line RAG example

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# Load documents
documents = SimpleDirectoryReader("data").load_data()

# Create index
index = VectorStoreIndex.from_documents(documents)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("What did the author do growing up?")
print(response)
```

## Core concepts

### 1. Data connectors - Load documents

```python
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.readers.web import SimpleWebPageReader
from llama_index.readers.github import GithubRepositoryReader

# Directory of files
documents = SimpleDirectoryReader("./data").load_data()

# Web pages
reader = SimpleWebPageReader()
documents = reader.load_data(["https://example.com"])

# GitHub repository
reader = GithubRepositoryReader(owner="user", repo="repo")
documents = reader.load_data(branch="main")

# Manual document creation
doc = Document(
    text="This is the document content",
    metadata={"source": "manual", "date": "2025-01-01"}
)
```

### 2. Indices - Structure data

```python
from llama_index.core import VectorStoreIndex, ListIndex, TreeIndex

# Vector index (most common - semantic search)
vector_index = VectorStoreIndex.from_documents(documents)

# List index (sequential scan)
list_index = ListIndex.from_documents(documents)

# Tree index (hierarchical summary)
tree_index = TreeIndex.from_documents(documents)

# Save index
index.storage_context.persist(persist_dir="./storage")

# Load index
from llama_index.core import load_index_from_storage, StorageContext
storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context)
```

### 3. Query engines - Ask questions

```python
# Basic query
query_engine = index.as_query_engine()
response = query_engine.query("What is the main topic?")
print(response)

# Streaming response
query_engine = index.as_query_engine(streaming=True)
response = query_engine.query("Explain quantum computing")
for text in response.response_gen:
    print(text, end="", flush=True)

# Custom configuration
query_engine = index.as_query_engine(
    similarity_top_k=3,          # Return top 3 chunks
    response_mode="compact",     # Or "tree_summarize", "simple_summarize"
    verbose=True
)
```

### 4. Retrievers - Find relevant chunks

```python
# Vector retriever
retriever = index.as_retriever(similarity_top_k=5)
nodes = retriever.retrieve("machine learning")

# With filtering
retriever = index.as_retriever(
    similarity_top_k=3,
    filters={"metadata.category": "tutorial"}
)

# Custom retriever
from llama_index.core.retrievers import BaseRetriever

class CustomRetriever(BaseRetriever):
    def _retrieve(self, query_bundle):
        # Your custom retrieval logic
        return nodes
```

## Agents with tools

Details, code examples and parameter tables: [references/agents-with-tools.md](references/agents-with-tools.md). Read it when this step applies.

## Advanced RAG patterns

Details, code examples and parameter tables: [references/advanced-rag-patterns.md](references/advanced-rag-patterns.md). Read it when this step applies.

## Data ingestion patterns

### Multiple file types

```python
# Load all supported formats
documents = SimpleDirectoryReader(
    "./data",
    recursive=True,
    required_exts=[".pdf", ".docx", ".txt", ".md"]
).load_data()
```

### Web scraping

```python
from llama_index.readers.web import BeautifulSoupWebReader

reader = BeautifulSoupWebReader()
documents = reader.load_data(urls=[
    "https://docs.python.org/3/tutorial/",
    "https://docs.python.org/3/library/"
])
```

### Database

```python
from llama_index.readers.database import DatabaseReader

reader = DatabaseReader(
    sql_database_uri="postgresql://user:pass@localhost/db"
)
documents = reader.load_data(query="SELECT * FROM articles")
```

### API endpoints

```python
from llama_index.readers.json import JSONReader

reader = JSONReader()
documents = reader.load_data("https://api.example.com/data.json")
```

## Vector store integrations

### Chroma (local)

```python
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# Initialize Chroma
db = chromadb.PersistentClient(path="./chroma_db")
collection = db.get_or_create_collection("my_collection")

# Create vector store
vector_store = ChromaVectorStore(chroma_collection=collection)

# Use in index
from llama_index.core import StorageContext
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
```

### Pinecone (cloud)

```python
from llama_index.vector_stores.pinecone import PineconeVectorStore
import pinecone

# Initialize Pinecone
pinecone.init(api_key="your-key", environment="us-west1-gcp")
pinecone_index = pinecone.Index("my-index")

# Create vector store
vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
```

### FAISS (fast)

```python
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

# Create FAISS index
d = 1536  # Dimension of embeddings
faiss_index = faiss.IndexFlatL2(d)

vector_store = FaissVectorStore(faiss_index=faiss_index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
```

## Customization

### Custom LLM

```python
from llama_index.llms.anthropic import Anthropic
from llama_index.core import Settings

# Set global LLM
Settings.llm = Anthropic(model="claude-sonnet-4-5-20250929")

# Now all queries use Anthropic
query_engine = index.as_query_engine()
```

### Custom embeddings

```python
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Use HuggingFace embeddings
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-mpnet-base-v2"
)

index = VectorStoreIndex.from_documents(documents)
```

### Custom prompt templates

```python
from llama_index.core import PromptTemplate

qa_prompt = PromptTemplate(
    "Context: {context_str}\n"
    "Question: {query_str}\n"
    "Answer the question based only on the context. "
    "If the answer is not in the context, say 'I don't know'.\n"
    "Answer: "
)

query_engine = index.as_query_engine(text_qa_template=qa_prompt)
```

## Multi-modal RAG

### Image + text

```python
from llama_index.core import SimpleDirectoryReader
from llama_index.multi_modal_llms.openai import OpenAIMultiModal

# Load images and documents
documents = SimpleDirectoryReader(
    "./data",
    required_exts=[".jpg", ".png", ".pdf"]
).load_data()

# Multi-modal index
index = VectorStoreIndex.from_documents(documents)

# Query with multi-modal LLM
multi_modal_llm = OpenAIMultiModal(model="gpt-4o")
query_engine = index.as_query_engine(llm=multi_modal_llm)

response = query_engine.query("What is in the diagram on page 3?")
```

## Evaluation

### Response quality

```python
from llama_index.core.evaluation import RelevancyEvaluator, FaithfulnessEvaluator

# Evaluate relevance
relevancy = RelevancyEvaluator()
result = relevancy.evaluate_response(
    query="What is Python?",
    response=response
)
print(f"Relevancy: {result.passing}")

# Evaluate faithfulness (no hallucination)
faithfulness = FaithfulnessEvaluator()
result = faithfulness.evaluate_response(
    query="What is Python?",
    response=response
)
print(f"Faithfulness: {result.passing}")
```

## Best practices

1. **Use vector indices for most cases** - Best performance
2. **Save indices to disk** - Avoid re-indexing
3. **Chunk documents properly** - 512-1024 tokens optimal
4. **Add metadata** - Enables filtering and tracking
5. **Use streaming** - Better UX for long responses
6. **Enable verbose during dev** - See retrieval process
7. **Evaluate responses** - Check relevance and faithfulness
8. **Use chat engine for conversations** - Built-in memory
9. **Persist storage** - Don't lose your index
10. **Monitor costs** - Track embedding and LLM usage

## Common patterns

### Document Q&A system

```python
# Complete RAG pipeline
documents = SimpleDirectoryReader("docs").load_data()
index = VectorStoreIndex.from_documents(documents)
index.storage_context.persist(persist_dir="./storage")

# Query
query_engine = index.as_query_engine(
    similarity_top_k=3,
    response_mode="compact",
    verbose=True
)
response = query_engine.query("What is the main topic?")
print(response)
print(f"Sources: {[node.metadata['file_name'] for node in response.source_nodes]}")
```

### Chatbot with memory

```python
# Conversational interface
chat_engine = index.as_chat_engine(
    chat_mode="condense_plus_context",
    verbose=True
)

# Multi-turn chat
while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break
    response = chat_engine.chat(user_input)
    print(f"Bot: {response}")
```

## Performance benchmarks

| Operation | Latency | Notes |
|-----------|---------|-------|
| Index 100 docs | ~10-30s | One-time, can persist |
| Query (vector) | ~0.5-2s | Retrieval + LLM |
| Streaming query | ~0.5s first token | Better UX |
| Agent with tools | ~3-8s | Multiple tool calls |

## LlamaIndex vs LangChain

| Feature | LlamaIndex | LangChain |
|---------|------------|-----------|
| **Best for** | RAG, document Q&A | Agents, general LLM apps |
| **Data connectors** | 300+ (LlamaHub) | 100+ |
| **RAG focus** | Core feature | One of many |
| **Learning curve** | Easier for RAG | Steeper |
| **Customization** | High | Very high |
| **Documentation** | Excellent | Good |

**Use LlamaIndex when:**
- Your primary use case is RAG
- Need many data connectors
- Want simpler API for document Q&A
- Building knowledge retrieval system

**Use LangChain when:**
- Building complex agents
- Need more general-purpose tools
- Want more flexibility
- Complex multi-step workflows

## References

- **[Query Engines Guide](references/query_engines.md)** - Query modes, customization, streaming
- **[Agents Guide](references/agents.md)** - Tool creation, RAG agents, multi-step reasoning
- **[Data Connectors Guide](references/data_connectors.md)** - 300+ connectors, custom loaders

## Resources

- **GitHub**: https://github.com/run-llama/llama_index ⭐ 45,100+
- **Docs**: https://developers.llamaindex.ai/python/framework/
- **LlamaHub**: https://llamahub.ai (data connectors)
- **LlamaCloud**: https://cloud.llamaindex.ai (enterprise)
- **Discord**: https://discord.gg/dGcwcsnxhU
- **Version**: 0.14.7+
- **License**: MIT

## Agent operating procedure

1. **Check the environment.** Confirm the framework version, model provider, API keys and rate limits.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Test a single call or chain with a known input and inspect raw outputs.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Evaluate on a small labeled set; check structured outputs against their schema; log prompts and responses.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Outputs do not match the expected schema | Add validation and retries, tighten the schema, or simplify the prompt. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never send private or sensitive data to external APIs without the user's consent.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `langchain`: Framework for building LLM-powered applications with agents, chains, and RAG.
- `chroma`: Open-source embedding database for AI applications.
- `langsmith-observability`: LLM observability platform for tracing, evaluation, and monitoring.
