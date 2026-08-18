# Security model

Emulo reads private AI coding-session logs, so its trust boundaries must stay explicit.

## Local extraction and private state

`emulo.py` uses Python's standard library and makes no network calls. By default it discovers local JSONL history under Codex, Claude Code, and Copilot CLI paths, or a directory supplied with `--path`.

The extractor keeps only user-authored messages, removes known injected context, deduplicates repeated long text, and applies best-effort secret/PII redaction before writing selected text.

Plugin state lives under `EMULO_HOME` or `~/.emulo`, never inside the installed plugin cache. It includes immutable segments, validated evidence reports, versioned profiles, active pointers, migration records, and private receipt appendices.

## Model-provider boundary

Emulo's extractor, redaction, caches, and generated profiles stay local. Selected redacted text is processed by the model provider you choose. With a local model, the entire mining flow can remain local.

Workers receive only their assigned selected segment. The reducer receives validated bounded JSON reports rather than raw session logs.

## Bootstrap downloads

skills.sh downloads the selected `emulo` bootstrap. The skills.sh CLI reports anonymous installation telemetry by default; set `DISABLE_TELEMETRY=1` to opt out.

Outside a repository checkout, the bootstrap downloads only `emulo.py` and `MINING_PROMPT.md` from `raw.githubusercontent.com` at the exact release tag. Both files must match the SHA-256 values shipped in `runtime.json` before the active runtime pointer changes. These fetches happen before log discovery and read no session data.

## Redaction coverage and limits

Current patterns cover common API keys, Stripe and webhook secrets, Supabase and GitHub tokens, JWTs, AWS keys, Slack tokens, email addresses, phone numbers, IP addresses, and common secret assignments — including the spoken forms people actually paste to an agent (`the wifi password is …`, `psk …`), guarded so prose about passwords survives.

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
