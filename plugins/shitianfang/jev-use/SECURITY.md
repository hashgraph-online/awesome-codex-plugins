# Security

## Reporting a vulnerability

Report privately through GitHub's
[security advisories](https://github.com/shitianfang/jev-use/security/advisories/new)
for this repository. Please do not open a public issue for anything
exploitable. Expect a first reply within a week.

## What leaves your machine

jev-use sends the **state you ask about** to the judgment provider you
configure — TypeSafe, OpenRouter, or the Vercel AI Gateway. In practice that
means whatever you put in the state: page DOM, command output, transcript
messages, and, when the gate is enabled, the shell command being proposed
along with the session context around it.

Credentials inside a **gated action** do not: the hook hands over whatever
the agent proposed, so `jev_gate` and `jev.gate()` redact the action before
the call — URL passwords, auth and cookie headers, `-u user:pass`,
`--token=`/`SECRET=` values, and known key shapes (`sk-`, `ghp_`, `AKIA`,
JWTs) become `[redacted]`. The rules are a table in
[src/redact.ts](src/redact.ts). The state you write yourself is sent as
given — that part is your choice.

- There is no self-hosted path today. Jev is API-only.
- `JEV_BACKEND=mock` answers locally and makes **no network calls at all**.
  Use it to see exactly which calls a workload would have made.
- jev-use sends nothing anywhere else. There is no telemetry, no analytics,
  and no phone-home; the only outbound requests are the judgment calls to
  the provider you configured.
- Retention and training policy for the judged content is the provider's,
  not ours. Read theirs before sending production data.

## Credentials

API keys are read from the environment (`TYPESAFE_API_KEY`,
`OPENROUTER_API_KEY`, `AI_GATEWAY_API_KEY`) and are never written to disk,
never logged, and never included in an error message. `jev-use doctor`
prints which variable was found, never its value.

## The command gate

`jev_gate` and the PreToolUse hook are **opt-in** and can only ever return
deny or ask — they cannot grant a permission the harness would not otherwise
give.

When the backend is unreachable, the gate does **not** fall back to
allowing. The question is returned to the LLM with the typed reason
`unreachable`, so a command that could not be judged is never waved through
on the judge's behalf. The same holds for `unsure`: a verdict below the
confidence threshold escalates rather than resolving to a default.

Treat the gate as defence in depth, not as a sandbox. It is a model
judging a command, it has measured failure modes (see `bench/RESULTS.md`),
and it is not a substitute for running untrusted work in isolation.

## Supply chain

- No runtime dependencies on the judgment path.
- GitHub Actions are pinned to commit SHAs.
- `package-lock.json` is committed and CI installs with `npm ci`.
