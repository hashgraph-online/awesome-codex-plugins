# Optional local similarity retrieval

Use `scripts/local_similarity_index.py` only when exact context-pack retrieval misses relevant notes because terminology differs.

Build the index outside the vault in a machine-local location:

```text
python local_similarity_index.py build <project-folder> <machine-local-index.json>
```

Query it with `search`. The index stores vault-relative filenames and derived weighted word, bigram, and character features; it does not store note bodies. It is local-only, deterministic, optional, and safe to delete and rebuild. It performs similarity retrieval, not factual validation or neural embedding. Inspect every selected note and explain the visible matched features. Never commit the index or treat similarity as evidence that a claim is correct.
