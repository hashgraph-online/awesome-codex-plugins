# Security Policy

## Reporting a Vulnerability

**Do not file a public GitHub issue for security vulnerabilities.**

Instead, please report security issues responsibly by opening a private [GitHub Security Advisory](https://github.com/epicsagas/alcove/security/advisories/new) or contacting the maintainers directly.

We aim to acknowledge reports within **48 hours** and provide a substantive response within **5 business days**.

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.7.x   | ✅        |
| < 0.7   | ❌        |

Alcove is pre-1.0 software. Only the latest minor release receives security patches.

## Security Model

Alcove is an MCP (Model Context Protocol) server that provides AI agents scoped access to **private project documentation**. Understanding its security boundaries is critical.

### What Alcove Protects

1. **Document isolation** — Each project's documentation is stored in a separate directory. Path traversal attacks are mitigated via vault name validation (`validate_vault_name`) and canonical path checks that ensure resolved paths stay within the configured `docs_root`.

2. **MCP transport** — Alcove communicates over `stdio` by default. When using the HTTP server mode (`alcove serve`), authentication is enforced via a configurable Bearer token with **constant-time comparison** to prevent timing attacks.

3. **CORS restrictions** — The HTTP server restricts allowed origins to `localhost` / `127.0.0.1` only, with strict parsing to prevent bypass via subdomain tricks (e.g. `localhost.evil.com`).

4. **Embedding model data** — Embedding models are downloaded to a configurable cache directory. No document content is sent to external services; all embedding computation is local.

### What Alcove Does NOT Protect Against

- **Local user access** — Any user with local filesystem access can read the documentation store. Alcove is designed for single-user developer machines, not multi-tenant environments.
- **Compromised AI agent** — If an AI agent running on your machine is malicious, it can use Alcove's MCP tools to read any documentation the server has access to. Only connect Alcove to agents you trust.
- **Network exposure** — When running `alcove serve` without a token, anyone on the network can query your documentation. Always set a `--token` when binding to non-loopback interfaces.

## Security Features

### Path Traversal Prevention

All vault operations validate names to reject path separators, parent directory references (`..`), and hidden prefixes (`.`/`_`). File indexing uses `canonicalize()` + `starts_with()` checks to prevent symlink-based escape from the docs root.

### Bearer Token Authentication

The HTTP server supports optional Bearer token authentication:

```bash
alcove serve --port 8080 --token your-secret-token
```

When no token is set, the server logs a warning indicating open access.

### Local-Only Defaults

- Default server host: `127.0.0.1` (loopback only)
- CORS: restricted to `localhost` origins
- MCP: stdio transport (no network exposure)

## Best Practices for Users

1. **Set a token** when using HTTP server mode, especially on shared networks.
2. **Bind to localhost** (the default) unless you have a specific need for remote access.
3. **Review vault links** — symlinked vaults point to external directories. Ensure those directories don't contain sensitive files outside your intended scope.
4. **Don't commit** the alcove doc-repo into public repositories. It contains private project documentation.
5. **Review embedding model downloads** — the `alcove-full` feature downloads ML models at runtime. Verify the cache directory is on a trusted filesystem.

## Dependencies

Alcove is written in Rust and uses a minimal dependency set. Optional features (`alcove-full`, `alcove-server`) pull in additional crates for embedding (`fastembed`), vector storage (`rusqlite`), and HTTP serving (`axum`).

To audit dependencies:

```bash
cargo audit
```

## Disclosure Policy

When a vulnerability is confirmed:

1. A fix is prepared on a private branch.
2. A GitHub Security Advisory is published with a CVE if applicable.
3. The fix is included in the next release, with credit to the reporter (unless anonymity is requested).
