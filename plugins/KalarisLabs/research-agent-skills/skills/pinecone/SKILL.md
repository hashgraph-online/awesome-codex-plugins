---
name: pinecone
description: Guides use of Pinecone, a managed serverless vector database, through its Python client and the LangChain and LlamaIndex integrations. Covers creating indexes, upserting and querying vectors, metadata filtering, namespaces, hybrid dense and sparse search, index management, and deleting vectors. Use when building a production RAG system on a hosted vector store, adding semantic search or recommendations without running infrastructure, isolating per-user or per-tenant data with namespaces, combining dense and sparse vectors in one query, or filtering results by metadata. Do not use for self-hosted or local stores (Chroma, Weaviate) or offline similarity search (FAISS).
license: MIT
metadata:
  version: 1.0.0
  category: knowledge-and-rag
  maintainer: Kalaris Labs
  tags: RAG, Pinecone, Vector Database, Managed Service, Serverless, Hybrid Search, Production, Auto-Scaling, Low Latency, Recommendations
  dependencies: pinecone-client
---

# Pinecone - Managed Vector Database

The vector database for production AI applications.

## When to use Pinecone

**Use when:**
- Need managed, serverless vector database
- Production RAG applications
- Auto-scaling required
- Low latency critical (<100ms)
- Don't want to manage infrastructure
- Need hybrid search (dense + sparse vectors)

**Metrics**:
- Fully managed SaaS
- Auto-scales to billions of vectors
- **p95 latency <100ms**
- 99.9% uptime SLA

**Use alternatives instead**:
- **Chroma**: Self-hosted, open-source
- **FAISS**: Offline, pure similarity search
- **Weaviate**: Self-hosted with more features

## Quick start

### Installation

```bash
pip install pinecone-client
```

### Basic usage

```python
from pinecone import Pinecone, ServerlessSpec

# Initialize
pc = Pinecone(api_key="your-api-key")

# Create index
pc.create_index(
    name="my-index",
    dimension=1536,  # Must match embedding dimension
    metric="cosine",  # or "euclidean", "dotproduct"
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

# Connect to index
index = pc.Index("my-index")

# Upsert vectors
index.upsert(vectors=[
    {"id": "vec1", "values": [0.1, 0.2, ...], "metadata": {"category": "A"}},
    {"id": "vec2", "values": [0.3, 0.4, ...], "metadata": {"category": "B"}}
])

# Query
results = index.query(
    vector=[0.1, 0.2, ...],
    top_k=5,
    include_metadata=True
)

print(results["matches"])
```

## Core operations

### Create index

```python
# Serverless (recommended)
pc.create_index(
    name="my-index",
    dimension=1536,
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",         # or "gcp", "azure"
        region="us-east-1"
    )
)

# Pod-based (for consistent performance)
from pinecone import PodSpec

pc.create_index(
    name="my-index",
    dimension=1536,
    metric="cosine",
    spec=PodSpec(
        environment="us-east1-gcp",
        pod_type="p1.x1"
    )
)
```

### Upsert vectors

```python
# Single upsert
index.upsert(vectors=[
    {
        "id": "doc1",
        "values": [0.1, 0.2, ...],  # 1536 dimensions
        "metadata": {
            "text": "Document content",
            "category": "tutorial",
            "timestamp": "2025-01-01"
        }
    }
])

# Batch upsert (recommended)
vectors = [
    {"id": f"vec{i}", "values": embedding, "metadata": metadata}
    for i, (embedding, metadata) in enumerate(zip(embeddings, metadatas))
]

index.upsert(vectors=vectors, batch_size=100)
```

### Query vectors

```python
# Basic query
results = index.query(
    vector=[0.1, 0.2, ...],
    top_k=10,
    include_metadata=True,
    include_values=False
)

# With metadata filtering
results = index.query(
    vector=[0.1, 0.2, ...],
    top_k=5,
    filter={"category": {"$eq": "tutorial"}}
)

# Namespace query
results = index.query(
    vector=[0.1, 0.2, ...],
    top_k=5,
    namespace="production"
)

# Access results
for match in results["matches"]:
    print(f"ID: {match['id']}")
    print(f"Score: {match['score']}")
    print(f"Metadata: {match['metadata']}")
```

### Metadata filtering

```python
# Exact match
filter = {"category": "tutorial"}

# Comparison
filter = {"price": {"$gte": 100}}  # $gt, $gte, $lt, $lte, $ne

# Logical operators
filter = {
    "$and": [
        {"category": "tutorial"},
        {"difficulty": {"$lte": 3}}
    ]
}  # Also: $or

# In operator
filter = {"tags": {"$in": ["python", "ml"]}}
```

## Namespaces

```python
# Partition data by namespace
index.upsert(
    vectors=[{"id": "vec1", "values": [...]}],
    namespace="user-123"
)

# Query specific namespace
results = index.query(
    vector=[...],
    namespace="user-123",
    top_k=5
)

# List namespaces
stats = index.describe_index_stats()
print(stats['namespaces'])
```

## Hybrid search (dense + sparse)

```python
# Upsert with sparse vectors
index.upsert(vectors=[
    {
        "id": "doc1",
        "values": [0.1, 0.2, ...],  # Dense vector
        "sparse_values": {
            "indices": [10, 45, 123],  # Token IDs
            "values": [0.5, 0.3, 0.8]   # TF-IDF scores
        },
        "metadata": {"text": "..."}
    }
])

# Hybrid query
results = index.query(
    vector=[0.1, 0.2, ...],
    sparse_vector={
        "indices": [10, 45],
        "values": [0.5, 0.3]
    },
    top_k=5,
    alpha=0.5  # 0=sparse, 1=dense, 0.5=hybrid
)
```

## LangChain integration

```python
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings

# Create vector store
vectorstore = PineconeVectorStore.from_documents(
    documents=docs,
    embedding=OpenAIEmbeddings(),
    index_name="my-index"
)

# Query
results = vectorstore.similarity_search("query", k=5)

# With metadata filter
results = vectorstore.similarity_search(
    "query",
    k=5,
    filter={"category": "tutorial"}
)

# As retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
```

## LlamaIndex integration

```python
from llama_index.vector_stores.pinecone import PineconeVectorStore

# Connect to Pinecone
pc = Pinecone(api_key="your-key")
pinecone_index = pc.Index("my-index")

# Create vector store
vector_store = PineconeVectorStore(pinecone_index=pinecone_index)

# Use in LlamaIndex
from llama_index.core import StorageContext, VectorStoreIndex

storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
```

## Index management

```python
# List indices
indexes = pc.list_indexes()

# Describe index
index_info = pc.describe_index("my-index")
print(index_info)

# Get index stats
stats = index.describe_index_stats()
print(f"Total vectors: {stats['total_vector_count']}")
print(f"Namespaces: {stats['namespaces']}")

# Delete index
pc.delete_index("my-index")
```

## Delete vectors

```python
# Delete by ID
index.delete(ids=["vec1", "vec2"])

# Delete by filter
index.delete(filter={"category": "old"})

# Delete all in namespace
index.delete(delete_all=True, namespace="test")

# Delete entire index
index.delete(delete_all=True)
```

## Best practices

1. **Use serverless** - Auto-scaling, cost-effective
2. **Batch upserts** - More efficient (100-200 per batch)
3. **Add metadata** - Enable filtering
4. **Use namespaces** - Isolate data by user/tenant
5. **Monitor usage** - Check Pinecone dashboard
6. **Optimize filters** - Index frequently filtered fields
7. **Test with free tier** - 1 index, 100K vectors free
8. **Use hybrid search** - Better quality
9. **Set appropriate dimensions** - Match embedding model
10. **Regular backups** - Export important data

## Performance

| Operation | Latency | Notes |
|-----------|---------|-------|
| Upsert | ~50-100ms | Per batch |
| Query (p50) | ~50ms | Depends on index size |
| Query (p95) | ~100ms | SLA target |
| Metadata filter | ~+10-20ms | Additional overhead |

## Pricing (as of 2025)

**Serverless**:
- $0.096 per million read units
- $0.06 per million write units
- $0.06 per GB storage/month

**Free tier**:
- 1 serverless index
- 100K vectors (1536 dimensions)
- Great for prototyping

## Resources

- **Website**: https://www.pinecone.io
- **Docs**: https://docs.pinecone.io
- **Console**: https://app.pinecone.io
- **Pricing**: https://www.pinecone.io/pricing

## Agent operating procedure

1. **Check the environment.** Confirm the corpus, embedding model and vector store versions, and where the index will live.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Index a small subset and test retrieval on known question-passage pairs.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Measure recall@k on a labeled set; answers cite retrieved passages only.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Retrieval returns irrelevant chunks | Revisit chunking, add BM25/hybrid search, or re-rank before changing the generator. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Answers must come from retrieved text; say when the corpus does not contain the answer.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `faiss`: Facebook's library for efficient similarity search and clustering of dense vectors.
- `qdrant-vector-search`: High-performance vector similarity search engine for RAG and semantic search.
- `chroma`: Open-source embedding database for AI applications.
