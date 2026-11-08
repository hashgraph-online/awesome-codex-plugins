# Security Policy

## Reporting a vulnerability

Please report vulnerabilities privately via GitHub:
[Security → Report a vulnerability](https://github.com/vshulcz/deja-vu/security/advisories/new).
Do not open a public issue for anything you believe is exploitable.

You can expect an initial response within 72 hours. Please include a minimal
reproduction and, if the issue involves a session file format, a redacted
sample.

## What `deja update` checks

It downloads `checksums.txt` and the release archive for your platform from the
same GitHub release and compares sha256 before replacing the binary. That
catches a corrupt or truncated download; it does not catch a tampered release,
since whoever could replace the archive could replace the checksums beside it.

Releases are signed with cosign and carry build provenance, and the client does
not verify either. If you need that guarantee, verify before installing:

```sh
cosign verify-blob --bundle checksums.txt.sigstore.json \
  --certificate-identity-regexp 'https://github.com/vshulcz/deja-vu/.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com checksums.txt
```

Releases up to v0.21.4 carry `checksums.txt.sig` and `checksums.txt.pem`
instead; docs/SECURITY-MODEL.md shows how to verify those.

Nightly builds are prereleases and are not signed. `deja update` follows
`releases/latest`, which excludes them.

## Scope notes

deja-vu reads coding-agent session logs from the local disk and builds a local
index. It has no network listener by default (`deja mcp --http <addr>` is an
explicit opt-in listener; non-loopback addresses require `DEJA_MCP_TOKEN`); network access happens only in
`deja update` and `deja doctor` (release metadata from GitHub, no session
data), the once-a-day release check an interactive command starts (the same
metadata; off with `DEJA_OFFLINE=1` or `DEJA_NO_UPDATE_NOTICE=1`), `deja sync
ssh` (your own SSH connection), and `deja embed` and hybrid search, which send
text to the embedding endpoint you configured — normally Ollama or LM Studio on
localhost, and off entirely when you configure none. Reports about secrets surviving redaction in indexed, embedded or shared
output are in scope and appreciated.

See the [security model](docs/SECURITY-MODEL.md) for data flows, redaction
limits, trust assumptions, and release verification.

## Supported versions

Only the latest release receives fixes.
