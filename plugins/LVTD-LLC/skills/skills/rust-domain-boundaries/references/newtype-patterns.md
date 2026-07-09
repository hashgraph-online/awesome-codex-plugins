# Newtype Patterns

Use a newtype when a primitive value has business meaning, validation rules, or
security handling that would be easy to bypass if it stayed as `String`, `i64`,
or `Uuid` everywhere.

## Basic Shape

```rust
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct EmailAddress(String);

impl EmailAddress {
    pub fn parse(input: impl Into<String>) -> Result<Self, EmailAddressError> {
        let input = input.into();
        let candidate = input.trim();

        if candidate.is_empty() {
            return Err(EmailAddressError::Empty);
        }

        if !candidate.contains('@') {
            return Err(EmailAddressError::MissingAtSign);
        }

        Ok(Self(candidate.to_owned()))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl AsRef<str> for EmailAddress {
    fn as_ref(&self) -> &str {
        self.as_str()
    }
}
```

Keep the field private. If callers need construction for tests, provide a
checked constructor or a test-only helper under `#[cfg(test)]`.

## Conversion Guidance

- Use `TryFrom<String>` when callers already own a string.
- Use `FromStr` when parsing is idiomatic for config, CLI, or path values.
- Avoid `From<String>` for validated types; it implies conversion cannot fail.
- Avoid `Deref<Target = str>` unless the type is intentionally string-like and
  all string operations are safe.
- Use named constructors for intent when there are multiple validation modes,
  for example `Password::parse_plaintext` vs `PasswordHash::parse_phc`.

## Serde Boundary

For request DTOs, prefer deserializing raw strings and converting explicitly in
the handler or command constructor. This keeps HTTP error mapping under your
control.

For internal APIs or stored JSON, custom `Deserialize` can be useful:

```rust
impl<'de> serde::Deserialize<'de> for EmailAddress {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let value = String::deserialize(deserializer)?;
        Self::parse(value).map_err(serde::de::Error::custom)
    }
}
```

## SQL Mapping

Convert domain values at the repository edge:

```rust
sqlx::query!(
    "insert into subscriptions (email, name) values ($1, $2)",
    command.email.as_str(),
    command.name.as_str(),
)
.execute(pool)
.await?;
```

For frequent mappings, consider implementing `sqlx::Type`, `Encode`, and
`Decode`, but keep simple `.as_str()` mapping unless the repeated boilerplate is
material.

## Error Types

Make validation errors specific enough for tests and HTTP mapping:

```rust
#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum SubscriberNameError {
    #[error("name cannot be empty")]
    Empty,
    #[error("name is too long")]
    TooLong,
    #[error("name contains forbidden characters")]
    InvalidCharacters,
}
```

Do not put raw secrets, tokens, or passwords in validation error variants or
`Display` messages.
