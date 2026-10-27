---
name: sentencepiece
description: Language-independent tokenizer treating text as raw Unicode. Supports BPE and Unigram algorithms. Fast (50k sentences/sec), lightweight (6MB memory), deterministic vocabulary. Used by T5, ALBERT, XLNet, mBART. Train on raw text without pre-tokenization. Use when you need multilingual support, CJK languages, or reproducible tokenization.
license: MIT
metadata:
  version: 1.0.0
  category: ml-training
  maintainer: Kalaris Labs
  tags: Tokenization, SentencePiece, Language-Independent, BPE, Unigram, Multilingual, CJK Languages, Unicode, Deterministic, Google
  dependencies: sentencepiece, transformers
---

# SentencePiece - Language-Independent Tokenization

Unsupervised tokenizer that works on raw text without language-specific preprocessing.

## When to use SentencePiece

**Use SentencePiece when:**
- Building multilingual models (no language-specific rules)
- Working with CJK languages (Chinese, Japanese, Korean)
- Need reproducible tokenization (deterministic vocabulary)
- Want to train on raw text (no pre-tokenization needed)
- Require lightweight deployment (6MB memory, 50k sentences/sec)

**Performance**:
- **Speed**: 50,000 sentences/sec
- **Memory**: ~6MB for loaded model
- **Languages**: All (language-independent)

**Use alternatives instead**:
- **HuggingFace Tokenizers**: Faster training, more flexibility
- **tiktoken**: OpenAI models (GPT-3.5/4)
- **BERT WordPiece**: English-centric tasks

## Quick start

### Installation

```bash
# Python
pip install sentencepiece

# C++ (requires CMake)
git clone https://github.com/google/sentencepiece.git
cd sentencepiece
mkdir build && cd build
cmake .. && make -j $(nproc)
sudo make install
```

### Train model

```bash
# Command-line (BPE with 8000 vocab)
spm_train --input=data.txt --model_prefix=m --vocab_size=8000 --model_type=bpe

# Python API
import sentencepiece as spm

spm.SentencePieceTrainer.train(
    input='data.txt',
    model_prefix='m',
    vocab_size=8000,
    model_type='bpe'
)
```

**Training time**: ~1-2 minutes for 100MB corpus

### Encode and decode

```python
import sentencepiece as spm

# Load model
sp = spm.SentencePieceProcessor(model_file='m.model')

# Encode to pieces
pieces = sp.encode('This is a test', out_type=str)
print(pieces)  # ['▁This', '▁is', '▁a', '▁test']

# Encode to IDs
ids = sp.encode('This is a test', out_type=int)
print(ids)  # [284, 47, 11, 1243]

# Decode
text = sp.decode(ids)
print(text)  # "This is a test"
```

## Language-independent design

### Whitespace as symbol (▁)

```python
text = "Hello world"
pieces = sp.encode(text, out_type=str)
print(pieces)  # ['▁Hello', '▁world']

# Decode preserves spaces
decoded = sp.decode_pieces(pieces)
print(decoded)  # "Hello world"
```

**Key principle**: Treat text as raw Unicode, whitespace = ▁ (meta symbol)

## Tokenization algorithms

### BPE (Byte-Pair Encoding)

```python
spm.SentencePieceTrainer.train(
    input='data.txt',
    model_prefix='bpe_model',
    vocab_size=16000,
    model_type='bpe'
)
```

**Used by**: mBART

### Unigram (default)

```python
spm.SentencePieceTrainer.train(
    input='data.txt',
    model_prefix='unigram_model',
    vocab_size=8000,
    model_type='unigram'
)
```

**Used by**: T5, ALBERT, XLNet

## Training configuration

### Essential parameters

```python
spm.SentencePieceTrainer.train(
    input='corpus.txt',
    model_prefix='m',
    vocab_size=32000,
    model_type='unigram',
    character_coverage=0.9995,  # 1.0 for CJK
    user_defined_symbols=['[SEP]', '[CLS]'],
    unk_piece='<unk>',
    num_threads=16
)
```

### Character coverage

| Language Type | Coverage | Rationale |
|---------------|----------|-----------|
| English       | 0.9995   | Most common chars |
| CJK (Chinese) | 1.0      | All characters needed |
| Multilingual  | 0.9995   | Balance |

## Encoding options

### Subword regularization

```python
# Sample different tokenizations
for _ in range(3):
    pieces = sp.encode('tokenization', out_type=str, enable_sampling=True, alpha=0.1)
    print(pieces)

# Output (different each time):
# ['▁token', 'ization']
# ['▁tok', 'en', 'ization']
```

**Use case**: Data augmentation for robustness.

## Common patterns

### T5-style training

```python
spm.SentencePieceTrainer.train(
    input='c4_corpus.txt',
    model_prefix='t5',
    vocab_size=32000,
    model_type='unigram',
    user_defined_symbols=[f'<extra_id_{i}>' for i in range(100)],
    unk_id=2,
    eos_id=1,
    pad_id=0
)
```

### Integration with transformers

```python
from transformers import T5Tokenizer

# T5 uses SentencePiece internally
tokenizer = T5Tokenizer.from_pretrained('t5-base')
inputs = tokenizer('translate English to French: Hello', return_tensors='pt')
```

## Performance benchmarks

### Training speed

| Corpus | BPE (16k) | Unigram (8k) |
|--------|-----------|--------------|
| 100 MB | 1-2 min   | 3-4 min      |
| 1 GB   | 10-15 min | 30-40 min    |

### Tokenization speed

- **SentencePiece**: 50,000 sentences/sec
- **HF Tokenizers**: 200,000 sentences/sec (4× faster)

## Supported models

**T5 family**: `t5-base`, `t5-large` (32k vocab, Unigram)
**ALBERT**: `albert-base-v2` (30k vocab, Unigram)
**XLNet**: `xlnet-base-cased` (32k vocab, Unigram)
**mBART**: `facebook/mbart-large-50` (250k vocab, BPE)

## References

- **[Training Guide](references/training.md)** - Detailed options, corpus preparation
- **[Algorithms](references/algorithms.md)** - BPE vs Unigram, subword regularization

## Resources

- **GitHub**: https://github.com/google/sentencepiece ⭐ 10,000+
- **Paper**: https://arxiv.org/abs/1808.06226 (EMNLP 2018)
- **Version**: 0.2.0+

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

- `huggingface-tokenizers`: Provides the HuggingFace Tokenizers library (Rust core with Python and Node.js bindings) for training and using BPE, WordPiece, and Unigram…
