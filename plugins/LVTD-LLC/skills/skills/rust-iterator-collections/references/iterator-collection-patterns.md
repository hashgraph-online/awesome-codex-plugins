# Iterator And Collection Patterns

Use this reference when converting loops, reviewing map/set code, or designing
custom collection APIs.

## Iteration Modes

| Code | Meaning |
|------|---------|
| `items.iter()` | Borrow each item as `&T` |
| `items.iter_mut()` | Mutably borrow each item as `&mut T` |
| `items.into_iter()` | Consume the collection and yield owned items |
| `items.drain(..)` | Remove and yield owned items while retaining allocation |

## Fallible Pipelines

```rust
let users: Result<Vec<User>, ParseUserError> =
    rows.into_iter().map(User::try_from).collect();
```

Use `try_fold` when accumulating with fallible operations:

```rust
let total = values.iter().try_fold(0_u64, |acc, value| {
    acc.checked_add(*value).ok_or(Overflow)
})?;
```

## Entry API

```rust
use std::collections::HashMap;

fn count_words(words: impl IntoIterator<Item = String>) -> HashMap<String, usize> {
    let mut counts = HashMap::new();
    for word in words {
        *counts.entry(word).or_insert(0) += 1;
    }
    counts
}
```

Prefer `or_insert_with` when constructing the default is expensive.

## Custom Iterator Checklist

- Implement `Iterator` directly only when adapters cannot express the behavior.
- Keep iterator state minimal and explicit.
- Implement `ExactSizeIterator`, `DoubleEndedIterator`, or `FusedIterator` only
  when their contracts are true.
- Prefer returning `impl Iterator<Item = T>` from helper functions when the
  concrete adapter type is noisy and unimportant.

## Allocation Review

- Can the code return an iterator instead of a `Vec`?
- Can it `extend` an existing collection?
- Is a `collect` needed for sorting, deduplication, random access, or ownership?
- Is capacity known from `size_hint`, input length, or protocol metadata?
