# Advanced Features

### Union Types

```python
from typing import Union

class TextContent(BaseModel):
    type: str = "text"
    content: str

class ImageContent(BaseModel):
    type: str = "image"
    url: HttpUrl
    caption: str

class Post(BaseModel):
    title: str
    content: Union[TextContent, ImageContent]  # Either type

# LLM chooses appropriate type based on content
```

### Dynamic Models

```python
from pydantic import create_model

# Create model at runtime
DynamicUser = create_model(
    'User',
    name=(str, ...),
    age=(int, Field(ge=0)),
    email=(EmailStr, ...)
)

user = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[...],
    response_model=DynamicUser
)
```

### Custom Modes

```python
# For providers without native structured outputs
client = instructor.from_anthropic(
    Anthropic(),
    mode=instructor.Mode.JSON  # JSON mode
)

# Available modes:
# - Mode.ANTHROPIC_TOOLS (recommended for Claude)
# - Mode.JSON (fallback)
# - Mode.TOOLS (OpenAI tools)
```

### Context Management

```python
# Single-use client
with instructor.from_anthropic(Anthropic()) as client:
    result = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[...],
        response_model=YourModel
    )
    # Client closed automatically
```
