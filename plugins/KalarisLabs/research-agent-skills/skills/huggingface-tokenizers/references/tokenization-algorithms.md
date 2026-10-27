# Tokenization algorithms

### BPE (Byte-Pair Encoding)

**How it works**:
1. Start with character-level vocabulary
2. Find most frequent character pair
3. Merge into new token, add to vocabulary
4. Repeat until vocabulary size reached

**Used by**: GPT-2, GPT-3, RoBERTa, BART, DeBERTa

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import ByteLevel

tokenizer = Tokenizer(BPE(unk_token="<|endoftext|>"))
tokenizer.pre_tokenizer = ByteLevel()

trainer = BpeTrainer(
    vocab_size=50257,
    special_tokens=["<|endoftext|>"],
    min_frequency=2
)

tokenizer.train(files=["data.txt"], trainer=trainer)
```

**Advantages**:
- Handles OOV words well (breaks into subwords)
- Flexible vocabulary size
- Good for morphologically rich languages

**Trade-offs**:
- Tokenization depends on merge order
- May split common words unexpectedly

### WordPiece

**How it works**:
1. Start with character vocabulary
2. Score merge pairs: `frequency(pair) / (frequency(first) × frequency(second))`
3. Merge highest scoring pair
4. Repeat until vocabulary size reached

**Used by**: BERT, DistilBERT, MobileBERT

```python
from tokenizers import Tokenizer
from tokenizers.models import WordPiece
from tokenizers.trainers import WordPieceTrainer
from tokenizers.pre_tokenizers import Whitespace
from tokenizers.normalizers import BertNormalizer

tokenizer = Tokenizer(WordPiece(unk_token="[UNK]"))
tokenizer.normalizer = BertNormalizer(lowercase=True)
tokenizer.pre_tokenizer = Whitespace()

trainer = WordPieceTrainer(
    vocab_size=30522,
    special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
    continuing_subword_prefix="##"
)

tokenizer.train(files=["corpus.txt"], trainer=trainer)
```

**Advantages**:
- Prioritizes meaningful merges (high score = semantically related)
- Used successfully in BERT (state-of-the-art results)

**Trade-offs**:
- Unknown words become `[UNK]` if no subword match
- Saves vocabulary, not merge rules (larger files)

### Unigram

**How it works**:
1. Start with large vocabulary (all substrings)
2. Compute loss for corpus with current vocabulary
3. Remove tokens with minimal impact on loss
4. Repeat until vocabulary size reached

**Used by**: ALBERT, T5, mBART, XLNet (via SentencePiece)

```python
from tokenizers import Tokenizer
from tokenizers.models import Unigram
from tokenizers.trainers import UnigramTrainer

tokenizer = Tokenizer(Unigram())

trainer = UnigramTrainer(
    vocab_size=8000,
    special_tokens=["<unk>", "<s>", "</s>"],
    unk_token="<unk>"
)

tokenizer.train(files=["data.txt"], trainer=trainer)
```

**Advantages**:
- Probabilistic (finds most likely tokenization)
- Works well for languages without word boundaries
- Handles diverse linguistic contexts

**Trade-offs**:
- Computationally expensive to train
- More hyperparameters to tune
