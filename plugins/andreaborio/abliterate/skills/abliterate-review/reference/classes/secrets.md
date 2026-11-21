# Secrets and sensitive data exposure (CWE-798, CWE-532, CWE-200, CWE-209)

## Sources
- Hardcoded: string literals in source, config committed to the repo, CI files, Dockerfiles (`ENV`, `ARG`), Terraform/Helm values, notebooks, mobile/frontend bundles, `.env` files tracked by Git.
- Runtime leaks: request/response logging, `console.log(req)` / `logger.info(config)`, exception handlers that return the exception, debug pages, `repr` of settings objects, analytics/telemetry payloads, URLs with tokens (end up in logs and `Referer`).
- Over-exposed data: serializers returning whole models (password hash, tokens, internal ids, other users' emails), GraphQL fields, admin fields in public JSON, verbose validation errors, stack traces, SQL in errors.

## Sinks
| Stack | Where it leaks | Safer pattern |
| --- | --- | --- |
| Any | `logger.*(req.headers)`, `log(req.body)`, `log(user)`, `log(process.env)` | redaction list (`authorization`, `cookie`, `password`, `token`), log ids not objects |
| Node | `res.status(500).json({error: err})`, `err.stack` in response, Express default error handler in non-production env | generic message + correlation id; `NODE_ENV=production` |
| Python | `DEBUG = True`, Flask `app.run(debug=True)`, `traceback.format_exc()` in response, `repr(settings)` | handlers that return generic body; `DEBUG` from env |
| Java | `server.error.include-stacktrace`, `include-message`, Actuator `/env`, `/heapdump`, `/configprops` exposed | restrict `management.endpoints.web.exposure.include`, secure actuator |
| Rails / Laravel | `config.consider_all_requests_local`, `APP_DEBUG=true`, `render json: user` / `return $user` | `as_json(only:)`, API resources / `$hidden` |
| Serializers | `res.json(user)`, DRF `fields='__all__'`, `to_json`, Jackson on entity | explicit DTO / `fields` allowlist |
| Client bundles | `NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*` holding a server secret | keep server-only; proxy through backend |

## Guards that work / Look-alike guards
Work:
- Secrets loaded from a secret manager or environment at runtime; repo contains only names and `.env.example` with empty/placeholder values.
- Structured log redaction applied at the logger (pino `redact`, Python logging filter, Logback masking) so every call path is covered.
- Explicit response DTOs; fields not listed are not sent.
- Generic client errors, detailed server-side logs.
- Rotation: revoke at the provider, replace, and purge from history only as a secondary step.

Look-alike:
- Deleting the secret in a later commit (still in history and in forks/clones).
- Base64 or hex "encoding", XOR, or a reversible obfuscation presented as encryption.
- `.gitignore` entry added after the file was committed.
- Frontend hiding of a field the API still returns.
- Masking in the UI while the response/log has the full value.
- `NEXT_PUBLIC_` prefix assumed to be private.
- Redaction by key name only when the value also appears in a URL or free-text message.

## Falsify before reporting
1. Is it a real credential or a placeholder/fixture? Signals of non-secret: `example`, `changeme`, `xxxx`, `test`, documented vendor sample keys, publishable keys designed to be public (client-side analytics IDs, publishable payment keys), local-only dev credentials for a throwaway container.
2. Does the key format and surrounding code show it is used against a real service, and is it live-scope vs test-scope? Do NOT try the credential; never call the provider.
3. Is the file shipped (tracked, in an image layer, in a bundle) or only a local ignored file? Check Git tracking state read-only via the file list, not by opening ignored files.
4. For logs/errors: does the value actually reach the log/response on a routed request, and does the logger redact it?
5. For over-exposure: does the serializer output include the field, or is it removed by a `select`/`hidden`/DTO on this path?
6. Confirm: a test with a synthetic marker value (`secret-marker-123` in the field) asserts it is absent from the serialized response/log output.

## Severity cues
- Raises: live production credential with broad scope, key in a public repo or client bundle, password hashes or tokens returned to other users, long-lived signing keys, secrets in logs shipped to third parties.
- Lowers: scoped read-only test key, already-rotated, internal-only log store with restricted access, field exposed only to its owner.
- How to cite: give file path, line, and secret TYPE (for example "AWS access key", "JWT signing secret"); never repeat, truncate, or hash the value. Recommend rotation whenever a real credential was committed or logged, because removal does not revoke it.

## Regression test
- Fails before: create a user with a synthetic secret-like field value, call the endpoint, assert the response JSON has no key for the secret field (`passwordHash`, `apiToken`); before the fix it is present.
- Logging: run the handler with a request carrying `Authorization: Bearer marker` and assert captured log output does not contain `marker`.
- Error path: force an exception; assert the body has the generic message and no stack trace or SQL text.
- Config scan test: assert required secrets come from env and the app fails closed when missing, instead of falling back to a literal default.
- Allowed case: the owner still sees the fields they are entitled to; correlation id still appears in logs.
