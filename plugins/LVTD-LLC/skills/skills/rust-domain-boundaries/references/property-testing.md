# Property Testing Domain Types

Use property tests when a parser or constructor has many possible inputs and a
small example table is unlikely to cover edge cases. Good candidates include
names, slugs, email-like identifiers, idempotency keys, path segments, and
custom numeric ranges.

## Test Strategy

1. Keep example tests for important named cases. They document product rules.
2. Add generated valid inputs to prove broad acceptance.
3. Add generated invalid inputs to prove rejection boundaries.
4. Assert the stable property, not implementation details.

Useful properties:

- Accepted values can be displayed or serialized without panicking.
- Accepted values round-trip through the accessor.
- Rejected values never reach the repository or command handler.
- Normalization is idempotent: parsing an already-normalized output gives the
  same value.
- Length limits are enforced before database insertion.

## Proptest Sketch

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn subscriber_names_reject_blank_input(raw in "\\s*") {
        prop_assume!(!raw.is_empty());
        prop_assert!(SubscriberName::parse(raw).is_err());
    }

    #[test]
    fn subscriber_names_accept_non_empty_trimmed_text(raw in "[a-zA-Z][a-zA-Z ]{0,80}") {
        let parsed = SubscriberName::parse(raw.clone())?;
        prop_assert_eq!(parsed.as_str(), raw.trim());
    }
}
```

## Fake Data

Use `fake` or a small custom generator for realistic valid values. Avoid random
internet-looking data if the validation rules are stricter than the generator.

```rust
use fake::{Fake, faker::internet::en::SafeEmail};

#[test]
fn generated_safe_emails_are_accepted() {
    for _ in 0..100 {
        let email: String = SafeEmail().fake();
        assert!(EmailAddress::parse(email).is_ok());
    }
}
```

## Keep Tests Deterministic

- Seed randomness when the framework supports it.
- Keep generated input size bounded so tests remain fast.
- Store regression cases found by shrinking as named example tests.
- Do not use property tests as a substitute for clear domain rules.
