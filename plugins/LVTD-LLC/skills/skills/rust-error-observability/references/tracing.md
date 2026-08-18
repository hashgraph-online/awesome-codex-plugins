# Tracing Patterns

Use `tracing` spans to connect request, database, upstream, and worker events.
Logs without spans often lose the request context that makes production
debugging useful.

## Handler Instrumentation

```rust
#[tracing::instrument(
    name = "Create subscription",
    skip(pool, email_client, payload),
    fields(request_id = %request_id, subscriber_email = tracing::field::Empty)
)]
pub async fn subscribe(
    payload: web::Json<SubscribeRequest>,
    pool: web::Data<PgPool>,
    email_client: web::Data<EmailClient>,
) -> Result<HttpResponse, SubscribeError> {
    let command = SubscribeCommand::try_from(payload.into_inner())?;
    tracing::Span::current().record("subscriber_email", command.email.as_str());
    // ...
    Ok(HttpResponse::Ok().finish())
}
```

Skip large objects and secret-bearing values. Record safe fields only after
validation and redaction decisions are clear.

## Subscriber Setup

Look for existing initialization before adding another subscriber. A typical app
has one setup function used by `main` and tests:

```rust
pub fn init_subscriber(env_filter: String) {
    let env_filter = tracing_subscriber::EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| env_filter.into());

    tracing_subscriber::fmt()
        .with_env_filter(env_filter)
        .with_target(true)
        .init();
}
```

In tests, initialize once with `try_init` or a `OnceLock` to avoid panics from
multiple global subscriber installs.

## Useful Fields

- `request_id`
- `user_id` or tenant ID when safe.
- `job_id` and attempt number.
- `upstream` service name.
- `idempotency_key` when it is not secret.
- Database operation name, not full SQL with user data.

## Failure Events

Use `tracing::error!` or `tracing::warn!` at the boundary that decides what
happens next:

```rust
tracing::error!(
    error = ?err,
    "request failed with unexpected error"
);
```

Use `?err` for debug diagnostics when the error is safe. Use `%err` when the
display message is intentionally redacted.
