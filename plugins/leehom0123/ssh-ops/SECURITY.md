# Security Policy

## Reporting a Vulnerability

Report vulnerabilities privately through [GitHub Security Advisories](https://github.com/leehom0123/ssh-ops/security/advisories/new). We aim to acknowledge reports within 5 business days and to ship a fix or guidance within 30 days, depending on severity.

## Scope

The supported surface is the CLI (`cli.py`), the MCP server (`mcp_server.py`), and the `ssh_client/` package. Bugs that allow an unintended remote command, credential leakage (private keys, `sudo_password`), or path allow-list escape are treated as security issues.

## Documented limitations

Security-relevant boundaries are specified in the [runtime reference](docs/reference.md); read it before relying on a control:

- Command filtering first rejects blacklist regex matches (`re.search`), then requires a full-command match (`re.fullmatch`) when the whitelist is nonempty, then applies `command_template`. Empty lists impose no filtering. Internal helper commands and `run-script` bypass both filters and the template. Other script invocations are filtered, but script contents are not. Regex filtering is a guardrail, not execution isolation; shell operators can still pass broad patterns.
- Path allow-lists use directory-boundary comparison. Local paths resolve on the client; remote paths are normalized lexically without resolving remote symlinks. Empty lists are unrestricted. These checks cover transfer/text-I/O paths, not arbitrary commands or job directories; they are not a filesystem sandbox.
- Ordinary `sudo` commands feed the configured password through SSH channel stdin to `sudo -S`, not through remote process arguments. The elevated shell redirects command stdin from `/dev/null`, keeping unread passwords out of command input even with cached credentials or NOPASSWD. Bash sudo transfers and text reads stage files under randomly named `/tmp` paths, without exclusive reservation or guaranteed private permissions. Upload installation moves the staged file into place on success; download/read paths attempt removal. Failures can leave staged files behind. Sudo text writes also use a local temporary file.
- Background sudo jobs instead upload `<jobs_dir>/<job_id>/pass` over SFTP; `jobs_dir` defaults to `<scripts_dir>/.jobs`, not `/tmp`. The writer requests mode 0600 only for a newly created file, after writing, and tolerates chmod failures. The wrapper reads the password, attempts deletion, and feeds it to `sudo -S` over stdin. An elevated shell redirects the job's stdin from `/dev/null` before executing it, without overriding sudo's password pipe. Non-sudo jobs also use `/dev/null` for stdin. A failed launch can leave the file behind. Protect staging and job directories with restrictive permissions and umask.
- Login passwords, private-key passphrases (`key_password`), and `sudo_password`, when configured, are plaintext in local YAML files; `sudo_password` falls back to the login password when absent or empty. Restrict file permissions, keep credentials out of version control, and prefer key authentication. MCP error argument summaries redact values under known secret keys, but exception messages and tool output are not scrubbed. Do not embed secrets in command/content strings or assume responses are secret-free.
- Host-key checking defaults to trust on first use (`tofu`). Its separate pre-authentication probe records unknown key types and rejects changed stored keys of the same type; persistence failure only emits a warning. Verify first-use fingerprints independently, or pre-seed checkout-local `known_hosts` and use `strict`. The proxy path also verifies the authenticating transport's own negotiated key with the same rules before any credential is sent, so verification is bound to the authenticated connection, not only to the probe. Direct SSH additionally checks loaded system and checkout-local keys through Paramiko. `insecure` skips the probe and proxy verification but can still reject a loaded-key mismatch on the direct path.
- MCP HTTP defaults to loopback. Binding beyond loopback requires a bearer token, but HTTP is plaintext and the token is a launch argument visible in local process listings. Use an HTTPS reverse proxy or a trusted local connection. Token access grants all service tools; there are no per-user or per-server permissions or Origin checks.

## Supported versions

| Version | Supported |
|---|---|
| 1.x | ✅ |
| < 1.0 | ❌ |
