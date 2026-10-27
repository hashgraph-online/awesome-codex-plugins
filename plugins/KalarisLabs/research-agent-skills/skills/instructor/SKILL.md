---
name: instructor
description: Extracts structured, validated data from LLM responses using the Instructor Python library with Pydantic response models, including nested models, enums, custom validators, automatic retries with validation error feedback, and streaming of partial objects or iterables. Works with Anthropic, OpenAI, and local Ollama models. Use when pulling typed fields or entities out of free text, when classifying text into fixed categories, when an LLM must return JSON that passes schema validation, when failed extractions need automatic retry, or when streaming partial structured results. Not for prompt optimization (use DSPy) or building multi-step chains (use LangChain).
license: MIT
metadata:
  version: 1.0.0
  category: llm-applications
  maintainer: Kalaris Labs
  tags: Prompt Engineering, Instructor, Structured Output, Pydantic, Data Extraction, JSON Parsing, Type Safety, Validation, Streaming, OpenAI, Anthropic
  dependencies: instructor, pydantic, openai, anthropic
---

# Instructor: Structured LLM Outputs

## When to Use This Skill

Use Instructor when you need to:
- **Extract structured data** from LLM responses reliably
- **Validate outputs** against Pydantic schemas automatically
- **Retry failed extractions** with automatic error handling
- **Parse complex JSON** with type safety and validation
- **Stream partial results** for real-time processing
- **Support multiple LLM providers** with consistent API


## Installation

```bash
# Base installation
pip install instructor

# With specific providers
pip install "instructor[anthropic]"  # Anthropic Claude
pip install "instructor[openai]"     # OpenAI
pip install "instructor[all]"        # All providers
```

## Quick Start

### Basic Example: Extract User Data

```python
import instructor
from pydantic import BaseModel
from anthropic import Anthropic

# Define output structure
class User(BaseModel):
    name: str
    age: int
    email: str

# Create instructor client
client = instructor.from_anthropic(Anthropic())

# Extract structured data
user = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "John Doe is 30 years old. His email is john@example.com"
    }],
    response_model=User
)

print(user.name)   # "John Doe"
print(user.age)    # 30
print(user.email)  # "john@example.com"
```

### With OpenAI

```python
from openai import OpenAI

client = instructor.from_openai(OpenAI())

user = client.chat.completions.create(
    model="gpt-4o-mini",
    response_model=User,
    messages=[{"role": "user", "content": "Extract: Alice, 25, alice@email.com"}]
)
```

## Core Concepts

### 1. Response Models (Pydantic)

Response models define the structure and validation rules for LLM outputs.

#### Basic Model

```python
from pydantic import BaseModel, Field

class Article(BaseModel):
    title: str = Field(description="Article title")
    author: str = Field(description="Author name")
    word_count: int = Field(description="Number of words", gt=0)
    tags: list[str] = Field(description="List of relevant tags")

article = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Analyze this article: [article text]"
    }],
    response_model=Article
)
```

**Benefits:**
- Type safety with Python type hints
- Automatic validation (word_count > 0)
- Self-documenting with Field descriptions
- IDE autocomplete support

#### Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    country: str

class Person(BaseModel):
    name: str
    age: int
    address: Address  # Nested model

person = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "John lives at 123 Main St, Boston, USA"
    }],
    response_model=Person
)

print(person.address.city)  # "Boston"
```

#### Optional Fields

```python
from typing import Optional

class Product(BaseModel):
    name: str
    price: float
    discount: Optional[float] = None  # Optional
    description: str = Field(default="No description")  # Default value

# LLM doesn't need to provide discount or description
```

#### Enums for Constraints

```python
from enum import Enum

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class Review(BaseModel):
    text: str
    sentiment: Sentiment  # Only these 3 values allowed

review = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "This product is amazing!"
    }],
    response_model=Review
)

print(review.sentiment)  # Sentiment.POSITIVE
```

### 2. Validation

Pydantic validates LLM outputs automatically. If validation fails, Instructor retries.

#### Built-in Validators

```python
from pydantic import Field, EmailStr, HttpUrl

class Contact(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=120)  # 0 <= age <= 120
    email: EmailStr  # Validates email format
    website: HttpUrl  # Validates URL format

# If LLM provides invalid data, Instructor retries automatically
```

#### Custom Validators

```python
from pydantic import field_validator

class Event(BaseModel):
    name: str
    date: str
    attendees: int

    @field_validator('date')
    def validate_date(cls, v):
        """Ensure date is in YYYY-MM-DD format."""
        import re
        if not re.match(r'\d{4}-\d{2}-\d{2}', v):
            raise ValueError('Date must be YYYY-MM-DD format')
        return v

    @field_validator('attendees')
    def validate_attendees(cls, v):
        """Ensure positive attendees."""
        if v < 1:
            raise ValueError('Must have at least 1 attendee')
        return v
```

#### Model-Level Validation

```python
from pydantic import model_validator

class DateRange(BaseModel):
    start_date: str
    end_date: str

    @model_validator(mode='after')
    def check_dates(self):
        """Ensure end_date is after start_date."""
        from datetime import datetime
        start = datetime.strptime(self.start_date, '%Y-%m-%d')
        end = datetime.strptime(self.end_date, '%Y-%m-%d')

        if end < start:
            raise ValueError('end_date must be after start_date')
        return self
```

### 3. Automatic Retrying

Instructor retries automatically when validation fails, providing error feedback to the LLM.

```python
# Retries up to 3 times if validation fails
user = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Extract user from: John, age unknown"
    }],
    response_model=User,
    max_retries=3  # Default is 3
)

# If age can't be extracted, Instructor tells the LLM:
# "Validation error: age - field required"
# LLM tries again with better extraction
```

**How it works:**
1. LLM generates output
2. Pydantic validates
3. If invalid: Error message sent back to LLM
4. LLM tries again with error feedback
5. Repeats up to max_retries

### 4. Streaming

Stream partial results for real-time processing.

#### Streaming Partial Objects

```python
from instructor import Partial

class Story(BaseModel):
    title: str
    content: str
    tags: list[str]

# Stream partial updates as LLM generates
for partial_story in client.messages.create_partial(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Write a short sci-fi story"
    }],
    response_model=Story
):
    print(f"Title: {partial_story.title}")
    print(f"Content so far: {partial_story.content[:100]}...")
    # Update UI in real-time
```

#### Streaming Iterables

```python
class Task(BaseModel):
    title: str
    priority: str

# Stream list items as they're generated
tasks = client.messages.create_iterable(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Generate 10 project tasks"
    }],
    response_model=Task
)

for task in tasks:
    print(f"- {task.title} ({task.priority})")
    # Process each task as it arrives
```

## Provider Configuration

Details, code examples and parameter tables: [references/provider-configuration.md](references/provider-configuration.md). Read it when this step applies.

## Common Patterns

Details, code examples and parameter tables: [references/common-patterns.md](references/common-patterns.md). Read it when this step applies.

## Advanced Features

Details, code examples and parameter tables: [references/advanced-features.md](references/advanced-features.md). Read it when this step applies.

## Error Handling

Details, code examples and parameter tables: [references/error-handling.md](references/error-handling.md). Read it when this step applies.

## Best Practices

### 1. Clear Field Descriptions

```python
# ❌ Bad: Vague
class Product(BaseModel):
    name: str
    price: float

# ✅ Good: Descriptive
class Product(BaseModel):
    name: str = Field(description="Product name from the text")
    price: float = Field(description="Price in USD, without currency symbol")
```

### 2. Use Appropriate Validation

```python
# ✅ Good: Constrain values
class Rating(BaseModel):
    score: int = Field(ge=1, le=5, description="Rating from 1 to 5 stars")
    review: str = Field(min_length=10, description="Review text, at least 10 chars")
```

### 3. Provide Examples in Prompts

```python
messages = [{
    "role": "user",
    "content": """Extract person info from: "John, 30, engineer"

Example format:
{
  "name": "John Doe",
  "age": 30,
  "occupation": "engineer"
}"""
}]
```

### 4. Use Enums for Fixed Categories

```python
# ✅ Good: Enum ensures valid values
class Status(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Application(BaseModel):
    status: Status  # LLM must choose from enum
```

### 5. Handle Missing Data Gracefully

```python
class PartialData(BaseModel):
    required_field: str
    optional_field: Optional[str] = None
    default_field: str = "default_value"

# LLM only needs to provide required_field
```

## Comparison to Alternatives

| Feature | Instructor | Manual JSON | LangChain | DSPy |
|---------|------------|-------------|-----------|------|
| Type Safety | ✅ Yes | ❌ No | ⚠️ Partial | ✅ Yes |
| Auto Validation | ✅ Yes | ❌ No | ❌ No | ⚠️ Limited |
| Auto Retry | ✅ Yes | ❌ No | ❌ No | ✅ Yes |
| Streaming | ✅ Yes | ❌ No | ✅ Yes | ❌ No |
| Multi-Provider | ✅ Yes | ⚠️ Manual | ✅ Yes | ✅ Yes |
| Learning Curve | Low | Low | Medium | High |

**When to choose Instructor:**
- Need structured, validated outputs
- Want type safety and IDE support
- Require automatic retries
- Building data extraction systems

**When to choose alternatives:**
- DSPy: Need prompt optimization
- LangChain: Building complex chains
- Manual: Simple, one-off extractions

## Resources

- **Documentation**: https://python.useinstructor.com
- **GitHub**: https://github.com/jxnl/instructor
- **Cookbook**: https://python.useinstructor.com/examples
- **Discord**: Community support available

## See Also

- `references/validation.md` - Advanced validation patterns
- `references/providers.md` - Provider-specific configuration
- `references/examples.md` - Real-world use cases

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
