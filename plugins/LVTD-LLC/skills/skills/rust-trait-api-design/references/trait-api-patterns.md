# Trait API Patterns

Use this reference when designing public Rust APIs or reviewing trait-heavy
code.

## Generics Vs Trait Objects

| Need | Prefer |
|------|--------|
| One concrete type per call site, optimizer can specialize | `fn f<T: Trait>(value: T)` |
| Caller should pass anything iterable | `fn f<I: IntoIterator<Item = T>>(items: I)` |
| Store heterogeneous values together | `Vec<Box<dyn Trait>>` |
| Runtime plugin boundary | `Arc<dyn Trait + Send + Sync>` |
| Hide one concrete return type | `-> impl Trait` |
| Return one of several implementors | `-> Box<dyn Trait>` or an enum |

## Conversion Trait Selection

| Situation | Trait |
|-----------|-------|
| Infallible owned conversion | `From<T> for U` |
| Fallible owned conversion | `TryFrom<T> for U` |
| Cheap borrowed view | `AsRef<T>` or `AsMut<T>` |
| Generic lookup with equivalent owned/borrowed equality | `Borrow<T>` |
| Clone only when mutation or ownership is needed | `Cow<'a, T>` |

Do not implement `Into` or `TryInto` directly unless a coherence edge case
prevents implementing `From` or `TryFrom`.

## Associated Types Vs Generic Traits

```rust
trait Parser {
    type Output;
    fn parse(&self, input: &str) -> Result<Self::Output, ParseError>;
}
```

Use an associated type when each parser has one output type. Use a generic
method or generic trait only when the same implementation supports multiple
output types.

## Public Trait Checklist

- Is downstream implementation allowed? If not, use a sealed trait pattern.
- Are object-safety requirements intentional and documented?
- For async methods, have you chosen between private `async fn`, public
  `fn -> impl Future + Send`, `trait-variant`, or boxed futures based on
  `Send` and dynamic-dispatch requirements?
- Are `Send`, `Sync`, and `'static` bounds placed at the storage/spawn boundary
  rather than every trait definition?
- Are default methods small and expressed in terms of required methods?
- Does the trait name describe capability, not implementation?
