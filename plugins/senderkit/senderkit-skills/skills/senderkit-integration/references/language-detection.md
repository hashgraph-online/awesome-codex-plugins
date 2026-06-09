# Language and provider detection

Use this reference when the project stack, framework, or existing notification provider is not obvious.

## Stack detection

Check these files first:

| Ecosystem | Signals |
| --- | --- |
| Node.js / TypeScript | `package.json`, `pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `bun.lock`, `tsconfig.json`, `next.config.*`, `vite.config.*` |
| Python | `pyproject.toml`, `requirements.txt`, `Pipfile`, `poetry.lock`, `manage.py`, `app/main.py` |
| Go | `go.mod`, `go.sum`, `cmd/`, `internal/` |
| Ruby | `Gemfile`, `Gemfile.lock`, `config/routes.rb` |
| PHP | `composer.json`, `artisan`, `symfony.lock` |
| Java / Kotlin | `pom.xml`, `build.gradle`, `build.gradle.kts`, `src/main/java`, `src/main/kotlin` |
| .NET | `*.csproj`, `*.sln`, `Program.cs`, `appsettings*.json` |
| Rust | `Cargo.toml`, `Cargo.lock`, `src/main.rs` |

Search for existing sends with terms like:

```text
sendEmail|send_email|mailer|mail|smtp|nodemailer|resend|sendgrid|postmark|mailgun|ses|twilio|sns|apns|fcm|expo|webpush|notification|template|webhook
```

## Existing provider signals

- Resend: `resend`, `RESEND_API_KEY`, `emails.send`, React Email examples.
- SendGrid: `@sendgrid/mail`, `SENDGRID_API_KEY`, `custom_args`, `dynamic_template_data`.
- Postmark: `postmark`, `POSTMARK_SERVER_TOKEN`, `Metadata`, message streams.
- Mailgun: `mailgun.js`, `MAILGUN_API_KEY`, `v:` custom variables, domain config.
- AWS SES/SNS: `@aws-sdk/client-sesv2`, `boto3`, `SendEmailCommand`, `EmailTags`, `MessageAttributes`.
- SMTP/Nodemailer: `SMTP_URL`, `nodemailer.createTransport`, host/port/user/pass config.
- Twilio/SNS SMS: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `PublishCommand`.
- Push: APNs, FCM/Firebase Admin, Expo push tokens, web push subscriptions.

## Integration path by ecosystem

### Node.js / TypeScript

- Prefer the official SenderKit SDK when current docs or package metadata confirm the package name.
- If the app is Next.js, Remix, Nuxt, SvelteKit, Astro, Express, Hono, or another server-capable framework, send only from server routes/actions/jobs.
- Add a local wrapper that accepts app-domain inputs and calls SenderKit. Keep framework handlers thin.
- Use `fetch` REST fallback when avoiding a dependency or when SDK package naming is uncertain.

### Python

- Use `httpx` or `requests` unless an official SenderKit Python SDK is confirmed.
- In Django/FastAPI/Flask, place the client in an infrastructure/service module and inject settings from environment.
- Use short request timeouts and preserve background-job retry behavior.

### Go

- Use `net/http` with `context.Context`, explicit timeout, typed request/response structs, and stable idempotency keys.
- Keep the SenderKit client behind an interface so tests can fake it.

### Ruby / PHP / Java / .NET / Rust / other

- Use the REST API unless current SenderKit docs provide an official SDK for the stack.
- Follow the platform's normal HTTP client, config, logging, and test patterns.
- Keep credentials in the framework's secret/config system, not source code.

## What to produce

For a normal integration, produce:

- Environment/config additions for `SENDERKIT_API_KEY`.
- A local SenderKit client or provider module.
- One migrated send flow with tests, then apply the same pattern to remaining flows.
- A render or test-send verification path.
- Notes for any old-provider behavior intentionally left in place during rollout.
