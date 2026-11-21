# Security

## Reporting a vulnerability

Please don't put details of a vulnerability in a public issue. Open an issue titled "Security contact" with no details, and we'll reply with a private way to send them.

Supported: the latest release on `main`.

## What fanout runs

fanout has no dependencies and no server. Its hooks run `node fanout.mjs <hook>` on your machine and read git. The only network call is the same-work check, made through your own signed-in `claude` or `codex` CLI; `FANOUT_CLAIM_JUDGE=off` turns it off. See [PRIVACY.md](PRIVACY.md).
