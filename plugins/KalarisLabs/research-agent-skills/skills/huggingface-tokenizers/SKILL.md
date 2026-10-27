---
name: huggingface-tokenizers
description: Provides the HuggingFace Tokenizers library (Rust core with Python and Node.js bindings) for training and using BPE, WordPiece, and Unigram tokenizers. Covers the pipeline of normalizers, pre-tokenizers, models, post-processors and decoders, padding and truncation, batch encoding, alignment tracking, and conversion to transformers PreTrainedTokenizerFast. Use when training a custom tokenizer or vocabulary on a new corpus, tokenizing large text corpora quickly, mapping tokens back to character offsets for NER or question answering, or configuring normalization and special tokens. Use when wrapping a custom tokenizer for transformers. For SentencePiece models or tiktoken, use those tools instead; for loading a pretrained tokenizer only, AutoTokenizer is enough.
license: MIT
metadata:
  version: 1.0.0
  category: ml-training
  maintainer: Kalaris Labs
  tags: Tokenization, HuggingFace, BPE, WordPiece, Unigram, Fast Tokenization, Rust, Custom Tokenizer, Alignment Tracking, Production
  dependencies: tokenizers, transformers, datasets
---

# HuggingFace Tokenizers - Fast Tokenization for NLP

Fast, production-ready tokenizers with Rust performance and Python ease-of-use.

## When to use HuggingFace Tokenizers

**Use HuggingFace Tokenizers when:**
- Need extremely fast tokenization (<20s per GB of text)
- Training custom tokenizers from scratch
- Want alignment tracking (token → original text position)
- Building production NLP pipelines
- Need to tokenize large corpora efficiently

**Performance**:
- **Speed**: <20 seconds to tokenize 1GB on CPU
- **Implementation**: Rust core with Python/Node.js bindings
- **Efficiency**: 10-100× faster than pure Python implementations

**Use alternatives instead**:
- **SentencePiece**: Language-independent, used by T5/ALBERT
- **tiktoken**: OpenAI's BPE tokenizer for GPT models
- **transformers AutoTokenizer**: Loading pretrained only (uses this library internally)

## Quick start

### Installation

```bash
# Install tokenizers
pip install tokenizers

# With transformers integration
pip install tokenizers transformers
```

### Load pretrained tokenizer

```python
from tokenizers import Tokenizer

# Load from HuggingFace Hub
tokenizer = Tokenizer.from_pretrained("bert-base-uncased")

# Encode text
output = tokenizer.encode("Hello, how are you?")
print(output.tokens)  # ['hello', ',', 'how', 'are', 'you', '?']
print(output.ids)     # [7592, 1010, 2129, 2024, 2017, 1029]

# Decode back
text = tokenizer.decode(output.ids)
print(text)  # "hello, how are you?"
```

### Train custom BPE tokenizer

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

# Initialize tokenizer with BPE model
tokenizer = Tokenizer(BPE(unk_token="[UNK]"))
tokenizer.pre_tokenizer = Whitespace()

# Configure trainer
trainer = BpeTrainer(
    vocab_size=30000,
    special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
    min_frequency=2
)

# Train on files
files = ["train.txt", "validation.txt"]
tokenizer.train(files, trainer)

# Save
tokenizer.save("my-tokenizer.json")
```

**Training time**: ~1-2 minutes for 100MB corpus, ~10-20 minutes for 1GB

### Batch encoding with padding

```python
# Enable padding
tokenizer.enable_padding(pad_id=3, pad_token="[PAD]")

# Encode batch
texts = ["Hello world", "This is a longer sentence"]
encodings = tokenizer.encode_batch(texts)

for encoding in encodings:
    print(encoding.ids)
# [101, 7592, 2088, 102, 3, 3, 3]
# [101, 2023, 2003, 1037, 2936, 6251, 102]
```

## Tokenization algorithms

Details, code examples and parameter tables: [references/tokenization-algorithms.md](references/tokenization-algorithms.md). Read it when this step applies.

## Tokenization pipeline

Complete pipeline: **Normalization → Pre-tokenization → Model → Post-processing**

### Normalization

Clean and standardize text:

```python
from tokenizers.normalizers import NFD, StripAccents, Lowercase, Sequence

tokenizer.normalizer = Sequence([
    NFD(),           # Unicode normalization (decompose)
    Lowercase(),     # Convert to lowercase
    StripAccents()   # Remove accents
])

# Input: "Héllo WORLD"
# After normalization: "hello world"
```

**Common normalizers**:
- `NFD`, `NFC`, `NFKD`, `NFKC` - Unicode normalization forms
- `Lowercase()` - Convert to lowercase
- `StripAccents()` - Remove accents (é → e)
- `Strip()` - Remove whitespace
- `Replace(pattern, content)` - Regex replacement

### Pre-tokenization

Split text into word-like units:

```python
from tokenizers.pre_tokenizers import Whitespace, Punctuation, Sequence, ByteLevel

# Split on whitespace and punctuation
tokenizer.pre_tokenizer = Sequence([
    Whitespace(),
    Punctuation()
])

# Input: "Hello, world!"
# After pre-tokenization: ["Hello", ",", "world", "!"]
```

**Common pre-tokenizers**:
- `Whitespace()` - Split on spaces, tabs, newlines
- `ByteLevel()` - GPT-2 style byte-level splitting
- `Punctuation()` - Isolate punctuation
- `Digits(individual_digits=True)` - Split digits individually
- `Metaspace()` - Replace spaces with ▁ (SentencePiece style)

### Post-processing

Add special tokens for model input:

```python
from tokenizers.processors import TemplateProcessing

# BERT-style: [CLS] sentence [SEP]
tokenizer.post_processor = TemplateProcessing(
    single="[CLS] $A [SEP]",
    pair="[CLS] $A [SEP] $B [SEP]",
    special_tokens=[
        ("[CLS]", 1),
        ("[SEP]", 2),
    ],
)
```

**Common patterns**:
```python
# GPT-2: sentence <|endoftext|>
TemplateProcessing(
    single="$A <|endoftext|>",
    special_tokens=[("<|endoftext|>", 50256)]
)

# RoBERTa: <s> sentence </s>
TemplateProcessing(
    single="<s> $A </s>",
    pair="<s> $A </s> </s> $B </s>",
    special_tokens=[("<s>", 0), ("</s>", 2)]
)
```

## Alignment tracking

Track token positions in original text:

```python
output = tokenizer.encode("Hello, world!")

# Get token offsets
for token, offset in zip(output.tokens, output.offsets):
    start, end = offset
    print(f"{token:10} → [{start:2}, {end:2}): {text[start:end]!r}")

# Output:
# hello      → [ 0,  5): 'Hello'
# ,          → [ 5,  6): ','
# world      → [ 7, 12): 'world'
# !          → [12, 13): '!'
```

**Use cases**:
- Named entity recognition (map predictions back to text)
- Question answering (extract answer spans)
- Token classification (align labels to original positions)

## Integration with transformers

### Load with AutoTokenizer

```python
from transformers import AutoTokenizer

# AutoTokenizer automatically uses fast tokenizers
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

# Check if using fast tokenizer
print(tokenizer.is_fast)  # True

# Access underlying tokenizers.Tokenizer
fast_tokenizer = tokenizer.backend_tokenizer
print(type(fast_tokenizer))  # <class 'tokenizers.Tokenizer'>
```

### Convert custom tokenizer to transformers

```python
from tokenizers import Tokenizer
from transformers import PreTrainedTokenizerFast

# Train custom tokenizer
tokenizer = Tokenizer(BPE())
# ... train tokenizer ...
tokenizer.save("my-tokenizer.json")

# Wrap for transformers
transformers_tokenizer = PreTrainedTokenizerFast(
    tokenizer_file="my-tokenizer.json",
    unk_token="[UNK]",
    pad_token="[PAD]",
    cls_token="[CLS]",
    sep_token="[SEP]",
    mask_token="[MASK]"
)

# Use like any transformers tokenizer
outputs = transformers_tokenizer(
    "Hello world",
    padding=True,
    truncation=True,
    max_length=512,
    return_tensors="pt"
)
```

## Common patterns

### Train from iterator (large datasets)

```python
from datasets import load_dataset

# Load dataset
dataset = load_dataset("wikitext", "wikitext-103-raw-v1", split="train")

# Create batch iterator
def batch_iterator(batch_size=1000):
    for i in range(0, len(dataset), batch_size):
        yield dataset[i:i + batch_size]["text"]

# Train tokenizer
tokenizer.train_from_iterator(
    batch_iterator(),
    trainer=trainer,
    length=len(dataset)  # For progress bar
)
```

**Performance**: Processes 1GB in ~10-20 minutes

### Enable truncation and padding

```python
# Enable truncation
tokenizer.enable_truncation(max_length=512)

# Enable padding
tokenizer.enable_padding(
    pad_id=tokenizer.token_to_id("[PAD]"),
    pad_token="[PAD]",
    length=512  # Fixed length, or None for batch max
)

# Encode with both
output = tokenizer.encode("This is a long sentence that will be truncated...")
print(len(output.ids))  # 512
```

### Multi-processing

```python
from tokenizers import Tokenizer
from multiprocessing import Pool

# Load tokenizer
tokenizer = Tokenizer.from_file("tokenizer.json")

def encode_batch(texts):
    return tokenizer.encode_batch(texts)

# Process large corpus in parallel
with Pool(8) as pool:
    # Split corpus into chunks
    chunk_size = 1000
    chunks = [corpus[i:i+chunk_size] for i in range(0, len(corpus), chunk_size)]

    # Encode in parallel
    results = pool.map(encode_batch, chunks)
```

**Speedup**: 5-8× with 8 cores

## Performance benchmarks

### Training speed

| Corpus Size | BPE (30k vocab) | WordPiece (30k) | Unigram (8k) |
|-------------|-----------------|-----------------|--------------|
| 10 MB       | 15 sec          | 18 sec          | 25 sec       |
| 100 MB      | 1.5 min         | 2 min           | 4 min        |
| 1 GB        | 15 min          | 20 min          | 40 min       |

**Hardware**: 16-core CPU, tested on English Wikipedia

### Tokenization speed

| Implementation | 1 GB corpus | Throughput    |
|----------------|-------------|---------------|
| Pure Python    | ~20 minutes | ~50 MB/min    |
| HF Tokenizers  | ~15 seconds | ~4 GB/min     |
| **Speedup**    | **80×**     | **80×**       |

**Test**: English text, average sentence length 20 words

### Memory usage

| Task                    | Memory  |
|-------------------------|---------|
| Load tokenizer          | ~10 MB  |
| Train BPE (30k vocab)   | ~200 MB |
| Encode 1M sentences     | ~500 MB |

## Supported models

Pre-trained tokenizers available via `from_pretrained()`:

**BERT family**:
- `bert-base-uncased`, `bert-large-cased`
- `distilbert-base-uncased`
- `roberta-base`, `roberta-large`

**GPT family**:
- `gpt2`, `gpt2-medium`, `gpt2-large`
- `distilgpt2`

**T5 family**:
- `t5-small`, `t5-base`, `t5-large`
- `google/flan-t5-xxl`

**Other**:
- `facebook/bart-base`, `facebook/mbart-large-cc25`
- `albert-base-v2`, `albert-xlarge-v2`
- `xlm-roberta-base`, `xlm-roberta-large`

Browse all: https://huggingface.co/models?library=tokenizers

## References

- **[Training Guide](references/training.md)** - Train custom tokenizers, configure trainers, handle large datasets
- **[Algorithms Deep Dive](references/algorithms.md)** - BPE, WordPiece, Unigram explained in detail
- **[Pipeline Components](references/pipeline.md)** - Normalizers, pre-tokenizers, post-processors, decoders
- **[Transformers Integration](references/integration.md)** - AutoTokenizer, PreTrainedTokenizerFast, special tokens

## Resources

- **Docs**: https://huggingface.co/docs/tokenizers
- **GitHub**: https://github.com/huggingface/tokenizers ⭐ 9,000+
- **Version**: 0.20.0+
- **Course**: https://huggingface.co/learn/nlp-course/chapter6/1
- **Paper**: BPE (Sennrich et al., 2016), WordPiece (Schuster & Nakajima, 2012)

## Agent operating procedure

1. **Check the environment.** Check GPU type, memory and driver/CUDA versions (`nvidia-smi`), framework versions, and dataset location and size.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Do a smoke run: tiny model or subset, few steps, and confirm loss decreases and checkpoints save.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Track metrics on held-out data, compare against a baseline, and record seeds, configs and hardware.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| CUDA out-of-memory | Reduce batch size, enable gradient accumulation/checkpointing or mixed precision, or shard the model. |
| Loss is NaN or diverges | Lower the learning rate, check data for invalid values, and enable gradient clipping. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never claim training results without logs; estimate compute cost before launching large jobs.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `transformers`: Hugging Face Transformers for loading Hub models, running pipeline inference, text generation, and Trainer fine-tuning on NLP, vision, audi…
- `sentencepiece`: Language-independent tokenizer treating text as raw Unicode.
