# Ownership And Borrow Patterns

Use this reference when diagnosing borrow-checker failures or reviewing code
that uses shared ownership or interior mutability.

## Pick The Access Shape

| Need | Prefer | Avoid |
|------|--------|-------|
| Read during one call | `&T`, `&str`, `&[T]`, `&Path` | `&String`, `&Vec<T>`, `&PathBuf` |
| Mutate during one call | `&mut T` | `RefCell<T>` without a sharing requirement |
| Store for later | owned `T` | borrowed fields with broad lifetimes |
| Share in one thread | `Rc<T>` | `Arc<T>` unless threads are possible |
| Share across threads | `Arc<T>` | `Rc<T>` |
| Shared mutation | `Mutex<T>`, `RwLock<T>`, `RefCell<T>` by context | cloning payloads to dodge aliasing |

## Borrow Narrowing

```rust
// Bad: `first` keeps an immutable borrow of `items` alive during push.
let first = items.first();
items.push(new_item);
println!("{first:?}");

// Good: copy or compute what is needed before mutation.
let first_id = items.first().map(|item| item.id);
items.push(new_item);
println!("{first_id:?}");
```

## Moving Out Of Fields

Use `Option::take` or `std::mem::take` when a method must consume part of
`self` while leaving `self` valid.

```rust
struct Job {
    payload: Option<String>,
}

impl Job {
    fn finish(&mut self) -> Option<String> {
        self.payload.take()
    }
}
```

## Splitting Mutable Access

Prefer APIs that prove disjointness to the compiler:

- `slice.split_at_mut(index)` for two mutable slice regions.
- `HashMap::get_disjoint_mut` when several distinct map values are needed.
- `Vec::drain`, `retain`, and `dedup_by` for mutation while iterating.
- `HashMap::entry` for insert-or-update without double lookup.

## Interior Mutability Review

Before accepting `RefCell`, `Mutex`, or `RwLock`, write down:

- What invariant is protected?
- Who can borrow or lock it?
- Can calls re-enter while the borrow or lock is held?
- What happens on panic or poisoning?
- Can a narrower owned design remove the runtime check?
