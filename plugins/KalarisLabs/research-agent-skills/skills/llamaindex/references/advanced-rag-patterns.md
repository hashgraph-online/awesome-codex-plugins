# Advanced RAG patterns

### Chat engine (conversational)

```python
from llama_index.core.chat_engine import CondensePlusContextChatEngine

# Chat with memory
chat_engine = index.as_chat_engine(
    chat_mode="condense_plus_context",  # Or "context", "react"
    verbose=True
)

# Multi-turn conversation
response1 = chat_engine.chat("What is Python?")
response2 = chat_engine.chat("Can you give examples?")  # Remembers context
response3 = chat_engine.chat("What about web frameworks?")
```

### Metadata filtering

```python
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

# Filter by metadata
filters = MetadataFilters(
    filters=[
        ExactMatchFilter(key="category", value="tutorial"),
        ExactMatchFilter(key="difficulty", value="beginner")
    ]
)

retriever = index.as_retriever(
    similarity_top_k=3,
    filters=filters
)

query_engine = index.as_query_engine(filters=filters)
```

### Structured output

```python
from pydantic import BaseModel
from llama_index.core.output_parsers import PydanticOutputParser

class Summary(BaseModel):
    title: str
    main_points: list[str]
    conclusion: str

# Get structured response
output_parser = PydanticOutputParser(output_cls=Summary)
query_engine = index.as_query_engine(output_parser=output_parser)

response = query_engine.query("Summarize the document")
summary = response  # Pydantic model
print(summary.title, summary.main_points)
```
