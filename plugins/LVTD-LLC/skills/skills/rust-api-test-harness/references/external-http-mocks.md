# External HTTP Mocks

Use this reference when a Rust API test needs to verify outbound HTTP calls to
email providers, payment APIs, webhooks, search services, or other third-party
systems.

## Preferred Pattern

1. Start a local mock server in the test setup.
2. Point the application or client base URL at the mock server.
3. Configure the exact expected request: method, path, headers, body, and number
   of calls.
4. Exercise the public API through HTTP.
5. Assert both the API response and the mock expectations.

`wiremock` is a good default for Rust projects because it integrates cleanly
with async tests and can verify scoped request expectations.

## Client Design

Make external clients easy to test:

- Accept a base URL through configuration.
- Reuse one `reqwest::Client` instead of constructing a new client per request.
- Put authorization headers, timeouts, and serialization in one small client
  type.
- Keep request construction close to the client, not scattered across handlers.
- Return errors that preserve enough context for callers and operators.

## Test Cases To Cover

- Happy path with exact method, path, authorization, content type, and JSON/body.
- Non-2xx upstream responses.
- Timeouts or connection failures.
- Invalid or missing configuration.
- Duplicate submission behavior when external side effects are expensive.

## Mocking Boundaries

Mock systems outside the service boundary. Do not mock the Rust handler being
tested or the domain function whose behavior is the point of the test.

Good mock boundary:

```text
test -> local API server -> real handler/domain code -> mock external API
```

Weak mock boundary:

```text
test -> mocked handler -> no real API behavior exercised
```

## Practical Tips

- Use short timeouts in tests to avoid long hangs.
- Prefer named helper methods such as `mock_email_send_success` over inline mock
  setup when the expectation appears in multiple tests.
- Keep mock assertions strict enough to catch contract drift, but do not assert
  incidental headers that libraries may change.
- Use scoped mocks where available so expectations are verified before the test
  moves on.
