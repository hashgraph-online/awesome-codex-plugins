# Security model

Emulo reads private AI coding-session logs, so its trust boundaries must stay explicit.

## Reporting a vulnerability

Report security and redaction problems privately through GitHub's private vulnerability reporting: the "Report a vulnerability" button on this repository's Security tab. Do not open a public issue with details. See [MAINTENANCE.md](MAINTENANCE.md) for what is in scope.

## Local extraction and private state

`emulo.py` uses Python's standard library and makes no network calls. By default it discovers local session history under the Claude Code, Codex, Copilot CLI, OpenCode, and Google Antigravity paths, or a directory supplied with `--path`. Those logs are JSONL files, except OpenCode, which keeps a SQLite database and JSON session files. `CODEX_HOME` and `XDG_DATA_HOME` move the Codex and OpenCode roots; set but empty, they count as unset.

The extractor keeps only user-authored messages, removes known injected context, deduplicates repeated long text, and applies best-effort secret/PII redaction before writing selected text.

Plugin state lives under `EMULO_HOME` or `~/.emulo`, never inside the installed plugin cache. It includes immutable segments, validated evidence reports, versioned profiles, active pointers, migration records, and private receipt appendices.

## Model-provider boundary

Emulo's extractor, redaction, caches, and generated profiles stay local. Selected redacted text is processed by the model provider you choose. With a local model, the entire mining flow can remain local.

Workers receive only their assigned selected segment. The reducer receives validated bounded JSON reports rather than raw session logs.

## Bootstrap downloads

skills.sh downloads the selected `emulo` bootstrap. The skills.sh CLI reports anonymous installation telemetry by default; set `DISABLE_TELEMETRY=1` to opt out.

Outside a repository checkout, the bootstrap downloads only `emulo.py` and `MINING_PROMPT.md` from `raw.githubusercontent.com` at the exact release tag. Both files must match the SHA-256 values shipped in `runtime.json` before the active runtime pointer changes. These fetches happen before log discovery and read no session data.

## Redaction coverage and limits

Current patterns, each pinned by a sample in `tests/test_redaction_table.py`, cover OpenAI keys (`sk-`, `sk-proj-`, `sk-svcacct-`, `sk-admin-`), Anthropic keys (`sk-ant-`), Google API keys (`AIza` plus 35 characters), Stripe live secret keys (`sk_live_`), webhook secrets (`whsec_`), Supabase access tokens (`sbp_`), GitHub tokens (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`), JWTs (three dot-separated parts starting `eyJ`), AWS access key IDs (`AKIA`), Slack tokens (`xoxb-`, `xoxa-`, `xoxp-`, `xoxr-`, `xoxs-`), the password in a connection URL (`scheme://user:password@host`, tested for postgres, postgresql, mysql, mongodb+srv, redis, amqp and https, including a percent-encoded password such as one holding `%23`), email addresses, phone numbers with an international or trunk prefix, IPv4 addresses, and any value assigned with `=` or `:` to a name ending in `api_key`, `apikey`, `api-key`, `secret`, `token`, `password` or `passwd`, in any case, so `client_secret=` and `GITHUB_TOKEN=` are covered. They also cover the spoken forms people paste to an agent, `password is`, `passwd`, `passphrase`, `passkey`, `psk` and `wifi key` followed by a value, when that value has a digit or a symbol or is at least 12 characters long, so prose about passwords survives. Anything else passes through. For example `AWS_SECRET_ACCESS_KEY=...` is not redacted, because the name ends in `ACCESS_KEY`, and neither is a provider key with no fixed prefix. A connection URL password that holds a raw `#`, `/`, `?` or a space is not redacted, and neither is one after a user name that holds a raw @ sign, as in `postgres://user@corp.com:pw@host`, where only the user name is replaced. None of those characters is valid there unencoded, and the encoded forms are redacted.

Redaction is best-effort. Inspect generated private data before sharing anything. `--no-redact` is intentionally dangerous because selected raw text may then be sent to the chosen model provider.

## Fail-closed behavior

- Empty or malformed history writes no output.
- Segment, report, reduction, manifest, and pointer hashes are revalidated before reuse.
- Corrupt cache entries are quarantined and recomputed individually.
- Profile activation stages a complete immutable version before swapping the pointer.
- Legacy cutover moves the old discovery directory first and restores exact bytes/pointers on failure.
- Plugin installation and removal do not create, scan, or delete `EMULO_HOME`.

## Safe sharing

Share the rendered card or one short non-private trait. Do not commit or post session logs, Emulo caches, the full profile, or the private evidence appendix.
